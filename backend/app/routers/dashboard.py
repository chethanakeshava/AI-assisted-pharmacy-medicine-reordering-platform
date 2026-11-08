from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import User
from ..security import require_role
from ..services.metrics import dashboard

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard")
def get_dashboard(days: int = Query(30, ge=1, le=365), _: User = Depends(require_role("ops")),
                  db: Session = Depends(get_db)):
    return dashboard(db, days)
