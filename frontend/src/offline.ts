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
const API_HEALTH_URL = "http://localhost:8000/api/health";
let syncInProgress = false;

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

async function request<T>(storeName: string, mode: IDBTransactionMode, action: (store: IDBObjectStore) => IDBRequest<T>): Promise<T> {
  const db = await openDb();
  return new Promise((resolve, reject) => {
    const transaction = db.transaction(storeName, mode);
    const store = transaction.objectStore(storeName);
    const operation = action(store);
    operation.onsuccess = () => resolve(operation.result);
    operation.onerror = () => reject(operation.error || new Error("IndexedDB request failed"));
    transaction.onerror = () => reject(transaction.error || new Error("IndexedDB transaction failed"));
    transaction.oncomplete = () => db.close();
  });
}

export function cacheAssessment(userId: number, assessment: any) {
  return request(ASSESSMENTS, "readwrite", store => store.put({ key: String(userId), assessment, updated_at: Date.now() }));
}

export async function getCachedAssessment(userId: number): Promise<any | null> {
  return (await request<any>(ASSESSMENTS, "readonly", store => store.get(String(userId))))?.assessment ?? null;
}

export function saveAnswers(userId: number, assessmentId: string, answers: Record<string, string>) {
  return request(ANSWERS, "readwrite", store => store.put({
    key: `${userId}:${assessmentId}`,
    assessment_id: assessmentId,
    answers,
    updated_at: Date.now(),
  }));
}

export async function getAnswers(userId: number, assessmentId: string): Promise<Record<string, string>> {
  return (await request<any>(ANSWERS, "readonly", store => store.get(`${userId}:${assessmentId}`)))?.answers ?? {};
}

export function saveEvidence(record: {
  evidence_id: string;
  assessment_id: string;
  task_id: string;
  file: Blob;
  filename: string;
  media_type: string;
}) {
  return request(EVIDENCE, "readwrite", store => store.put({ ...record, created_at: Date.now() }));
}

export function getEvidence(evidenceId: string): Promise<any | null> {
  return request<any>(EVIDENCE, "readonly", store => store.get(evidenceId));
}

export async function enqueueOperation(input: Omit<QueueOperation, "queue_id" | "created_at" | "updated_at" | "retry_count" | "status">) {
  const operation: QueueOperation = {
    ...input,
    queue_id: `${input.operation_type}_${input.assessment_id}_${crypto.randomUUID()}`,
    created_at: Date.now(),
    updated_at: Date.now(),
    retry_count: 0,
    status: "pending",
  };
  await request(QUEUE, "readwrite", store => store.put(operation));
  return operation;
}

async function allQueueItems(): Promise<QueueOperation[]> {
  return (await request<QueueOperation[]>(QUEUE, "readonly", store => store.getAll())) || [];
}

function updateQueue(operation: QueueOperation) {
  return request(QUEUE, "readwrite", store => store.put(operation));
}

export async function getQueueStatus(assessmentId: string): Promise<SyncStatus | null> {
  const items = (await allQueueItems()).filter(item => item.assessment_id === assessmentId && item.status !== "synced");
  if (!items.length) return null;
  if (items.some(item => item.status === "syncing")) return "syncing";
  if (items.some(item => item.status === "failed")) return "failed";
  return "pending";
}

async function backendReachable(): Promise<boolean> {
  if (typeof navigator !== "undefined" && navigator.onLine === false) return false;
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), 3000);
  try {
    const response = await fetch(API_HEALTH_URL, {
      method: "GET",
      cache: "no-store",
      signal: controller.signal,
    });
    return response.ok;
  } catch {
    return false;
  } finally {
    window.clearTimeout(timeout);
  }
}

export async function syncPendingOperations(sender: (operation: QueueOperation) => Promise<void>) {
  if (syncInProgress) return { synced: 0, pending: 0 };
  if (!(await backendReachable())) {
    console.log("[SYNC] network/backend unavailable; queue remains pending");
    return { synced: 0, pending: 0 };
  }

  syncInProgress = true;
  try {
    const now = Date.now();
    const existing = await allQueueItems();
    // A tab/browser crash can leave an operation in "syncing" forever.
    for (const stale of existing) {
      if (stale.status === "syncing" && now - stale.updated_at > 30000) {
        stale.status = "pending";
        stale.updated_at = now;
        await updateQueue(stale);
      }
    }

    const operations = (await allQueueItems())
    .filter(item => (item.status === "pending" || item.status === "failed") && (!item.next_retry_at || item.next_retry_at <= Date.now()))
    .sort((a, b) => a.created_at - b.created_at);

    let synced = 0;
    let pending = 0;

    for (const operation of operations) {
      if (!(await backendReachable())) break;
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
      if (!(await backendReachable())) break;
    }

    return { synced, pending };
  } finally {
    syncInProgress = false;
  }
}

export function registerOfflineSync(sender: (operation: QueueOperation) => Promise<void>) {
  const attempt = () => {
    if (navigator.onLine === false) {
      console.log("[SYNC] browser offline; not attempting synchronization");
      return;
    }
    void syncPendingOperations(sender).catch(error => console.warn("[SYNC] queue processing failed", error));
  };
  window.addEventListener("online", attempt);
  return () => window.removeEventListener("online", attempt);
}
