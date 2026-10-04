import os
from pathlib import Path

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm

from .auth import (
    AdminUser,
    CurrentUser,
    WorkerUser,
    authenticate,
    create_access_token,
    seed_default_users,
)
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
    version="3.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:5173").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    seed_default_users()


@app.get("/api/health")
def health():
    return {"status": "ok", "groq_configured": bool(os.getenv("GROQ_API_KEY"))}


class LoginRequest(BaseModel):
    name: str
    password: str


class WorkerSignupRequest(BaseModel):
    name: str
    password: str
    phone: str
    dob: str


@app.post("/api/auth/login")
def login(payload: LoginRequest):
    user = authenticate(payload.name, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect name, password, phone number or date of birth")
    return {
        "access_token": create_access_token(user),
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "username": user["username"],
            "name": user["name"],
            "phone": user["phone"],
            "dob": user["dob"],
            "role": user["role"],
        },
    }


@app.post("/api/auth/signup")
def signup(payload: WorkerSignupRequest):
    name = payload.name.strip()
    phone = payload.phone.strip()
    dob = payload.dob.strip()

    if not name or not phone or not dob or not payload.password:
        raise HTTPException(status_code=400, detail="Name, password, phone number and date of birth are required")

    if store.get_user_by_username(name):
        raise HTTPException(status_code=409, detail="A user with this name already exists")

    if store.get_user_by_phone(phone):
        raise HTTPException(status_code=409, detail="A user with this phone number already exists")

    from .auth import password_hash
    user = store.create_user(
        username=name,
        name=name,
        phone=phone,
        dob=dob,
        password_hash=password_hash.hash(payload.password),
        role="worker",
    )
    return {
        "message": "Worker account created successfully",
        "user": {
            "id": user["id"],
            "username": user["username"],
            "name": user["name"],
            "phone": user["phone"],
            "dob": user["dob"],
            "role": user["role"],
        },
    }


@app.get("/api/auth/me")
def me(current_user: CurrentUser):
    return {
        "id": current_user["id"],
        "username": current_user["username"],
        "name": current_user["name"],
        "phone": current_user["phone"],
        "dob": current_user["dob"],
        "role": current_user["role"],
    }


@app.get("/api/qp")
def get_qp(_: CurrentUser):
    return QP


@app.get("/api/levels/{level}")
def get_level(level: int, _: CurrentUser):
    return {"level": level, "context": level_context(level)}


@app.get("/api/practical/tasks")
def get_practical_tasks(_: CurrentUser):
    return task_catalog()


@app.post("/api/worker/assessment")
def create_worker_assessment(payload: dict, worker: WorkerUser):
    assessment_id = payload.get("assessment_id")
    assessment = store.create_worker_assessment(worker["id"], payload, assessment_id=assessment_id)
    if assessment["existing"]:
        return assessment

    job = store.job(
        "level_suggestion",
        {
            "assessment_id": assessment["assessment_id"],
            "candidate": payload,
        },
    )

    def process_level():
        suggestion = infer_level(payload)
        store.save_level_suggestion(assessment["assessment_id"], suggestion)
        return {"assessment_id": assessment["assessment_id"], **suggestion}

    store.run_async(job, process_level)
    return {**assessment, "job_id": job["id"], "status": "queued"}


@app.get("/api/worker/assessment")
def get_worker_assessment(worker: WorkerUser):
    return store.worker_assessment(worker["id"])


@app.get("/api/user/{assessment_id}/assessment")
def get_user_assessment(assessment_id: str, worker: WorkerUser):
    return store.user_assessment(assessment_id, worker["id"])


@app.post("/api/worker/assessment/{assessment_id}/start")
def start_assessment(assessment_id: str, worker: WorkerUser):
    return store.start_assessment(assessment_id, worker["id"])


@app.get("/api/admin/assessments")
def admin_assessments(_: AdminUser):
    return store.admin_assessments()


@app.get("/api/admin/candidate/{assessment_id}")
def get_candidate(assessment_id: str, _: AdminUser):
    candidate = store.admin_candidate(assessment_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return candidate

@app.get("/api/admin/submissions/{assessment_id}")
def get_admin_submission(assessment_id: str, _: AdminUser):
    candidate = store.admin_candidate(assessment_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return {
        "assessment_id": assessment_id,
        "submitted": candidate["submitted"],
        "submitted_at": candidate["submitted_at"],
        "submission": candidate["submission"],
        "evidence": candidate["evidence"],
    }


@app.post("/api/admin/assessments/{assessment_id}/level-suggestion")
def create_level_suggestion(assessment_id: str, _: AdminUser):
    candidate = store.admin_candidate(assessment_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Assessment not found")
    if candidate["level_approved"]:
        raise HTTPException(status_code=409, detail="Approved level is immutable; AI recommendation cannot be regenerated")

    job = store.job(
        "level_suggestion",
        {
            "assessment_id": assessment_id,
            "candidate": candidate["candidate"],
        },
    )

    def process_level():
        suggestion = infer_level(candidate["candidate"])
        store.save_level_suggestion(assessment_id, suggestion)
        return {"assessment_id": assessment_id, **suggestion}

    store.run_async(job, process_level)
    return {"assessment_id": assessment_id, "job_id": job["id"], "status": "queued"}


@app.post("/api/admin/level-approval")
def approve_level(payload: dict, _: AdminUser):
    return store.approve_level(payload)


@app.post("/api/admin/assessments/{assessment_id}/level-unlock")
def unlock_level(assessment_id: str, _: AdminUser):
    result = store.unlock_level(assessment_id)
    if not result.get("unlocked"):
        raise HTTPException(status_code=409, detail=result.get("reason", "Unable to unlock level"))
    return result


@app.post("/api/admin/questions/generate")
def create_question_job(payload: dict, _: AdminUser):
    assessment_id = payload["assessment_id"]
    candidate = store.admin_candidate(assessment_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Assessment not found")
    if not candidate["level_approved"]:
        raise HTTPException(status_code=409, detail="Approve the NSQF level before generating questions")
    if candidate["questions_approved"]:
        raise HTTPException(status_code=409, detail="Questions are already approved and active")

    level = float(candidate["level"])
    job = store.job("question_generation", payload)

    def process_questions():
        questions = generate_questions(
            level,
            candidate["candidate"],
            payload.get("count", 10),
        )
        store.save_questions(assessment_id, questions)
        return {"assessment_id": assessment_id, "questions": questions, "nsqf_level": level}

    store.run_async(job, process_questions)
    return {"job_id": job["id"], "status": "queued"}


@app.post("/api/admin/questions/draft")
def save_question_draft(payload: dict, _: AdminUser):
    questions = payload.get("questions")
    if not isinstance(questions, list) or not questions:
        raise HTTPException(status_code=400, detail="Question draft is required")
    result = store.save_questions(payload["assessment_id"], questions)
    if not result.get("saved"):
        raise HTTPException(status_code=409, detail=result.get("reason", "Unable to save question draft"))
    return result


@app.post("/api/admin/questions/approve")
def approve_questions(payload: dict, _: AdminUser):
    return store.approve_questions(payload)


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str, _: AdminUser):
    item = store.get_job(job_id)
    return item or {"error": "not found"}


@app.post("/api/jobs/{job_id}/ack")
def acknowledge_job(job_id: str, _: AdminUser):
    store.acknowledge_job(job_id)
    return {"acknowledged": True}


@app.post("/api/submissions")
def submit_assessment(payload: dict, worker: WorkerUser):
    return store.submit(payload, worker["id"])


@app.post("/api/admin/assessments/{assessment_id}/grading/lock")
def lock_assessment_grading(assessment_id: str, payload: dict, _: AdminUser):
    result = store.lock_grading(assessment_id, payload)
    if not result.get("accepted"):
        raise HTTPException(status_code=409, detail=result.get("reason", "Unable to lock grading"))
    return result


@app.get("/api/worker/assessment/{assessment_id}/result")
def get_worker_result(assessment_id: str, worker: WorkerUser):
    result = store.worker_result(assessment_id, worker["id"])
    if result is None:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return result


@app.post("/api/evidence")
async def upload_evidence(
    worker: WorkerUser,
    assessment_id: str = Form(...),
    task_id: str = Form(...),
    media: UploadFile = File(...),
    evidence_id: str | None = Form(None),
):
    evidence_id = evidence_id or ("ev_" + __import__("uuid").uuid4().hex[:12])
    filename = Path(media.filename or "evidence.bin").name
    target = EVIDENCE_DIR / f"{evidence_id}_{filename}"
    target.write_bytes(await media.read())

    stored = store.add_evidence(
        evidence_id,
        assessment_id,
        task_id,
        filename,
        media.content_type or "application/octet-stream",
        str(target),
        worker["id"],
    )
    if not stored:
        target.unlink(missing_ok=True)
        raise HTTPException(status_code=404, detail="Assessment not found")

    return {"evidence_id": evidence_id, "status": "stored"}


@app.get("/api/assessor/{assessment_id}")
def get_assessor_view(assessment_id: str, _: AdminUser):
    return store.assessor(assessment_id)


@app.post("/api/assessor/{assessment_id}/evaluate")
def create_assessor_evaluation(assessment_id: str, payload: dict, _: AdminUser):
    view = store.assessor(assessment_id)
    if not view["submission"]:
        return {"accepted": False, "reason": "assessment_submission_not_found"}

    evaluation_payload = {
        **view["submission"],
        "assessment_id": assessment_id,
        "practical_scores": payload.get("practical_scores", []),
    }
    job = store.job("assessor_evaluation", evaluation_payload)
    store.run_async(job, lambda: evaluate_attempt(evaluation_payload))
    return {"accepted": True, "job_id": job["id"]}


@app.post("/api/admin/feedback")
def create_feedback(payload: dict, _: AdminUser):
    return generate_feedback(
        payload.get("evaluation", {}),
        payload.get("admin_note", ""),
    )


@app.post("/api/assessor/{assessment_id}/signoff")
def signoff(assessment_id: str, payload: dict, _: AdminUser):
    return store.signoff(assessment_id, payload)