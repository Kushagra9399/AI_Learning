import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import "./style.css";

const API = "http://localhost:8000/api";
const NSQF_LEVELS = [1, 2, 2.5, 3, 3.5, 4, 4.5, 5, 5.5, 6, 6.5, 7, 8] as const;
type NsqfLevel = typeof NSQF_LEVELS[number];
const TOKEN_KEY = "rpl_access_token";

type Role = "admin" | "worker";

type User = {
  id: number;
  username: string;
  role: Role;
};

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

type Assessment = {
  assessment_id: string;
  candidate: Candidate;
  level: number | null;
  level_suggestion?: any;
  level_approved: boolean;
  questions_draft?: Question[] | null;
  questions?: Question[] | null;
  questions_approved: boolean;
  started: boolean;
  submitted?: boolean;
  submitted_at?: string | null;
  submission?: any;
  evidence?: any[];
  grading?: { items?: any[]; total_marks?: number; max_marks?: number; locked?: boolean; locked_at?: string } | null;
  marks_locked?: boolean;
  marks_locked_at?: string | null;
};

function token() {
  return localStorage.getItem(TOKEN_KEY);
}

async function api(path: string, options: RequestInit = {}) {
  const headers = new Headers(options.headers);
  const accessToken = token();
  if (accessToken) headers.set("Authorization", `Bearer ${accessToken}`);
  if (options.body && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(API + path, { ...options, headers, cache: "no-store" });
  if (response.status === 401) {
    localStorage.removeItem(TOKEN_KEY);
    window.location.reload();
  }
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || data.reason || "Request failed");
  return data;
}

function Login({ onLogin }: { onLogin: (user: User) => void }) {
  const [mode, setMode] = useState<"signin" | "signup">("signin");
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [dob, setDob] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  function resetForm() {
    setName(""); setPhone(""); setDob(""); setPassword("");
    setError(""); setMessage("");
  }

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setLoading(true); setError(""); setMessage("");
    try {
      const payload = mode === "signup"
        ? { name: name.trim(), phone: phone.trim(), dob, password }
        : { name: name.trim(), password };
      if (mode === "signup") {
        const response = await fetch(API + "/auth/signup", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        const data = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(data.detail || "Unable to create worker account");
        setMessage("Worker account created. Sign in with your registered details.");
        setMode("signin");
        setPassword("");
        return;
      }

      const response = await fetch(API + "/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(data.detail || "Invalid sign-in details");
      localStorage.setItem(TOKEN_KEY, data.access_token);
      onLogin(data.user);
    } catch (error) {
      setError(error instanceof Error ? error.message : "Authentication failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="auth-page">
      <section className="auth-card">
        <div className="brand-mark">RPL</div>
        <h1>Recognition of Prior Learning</h1>
        <p className="muted">AI-assisted skill assessment platform</p>
        <div className="auth-tabs">
          <button type="button" className={mode === "signin" ? "active" : ""} onClick={() => { resetForm(); setMode("signin"); }}>Sign in</button>
          <button type="button" className={mode === "signup" ? "active" : ""} onClick={() => { resetForm(); setMode("signup"); }}>Worker sign up</button>
        </div>
        <form onSubmit={submit}>
          <label>Full name<input value={name} onChange={e => setName(e.target.value)} autoComplete="name" required /></label>
          {mode === "signup" && <>
            <label>Phone number<input type="tel" value={phone} onChange={e => setPhone(e.target.value)} autoComplete="tel" required /></label>
            <label>Date of birth<input type="date" value={dob} onChange={e => setDob(e.target.value)} autoComplete="bday" required /></label>
          </>}
          <label>Password<input type="password" value={password} onChange={e => setPassword(e.target.value)} autoComplete={mode === "signup" ? "new-password" : "current-password"} required /></label>
          {error && <p className="error">{error}</p>}
          {message && <p className="notice">{message}</p>}
          <button disabled={loading}>{loading ? (mode === "signup" ? "Creating account..." : "Signing in...") : (mode === "signup" ? "Create worker account" : "Sign in")}</button>
        </form>
        <p className="auth-help">
          {mode === "signin"
            ? "Workers can create an account from Worker sign up. Administrator accounts are provisioned separately."
            : "Worker registration is open here. Administrator accounts cannot be created from this page."}
        </p>
      </section>
    </main>
  );
}

function navigate(path: string) {
  window.history.pushState({}, "", path);
  window.dispatchEvent(new PopStateEvent("popstate"));
}

function Shell({ user, children, onLogout }: { user: User; children: React.ReactNode; onLogout: () => void }) {
  const [route, setRoute] = useState(window.location.pathname);
  useEffect(() => {
    const handler = () => setRoute(window.location.pathname);
    window.addEventListener("popstate", handler);
    return () => window.removeEventListener("popstate", handler);
  }, []);

  const links = user.role === "admin"
    ? [["/admin/dashboard", "Overview"], ["/admin/assessments", "Assessments"], ["/admin/submissions", "Submissions"]]
    : [["/worker/dashboard", "Overview"], ["/worker/profile", "My Profile"], ["/worker/assessment", "Assessment"], ["/worker/submission", "Submission"]];

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand"><div className="brand-mark small">RPL</div><div><strong>RPL Portal</strong><small>{user.role === "admin" ? "Administrator" : "Worker"}</small></div></div>
        <nav>{links.map(([path, label]) => <button key={path} className={route === path ? "nav-item active" : "nav-item"} onClick={() => navigate(path)}>{label}</button>)}</nav>
        <div className="sidebar-bottom"><span>{user.username}</span><button className="secondary" onClick={onLogout}>Sign out</button></div>
      </aside>
      <section className="content"><header className="mobile-top"><strong>RPL Portal</strong><span>{user.role}</span></header>{children}</section>
    </main>
  );
}

function WorkerDeclaration({candidate,setCandidate,onSubmit}:{candidate:Candidate;setCandidate:React.Dispatch<React.SetStateAction<Candidate>>;onSubmit:()=>void}) {
  return <><div className="form-grid">
    <label>Name<input value={candidate.name} onChange={e=>setCandidate({...candidate,name:e.target.value})}/></label>
    <label>Age<input type="number" value={candidate.age} onChange={e=>setCandidate({...candidate,age:Number(e.target.value)})}/></label>
    <label>Years of experience<input type="number" value={candidate.years_experience} onChange={e=>setCandidate({...candidate,years_experience:Number(e.target.value)})}/></label>
    <label>Occupation<input value={candidate.occupation} onChange={e=>setCandidate({...candidate,occupation:e.target.value})}/></label>
  </div>
  <label>Work performed / skills<textarea value={candidate.work_context} onChange={e=>setCandidate({...candidate,work_context:e.target.value})}/></label>
  <label>Prior training / certificates<textarea value={candidate.prior_training} onChange={e=>setCandidate({...candidate,prior_training:e.target.value})}/></label>
  <button onClick={onSubmit}>Submit declaration</button></>;
}

function WorkerDashboard({ user, onLogout }: { user: User; onLogout: () => void }) {
  const [route, setRoute] = useState(window.location.pathname);
  useEffect(() => {
    const handler = () => setRoute(window.location.pathname);
    window.addEventListener("popstate", handler);
    return () => window.removeEventListener("popstate", handler);
  }, []);
  const [assessment, setAssessment] = useState<Assessment | null>(null);
  const [candidate, setCandidate] = useState<Candidate>({
    name: "", age: 25, years_experience: 3,
    occupation: "Construction Electrician",
    work_context: "", prior_training: "",
  });
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [files, setFiles] = useState<Record<string, File>>({});
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [workerResult, setWorkerResult] = useState<any>(null);

  async function load() {
    try {
      const data = await api("/worker/assessment");
      if (data.exists) {
        setAssessment(data);
        if (data.candidate) setCandidate(data.candidate);
        if (data.exists && data.assessment_id) {
          try { setWorkerResult(await api(`/worker/assessment/${data.assessment_id}/result`)); } catch { setWorkerResult(null); }
        }
      }
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Unable to load assessment");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    const timer = window.setInterval(load, 2000);
    return () => window.clearInterval(timer);
  }, []);

  async function createAssessment() {
    setMessage("Submitting worker declaration...");
    try {
      const data = await api("/worker/assessment", { method: "POST", body: JSON.stringify(candidate) });
      await load();
      setMessage(data.existing ? "Your existing assessment was restored." : "Declaration submitted. Awaiting administrator review.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Unable to submit declaration");
    }
  }

  async function start() {
    if (!assessment) return;
    try {
      await api(`/worker/assessment/${assessment.assessment_id}/start`, { method: "POST" });
      await load();
      setMessage("Assessment started. Your attempt is locked to one submission.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Unable to start assessment");
    }
  }

  async function submit() {
    if (!assessment) return;
    setMessage("Uploading evidence and submitting...");
    try {
      for (const question of assessment.questions || []) {
        const file = files[question.id];
        if (!file) continue;
        const form = new FormData();
        form.append("assessment_id", assessment.assessment_id);
        form.append("task_id", question.id);
        form.append("media", file);
        await api("/evidence", { method: "POST", body: form });
      }

      const payload = {
        assessment_id: assessment.assessment_id,
        qp_code: "CON/Q0603",
        nsqf_level: assessment.level,
        candidate,
        answers: (assessment.questions || []).map(question => ({
          ...question,
          response: answers[question.id] || "",
          selected_option: question.type === "mcq" ? Number(answers[question.id]) : -1,
        })),
        practical_scores: [],
      };
      await api("/submissions", { method: "POST", body: JSON.stringify(payload) });
      await load();
      setMessage("Assessment submitted successfully.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Submission failed");
    }
  }

  if (loading) return <Shell user={user} onLogout={onLogout}><section className="panel"><p>Loading your assessment...</p></section></Shell>;

  const questions = assessment?.questions || [];
  const hasSubmitted = assessment?.submitted;

  const page = route;
  if (assessment && page === "/worker/profile") {
    return <Shell user={user} onLogout={onLogout}>
      <section className="page-heading"><p className="eyebrow">MY PROFILE</p><h1>{candidate.name || "Worker profile"}</h1><p className="muted">Your persisted worker information.</p></section>
      <section className="panel"><div className="form-grid">
        <label>Name<input value={candidate.name} readOnly /></label><label>Age<input value={candidate.age} readOnly /></label>
        <label>Years of experience<input value={candidate.years_experience} readOnly /></label><label>Occupation<input value={candidate.occupation} readOnly /></label>
      </div><label>Work performed / skills<textarea value={candidate.work_context} readOnly /></label><label>Prior training / certificates<textarea value={candidate.prior_training} readOnly /></label></section>
    </Shell>;
  }
  if (assessment && page === "/worker/submission") {
    return <Shell user={user} onLogout={onLogout}>
      <section className="page-heading"><p className="eyebrow">SUBMISSION</p><h1>Assessment submission</h1><p className="muted">Your final attempt and current workflow status.</p></section>
      <section className="panel">{assessment.submitted ? <><div className="status-banner success"><strong>Assessment submitted</strong><span>{assessment.submitted_at ? new Date(assessment.submitted_at).toLocaleString() : ""}</span></div>{workerResult?.locked && <div className="score-card"><span>Final score</span><strong>{workerResult.total_marks} / {workerResult.max_marks}</strong><small>Marks locked by administrator</small></div>}{(assessment.submission?.answers || []).map((q:any,i:number)=><article className="question-card" key={q.id || i}><div className="question-meta">QUESTION {i+1}</div><h3>{q.question}</h3><p><strong>Response:</strong> {q.options?.length ? (q.selected_option >= 0 ? q.options[q.selected_option] : "Not answered") : (q.response || "Not answered")}</p></article>)}</> : <p className="muted">You have not submitted your assessment.</p>}</section>
    </Shell>;
  }
  if (assessment && page === "/worker/assessment") {
    return <Shell user={user} onLogout={onLogout}>
      <section className="page-heading"><p className="eyebrow">ASSESSMENT</p><h1>NSQF Level {assessment.level ?? "Pending"}</h1><p className="muted">Complete your approved assessment.</p></section>
      {!assessment.level_approved && <section className="panel"><h2>Awaiting approval</h2><p>The administrator has not approved your level yet.</p></section>}
      {assessment.level_approved && !assessment.questions_approved && <section className="panel"><h2>Questions being prepared</h2><p>Your level is locked. The administrator is reviewing your question package.</p></section>}
      {assessment.questions_approved && !assessment.started && !assessment.submitted && <section className="panel"><h2>Assessment ready</h2><p>Your approved assessment is ready.</p><button onClick={start}>Start assessment</button></section>}
      {assessment.started && !assessment.submitted && <section className="panel">{questions.map(question => <article className="question-card" key={question.id}><div className="question-meta">{question.type.toUpperCase()} · {question.marks} marks</div><h3>{question.question}</h3>{question.type === "mcq" ? (question.options || []).map((option,i)=><label className="option" key={i}><input type="radio" name={question.id} checked={answers[question.id]===String(i)} onChange={()=>setAnswers({...answers,[question.id]:String(i)})}/>{option}</label>) : question.type === "text" ? <textarea value={answers[question.id] || ""} onChange={e=>setAnswers({...answers,[question.id]:e.target.value})}/> : <input type="file" accept={question.type === "image" ? "image/*" : "video/*"} onChange={e=>{const f=e.target.files?.[0];if(f)setFiles({...files,[question.id]:f})}}/>}</article>)}<button onClick={submit}>Submit assessment</button></section>}
      {assessment.submitted && workerResult?.locked && <section className="panel"><div className="score-card"><span>Final assessment score</span><strong>{workerResult.total_marks} / {workerResult.max_marks}</strong><small>Finalized and locked by the administrator</small></div></section>}
    </Shell>;
  }
  if (!assessment) return <Shell user={user} onLogout={onLogout}><section className="page-heading"><p className="eyebrow">WORKER PORTAL</p><h1>My profile</h1><p className="muted">Submit your prior experience and training for administrator review.</p></section><section className="panel"><WorkerDeclaration candidate={candidate} setCandidate={setCandidate} onSubmit={createAssessment}/></section>{message && <p className="notice">{message}</p>}</Shell>;

  return (
    <Shell user={user} onLogout={onLogout}>
      <section className="page-heading"><p className="eyebrow">WORKER PORTAL</p><h1>Overview</h1><p className="muted">Track your RPL assessment from declaration through submission.</p></section><p className="muted">Your progress is saved on the server and will remain available after refresh.</p>

      {!assessment && (
        <section className="panel">
          <h2>Worker declaration</h2>
          <p className="muted">Provide your prior experience and training. An administrator will review the AI-assisted NSQF recommendation.</p>
          <div className="form-grid">
            <label>Name<input value={candidate.name} onChange={e => setCandidate({...candidate, name:e.target.value})} /></label>
            <label>Age<input type="number" value={candidate.age} onChange={e => setCandidate({...candidate, age:Number(e.target.value)})} /></label>
            <label>Years of experience<input type="number" value={candidate.years_experience} onChange={e => setCandidate({...candidate, years_experience:Number(e.target.value)})} /></label>
            <label>Occupation<input value={candidate.occupation} onChange={e => setCandidate({...candidate, occupation:e.target.value})} /></label>
          </div>
          <label>Work performed / skills<textarea value={candidate.work_context} onChange={e => setCandidate({...candidate, work_context:e.target.value})} /></label>
          <label>Prior training / certificates<textarea value={candidate.prior_training} onChange={e => setCandidate({...candidate, prior_training:e.target.value})} /></label>
          <button onClick={createAssessment}>Submit declaration</button>
        </section>
      )}

      {assessment && (
        <>
          <section className="status-grid">
            <div className="status-card"><span>Assessment</span><strong>{assessment.assessment_id}</strong></div>
            <div className="status-card"><span>NSQF level</span><strong>{assessment.level ?? assessment.level_suggestion?.suggested_level ?? "Pending"}</strong></div>
            <div className="status-card"><span>Level approval</span><strong>{assessment.level_approved ? "Approved" : "Pending"}</strong></div>
            <div className="status-card"><span>Questions</span><strong>{assessment.questions_approved ? "Active" : "Pending approval"}</strong></div>
          </section>

          {!assessment.level_approved && <section className="panel"><h2>Awaiting administrator review</h2><p>{assessment.level_suggestion ? `AI recommendation: Level ${assessment.level_suggestion.suggested_level}. The administrator must approve it before the assessment can proceed.` : "AI analysis is being processed. This page checks the persisted assessment automatically."}</p></section>}

          {assessment.level_approved && !assessment.questions_approved && <section className="panel"><h2>Questions are being prepared</h2><p>The approved NSQF level is locked. The administrator is reviewing the generated questions.</p></section>}

          {assessment.questions_approved && !assessment.started && !hasSubmitted && <section className="panel"><h2>Assessment ready</h2><p>Your administrator has approved the assessment package for NSQF Level {assessment.level}.</p><button onClick={start}>Start assessment</button></section>}

          {assessment.started && !hasSubmitted && <section className="panel"><h2>Assessment · Level {assessment.level}</h2>{questions.map(question => (
            <article className="question-card" key={question.id}>
              <div className="question-meta">{question.type.toUpperCase()} · {question.marks} marks</div>
              <h3>{question.question}</h3>
              {question.type === "mcq" ? (question.options || []).map((option, i) => <label className="option" key={i}><input type="radio" name={question.id} checked={answers[question.id] === String(i)} onChange={() => setAnswers({...answers,[question.id]:String(i)})} />{option}</label>) : question.type === "text" ? <textarea value={answers[question.id] || ""} onChange={e => setAnswers({...answers,[question.id]:e.target.value})} placeholder="Write your answer" /> : <input type="file" accept={question.type === "image" ? "image/*" : "video/*"} onChange={e => { const file=e.target.files?.[0]; if(file) setFiles({...files,[question.id]:file}); }} />}
            </article>
          ))}<button onClick={submit}>Submit assessment</button></section>}

          {hasSubmitted && <section className="panel success"><h2>Assessment submitted</h2><p>Your one-time attempt has been recorded. Further review is handled by the administrator.</p>{workerResult?.locked && <div className="score-card"><span>Final score</span><strong>{workerResult.total_marks} / {workerResult.max_marks}</strong><small>Marks have been finalized by the administrator.</small></div>}</section>}
        </>
      )}
      {message && <p className="notice">{message}</p>}
    </Shell>
  );
}

function AdminDashboard({ user, onLogout }: { user: User; onLogout: () => void }) {
  const [route,setRoute]=useState(window.location.pathname);
  const [detailTab,setDetailTab]=useState<"worker"|"questions"|"answers">("worker");
  useEffect(()=>{const h=()=>setRoute(window.location.pathname);window.addEventListener("popstate",h);return()=>window.removeEventListener("popstate",h)},[]);
  const [assessments, setAssessments] = useState<any[]>([]);
  const [selected, setSelected] = useState<Assessment | null>(null);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [message, setMessage] = useState("");
  const [jobId, setJobId] = useState("");
  const [gradingMarks, setGradingMarks] = useState<Record<string, number>>({});
  const [selectedLevel, setSelectedLevel] = useState<NsqfLevel | "">("");

  async function loadList() {
    try { setAssessments(await api("/admin/assessments")); }
    catch (error) { setMessage(error instanceof Error ? error.message : "Unable to load assessments"); }
  }

  async function loadAssessment(id: string) {
    try {
      const data = await api(`/admin/candidate/${id}`);
      setSelected(data);
      setQuestions(data.questions_draft || data.questions || []);

      // Approval state comes only from the persisted backend flag.
      // Before approval, the AI recommendation is the default dropdown value.
      if (data.level_approved && data.level != null && NSQF_LEVELS.includes(Number(data.level) as NsqfLevel)) {
        setSelectedLevel(Number(data.level) as NsqfLevel);
      } else if (!data.level_approved && data.level_suggestion?.suggested_level != null && NSQF_LEVELS.includes(Number(data.level_suggestion.suggested_level) as NsqfLevel)) {
        setSelectedLevel(Number(data.level_suggestion.suggested_level) as NsqfLevel);
      } else {
        setSelectedLevel("");
      }
    } catch (error) { setMessage(error instanceof Error ? error.message : "Unable to load assessment"); }
  }

  useEffect(() => {
    loadList();
    const timer = window.setInterval(loadList, 3000);
    return () => window.clearInterval(timer);
  }, []);

  useEffect(() => {
    if (!jobId) return;
    const timer = window.setInterval(async () => {
      try {
        const job = await api(`/jobs/${jobId}`);
        if (job.status === "completed") {
          clearInterval(timer);
          await loadAssessment(job.result.assessment_id);
          setMessage("AI question draft generated and persisted. Review it before approval.");
        } else if (job.status === "failed") {
          clearInterval(timer);
          setMessage(job.error || "AI processing failed");
        }
      } catch (error) {
        clearInterval(timer);
        setMessage(error instanceof Error ? error.message : "Job polling failed");
      }
    }, 1000);
    return () => clearInterval(timer);
  }, [jobId]);

  async function regenerateLevel() {
    if (!selected || selected.level_approved) return;
    try {
      const data = await api(`/admin/assessments/${selected.assessment_id}/level-suggestion`, {method:"POST"});
      setJobId(data.job_id);
      setMessage("AI level recommendation started.");
    } catch (error) { setMessage(error instanceof Error ? error.message : "Unable to start analysis"); }
  }

  async function approveLevel() {
    if (!selected || selected.level_approved) return;
    const level = selectedLevel;
    if (level === "") return;
    try {
      await api("/admin/level-approval", {method:"POST",body:JSON.stringify({
        assessment_id:selected.assessment_id, nsqf_level:level, suggestion:selected.level_suggestion
      })});
      await loadAssessment(selected.assessment_id);
      await loadList();
      setMessage("NSQF level approved and locked. AI recommendations can no longer be generated for this assessment.");
    } catch (error) { setMessage(error instanceof Error ? error.message : "Unable to approve level"); }
  }

  async function unlockLevel() {
    if (!selected || !selected.level_approved) return;
    try {
      await api(`/admin/assessments/${selected.assessment_id}/level-unlock`, { method: "POST" });
      await loadAssessment(selected.assessment_id);
      await loadList();
      setMessage("NSQF level unlocked. The dropdown is editable again and the AI recommendation can be regenerated.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Unable to unlock level");
    }
  }

  async function generateQuestions() {
    if (!selected || !selected.level_approved || selected.questions_approved) return;
    try {
      const data = await api("/admin/questions/generate", {method:"POST",body:JSON.stringify({assessment_id:selected.assessment_id,count:10})});
      setJobId(data.job_id);
      setMessage("Question generation started.");
    } catch (error) { setMessage(error instanceof Error ? error.message : "Unable to generate questions"); }
  }

  async function approveQuestions() {
    if (!selected || selected.questions_approved || !questions.length) return;
    try {
      // Persist the current admin edits first. Approval itself reads only from DB.
      await api("/admin/questions/draft", {method:"POST",body:JSON.stringify({assessment_id:selected.assessment_id,questions})});
      const approved = await api("/admin/questions/approve", {method:"POST",body:JSON.stringify({assessment_id:selected.assessment_id})});
      await loadAssessment(selected.assessment_id);
      if (approved.questions) setQuestions(approved.questions);
      await loadList();
      setMessage("Question package approved and activated for the worker.");
    } catch (error) { setMessage(error instanceof Error ? error.message : "Unable to approve questions"); }
  }

  function answerFor(questionId: string) {
    return selected?.submission?.answers?.find((a:any) => String(a.id) === String(questionId));
  }

  function objectiveStatus(question: Question) {
    if (question.type !== "mcq") return null;
    const answer = answerFor(question.id);
    if (!answer || answer.selected_option === undefined || Number(answer.selected_option) < 0) return "unanswered";
    return Number(answer.selected_option) === Number((question as any).correct_option) ? "correct" : "incorrect";
  }

  async function lockGrading() {
    if (!selected || !selected.submitted || selected.marks_locked) return;
    try {
      const marks: Record<string, number> = {};
      questions.forEach(q => {
        if (q.type !== "mcq") marks[q.id] = Number(gradingMarks[q.id] ?? 0);
      });
      await api(`/admin/assessments/${selected.assessment_id}/grading/lock`, {
        method: "POST",
        body: JSON.stringify({ marks })
      });
      await loadAssessment(selected.assessment_id);
      await loadList();
      setMessage("Marks locked. The final score is now immutable and visible to the worker.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Unable to lock marks");
    }
  }

  function updateQuestion(index:number, changes:Partial<Question>) {
    setQuestions(current => current.map((q,i) => i===index ? {...q,...changes} : q));
  }

  const selectedId = route.startsWith("/admin/assessments/") ? route.split("/").pop() : null;
  useEffect(()=>{ if(selectedId && selectedId !== selected?.assessment_id) loadAssessment(selectedId); },[selectedId]);
  if (route === "/admin/dashboard") return <Shell user={user} onLogout={onLogout}><section className="page-heading"><p className="eyebrow">ADMIN PORTAL</p><h1>Overview</h1><p className="muted">Manage the complete RPL assessment lifecycle.</p></section><section className="status-grid"><div className="status-card"><span>Total assessments</span><strong>{assessments.length}</strong></div><div className="status-card"><span>Awaiting review</span><strong>{assessments.filter(x=>!x.level_approved).length}</strong></div><div className="status-card"><span>Active</span><strong>{assessments.filter(x=>x.questions_approved&&!x.submitted).length}</strong></div><div className="status-card"><span>Submitted</span><strong>{assessments.filter(x=>x.submitted).length}</strong></div></section><section className="panel"><h2>Recent assessments</h2>{assessments.slice(0,5).map(item=><button className="assessment-row" key={item.assessment_id} onClick={()=>navigate("/admin/assessments/"+item.assessment_id)}><span><strong>{item.candidate?.name||"Unnamed worker"}</strong><small>{item.assessment_id}</small></span><span>{item.submitted?"Submitted":"In progress"}</span></button>)}</section></Shell>;
  if (route === "/admin/submissions") return <Shell user={user} onLogout={onLogout}><section className="page-heading"><p className="eyebrow">ADMIN PORTAL</p><h1>Submissions</h1><p className="muted">Worker attempts submitted for review.</p></section><section className="panel">{assessments.filter(x=>x.submitted).map(item=><button className="assessment-row" key={item.assessment_id} onClick={()=>navigate("/admin/assessments/"+item.assessment_id)}><span><strong>{item.candidate?.name||"Unnamed worker"}</strong><small>{item.submitted_at ? new Date(item.submitted_at).toLocaleString() : "Submitted"}</small></span><span className="badge approved">SUBMITTED</span></button>)}{!assessments.some(x=>x.submitted)&&<p className="muted">No submissions yet.</p>}</section></Shell>;
  if (route === "/admin/assessments") return <Shell user={user} onLogout={onLogout}><section className="page-heading"><p className="eyebrow">ADMIN PORTAL</p><h1>Assessments</h1><p className="muted">Review every worker assessment.</p></section><section className="panel"><div className="panel-header"><h2>Worker assessments</h2><button className="secondary" onClick={loadList}>Refresh</button></div>{assessments.map(item=><button className="assessment-row" key={item.assessment_id} onClick={()=>navigate("/admin/assessments/"+item.assessment_id)}><span><strong>{item.candidate?.name||"Unnamed worker"}</strong><small>{item.assessment_id}</small></span><span>{item.submitted?"Submitted":item.level?"Level "+item.level:"Level pending"}</span></button>)}</section></Shell>;

  return (
    <Shell user={user} onLogout={onLogout}>
      <section className="page-heading"><div><p className="eyebrow">ASSESSMENT REVIEW</p><h1>{selected?.candidate?.name || "Assessment"}</h1><p className="muted">{selected?.assessment_id || "Select an assessment from the Assessments page."}</p></div><p className="muted">Every state transition is persisted and authorization is enforced by the API.</p></section>
      <div className="admin-layout">
        <section className="panel">
          <div className="panel-header"><h2>Worker assessments</h2><button className="secondary" onClick={loadList}>Refresh</button></div>
          {assessments.map(item => <button className={`assessment-row ${selected?.assessment_id===item.assessment_id?"selected":""}`} key={item.assessment_id} onClick={() => loadAssessment(item.assessment_id)}><span><strong>{item.candidate?.name || "Unnamed worker"}</strong><small>{item.assessment_id}</small></span><span>{item.level ? `Level ${item.level}` : "Level pending"}</span></button>)}
          {!assessments.length && <p className="muted">No worker assessments yet.</p>}
        </section>

        {selected ? <section className="panel">
          <div className="panel-header"><div><h2>{selected.candidate.name || "Worker assessment"}</h2><p className="muted">{selected.assessment_id}</p></div><span className={`badge ${selected.level_approved?"approved":"pending"}`}>{selected.level_approved?"LEVEL LOCKED":"REVIEW REQUIRED"}</span></div>

          <div className="detail-tabs" role="tablist" aria-label="Assessment details">
            <button className={detailTab==="worker" ? "detail-tab active" : "detail-tab"} onClick={()=>setDetailTab("worker")}>Worker inputs</button>
            <button className={detailTab==="questions" ? "detail-tab active" : "detail-tab"} onClick={()=>setDetailTab("questions")}>Question paper</button>
            <button className={detailTab==="answers" ? "detail-tab active" : "detail-tab"} onClick={()=>setDetailTab("answers")}>Worker answers</button>
          </div>

          {detailTab==="worker" && <section className="detail-pane">
            <div className="candidate-box">
              <h3>Worker information</h3>
              <div className="form-grid readonly-grid">
                <label>Name<input value={selected.candidate.name} readOnly /></label>
                <label>Age<input value={selected.candidate.age} readOnly /></label>
                <label>Years of experience<input value={selected.candidate.years_experience} readOnly /></label>
                <label>Occupation<input value={selected.candidate.occupation} readOnly /></label>
              </div>
              <label>Work performed / skills<textarea value={selected.candidate.work_context} readOnly /></label>
              <label>Prior training / certificates<textarea value={selected.candidate.prior_training || "No prior training listed"} readOnly /></label>
            </div>
            <section className="result">
              <h3>NSQF level</h3>
              <label>NSQF level
                <select value={selectedLevel} onChange={e=>setSelectedLevel(Number(e.target.value) as NsqfLevel)} disabled={selected.level_approved}>
                  <option value="">Select NSQF level</option>
                  {NSQF_LEVELS.map(level=><option key={level} value={level}>Level {level}</option>)}
                </select>
              </label>
              {selected.level_suggestion ? <>
                <p>{selected.level_suggestion.reason}</p>
                <small>AI recommendation: Level {selected.level_suggestion.suggested_level} · Confidence: {selected.level_suggestion.confidence}</small>
              </> : <p className="muted">No AI recommendation yet. Run the recommendation to preselect a level.</p>}
              <div className="actions">
                {!selected.level_approved && <button onClick={regenerateLevel}>{selected.level_suggestion ? "Regenerate recommendation" : "Run AI recommendation"}</button>}
                {!selected.level_approved
                  ? <button onClick={approveLevel} disabled={selectedLevel === ""}>Approve & lock level</button>
                  : <>
                      <span className="badge approved">LEVEL LOCKED</span>
                      <button className="secondary" onClick={unlockLevel}>Unlock level</button>
                    </>}
              </div>
            </section>
          </section>}

          {detailTab==="questions" && <section className="detail-pane">
            <div className="panel-header">
              <div><h3>Question paper</h3><p className="muted">{selected.questions_approved ? "Approved and locked" : "Draft — editable until approval"}</p></div>
              <span className={`badge ${selected.questions_approved ? "approved" : "pending"}`}>{selected.questions_approved ? "LOCKED" : "DRAFT"}</span>
            </div>
            <p className="muted">{selected.level_approved ? `NSQF Level ${selected.level} · ${questions.length} questions` : "Approve the level before generating questions."}</p>
            {!selected.questions_approved && <button onClick={generateQuestions} disabled={!selected.level_approved}>Generate questions</button>}
            {questions.length > 0 && <div className="question-editor">
              {questions.map((q,i) => selected.questions_approved ? (
                <article className="question-card locked-question" key={q.id}>
                  <div className="question-meta">QUESTION {i+1} · {q.type.toUpperCase()} · {q.marks} MARKS</div>
                  <h3>{q.question}</h3>
                  {q.options?.length ? <ol className="question-options">{q.options.map((option,j)=><li key={j}>{option}</li>)}</ol> : null}
                  <span className="lock-note">Approved question · read only</span>
                </article>
              ) : (
                <article className="question-card" key={q.id}>
                  <input value={q.question} onChange={e=>updateQuestion(i,{question:e.target.value})}/>
                  {q.options?.length ? <div className="question-options-editor">{q.options.map((option,j)=><input key={j} value={option} onChange={e=>updateQuestion(i,{options:q.options?.map((x,k)=>k===j?e.target.value:x)})}/>)}</div> : null}
                  <div className="inline-fields"><select value={q.type} onChange={e=>updateQuestion(i,{type:e.target.value as Question["type"]})}><option value="mcq">MCQ</option><option value="text">Text</option><option value="image">Image</option><option value="video">Video</option></select><input type="number" min="1" max="10" value={q.marks} onChange={e=>updateQuestion(i,{marks:Number(e.target.value)})}/></div>
                  <button className="danger" onClick={()=>setQuestions(current=>current.filter((_,x)=>x!==i))}>Delete</button>
                </article>
              ))}
            </div>}
            {!selected.questions_approved && <button onClick={approveQuestions} disabled={!questions.length}>Approve & activate assessment</button>}
          </section>}

          {detailTab==="answers" && <section className="detail-pane">
            <div className="panel-header">
              <div><h3>Worker answers</h3><p className="muted">{selected.submitted ? `Submitted ${selected.submitted_at ? new Date(selected.submitted_at).toLocaleString() : ""}` : "Not submitted yet"}</p></div>
              <div className="grading-header-actions">
                {selected.marks_locked ? <span className="badge approved">MARKS LOCKED</span> : selected.submitted ? <button onClick={lockGrading}>Lock & submit marks</button> : null}
                {selected.grading?.total_marks !== undefined && <strong className="total-score">{selected.grading.total_marks} / {selected.grading.max_marks}</strong>}
              </div>
            </div>
            {selected.submitted && selected.submission ? <div className="submission-summary">
              {(selected.submission.answers || []).map((answer:any,index:number)=>{
                const q = questions.find(item => String(item.id) === String(answer.id)) || answer;
                const status = objectiveStatus(q);
                const lockedItem = selected.grading?.items?.find((item:any)=>String(item.question_id)===String(q.id));
                const subjective = ["text","image","video"].includes(q.type);
                const awarded = lockedItem?.marks_awarded ?? gradingMarks[q.id] ?? 0;
                return <article className={`question-card answer-card ${status==="correct"?"answer-correct":status==="incorrect"?"answer-incorrect":""}`} key={answer.id || index}>
                  <div className="question-meta">QUESTION {index+1} · {q.type?.toUpperCase() || "TEXT"} · {q.marks || 0} MARKS
                    {status==="correct" && <span className="answer-badge correct">✓ Correct</span>}
                    {status==="incorrect" && <span className="answer-badge incorrect">✕ Incorrect</span>}
                    {status==="unanswered" && <span className="answer-badge unanswered">— Unanswered</span>}
                  </div>
                  <h3>{q.question}</h3>
                  {q.options?.length ? <p><strong>Selected:</strong> {answer.selected_option >= 0 ? q.options[answer.selected_option] : "Not answered"}</p> : <p><strong>Response:</strong> {answer.response || "Not answered"}</p>}
                  {subjective && <div className="manual-marking">
                    <label>Admin marks
                      <input type="number" min="0" max={q.marks || 0} step="1" value={awarded} disabled={selected.marks_locked} onChange={e=>setGradingMarks({...gradingMarks,[q.id]:Number(e.target.value)})}/>
                      <small>Maximum: {q.marks || 0} marks</small>
                    </label>
                    <span className="marking-note">{selected.marks_locked ? "Final mark locked" : "Enter the mark before locking"}</span>
                  </div>}
                </article>;
              })}
              <div className="grading-footer">
                <div><span>Final total</span><strong>{selected.marks_locked ? `${selected.grading?.total_marks || 0} / ${selected.grading?.max_marks || 0}` : `${questions.reduce((sum,q)=>sum+(q.type==="mcq" && objectiveStatus(q)==="correct" ? q.marks : q.type!=="mcq" ? Number(gradingMarks[q.id]||0) : 0),0)} / ${questions.reduce((sum,q)=>sum+(q.marks||0),0)}`}</strong></div>
                {!selected.marks_locked && selected.submitted && <button onClick={lockGrading}>Lock & submit marks</button>}
              </div>
            </div> : <div className="empty"><p className="muted">The worker has not submitted the assessment yet.</p></div>}
          </section>}
        </section> : <section className="panel empty"><h2>Select an assessment</h2><p className="muted">Choose a worker from the list to review their declaration and assessment state.</p></section>}
      </div>
      {message && <p className="notice">{message}</p>}
    </Shell>
  );
}

function App() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token()) { setLoading(false); return; }
    api("/auth/me").then(setUser).catch(() => {}).finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (user && (window.location.pathname === "/" || (window.location.pathname === "/login" || window.location.pathname === "/signup"))) {
      navigate(user.role === "admin" ? "/admin/dashboard" : "/worker/dashboard");
    }
  }, [user]);

  if (loading) return <main className="auth-page"><p>Loading...</p></main>;
  if (!user) return <Login onLogin={(nextUser) => { setUser(nextUser); navigate(nextUser.role === "admin" ? "/admin/dashboard" : "/worker/dashboard"); }} />;

  const logout = () => { localStorage.removeItem(TOKEN_KEY); setUser(null); navigate("/login"); };
  return user.role === "admin" ? <AdminDashboard user={user} onLogout={logout} /> : <WorkerDashboard user={user} onLogout={logout} />;
}

createRoot(document.getElementById("root")!).render(<React.StrictMode><App /></React.StrictMode>);
