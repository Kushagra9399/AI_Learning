# Demo Runbook — 3 to 4 hour submission sprint

## 1. Start
Terminal 1:
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Terminal 2:
```cd frontend
npm install
npm run dev
```

Open the Vite URL.

## 2. Candidate demo
1. Enter a worker name, experience and work context containing "electrician".
2. Click **Download assessment package**.
3. Show the async job/waiting screen.
4. Complete the theory assessment.
5. Click **Save single attempt**.
6. Capture one image/video for a practical task.
7. Click **Submit for evaluation**.
8. Show the generated Assessment ID.
9. Click **Open assessor dashboard**.

## 3. Assessor demo
1. Show self-declaration and evidence.
2. Enter practical scores for the five tasks.
3. Click **Run AI-assisted evaluation**.
4. Show overall score, provisional pass/gap status and NOS results.
5. Explain that the AI calculation is standardized assistance, not certification.
6. Click **Sign off**.

## 4. Offline demo
For a quick demonstration, download the package first, then switch the browser to offline mode and reload/use the saved package. The assessment package and captured evidence remain in IndexedDB. When connectivity returns, queued submission/evidence synchronization resumes.

## 5. What to say
- "The worker declares prior learning instead of starting from a training curriculum."
- "The engine maps the declaration to a fixed QP/NOS competency framework."
- "Theory is available offline; practical evidence can be captured offline."
- "Standardized rubrics make assessor scoring more consistent."
- "AI organizes and calculates evidence; the authorized assessor retains final judgement."
- "The architecture is designed for low-connectivity environments."

## 6. Validation caveat
The repository contains an inter-assessor agreement harness, but its sample values are placeholders. Do not claim measured improvement until real anonymized assessor data is collected.
