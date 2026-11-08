from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Notification, Order, Prescription, RefillSchedule, User
from ..security import require_role
from ..services import gate
from ..services.serialize import order_out

router = APIRouter(prefix="/store", tags=["store"])
Staff = Depends(require_role("store_staff"))


class PackIn(BaseModel):
    invoice_no: str = Field(pattern=r"^[A-Za-z0-9/\-]{3,30}$")


class HandoverIn(BaseModel):
    handed_to: str = Field(min_length=2, max_length=60)


def _mine(db: Session, order_id: int, staff: User) -> Order:
    o = db.get(Order, order_id)
    if not o or o.store_id != staff.store_id:   # 404, so other stores' orders cannot be probed
        raise HTTPException(404, "Order not found")
    return o


@router.get("/orders")
def orders(staff: User = Staff, db: Session = Depends(get_db)):
    rows = db.scalars(select(Order).where(Order.store_id == staff.store_id,
                      Order.status.in_(["APPROVED", "PACKED", "DISPATCHED"])).order_by(Order.id)).all()
    out = []
    for o in rows:
        d = order_out(o)
        d["customer"] = db.get(User, o.user_id).name
        d["items"] = [i for i in d["items"] if i["status"] != "REJECTED"]
        out.append(d)
    return out


@router.post("/orders/{order_id}/pack")
def pack(order_id: int, body: PackIn, staff: User = Staff, db: Session = Depends(get_db)):
    o = _mine(db, order_id, staff)
    if o.status != "APPROVED":
        raise HTTPException(409, f"Order is {o.status}; it cannot be packed")
    live = [i for i in o.items if i.status != "REJECTED"]
    if not live or any(i.status != "APPROVED" for i in live):
        raise HTTPException(409, "Every item must be approved by a pharmacist before packing")
    dup = db.scalars(select(Order.id).where(Order.store_id == o.store_id, Order.invoice_no == body.invoice_no,
                                            Order.id != o.id)).first()
    if dup:
        raise HTTPException(409, "This invoice number is already used at your store")
    try:
        for i in live:
            gate.advance_item(db, i, "PACKED")
    except gate.GateError as e:
        raise HTTPException(409, str(e))
    o.status, o.invoice_no, o.packed_at = "PACKED", body.invoice_no, datetime.now(timezone.utc)
    db.commit()
    return order_out(o)


@router.post("/orders/{order_id}/handover")
def handover(order_id: int, body: HandoverIn, staff: User = Staff, db: Session = Depends(get_db)):
    o = _mine(db, order_id, staff)
    if o.status != "PACKED":
        raise HTTPException(409, f"Order is {o.status}; pack it first")
    try:
        for i in o.items:
            if i.status == "PACKED":
                gate.advance_item(db, i, "DISPATCHED")
    except gate.GateError as e:
        raise HTTPException(409, str(e))
    o.status, o.handover_to, o.dispatched_at = "DISPATCHED", body.handed_to.strip(), datetime.now(timezone.utc)
    _remember_for_refills(db, o)
    db.add(Notification(user_id=o.user_id, channel="sms",
                        body=f"Order {o.code} is on its way from {o.store.name} with {o.handover_to}."))
    db.commit()
    return order_out(o)


def _remember_for_refills(db: Session, o: Order) -> None:
    """Dispatch starts the refill clock. Doses per day come from the AI draft only if it read them."""
    rx = db.get(Prescription, o.prescription_id) if o.prescription_id else None
    doses = {i["product_id"]: i.get("doses_per_day") for i in (rx.ai_draft or {}).get("items", [])} if rx else {}
    for it in o.items:
        if it.status != "DISPATCHED":
            continue
        s = db.scalars(select(RefillSchedule).where(
            RefillSchedule.user_id == o.user_id, RefillSchedule.profile_id == o.profile_id,
            RefillSchedule.product_id == it.product_id)).first()
        if not s:
            s = RefillSchedule(user_id=o.user_id, profile_id=o.profile_id, product_id=it.product_id,
                               qty=it.qty, doses_per_day=doses.get(it.product_id))
            db.add(s)
        s.qty, s.last_order_at, s.prescription_id, s.last_reminded_at = it.qty, datetime.now(timezone.utc), o.prescription_id, None
        s.doses_per_day = s.doses_per_day or doses.get(it.product_id)   # a dose the customer confirmed wins
