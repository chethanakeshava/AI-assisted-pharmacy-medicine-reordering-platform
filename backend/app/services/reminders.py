"""Refill maths and reminders. days_supply = packs x units per pack / doses per day."""
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Notification, Order, OrderItem, RefillSchedule

REMIND_BEFORE_DAYS = 3
OPEN = ("AWAITING_PHARMACIST", "ON_HOLD", "APPROVED", "NO_STOCK", "PACKED")


def aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def days_supply(units_per_pack: int, qty: int, doses_per_day: float | None) -> int | None:
    if not doses_per_day or doses_per_day <= 0:
        return None
    return int(qty * units_per_pack / doses_per_day)


def view(s: RefillSchedule, today: date | None = None) -> dict:
    today = today or datetime.now(timezone.utc).date()
    ds = days_supply(s.product.units_per_pack, s.qty, s.doses_per_day)
    out = {"id": s.id, "product_id": s.product_id, "product_name": s.product.name, "pack": s.product.pack,
           "qty": s.qty, "doses_per_day": s.doses_per_day, "days_supply": ds,
           "runout_date": None, "days_left": None, "state": "needs_dose"}
    if ds is not None:
        runout = (aware(s.last_order_at) + timedelta(days=ds)).date()
        left = (runout - today).days
        out.update(runout_date=runout.isoformat(), days_left=left,
                   state="due" if left <= REMIND_BEFORE_DAYS else "upcoming")
    return out


def send_due_reminders(db: Session, today: date | None = None) -> int:
    """Mock SMS into the notifications table. Idempotent per refill cycle; skipped while an order is open."""
    today = today or datetime.now(timezone.utc).date()
    sent = 0
    for s in db.scalars(select(RefillSchedule)).all():
        v = view(s, today)
        if v["state"] != "due":
            continue
        if s.last_reminded_at and aware(s.last_reminded_at) >= aware(s.last_order_at):
            continue
        open_order = db.scalars(select(Order.id).join(OrderItem).where(
            Order.user_id == s.user_id, OrderItem.product_id == s.product_id, Order.status.in_(OPEN))).first()
        if open_order:
            continue
        when = "has run out" if v["days_left"] < 0 else f"will run out around {v['runout_date']}"
        db.add(Notification(user_id=s.user_id, channel="sms",
                            body=f"Your {s.product.name} {when}. Reorder in one tap in MediBridge > Refills."))
        s.last_reminded_at = datetime.now(timezone.utc)
        sent += 1
    db.commit()
    return sent
