import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import "./style.css";

const API = "http://localhost:8000/api";

type Candidate = {
  name: string;
  age: number;
  years_experience: number;
  occupation: string;
  work_context: string;
  prior_training: string;
};

type Question = {
  id: string;
  type: "mcq" | "text" | "image" | "video";
  question: string;
  options?: string[];
  marks: number;
};

type Job = {
  status: string;
  result?: any;
  error?: string;
};

function useJob(jobId: string) {
  const [job, setJob] = useState<Job | null>(null);

  useEffect(() => {
    if (!jobId) return;

    const timer = window.setInterval(async () => {
      try {
        const response = await fetch(API + "/jobs/" + jobId);
        const data = await response.json();
        setJob(data);

        if (data.status === "completed" || data.status === "failed") {
          window.clearInterval(timer);
        }
      } catch (error) {
        console.error("Job polling failed:", error);
      }
    }, 700);

    return () => window.clearInterval(timer);
  }, [jobId]);

  return job;
}

function WorkerDashboard() {
  const [candidate, setCandidate] = useState<Candidate>({
    name: "",
    age: 25,
    years_experience: 3,
    occupation: "Construction Electrician",
    work_context: "",
    prior_training: "",
  });

  const [assessmentId, setAssessmentId] = useState("");
  const [jobId, setJobId] = useState("");
  const [level, setLevel] = useState<number | null>(null);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [files, setFiles] = useState<Record<string, File>>({});
  const [step, setStep] = useState<"info" | "waiting" | "ready" | "test" | "done">("info");
  const [message, setMessage] = useState("");

  const job = useJob(jobId);

  useEffect(() => {
    if (!job) return;

    if (job.status === "completed") {
      if (job.result?.suggested_level) {
        setLevel(job.result.suggested_level);
        setStep("waiting");
        setMessage("AI NSQF recommendation is ready for administrator review.");
      }

      if (job.result?.questions) {
        setQuestions(job.result.questions);
        setStep("ready");
      }
    }

    if (job.status === "failed") {
      setMessage(job.error || "Backend processing failed.");
    }
  }, [job]);

  async function submitInformation() {
    setMessage("");

    const response = await fetch(API + "/admin/level-suggestion", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(candidate),
    });

    const data = await response.json();

    setAssessmentId(data.assessment_id);
    setJobId(data.job_id);
    setStep("waiting");
  }

  async function checkAssessment() {
    if (!assessmentId) return;

    const response = await fetch(API + "/user/" + assessmentId + "/assessment");
    const data = await response.json();

    if (!data.exists) {
      setMessage("Assessment not found.");
      return;
    }

    if (data.level) {
      setLevel(data.level);
    }

    if (data.questions_approved) {
      setQuestions(data.questions || []);
      setStep("ready");
      setMessage("Assessment approved. You can start your one-time attempt.");
    } else if (data.level_approved) {
      setMessage("NSQF level approved. Waiting for administrator question approval.");
    } else {
      setMessage("Waiting for administrator level approval.");
    }
  }

  async function startAssessment() {
    const response = await fetch(API + "/user/" + assessmentId + "/start", {
      method: "POST",
    });

    const data = await response.json();

    if (!data.accepted) {
      setMessage(data.reason || "Assessment cannot be started.");
      return;
    }

    setStep("test");
    setMessage("Attempt started. This assessment cannot be restarted.");
  }

  async function submitAssessment() {
    setMessage("Uploading evidence and submitting assessment...");

    for (const question of questions) {
      const file = files[question.id];

      if (!file) continue;

      const form = new FormData();
      form.append("assessment_id", assessmentId);
      form.append("task_id", question.id);
      form.append("media", file);

      await fetch(API + "/evidence", {
        method: "POST",
        body: form,
      });
    }

    const payload = {
      assessment_id: assessmentId,
      qp_code: "CON/Q0603",
      nsqf_level: level,
      candidate,
      answers: questions.map((question) => ({
        ...question,
        response: answers[question.id] || "",
        selected_option:
          question.type === "mcq"
            ? Number(answers[question.id])
            : -1,
      })),
      practical_scores: [],
    };

    const response = await fetch(API + "/submissions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const data = await response.json();

    if (!data.accepted) {
      setMessage("Submission failed: " + data.reason);
      return;
    }

    setStep("done");
    setMessage("Assessment submitted successfully.");
  }

  function renderQuestion(question: Question) {
    if (question.type === "mcq") {
      return (
        <div className="question-options">
          {(question.options || []).map((option, index) => (
            <label key={index}>
              <input
                type="radio"
                name={question.id}
                checked={answers[question.id] === String(index)}
                onChange={() =>
                  setAnswers({
                    ...answers,
                    [question.id]: String(index),
                  })
                }
              />
              {option}
            </label>
          ))}
        </div>
      );
    }

    if (question.type === "text") {
      return (
        <textarea
          placeholder="Write your answer"
          value={answers[question.id] || ""}
          onChange={(event) =>
            setAnswers({
              ...answers,
              [question.id]: event.target.value,
            })
          }
        />
      );
    }

    return (
      <>
        <p>
          Upload the evidence requested by the administrator for this
          practical question.
        </p>
        <input
          type="file"
          accept={question.type === "image" ? "image/*" : "video/*"}
          capture="environment"
          onChange={(event) => {
            const file = event.target.files?.[0];
            if (file) {
              setFiles({
                ...files,
                [question.id]: file,
              });
            }
          }}
        />
      </>
    );
  }

  return (
    <Shell title="Worker Dashboard">
      {step === "info" && (
        <section>
          <h1>Recognition of Prior Learning</h1>
          <p>
            Submit your prior work experience. The administrator will review
            the AI-assisted NSQF recommendation.
          </p>

          <input
            placeholder="Name"
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
              setCandidate({
                ...candidate,
                age: Number(event.target.value),
              })
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

          <input
            placeholder="Occupation"
            value={candidate.occupation}
            onChange={(event) =>
              setCandidate({
                ...candidate,
                occupation: event.target.value,
              })
            }
          />

          <textarea
            placeholder="Work performed / skills"
            value={candidate.work_context}
            onChange={(event) =>
              setCandidate({
                ...candidate,
                work_context: event.target.value,
              })
            }
          />

          <textarea
            placeholder="Prior training / certificates"
            value={candidate.prior_training}
            onChange={(event) =>
              setCandidate({
                ...candidate,
                prior_training: event.target.value,
              })
            }
          />

          <button onClick={submitInformation}>
            Submit information
          </button>
        </section>
      )}

      {step === "waiting" && (
        <section>
          <h2>Awaiting Administrator Review</h2>
          <p>
            Assessment ID: <code>{assessmentId}</code>
          </p>
          <p>
            AI suggested NSQF Level:{" "}
            <strong>{level ?? "processing"}</strong>
          </p>
          <button onClick={checkAssessment}>
            Check assessment status
          </button>
        </section>
      )}

      {step === "ready" && (
        <section>
          <h2>Assessment Ready</h2>
          <p>
            NSQF Level: <strong>{level}</strong>
          </p>
          <p>
            Starting the assessment locks your attempt. You cannot restart
            after starting.
          </p>
          <button onClick={startAssessment}>
            Start One-Time Assessment
          </button>
        </section>
      )}

      {step === "test" && (
        <section>
          <h2>Assessment · NSQF Level {level}</h2>

          {questions.map((question) => (
            <article key={question.id} className="question-card">
              <small>
                {question.type.toUpperCase()} · {question.marks} marks
              </small>

              <h3>{question.question}</h3>

              {renderQuestion(question)}
            </article>
          ))}

          <button onClick={submitAssessment}>
            Submit Assessment
          </button>
        </section>
      )}

      {step === "done" && (
        <section>
          <h2>Assessment Submitted</h2>
          <p>{message}</p>
          <p>
            The administrator will review AI evaluation and practical
            image/video evidence.
          </p>
        </section>
      )}

      {message && step !== "done" && (
        <p className="notice">{message}</p>
      )}
    </Shell>
  );
}

function AdminDashboard() {
  const [assessmentId, setAssessmentId] = useState("");
  const [candidate, setCandidate] = useState<Candidate | null>(null);
  const [suggestion, setSuggestion] = useState<any>(null);
  const [level, setLevel] = useState(4);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [jobId, setJobId] = useState("");
  const [message, setMessage] = useState("");

  const job = useJob(jobId);

  useEffect(() => {
    if (!job) return;

    if (job.status === "completed") {
      if (job.result?.suggested_level) {
        setSuggestion(job.result);
        setLevel(job.result.suggested_level);
        setMessage("AI NSQF recommendation is ready for approval.");
      }

      if (job.result?.questions) {
        setQuestions(job.result.questions);
        setMessage("AI question draft is ready for administrator review.");
      }
    }

    if (job.status === "failed") {
      setMessage(job.error || "AI processing failed.");
    }
  }, [job]);

  async function loadCandidate() {
    const response = await fetch(
      API + "/admin/candidate/" + assessmentId
    );
    const data = await response.json();

    if (!data.assessment_id || !data.candidate) {
      setMessage("Candidate not found.");
      return;
    }

    setCandidate(JSON.parse(data.candidate));
    setLevel(data.level || 4);
    setSuggestion(
      data.level_suggestion
        ? JSON.parse(data.level_suggestion)
        : null
    );
    setQuestions(
      data.questions
        ? JSON.parse(data.questions)
        : []
    );
  }

  async function runLevelAnalysis() {
    if (!candidate) return;

    const response = await fetch(API + "/admin/level-suggestion", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(candidate),
    });

    const data = await response.json();

    setAssessmentId(data.assessment_id);
    setJobId(data.job_id);
    setMessage("Groq NSQF level analysis started.");
  }

  async function approveLevel() {
    await fetch(API + "/admin/level-approval", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        assessment_id: assessmentId,
        nsqf_level: level,
        candidate,
        suggestion,
      }),
    });

    setMessage(
      "NSQF level approved. Question generation is now available."
    );
  }

  async function generateQuestions() {
    const response = await fetch(
      API + "/admin/questions/generate",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          assessment_id: assessmentId,
          nsqf_level: level,
          candidate,
          count: 10,
        }),
      }
    );

    const data = await response.json();
    setJobId(data.job_id);
    setMessage("Groq question generation started.");
  }

  async function approveQuestions() {
    await fetch(API + "/admin/questions/approve", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        assessment_id: assessmentId,
        questions,
      }),
    });

    setMessage(
      "Questions and marking scheme approved. Test is now active for the worker."
    );
  }

  function updateQuestion(
    index: number,
    changes: Partial<Question>
  ) {
    const updated = [...questions];
    updated[index] = {
      ...updated[index],
      ...changes,
    };
    setQuestions(updated);
  }

  return (
    <Shell title="Admin Dashboard">
      <section>
        <h1>RPL Administration</h1>

        <div className="toolbar">
          <input
            placeholder="Assessment ID"
            value={assessmentId}
            onChange={(event) =>
              setAssessmentId(event.target.value)
            }
          />
          <button onClick={loadCandidate}>
            Load Candidate
          </button>
        </div>

        {candidate && (
          <>
            <h2>Worker Declaration</h2>
            <pre>{JSON.stringify(candidate, null, 2)}</pre>

            <section className="result">
              <h2>AI NSQF Recommendation</h2>

              {suggestion ? (
                <>
                  <h1>Level {suggestion.suggested_level}</h1>
                  <p>
                    Confidence: {suggestion.confidence}
                  </p>
                  <p>{suggestion.reason}</p>
                </>
              ) : (
                <p>No AI recommendation has been generated yet.</p>
              )}

              <label>
                Administrator Approved Level
                <input
                  type="number"
                  min="1"
                  max="8"
                  value={level}
                  onChange={(event) =>
                    setLevel(Number(event.target.value))
                  }
                />
              </label>

              <button
                onClick={approveLevel}
                disabled={!suggestion}
              >
                Approve Level
              </button>
            </section>

            <button onClick={runLevelAnalysis}>
              Run Groq Level Analysis
            </button>

            <hr />

            <h2>AI Question Generation</h2>

            <p>
              NSQF Level {level} module context will be injected into
              the backend Groq prompt.
            </p>

            <button onClick={generateQuestions}>
              Generate Questions
            </button>

            {questions.length > 0 && (
              <section>
                <h2>Review Questions & Marking Scheme</h2>

                {questions.map((question, index) => (
                  <article
                    key={question.id}
                    className="question-card"
                  >
                    <input
                      value={question.question}
                      onChange={(event) =>
                        updateQuestion(index, {
                          question: event.target.value,
                        })
                      }
                    />

                    <select
                      value={question.type}
                      onChange={(event) =>
                        updateQuestion(index, {
                          type: event.target.value as Question["type"],
                        })
                      }
                    >
                      <option value="mcq">MCQ</option>
                      <option value="text">Text</option>
                      <option value="image">Image</option>
                      <option value="video">Video</option>
                    </select>

                    <input
                      type="number"
                      min="1"
                      max="10"
                      value={question.marks}
                      onChange={(event) =>
                        updateQuestion(index, {
                          marks: Number(event.target.value),
                        })
                      }
                    />

                    <button
                      onClick={() =>
                        setQuestions(
                          questions.filter(
                            (_, questionIndex) =>
                              questionIndex !== index
                          )
                        )
                      }
                    >
                      Delete
                    </button>
                  </article>
                ))}

                <button
                  onClick={() =>
                    setQuestions([
                      ...questions,
                      {
                        id: "q-" + Date.now(),
                        type: "text",
                        question: "New question",
                        options: [],
                        marks: 1,
                      },
                    ])
                  }
                >
                  Add Question
                </button>

                <button onClick={approveQuestions}>
                  Approve & Activate Test
                </button>
              </section>
            )}
          </>
        )}

        {message && <p className="notice">{message}</p>}
      </section>
    </Shell>
  );
}

function Shell({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <main>
      <header>
        <div>
          <strong>{title}</strong>
          <span>AI-Assisted Recognition of Prior Learning</span>
        </div>

        <nav>
          <a href="/">Worker</a>
          {" · "}
          <a href="/?admin=1">Admin</a>
        </nav>
      </header>

      {children}
    </main>
  );
}

function App() {
  const isAdmin = new URLSearchParams(window.location.search).has(
    "admin"
  );

  return isAdmin ? <AdminDashboard /> : <WorkerDashboard />;
}

createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
