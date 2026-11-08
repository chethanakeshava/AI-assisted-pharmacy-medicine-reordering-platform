from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import User
from ..security import require_role
from ..services.reminders import send_due_reminders
from ..services.routing import reroute_waiting
from ..services.stockcsv import apply_stock_csv

router = APIRouter(tags=["stock"])
MAX_CSV = 1024 * 1024


@router.post("/stock/upload")
async def upload_stock(file: UploadFile = File(...), _: User = Depends(require_role("pharmacist")),
                       db: Session = Depends(get_db)):
    raw = await file.read(MAX_CSV + 1)
    if len(raw) > MAX_CSV:
        raise HTTPException(413, "File is too large (max 1 MB)")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(422, {"errors": ["The file must be a UTF-8 CSV"]})
    applied, errors = apply_stock_csv(db, text)
    if errors:
        db.rollback()
        raise HTTPException(422, {"errors": errors})  # nothing is applied unless every row is valid
    rerouted = reroute_waiting(db)
    db.commit()
    return {"applied": applied, "rerouted": rerouted}


@router.post("/admin/run-reminders")
def run_reminders(_: User = Depends(require_role("pharmacist")), db: Session = Depends(get_db)):
    """Normally a daily scheduled job (python -m app.jobs). Exposed so reviewers can trigger it."""
    return {"sent": send_due_reminders(db)}
