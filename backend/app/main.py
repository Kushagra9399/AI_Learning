from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .store import store
from .services import generate_questions, evaluate_attempt, recommend
from .qp import QP

app = FastAPI(title="AI-Assisted RPL Skill Assessment", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/api/health")
def health(): return {"status":"ok"}

@app.get("/api/qp")
def qp(): return QP

@app.post("/api/declarations/map")
def map_declaration(payload: dict):
    text = str(payload).lower()
    matched = any(x in text for x in ("electrician","electrical wiring","construction electrical"))
    return {"qp_code":"CON/Q0603" if matched else None,"nsqf_level":4 if matched else None,"confidence":0.96 if matched else 0.0,"assessor_selection_required":not matched}

@app.post("/api/jobs/questions")
def question_job(payload: dict):
    job=store.job("question_generation",payload)
    store.run_async(job, lambda: {"questions":generate_questions(payload.get("count",12)),"qp_code":"CON/Q0603"})
    return {"message":"question generation added","job_id":job["id"],"status":"queued"}

@app.post("/api/jobs/evaluation")
def evaluation_job(payload: dict):
    job=store.job("evaluation",payload)
    store.run_async(job, lambda: evaluate_attempt(payload))
    return {"message":"evaluation added","job_id":job["id"],"status":"queued"}

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
    store.ack(job_id); return {"job_id":job_id,"acknowledged":True}

@app.post("/api/submissions")
def submit(payload:dict):
    # assessment_id is unique: the same attempt cannot be submitted twice.
    if not store.submit(payload): return {"accepted":False,"reason":"single_attempt_already_submitted"}
    return {"accepted":True,"assessment_id":payload["assessment_id"]}

@app.get("/api/assessor/{assessment_id}")
def assessor_view(assessment_id:str):
    return store.assessor(assessment_id)

@app.post("/api/assessor/{assessment_id}/signoff")
def signoff(assessment_id:str,payload:dict):
    return store.signoff(assessment_id,payload)
