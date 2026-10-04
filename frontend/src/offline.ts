export type SyncStatus = "pending" | "syncing" | "synced" | "failed";

export type QueueOperation = {
  queue_id: string;
  assessment_id: string;
  operation_type: "profile" | "submission" | "evidence";
  payload: any;
  created_at: number;
  updated_at: number;
  retry_count: number;
  status: SyncStatus;
  last_error?: string;
  next_retry_at?: number;
};

const DB_NAME = "rpl-offline";
const DB_VERSION = 1;
const QUEUE = "sync_queue";
const ASSESSMENTS = "assessments";
const ANSWERS = "answers";
const EVIDENCE = "evidence";

function openDb(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);
    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains(QUEUE)) db.createObjectStore(QUEUE, { keyPath: "queue_id" });
      if (!db.objectStoreNames.contains(ASSESSMENTS)) db.createObjectStore(ASSESSMENTS, { keyPath: "key" });
      if (!db.objectStoreNames.contains(ANSWERS)) db.createObjectStore(ANSWERS, { keyPath: "key" });
      if (!db.objectStoreNames.contains(EVIDENCE)) db.createObjectStore(EVIDENCE, { keyPath: "evidence_id" });
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error || new Error("Unable to open offline storage"));
  });
}

function tx(storeName: string, mode: IDBTransactionMode): Promise<IDBObjectStore> {
  return openDb().then(db => new Promise((resolve, reject) => {
    const transaction = db.transaction(storeName, mode);
    transaction.oncomplete = () => db.close();
    transaction.onerror = () => reject(transaction.error || new Error("IndexedDB transaction failed"));
    resolve(transaction.objectStore(storeName));
  }));
}

export async function cacheAssessment(userId: number, assessment: any) {
  const store = await tx(ASSESSMENTS, "readwrite");
  return new Promise<void>((resolve, reject) => {
    const request = store.put({ key: String(userId), assessment, updated_at: Date.now() });
    request.onsuccess = () => resolve();
    request.onerror = () => reject(request.error);
  });
}

export async function getCachedAssessment(userId: number): Promise<any | null> {
  const store = await tx(ASSESSMENTS, "readonly");
  return new Promise((resolve, reject) => {
    const request = store.get(String(userId));
    request.onsuccess = () => resolve(request.result?.assessment ?? null);
    request.onerror = () => reject(request.error);
  });
}

export async function saveAnswers(userId: number, assessmentId: string, answers: Record<string, string>) {
  const store = await tx(ANSWERS, "readwrite");
  return new Promise<void>((resolve, reject) => {
    const request = store.put({ key: String(userId), assessment_id: assessmentId, answers, updated_at: Date.now() });
    request.onsuccess = () => resolve();
    request.onerror = () => reject(request.error);
  });
}

export async function getAnswers(userId: number): Promise<Record<string, string>> {
  const store = await tx(ANSWERS, "readonly");
  return new Promise((resolve, reject) => {
    const request = store.get(String(userId));
    request.onsuccess = () => resolve(request.result?.answers ?? {});
    request.onerror = () => reject(request.error);
  });
}

export async function saveEvidence(record: {
  evidence_id: string;
  assessment_id: string;
  task_id: string;
  file: Blob;
  filename: string;
  media_type: string;
}) {
  const store = await tx(EVIDENCE, "readwrite");
  return new Promise<void>((resolve, reject) => {
    const request = store.put({ ...record, created_at: Date.now() });
    request.onsuccess = () => resolve();
    request.onerror = () => reject(request.error);
  });
}

export async function getEvidence(evidenceId: string): Promise<any | null> {
  const store = await tx(EVIDENCE, "readonly");
  return new Promise((resolve, reject) => {
    const request = store.get(evidenceId);
    request.onsuccess = () => resolve(request.result ?? null);
    request.onerror = () => reject(request.error);
  });
}

export async function enqueueOperation(input: Omit<QueueOperation, "queue_id" | "created_at" | "updated_at" | "retry_count" | "status">) {
  const now = Date.now();
  const operation: QueueOperation = {
    ...input,
    queue_id: `${input.operation_type}_${input.assessment_id}_${crypto.randomUUID()}`,
    created_at: now,
    updated_at: now,
    retry_count: 0,
    status: "pending",
  };
  const store = await tx(QUEUE, "readwrite");
  return new Promise<QueueOperation>((resolve, reject) => {
    const request = store.put(operation);
    request.onsuccess = () => resolve(operation);
    request.onerror = () => reject(request.error);
  });
}

async function allQueueItems(): Promise<QueueOperation[]> {
  const store = await tx(QUEUE, "readonly");
  return new Promise((resolve, reject) => {
    const request = store.getAll();
    request.onsuccess = () => resolve(request.result as QueueOperation[]);
    request.onerror = () => reject(request.error);
  });
}

async function updateQueue(operation: QueueOperation) {
  const store = await tx(QUEUE, "readwrite");
  return new Promise<void>((resolve, reject) => {
    const request = store.put(operation);
    request.onsuccess = () => resolve();
    request.onerror = () => reject(request.error);
  });
}

export async function getQueueStatus(assessmentId: string): Promise<SyncStatus | null> {
  const items = (await allQueueItems()).filter(item => item.assessment_id === assessmentId && item.status !== "synced");
  if (!items.length) return null;
  if (items.some(item => item.status === "syncing")) return "syncing";
  if (items.some(item => item.status === "failed")) return "failed";
  return "pending";
}

export async function syncPendingOperations(
  sender: (operation: QueueOperation) => Promise<void>
): Promise<{ synced: number; pending: number }> {
  if (typeof navigator !== "undefined" && navigator.onLine === false) {
    return { synced: 0, pending: 0 };
  }

  const now = Date.now();
  const operations = (await allQueueItems())
    .filter(item => (item.status === "pending" || item.status === "failed") && (!item.next_retry_at || item.next_retry_at <= now))
    .sort((a, b) => a.created_at - b.created_at);

  let synced = 0;
  let pending = 0;

  for (const operation of operations) {
    if (typeof navigator !== "undefined" && navigator.onLine === false) break;

    operation.status = "syncing";
    operation.updated_at = Date.now();
    await updateQueue(operation);

    try {
      await sender(operation);
      operation.status = "synced";
      operation.last_error = undefined;
      operation.next_retry_at = undefined;
      operation.updated_at = Date.now();
      await updateQueue(operation);
      synced += 1;
    } catch (error) {
      operation.status = "pending";
      operation.retry_count += 1;
      operation.last_error = error instanceof Error ? error.message : String(error);
      operation.next_retry_at = Date.now() + Math.min(60000, 1000 * Math.pow(2, Math.min(operation.retry_count - 1, 6)));
      operation.updated_at = Date.now();
      await updateQueue(operation);
      pending += 1;
      console.warn("[SYNC] retry scheduled", operation.assessment_id, operation.operation_type, operation.last_error);
      if (typeof navigator !== "undefined" && navigator.onLine === false) break;
    }
  }

  return { synced, pending };
}

export function registerOfflineSync(sender: (operation: QueueOperation) => Promise<void>) {
  const attempt = () => {
    void syncPendingOperations(sender).catch(error => console.warn("[SYNC] queue processing failed", error));
  };
  window.addEventListener("online", attempt);
  attempt();
  return () => window.removeEventListener("online", attempt);
}
