import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models import Order, OrderItem, Product, User
from app.services import gate


def pending_item(db):
    return db.scalars(select(OrderItem).join(Order).where(Order.code == "RX-50214")).one()


def pharmacist(db):
    return db.scalars(select(User).where(User.role == "pharmacist")).one()


def test_unapproved_h_item_cannot_be_packed(db):
    with pytest.raises(gate.GateError):
        gate.advance_item(db, pending_item(db), "PACKED")


def test_pending_cannot_skip_to_packed_even_after_state_check(db):
    item = pending_item(db)
    item.status = "PACKED"  # bypass the service on purpose
    with pytest.raises(IntegrityError):
        db.commit()  # DB constraint is the last line of defence
    db.rollback()


def test_approve_then_pack_then_dispatch(db):
    item = pending_item(db)
    gate.approve_item(db, item, pharmacist(db))
    gate.advance_item(db, item, "PACKED")
    gate.advance_item(db, item, "DISPATCHED")
    db.commit()
    assert item.status == "DISPATCHED" and item.approved_by is not None


def test_only_pharmacist_can_approve(db):
    store_user = db.scalars(select(User).where(User.role == "store_staff")).one()
    with pytest.raises(gate.GateError):
        gate.approve_item(db, pending_item(db), store_user)


def test_reject_needs_reason(db):
    with pytest.raises(gate.GateError):
        gate.reject_item(db, pending_item(db), pharmacist(db), "  ")


def test_schedule_x_and_narcotic_never_sellable(db):
    assert not gate.is_sellable(db, "X") and not gate.is_sellable(db, "NARCOTIC")
    assert gate.is_sellable(db, "H") and gate.is_sellable(db, "OTC")


def test_db_rejects_narcotic_order_item(db):
    p = db.scalars(select(Product).where(Product.schedule == "NARCOTIC")).one()
    o = db.scalars(select(Order)).first()
    db.add(OrderItem(order_id=o.id, product_id=p.id, qty=1, schedule="NARCOTIC", unit_price=1))
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()
