# AI-Assisted Skill Assessment Tool for Recognition of Prior Learning (RPL)

This branch implements an MSDE/NCVET-oriented RPL workflow for **Construction Electrician - LV (CON/Q0603), Version 5.0, NSQF Level 4**.

## Implemented scope

- Structured self-declaration and deterministic QP mapping.
- QP/NOS/PC competency model with fixed identifiers and official QP reference.
- Async assessment-package generation with `job_id`, status polling and ACK.
- Theory questions mapped to NOS and PC.
- Practical tasks with standardized, assessor-entered rubrics and safety instructions.
- Photo/video evidence capture in the browser.
- Offline assessment/evidence storage using IndexedDB and a service-worker shell.
- Reconnection queue for assessment/evidence synchronization.
- Single-attempt enforcement using a persistent SQLite submission store.
- Persistent async jobs with retry-friendly status records.
- Assessor-facing API containing submission, evidence and sign-off data.
- Validation harness for inter-assessor agreement metrics.

## RPL workflow

```
Self declaration
      |
      v
QP / NOS / PC mapping
      |
      +--> Theory assessment
      |
      +--> Practical tasks --> Photo/video evidence
      |
      v
Standardized scoring
      |
      v
Competency profile + gap analysis
      |
      v
AI recommendation
      |
      v
Human assessor review / override / sign-off
```

The system does **not** issue a certificate and does not treat AI output as a certification decision.

## Offline workflow

1. Connect once to download the assessment package.
2. Questions are stored in IndexedDB.
3. The theory attempt and evidence metadata/media are stored locally.
4. The attempt is single-use.
5. When connectivity returns, the browser queues evaluation and evidence sync.
6. Backend persists jobs/submissions/evidence metadata in SQLite.
7. Job polling is the guaranteed browser delivery mechanism; an inbound browser webhook is not assumed.

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

## Validation

Run the example harness with:

```bash
cd backend
python validation/test_inter_assessor.py
```

The example numbers are placeholders only. For a credible problem-statement submission, replace them with anonymized scores from multiple assessors on a fixed test set and report agreement statistics without claiming improvement until measured.

## Assessor boundary

AI may help organize evidence, generate question wording and calculate standardized scores. It must not invent QP/NOS/PC identifiers, alter official pass rules, authenticate evidence by itself, or issue certification. The authorized assessor retains final judgement, can override AI-assisted results with a reason, and signs off the competency outcome.

## Reference

Official QP: https://s3.ap-south-1.amazonaws.com/nsdcproddocuments/qpPdf/CON_Q0603_v5.0.pdf


## Authentication and persistent workflow

The RPL application uses role-based JWT authentication with two roles:

- **Admin**: manages worker assessments, reviews AI recommendations, approves and locks the NSQF level, and reviews/approves generated question packages.
- **Worker**: submits their declaration, sees only their own persisted assessment, and can start/submit only after administrator approval.

Assessment state is stored in SQLite. AI question generation is persisted as a **draft** before administrator approval. Once the NSQF level is approved it is immutable, and the API rejects new AI level recommendations for that assessment. Once questions are approved, the active question package is immutable through the generation flow.

### Authentication configuration

Copy `backend/.env.example` to `backend/.env` and set:

```env
JWT_SECRET=<long-random-secret>
ADMIN_PASSWORD=<admin-password>
WORKER_PASSWORD=<worker-password>
```

The default usernames created at startup are `admin` and `worker`. Passwords are hashed with Argon2; JWTs are used for authenticated API access.

Start the backend and frontend normally:

```bash
cd backend
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# another terminal
cd frontend
npm install
npm run dev
```

Open the frontend at `http://localhost:5173`. The application always starts at the login screen and selects the dashboard from the authenticated user's server-side role.
