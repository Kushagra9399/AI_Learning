from pathlib import Path
import uuid
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from .store import store
from .services import generate_questions, evaluate_attempt, recommend
from .qp import QP
from .practical import task_catalog

EVIDENCE_DIR = Path(__file__).resolve().parents[1] / "evidence"
EVIDENCE_DIR.mkdir(exist_ok=True)

app = FastAPI(title="AI-Assisted RPL Skill Assessment", version="1.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/api/health")
def health(): return {"status":"ok","storage":"sqlite"}

@app.get("/api/qp")
def qp(): return QP

@app.get("/api/practical/tasks")
def practical_tasks(): return task_catalog()

@app.post("/api/declarations/map")
def map_declaration(payload: dict):
    text = " ".join(str(v) for v in payload.values()).lower()
    matched = any(x in text for x in ("electrician","electrical wiring","construction electrical"))
    return {"qp_code":"CON/Q0603" if matched else None,"nsqf_level":4 if matched else None,
            "confidence":0.96 if matched else 0.0,"assessor_selection_required":not matched}

@app.post("/api/jobs/questions")
def question_job(payload: dict):
    job=store.job("question_generation",payload)
    store.run_async(job, lambda: {"questions":generate_questions(payload.get("count",12)),"qp_code":QP["qp_code"]})
    return {"message":"question generation added","job_id":job["id"],"status":"queued"}

@app.post("/api/jobs/evaluation")
def evaluation_job(payload: dict):
    job=store.job("evaluation",payload)
    store.run_async(job, lambda: evaluate_attempt(payload))
    return {"message":"evaluation added","job_id":job["id"],"status":"queued","accepted":True}

@app.post("/api/jobs/recommendation")
def recommendation_job(payload: dict):
    job=store.job("recommendation",payload)
    store.run_async(job, lambda: recommend(payload))
    return {"message":"recommendation added","job_id":job["id"],"status":"queued"}

@app.get("/api/jobs/{job_id}")
def job(job_id:str):
    item=store.get(job_id)
    if not item: return {"error":"not found"}
    return item

@app.post("/api/jobs/{job_id}/ack")
def ack(job_id:str):
    store.ack(job_id)
    return {"job_id":job_id,"acknowledged":True}

@app.post("/api/submissions")
def submit(payload:dict):
    return {"accepted":store.submit(payload),"assessment_id":payload["assessment_id"]}

@app.post("/api/evidence")
async def upload_evidence(assessment_id: str = Form(...), task_id: str = Form(...), media: UploadFile = File(...)):
    evidence_id="ev_"+uuid.uuid4().hex[:12]
    safe_name=Path(media.filename or "evidence.bin").name
    target=EVIDENCE_DIR / f"{evidence_id}_{safe_name}"
    target.write_bytes(await media.read())
    with store._conn() as c:
        c.execute("INSERT INTO evidence VALUES (?,?,?,?,?,?,?)",
                  (evidence_id,assessment_id,task_id,safe_name,media.content_type or "application/octet-stream",str(target),__import__("datetime").datetime.utcnow().isoformat()))
    return {"evidence_id":evidence_id,"status":"stored","assessment_id":assessment_id,"task_id":task_id}

@app.get("/api/assessor/{assessment_id}")
def assessor_view(assessment_id:str):
    view=store.assessor(assessment_id)
    with store._conn() as c:
        rows=c.execute("SELECT evidence_id,task_id,filename,media_type,created_at FROM evidence WHERE assessment_id=? ORDER BY created_at",(assessment_id,)).fetchall()
    view["evidence"]=[dict(x) for x in rows]
    return view

@app.post("/api/assessor/{assessment_id}/evaluate")
def assessor_evaluate(assessment_id:str,payload:dict):
    view=store.assessor(assessment_id)
    if not view["submission"]:
        return {"accepted":False,"reason":"assessment_not_found"}
    evaluation_payload={**view["submission"],"assessment_id":assessment_id,"practical_scores":payload.get("practical_scores",[])}
    job=store.job("assessor_evaluation",evaluation_payload)
    store.run_async(job, lambda: evaluate_attempt(evaluation_payload))
    return {"accepted":True,"job_id":job["id"],"status":"queued","assessor_id":payload.get("assessor_id")}

@app.post("/api/assessor/{assessment_id}/signoff")
def signoff(assessment_id:str,payload:dict):
    return store.signoff(assessment_id,payload)
