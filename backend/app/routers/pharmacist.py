from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import H1Register, Notification, Order, OrderItem, Prescription, Product, Store, User
from ..security import require_role
from ..services import gate
from ..services.routing import route_order
from ..services.serialize import order_out

router = APIRouter(prefix="/pharmacist", tags=["pharmacist"])
Pharma = Depends(require_role("pharmacist"))


class H1Details(BaseModel):
    patient_name: str = Field(min_length=2, max_length=80)
    prescriber_name: str = Field(min_length=2, max_length=80)
    prescriber_reg_no: str = Field(min_length=2, max_length=40)


class ApproveIn(BaseModel):
    h1: H1Details | None = None


class ReasonIn(BaseModel):
    reason: str = Field(min_length=3, max_length=300)


class EditIn(BaseModel):
    product_id: int | None = None
    qty: int | None = Field(None, ge=1, le=20)


class AddIn(BaseModel):
    product_id: int
    qty: int = Field(ge=1, le=20)


def _open_order(db: Session, order_id: int) -> Order:
    o = db.get(Order, order_id)
    if not o:
        raise HTTPException(404, "Order not found")
    if o.status != "AWAITING_PHARMACIST":
        raise HTTPException(409, f"Order is {o.status}; it cannot be reviewed now")
    return o


def _item(o: Order, item_id: int) -> OrderItem:
    it = next((i for i in o.items if i.id == item_id), None)
    if not it:
        raise HTTPException(404, "Item not found")
    return it


def _fail(e: gate.GateError):
    raise HTTPException(409, str(e))


@router.get("/queue")
def queue(_: User = Pharma, db: Session = Depends(get_db)):
    rows = db.scalars(select(Order).where(Order.status.in_(["AWAITING_PHARMACIST", "ON_HOLD"]))
                      .order_by(Order.created_at)).all()
    out = []
    for o in rows:
        d = order_out(o)
        rx = db.get(Prescription, o.prescription_id) if o.prescription_id else None
        d["ai_draft"] = rx.ai_draft if rx else None
        d["customer"] = db.get(User, o.user_id).name
        out.append(d)
    return out


@router.post("/orders/{order_id}/items/{item_id}/approve")
def approve(order_id: int, item_id: int, body: ApproveIn | None = None, pharm: User = Pharma,
            db: Session = Depends(get_db)):
    o = _open_order(db, order_id)
    it = _item(o, item_id)
    rx = db.get(Prescription, o.prescription_id) if o.prescription_id else None
    if it.schedule in gate.GATED and (rx is None or rx.status == "REUPLOAD"):
        raise HTTPException(409, "A valid prescription is needed to approve this item")
    if it.schedule == "H1":
        if not body or not body.h1:
            raise HTTPException(422, "H1 items need patient and prescriber details for the register")
    try:
        gate.approve_item(db, it, pharm)
    except gate.GateError as e:
        _fail(e)
    if it.schedule == "H1":
        db.add(H1Register(order_item_id=it.id, logged_by=pharm.id, **body.h1.model_dump()))
    db.commit()
    return order_out(o)


@router.post("/orders/{order_id}/items/{item_id}/reject")
def reject(order_id: int, item_id: int, body: ReasonIn, pharm: User = Pharma, db: Session = Depends(get_db)):
    o = _open_order(db, order_id)
    try:
        gate.reject_item(db, _item(o, item_id), pharm, body.reason)
    except gate.GateError as e:
        _fail(e)
    db.commit()
    return order_out(o)


@router.patch("/orders/{order_id}/items/{item_id}")
def edit(order_id: int, item_id: int, body: EditIn, _: User = Pharma, db: Session = Depends(get_db)):
    o = _open_order(db, order_id)
    it = _item(o, item_id)
    if it.status != "PENDING":
        raise HTTPException(409, "Only items still pending can be edited")
    if body.product_id is not None:
        p = db.get(Product, body.product_id)
        if not p:
            raise HTTPException(422, "Product not found")
        if not gate.is_sellable(db, p.schedule):
            raise HTTPException(422, f"{p.name} cannot be sold online")
        it.product_id, it.schedule, it.unit_price = p.id, p.schedule, p.price
    if body.qty is not None:
        it.qty = body.qty
    db.commit()
    return order_out(o)


@router.post("/orders/{order_id}/items", status_code=201)
def add_item(order_id: int, body: AddIn, _: User = Pharma, db: Session = Depends(get_db)):
    o = _open_order(db, order_id)
    p = db.get(Product, body.product_id)
    if not p:
        raise HTTPException(422, "Product not found")
    if not gate.is_sellable(db, p.schedule):
        raise HTTPException(422, f"{p.name} cannot be sold online")
    o.items.append(OrderItem(product_id=p.id, qty=body.qty, schedule=p.schedule, unit_price=p.price))
    db.commit()
    return order_out(o)


@router.post("/orders/{order_id}/reupload")
def request_reupload(order_id: int, body: ReasonIn, _: User = Pharma, db: Session = Depends(get_db)):
    o = _open_order(db, order_id)
    rx = db.get(Prescription, o.prescription_id) if o.prescription_id else None
    if rx:
        rx.status, rx.review_note = "REUPLOAD", body.reason
    o.status = "ON_HOLD"
    db.add(Notification(user_id=o.user_id, channel="sms",
                        body=f"Order {o.code}: please upload a clearer prescription photo. {body.reason}"))
    db.commit()
    return order_out(o)


@router.post("/orders/{order_id}/finalize")
def finalize(order_id: int, _: User = Pharma, db: Session = Depends(get_db)):
    o = _open_order(db, order_id)
    if any(i.status == "PENDING" for i in o.items):
        raise HTTPException(409, "Every item must be approved or rejected first")
    approved = [i for i in o.items if i.status == "APPROVED"]
    o.status = "REJECTED" if not approved else "APPROVED"
    if approved and not route_order(db, o):
        o.status = "NO_STOCK"   # waits for the next stock file; the customer is told
    o.verified_at = datetime.now(timezone.utc)
    rx = db.get(Prescription, o.prescription_id) if o.prescription_id else None
    if rx:
        rx.status = "APPROVED" if approved else "REJECTED"
    if not approved:
        text = f"Order {o.code} could not be approved."
    elif o.status == "NO_STOCK":
        text = f"Order {o.code} is approved. We are finding a store that has all your medicines."
    else:
        text = f"Order {o.code} is approved and being prepared at {db.get(Store, o.store_id).name}."
    db.add(Notification(user_id=o.user_id, channel="sms", body=text))
    db.commit()
    return order_out(o)
