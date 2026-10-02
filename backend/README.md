# RPL backend
Run: `pip install -r requirements.txt && uvicorn app.main:app --reload --port 8000`.
The API is intentionally asynchronous. The browser polls job IDs because a normal SPA cannot receive an inbound webhook reliably during low connectivity. Practical scores are assessor-entered; AI only assists with evidence organization and recommendation.
