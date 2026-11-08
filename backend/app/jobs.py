"""Daily job: python -m app.jobs  (schedule with cron or the host's scheduler)."""
from .db import SessionLocal
from .services.reminders import send_due_reminders

if __name__ == "__main__":
    with SessionLocal() as db:
        print(f"Reminders sent: {send_due_reminders(db)}")
