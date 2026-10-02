# AI-Assisted Skill Assessment Tool for Recognition of Prior Learning (RPL)

This branch reworks the original AI Learning prototype into an MSDE/NCVET-oriented RPL assessment workflow.

## Repository structure
- **frontend/** — React + Vite interface, offline assessment package storage, single-attempt test flow and job polling.
- **backend/** — FastAPI services for QP mapping, asynchronous question generation, deterministic scoring, recommendation and assessor sign-off.
- **images/** — original project assets retained where useful.

## Reference qualification
The MVP is anchored to **Construction Electrician - LV (CON/Q0603), Version 5.0, NSQF Level 4**. The QP contains seven compulsory NOS units and a 70% aggregate pass threshold. QP/NOS identifiers are kept deterministic so an LLM cannot invent a qualification framework.

## Low-connectivity workflow
1. Worker completes a structured prior-experience declaration.
2. Backend maps the declaration to the supported QP.
3. Question generation is queued and immediately returns a job_id.
4. The frontend polls the job and stores the completed assessment package locally.
5. The worker can take the test offline.
6. A unique assessment_id enforces one test attempt.
7. The completed attempt remains locally available until connectivity returns.
8. Evaluation and recommendation run asynchronously and are delivered through job polling.
9. Assessor-facing output explicitly separates AI assistance from final human judgement.

A normal browser SPA cannot reliably expose an inbound HTTP webhook. Therefore polling is the guaranteed delivery mechanism; a server/relay callback can be added when the deployment environment provides one.

## Run

### Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Assessor boundary
The system is an **AI-assisted** assessment tool. It does not issue a certificate. Practical evidence, authenticity, assessor rubric scoring, overrides and final certification/sign-off remain human-controlled.

## Current scope
The repository now contains the requested frontend/backend separation and low-connectivity async workflow. Practical image/video evidence capture, richer assessor rubric screens and a formal inter-assessor agreement experiment should be added as the next validation layer rather than being represented as automated certification.