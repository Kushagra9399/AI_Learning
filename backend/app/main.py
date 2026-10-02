import os
import uuid
from pathlib import Path

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .practical import task_catalog
from .qp import QP
from .services import (
    evaluate_attempt,
    generate_feedback,
    generate_questions,
    infer_level,
    level_context,
    recommend,
)
from .store import store


EVIDENCE_DIR = Path(__file__).resolve().parents[1] / "evidence"
EVIDENCE_DIR.mkdir(exist_ok=True)

app = FastAPI(
    title="AI-Assisted RPL Skill Assessment",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "groq_configured": bool(os.getenv("GROQ_API_KEY")),
    }


@app.get("/api/qp")
def get_qp():
    return QP


@app.get("/api/levels/{level}")
def get_level(level: int):
    return {
        "level": level,
        "context": level_context(level),
    }


@app.get("/api/practical/tasks")
def get_practical_tasks():
    return task_catalog()


@app.post("/api/admin/level-suggestion")
def create_level_suggestion(payload: dict):
    assessment_id = "assessment_" + uuid.uuid4().hex[:12]
    store.ensure_assessment(assessment_id, payload)

    job = store.job(
        "level_suggestion",
        {
            "assessment_id": assessment_id,
            "candidate": payload,
        },
    )

    def process_level():
        suggestion = infer_level(payload)
        store.save_level_suggestion(assessment_id, suggestion)
        return {
            "assessment_id": assessment_id,
            **suggestion,
        }

    store.run_async(job, process_level)

    return {
        "assessment_id": assessment_id,
        "job_id": job["id"],
        "status": "queued",
    }


@app.post("/api/admin/level-approval")
def approve_level(payload: dict):
    return store.approve_level(payload)


@app.get("/api/admin/candidate/{assessment_id}")
def get_candidate(assessment_id: str):
    return store.admin_candidate(assessment_id)


@app.post("/api/admin/questions/generate")
def create_question_job(payload: dict):
    level = int(payload["nsqf_level"])
    candidate = payload.get("candidate", {})

    job = store.job("question_generation", payload)

    store.run_async(
        job,
        lambda: {
            "questions": generate_questions(
                level,
                candidate,
                payload.get("count", 10),
            ),
            "nsqf_level": level,
        },
    )

    return {
        "job_id": job["id"],
        "status": "queued",
    }


@app.post("/api/admin/questions/approve")
def approve_questions(payload: dict):
    return store.approve_questions(payload)


@app.get("/api/user/{assessment_id}/assessment")
def get_user_assessment(assessment_id: str):
    return store.user_assessment(assessment_id)


@app.post("/api/user/{assessment_id}/start")
def start_assessment(assessment_id: str):
    return store.start_assessment(assessment_id)


@app.post("/api/jobs/evaluation")
def create_evaluation_job(payload: dict):
    job = store.job("evaluation", payload)
    store.run_async(
        job,
        lambda: evaluate_attempt(payload),
    )
    return {
        "job_id": job["id"],
        "status": "queued",
    }


@app.post("/api/jobs/recommendation")
def create_recommendation_job(payload: dict):
    job = store.job("recommendation", payload)
    store.run_async(
        job,
        lambda: recommend(payload),
    )
    return {
        "job_id": job["id"],
        "status": "queued",
    }


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str):
    item = store.get_job(job_id)
    return item or {"error": "not found"}


@app.post("/api/jobs/{job_id}/ack")
def acknowledge_job(job_id: str):
    store.acknowledge_job(job_id)
    return {"acknowledged": True}


@app.post("/api/submissions")
def submit_assessment(payload: dict):
    return store.submit(payload)


@app.post("/api/evidence")
async def upload_evidence(
    assessment_id: str = Form(...),
    task_id: str = Form(...),
    media: UploadFile = File(...),
):
    evidence_id = "ev_" + uuid.uuid4().hex[:12]
    filename = Path(media.filename or "evidence.bin").name
    target = EVIDENCE_DIR / f"{evidence_id}_{filename}"

    target.write_bytes(await media.read())

    store.add_evidence(
        evidence_id,
        assessment_id,
        task_id,
        filename,
        media.content_type or "application/octet-stream",
        str(target),
    )

    return {
        "evidence_id": evidence_id,
        "status": "stored",
    }


@app.get("/api/assessor/{assessment_id}")
def get_assessor_view(assessment_id: str):
    return store.assessor(assessment_id)


@app.post("/api/assessor/{assessment_id}/evaluate")
def create_assessor_evaluation(
    assessment_id: str,
    payload: dict,
):
    view = store.assessor(assessment_id)

    if not view["submission"]:
        return {
            "accepted": False,
            "reason": "assessment_submission_not_found",
        }

    evaluation_payload = {
        **view["submission"],
        "practical_scores": payload.get("practical_scores", []),
    }

    job = store.job(
        "assessor_evaluation",
        evaluation_payload,
    )

    store.run_async(
        job,
        lambda: evaluate_attempt(evaluation_payload),
    )

    return {
        "accepted": True,
        "job_id": job["id"],
    }


@app.post("/api/admin/feedback")
def create_feedback(payload: dict):
    return generate_feedback(
        payload.get("evaluation", {}),
        payload.get("admin_note", ""),
    )


@app.post("/api/assessor/{assessment_id}/signoff")
def signoff(assessment_id: str, payload: dict):
    return store.signoff(assessment_id, payload)
