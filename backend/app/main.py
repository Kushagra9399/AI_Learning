import uuid
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from .store import store
from .services import infer_level, generate_questions, evaluate_attempt, recommend, generate_feedback, level_context
from .qp import QP
from .practical import task_catalog

EVIDENCE_DIR=Path(__file__).resolve().parents[1]/"evidence"; EVIDENCE_DIR.mkdir(exist_ok=True)
app=FastAPI(title="AI-Assisted RPL Skill Assessment",version="2.0.0")
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_methods=["*"],allow_headers=["*"])

@app.get("/api/health")
def health(): return {"status":"ok","groq_configured":bool(__import__("os").getenv("GROQ_API_KEY"))}

@app.get("/api/qp")
def qp(): return QP

@app.get("/api/levels/{level}")
def level(level:int): return {"level":level,"context":level_context(level)}

@app.get("/api/practical/tasks")
def practical_tasks(): return task_catalog()

@app.post("/api/admin/level-suggestion")
def level_suggestion(payload:dict):
    job=store.job("level_suggestion",payload)
    store.run_async(job,lambda:infer_level(payload))
    return {"job_id":job["id"],"status":"queued"}

@app.post("/api/admin/level-approval")
def level_approval(payload:dict):
    return store.approve_level(payload)

@app.get("/api/admin/candidate/{assessment_id}")
def candidate(assessment_id:str): return store.admin_candidate(assessment_id)

@app.post("/api/admin/questions/generate")
def question_job(payload:dict):
    level=int(payload["nsqf_level"]); candidate=payload.get("candidate",{})
    job=store.job("question_generation",payload)
    store.run_async(job,lambda:{"questions":generate_questions(level,candidate,payload.get("count",10)),"nsqf_level":level})
    return {"job_id":job["id"],"status":"queued"}

@app.post("/api/admin/questions/approve")
def approve_questions(payload:dict): return store.approve_questions(payload)

@app.get("/api/user/{assessment_id}/assessment")
def user_assessment(assessment_id:str): return store.user_assessment(assessment_id)

@app.post("/api/user/{assessment_id}/start")
def start_assessment(assessment_id:str): return store.start_assessment(assessment_id)

@app.post("/api/jobs/evaluation")
def evaluation_job(payload:dict):
    job=store.job("evaluation",payload); store.run_async(job,lambda:evaluate_attempt(payload))
    return {"job_id":job["id"],"status":"queued"}

@app.post("/api/jobs/recommendation")
def recommendation_job(payload:dict):
    job=store.job("recommendation",payload); store.run_async(job,lambda:recommend(payload))
    return {"job_id":job["id"],"status":"queued"}

@app.get("/api/jobs/{job_id}")
def job(job_id:str):
    item=store.get(job_id); return item or {"error":"not found"}

@app.post("/api/jobs/{job_id}/ack")
def ack(job_id:str): store.ack(job_id); return {"acknowledged":True}

@app.post("/api/submissions")
def submit(payload:dict): return store.submit(payload)

@app.post("/api/evidence")
async def evidence(assessment_id:str=Form(...),task_id:str=Form(...),media:UploadFile=File(...)):
    eid="ev_"+uuid.uuid4().hex[:12]; name=Path(media.filename or "evidence.bin").name
    target=EVIDENCE_DIR/f"{eid}_{name}"; target.write_bytes(await media.read())
    store.add_evidence(eid,assessment_id,task_id,name,media.content_type or "application/octet-stream",str(target))
    return {"evidence_id":eid,"status":"stored"}

@app.get("/api/assessor/{assessment_id}")
def assessor(assessment_id:str): return store.assessor(assessment_id)

@app.post("/api/assessor/{assessment_id}/evaluate")
def assessor_evaluate(assessment_id:str,payload:dict):
    view=store.assessor(assessment_id)
    if not view["submission"]: return {"accepted":False,"reason":"assessment_not_found"}
    p={**view["submission"],"practical_scores":payload.get("practical_scores",[])}
    job=store.job("assessor_evaluation",p); store.run_async(job,lambda:evaluate_attempt(p))
    return {"accepted":True,"job_id":job["id"]}

@app.post("/api/admin/feedback")
def feedback(payload:dict): return generate_feedback(payload.get("evaluation",{}),payload.get("admin_note",""))

@app.post("/api/assessor/{assessment_id}/signoff")
def signoff(assessment_id:str,payload:dict): return store.signoff(assessment_id,payload)
