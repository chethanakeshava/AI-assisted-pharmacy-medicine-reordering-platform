# Pharmacy Reorder

Run backend (Day 1):
    cd backend && pip install -r requirements.txt && cp .env.example .env
    python -m app.seed && uvicorn app.main:app --reload
    pytest

Demo logins (test mode, OTP shown by the API in dev): customers 9000000001-3, pharmacist 9000000010, store staff 9000000020.
