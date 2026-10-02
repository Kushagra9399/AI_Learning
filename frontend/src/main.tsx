import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import "./style.css";

const API = "http://localhost:8000/api";
const DB_NAME = "rpl_offline_v3";

type Candidate = {
  name: string;
  age: number;
  years_experience: number;
  occupation: string;
  work_context: string;
  prior_training: string;
};

type Task = {
  id: string;
  title: string;
  instructions: string;
  safety: string;
  max_score: number;
  rubric: { criterion: string; weight: number }[];
};

type EvidenceItem = {
  id: string;
  assessment_id: string;
  task_id: string;
  name: string;
  type: string;
  blob: File;
  sync_status: string;
};

function openDB(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, 1);
    request.onupgradeneeded = () => {
      const db = request.result;
      ["packages", "attempts", "evidence"].forEach((name) => {
        if (!db.objectStoreNames.contains(name)) {
          db.createObjectStore(name, { keyPath: "id" });
        }
      });
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

async function put(store: string, value: unknown) {
  const db = await openDB();
  return new Promise<void>((resolve, reject) => {
    const tx = db.transaction(store, "readwrite");
    tx.objectStore(store).put(value);
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
}

async function get<T>(store: string, id: string): Promise<T | undefined> {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(store, "readonly");
    const request = tx.objectStore(store).get(id);
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

async function getAll<T>(store: string): Promise<T[]> {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(store, "readonly");
    const request = tx.objectStore(store).getAll();
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

function App() {
  const [online, setOnline] = useState(navigator.onLine);
  const [stage, setStage] = useState("declare");
  const [candidate, setCandidate] = useState<Candidate>({
    name: "",
    age: 18,
    years_experience: 0,
    occupation: "Construction Electrician",
    work_context: "",
    prior_training: "",
  });
  const [jobId, setJobId] = useState("");
  const [questions, setQuestions] = useState<any[]>([]);
  const [answers, setAnswers] = useState<Record<string, number>>({});
  const [assessmentId, setAssessmentId] = useState("");
  const [tasks, setTasks] = useState<Task[]>([]);
  const [evidence, setEvidence] = useState<Record<string, EvidenceItem[]>>({});
  const [error, setError] = useState("");

  useEffect(() => {
    navigator.serviceWorker?.register("/sw.js").catch(() => undefined);

    const updateNetwork = () => setOnline(navigator.onLine);
    window.addEventListener("online", updateNetwork);
    window.addEventListener("offline", updateNetwork);

    fetch(API + "/practical/tasks")
      .then((response) => response.json())
      .then((data) => setTasks(data.tasks || []))
      .catch(() => undefined);

    return () => {
      window.removeEventListener("online", updateNetwork);
      window.removeEventListener("offline", updateNetwork);
    };
  }, []);

  useEffect(() => {
    if (!jobId || !online) return;

    const timer = window.setInterval(async () => {
      const response = await fetch(API + "/jobs/" + jobId);
      const job = await response.json();

      if (job.status === "completed") {
        await put("packages", {
          id: "construction-electrician",
          questions: job.result.questions,
        });
        setQuestions(job.result.questions);
        setJobId("");
        setStage("test");
      }

      if (job.status === "failed") {
        setError(job.error || "Question generation failed.");
        setJobId("");
      }
    }, 1000);

    return () => window.clearInterval(timer);
  }, [jobId, online]);

  useEffect(() => {
    if (!online) return;

    getAll<any>("attempts")
      .then((attempts) =>
        attempts
          .filter((item) => item.sync_status === "queued")
          .forEach((item) => syncSubmission(item.payload))
      )
      .catch(() => undefined);

    syncEvidence().catch(() => undefined);
  }, [online]);

  async function generatePackage() {
    setError("");

    if (!online) {
      setError("Connect once to download the assessment package.");
      return;
    }

    const mappingResponse = await fetch(API + "/declarations/map", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(candidate),
    });
    const mapping = await mappingResponse.json();

    if (!mapping.qp_code) {
      setError("This demo currently supports Construction Electrician - LV.");
      return;
    }

    const response = await fetch(API + "/jobs/questions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ qp_code: mapping.qp_code, count: 12 }),
    });
    const data = await response.json();

    setJobId(data.job_id);
    setStage("waiting");
  }

  async function useOfflinePackage() {
    const packageData = await get<any>("packages", "construction-electrician");

    if (!packageData) {
      setError("No downloaded assessment package is available offline.");
      return;
    }

    setQuestions(packageData.questions);
    setStage("test");
  }

  async function submitTheory() {
    setError("");

    if (Object.keys(answers).length !== questions.length) {
      setError("Answer every question before the single submission.");
      return;
    }

    const id = "assessment_" + crypto.randomUUID();
    const payload = {
      assessment_id: id,
      candidate_id: candidate.name || "offline-candidate",
      qp_code: "CON/Q0603",
      candidate,
      answers: questions.map((question) => ({
        ...question,
        selected_option: answers[question.id],
      })),
      practical_scores: [],
    };

    await put("attempts", {
      id,
      payload,
      sync_status: online ? "pending" : "queued",
    });

    setAssessmentId(id);
    setStage("practical");

    if (online) {
      await syncSubmission(payload);
    }
  }

  async function syncSubmission(payload: any) {
    try {
      const response = await fetch(API + "/submissions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const result = await response.json();

      if (!result.accepted) {
        setError(result.reason || "Assessment has already been submitted.");
        return false;
      }

      await put("attempts", {
        id: payload.assessment_id,
        payload,
        sync_status: "submitted",
      });

      return true;
    } catch {
      setError("Submission is queued locally until connectivity returns.");
      return false;
    }
  }

  async function captureEvidence(task: Task) {
    if (!assessmentId) {
      setError("Submit the theory assessment first.");
      return;
    }

    const input = document.createElement("input");
    input.type = "file";
    input.accept = "image/*,video/*";
    input.capture = "environment";

    input.onchange = async () => {
      const file = input.files?.[0];
      if (!file) return;

      const item: EvidenceItem = {
        id: "evidence_" + crypto.randomUUID(),
        assessment_id: assessmentId,
        task_id: task.id,
        name: file.name,
        type: file.type,
        blob: file,
        sync_status: "pending",
      };

      await put("evidence", item);
      setEvidence((current) => ({
        ...current,
        [task.id]: [...(current[task.id] || []), item],
      }));

      if (online) await syncEvidence();
    };

    input.click();
  }

  async function syncEvidence() {
    if (!navigator.onLine) return;

    const items = await getAll<EvidenceItem>("evidence");

    for (const item of items.filter((value) => value.sync_status !== "synced")) {
      const form = new FormData();
      form.append("assessment_id", item.assessment_id);
      form.append("task_id", item.task_id);
      form.append("media", item.blob, item.name);

      try {
        await fetch(API + "/evidence", { method: "POST", body: form });
        item.sync_status = "synced";
        await put("evidence", item);
      } catch {
        // Keep the item queued for the next reconnect.
      }
    }
  }

  async function finishSubmission() {
    const saved = await get<any>("attempts", assessmentId);
    if (!saved) return;

    if (online) {
      await syncSubmission(saved.payload);
      setStage("submitted");
    } else {
      await put("attempts", {
        ...saved,
        sync_status: "queued",
      });
      setStage("submitted");
    }
  }

  const assessorId = new URLSearchParams(window.location.search).get("assessor");

  return (
    <main>
      <header>
        <div>
          <strong>RPL Skill Assessment</strong>
          <span>Construction Electrician · NSQF Level 4</span>
        </div>
        <b className={online ? "online" : "offline"}>
          {online ? "Online" : "Offline"}
        </b>
      </header>

      {stage === "declare" && (
        <section>
          <h1>Recognition of Prior Learning</h1>
          <p>
            Structured self-declaration maps prior work experience to the
            qualification framework. AI assists the process; the assessor
            makes the final decision.
          </p>

          <input
            placeholder="Worker name"
            value={candidate.name}
            onChange={(event) =>
              setCandidate({ ...candidate, name: event.target.value })
            }
          />

          <input
            type="number"
            placeholder="Age"
            value={candidate.age}
            onChange={(event) =>
              setCandidate({ ...candidate, age: Number(event.target.value) })
            }
          />

          <input
            type="number"
            placeholder="Years of experience"
            value={candidate.years_experience}
            onChange={(event) =>
              setCandidate({
                ...candidate,
                years_experience: Number(event.target.value),
              })
            }
          />

          <textarea
            placeholder="Work context and tasks performed"
            value={candidate.work_context}
            onChange={(event) =>
              setCandidate({ ...candidate, work_context: event.target.value })
            }
          />

          <textarea
            placeholder="Prior training or certificates"
            value={candidate.prior_training}
            onChange={(event) =>
              setCandidate({
                ...candidate,
                prior_training: event.target.value,
              })
            }
          />

          <button onClick={generatePackage}>Download assessment package</button>

          {!online && (
            <button onClick={useOfflinePackage}>
              Use downloaded package
            </button>
          )}
        </section>
      )}

      {stage === "waiting" && (
        <section>
          <h2>Preparing assessment package</h2>
          <p>
            The question-generation job is running asynchronously.
            Job ID: <code>{jobId}</code>
          </p>
          <p>The completed package will be saved locally for offline use.</p>
        </section>
      )}

      {stage === "test" && (
        <section>
          <h2>Theory assessment</h2>
          <p>One attempt. Answer all questions before submitting.</p>

          {questions.map((question, index) => (
            <article key={question.id}>
              <small>
                {index + 1}. {question.nos_code} / {question.pc_id}
              </small>
              <h3>{question.question}</h3>

              {question.options.map((option: string, optionIndex: number) => (
                <label key={optionIndex}>
                  <input
                    type="radio"
                    name={question.id}
                    checked={answers[question.id] === optionIndex}
                    onChange={() =>
                      setAnswers({
                        ...answers,
                        [question.id]: optionIndex,
                      })
                    }
                  />
                  {option}
                </label>
              ))}
            </article>
          ))}

          <button onClick={submitTheory}>Submit single attempt</button>
        </section>
      )}

      {stage === "practical" && (
        <section>
          <h2>Practical evidence</h2>
          <p>
            Capture evidence for the assessor. Practical scores are never
            entered by the worker.
          </p>

          {tasks.map((task) => (
            <article key={task.id}>
              <h3>
                {task.id} — {task.title}
              </h3>
              <p>{task.instructions}</p>
              <p>
                <strong>Safety:</strong> {task.safety}
              </p>

              <ul>
                {task.rubric.map((criterion) => (
                  <li key={criterion.criterion}>
                    {criterion.criterion} — {criterion.weight} points
                  </li>
                ))}
              </ul>

              <button onClick={() => captureEvidence(task)}>
                Capture photo/video
              </button>

              <small>
                Evidence attached: {(evidence[task.id] || []).length}
              </small>
            </article>
          ))}

          <button onClick={finishSubmission}>Finish submission</button>
        </section>
      )}

      {stage === "submitted" && (
        <section>
          <h2>Assessment submitted</h2>
          <p>
            Assessment ID: <code>{assessmentId}</code>
          </p>
          <p>
            The assessor can now review the declaration, evidence and practical
            rubric.
          </p>

          <a href={"?assessor=" + encodeURIComponent(assessmentId)}>
            <button>Open assessor dashboard</button>
          </a>
        </section>
      )}

      {assessorId && (
        <AssessorDashboard
          assessmentId={assessorId}
          tasks={tasks}
          online={online}
        />
      )}

      {error && <p className="error">{error}</p>}
    </main>
  );
}

function DashboardRouter(){const admin=new URLSearchParams(window.location.search).has("admin");return admin?<AdminDashboard/>:<UserDashboard/>}\n\ncreateRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
