from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Notification, Order, OrderItem, Prescription, RefillSchedule, User
from ..security import require_role
from ..services.gate import GATED, is_sellable
from ..services.reminders import view
from ..services.serialize import order_out

router = APIRouter(tags=["refills"])
Cust = Depends(require_role("customer"))


class DoseIn(BaseModel):
    doses_per_day: float = Field(ge=0.25, le=8)


def _mine(db: Session, rid: int, user: User) -> RefillSchedule:
    s = db.get(RefillSchedule, rid)
    if not s or s.user_id != user.id:
        raise HTTPException(404, "Refill not found")
    return s


@router.get("/refills")
def refills(user: User = Cust, db: Session = Depends(get_db)):
    rows = [view(s) for s in db.scalars(select(RefillSchedule).where(RefillSchedule.user_id == user.id)).all()]
    order = {"due": 0, "upcoming": 1, "needs_dose": 2}
    return sorted(rows, key=lambda r: (order[r["state"]], r["days_left"] if r["days_left"] is not None else 9999))


@router.patch("/refills/{rid}")
def set_dose(rid: int, body: DoseIn, user: User = Cust, db: Session = Depends(get_db)):
    s = _mine(db, rid, user)
    s.doses_per_day = body.doses_per_day   # confirmed by the customer, never guessed
    s.last_reminded_at = None
    db.commit()
    return view(s)


@router.delete("/refills/{rid}", status_code=204)
def stop(rid: int, user: User = Cust, db: Session = Depends(get_db)):
    db.delete(_mine(db, rid, user))
    db.commit()


@router.post("/refills/{rid}/reorder", status_code=201)
def reorder(rid: int, user: User = Cust, db: Session = Depends(get_db)):
    s = _mine(db, rid, user)
    p = s.product
    if not is_sellable(db, p.schedule):
        raise HTTPException(409, f"{p.name} cannot be sold online")
    rx = db.get(Prescription, s.prescription_id) if s.prescription_id else None
    if p.schedule in GATED and (rx is None or rx.status in {"REUPLOAD", "REJECTED"}):
        raise HTTPException(409, "Please upload a new prescription to reorder this medicine")
    o = Order(code="tmp", user_id=user.id, profile_id=s.profile_id, prescription_id=s.prescription_id,
              status="AWAITING_PHARMACIST")
    o.items.append(OrderItem(product_id=p.id, qty=s.qty, schedule=p.schedule, unit_price=p.price))
    db.add(o)
    db.flush()
    o.code = f"RX-{50300 + o.id}"
    db.commit()
    return order_out(o)


@router.get("/notifications")
def notifications(user: User = Cust, db: Session = Depends(get_db)):
    rows = db.scalars(select(Notification).where(Notification.user_id == user.id)
                      .order_by(Notification.id.desc()).limit(50)).all()
    return [{"id": n.id, "channel": n.channel, "body": n.body, "created_at": n.created_at.isoformat()} for n in rows]
