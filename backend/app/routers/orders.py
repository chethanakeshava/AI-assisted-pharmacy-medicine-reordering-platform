from typing import Literal

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import FamilyProfile, Order, OrderItem, Prescription, Product, User
from ..security import require_role
from ..services import crypto, extractor, matcher
from ..services.gate import GATED, is_sellable
from ..services.serialize import order_out
from ..services.uploads import read_prescription_image

router = APIRouter(prefix="/orders", tags=["orders"])
MAX_QTY = 20


class ItemIn(BaseModel):
    product_id: int
    qty: int = Field(ge=1, le=MAX_QTY)


class OrderIn(BaseModel):
    payment_method: Literal["COD", "UPI_TEST"] = "COD"
    profile_id: int | None = None
    prescription_id: int | None = None
    items: list[ItemIn] = Field(min_length=1, max_length=30)


@router.post("", status_code=201)
def create(body: OrderIn, user: User = Depends(require_role("customer")), db: Session = Depends(get_db)):
    if body.profile_id is not None:
        prof = db.get(FamilyProfile, body.profile_id)
        if not prof or prof.user_id != user.id:
            raise HTTPException(404, "Profile not found")
    if body.prescription_id is not None:
        rx = db.get(Prescription, body.prescription_id)
        if not rx or rx.user_id != user.id:
            raise HTTPException(404, "Prescription not found")
    order = Order(code="tmp", user_id=user.id, profile_id=body.profile_id,
                  prescription_id=body.prescription_id, status="AWAITING_PHARMACIST",
                  payment_method=body.payment_method)
    needs_rx = False
    for it in body.items:
        p = db.get(Product, it.product_id)
        if not p:
            raise HTTPException(422, f"Product {it.product_id} not found")
        if not is_sellable(db, p.schedule):
            raise HTTPException(422, f"{p.name} cannot be sold online")
        needs_rx |= p.schedule in GATED
        order.items.append(OrderItem(product_id=p.id, qty=it.qty, schedule=p.schedule, unit_price=p.price))
    if needs_rx and body.prescription_id is None:
        raise HTTPException(422, "A prescription is required for these medicines")
    db.add(order)
    db.flush()
    order.code = f"RX-{50300 + order.id}"
    db.commit()
    return order_out(order)


@router.get("")
def mine(user: User = Depends(require_role("customer")), db: Session = Depends(get_db)):
    rows = db.scalars(select(Order).where(Order.user_id == user.id).order_by(Order.id.desc())).all()
    return [order_out(o) for o in rows]


def _own(db: Session, order_id: int, user: User) -> Order:
    o = db.get(Order, order_id)
    if not o or o.user_id != user.id:
        raise HTTPException(404, "Order not found")
    return o


@router.get("/{order_id}")
def one(order_id: int, user: User = Depends(require_role("customer")), db: Session = Depends(get_db)):
    o = _own(db, order_id, user)
    d = order_out(o)
    rx = db.get(Prescription, o.prescription_id) if o.prescription_id else None
    d["review_note"] = rx.review_note if rx else None
    return d


@router.post("/{order_id}/reorder", status_code=201)
def reorder(order_id: int, user: User = Depends(require_role("customer")), db: Session = Depends(get_db)):
    """One-tap reorder: same medicines, same prescription. A pharmacist still checks it again."""
    old = _own(db, order_id, user)
    if old.status not in {"APPROVED", "PACKED", "DISPATCHED"}:
        raise HTTPException(409, "Only a completed order can be reordered")
    rx = db.get(Prescription, old.prescription_id) if old.prescription_id else None
    if rx and rx.status in {"REUPLOAD", "REJECTED"}:
        raise HTTPException(409, "This prescription needs to be uploaded again")
    new = Order(code="tmp", user_id=user.id, profile_id=old.profile_id,
                prescription_id=old.prescription_id, status="AWAITING_PHARMACIST",
                payment_method=old.payment_method)
    for it in old.items:
        p = db.get(Product, it.product_id)
        if it.status == "REJECTED" or not is_sellable(db, p.schedule):
            continue
        new.items.append(OrderItem(product_id=p.id, qty=it.qty, schedule=p.schedule, unit_price=p.price))
    if not new.items:
        raise HTTPException(409, "Nothing from this order can be reordered")
    if any(i.schedule in GATED for i in new.items) and rx is None:
        raise HTTPException(409, "A prescription is needed to reorder these medicines")
    db.add(new)
    db.flush()
    new.code = f"RX-{50300 + new.id}"
    db.commit()
    return order_out(new)


@router.post("/{order_id}/reupload")
async def reupload(order_id: int, file: UploadFile = File(...),
                   user: User = Depends(require_role("customer")), db: Session = Depends(get_db)):
    o = _own(db, order_id, user)
    if o.status != "ON_HOLD":
        raise HTTPException(409, "This order is not waiting for a new prescription")
    data, mime = await read_prescription_image(file)
    draft = matcher.build_draft(db, extractor.extract(data, mime, file.filename or ""))
    rx = Prescription(user_id=user.id, profile_id=o.profile_id, enc_path=crypto.save_encrypted(data), ai_draft=draft)
    db.add(rx)
    db.flush()
    o.prescription_id, o.status = rx.id, "AWAITING_PHARMACIST"
    db.commit()
    return order_out(o)


@router.post("/{order_id}/pay")
def pay(order_id: int, user: User = Depends(require_role("customer")), db: Session = Depends(get_db)):
    """Mock UPI payment (test mode). Allowed once the pharmacist has approved, because only then is the amount final."""
    o = _own(db, order_id, user)
    if o.payment_method != "UPI_TEST":
        raise HTTPException(409, "This order is paid on delivery")
    if o.payment_status == "PAID_TEST":
        raise HTTPException(409, "This order is already paid")
    if o.status not in {"APPROVED", "NO_STOCK", "PACKED"}:
        raise HTTPException(409, "You can pay after the pharmacist approves your order")
    o.payment_status = "PAID_TEST"
    db.commit()
    return order_out(o)
