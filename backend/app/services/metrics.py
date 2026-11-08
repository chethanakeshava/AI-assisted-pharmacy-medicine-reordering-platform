from datetime import datetime, timedelta, timezone
from statistics import median

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models import AccessLog, Order, OrderItem, Store
from .reminders import aware

TARGET_MINUTES = 10


def minutes_between(start: datetime, end: datetime) -> float:
    return (aware(end) - aware(start)).total_seconds() / 60


def dashboard(db: Session, days: int = 30) -> dict:
    since = datetime.now(timezone.utc) - timedelta(days=days)
    orders = [o for o in db.scalars(select(Order)).all() if aware(o.created_at) >= since]
    verified = [minutes_between(o.created_at, o.verified_at) for o in orders if o.verified_at]
    decided = [o for o in orders if o.verified_at]
    rejected_orders = [o for o in decided if o.status == "REJECTED"]
    reasons: dict[str, int] = {}
    for it in db.scalars(select(OrderItem).where(OrderItem.status == "REJECTED")).all():
        if aware(it.order.created_at) >= since:
            reasons[it.reject_reason or "No reason"] = reasons.get(it.reject_reason or "No reason", 0) + 1
    by_store = []
    for s in db.scalars(select(Store).order_by(Store.name)).all():
        mine = [o for o in orders if o.store_id == s.id]
        done = [minutes_between(o.created_at, o.dispatched_at) / 60 for o in mine if o.dispatched_at]
        by_store.append({"store": s.name, "orders": len(mine), "dispatched": len(done),
                         "median_hours_to_dispatch": round(median(done), 1) if done else None})
    violations = db.scalar(select(func.count()).select_from(OrderItem).where(
        OrderItem.schedule.in_(["H", "H1"]), OrderItem.status.in_(["PACKED", "DISPATCHED"]),
        OrderItem.approved_by.is_(None)))
    return {
        "days": days, "orders": len(orders),
        "open": {k: sum(1 for o in orders if o.status == k) for k in ("AWAITING_PHARMACIST", "ON_HOLD", "NO_STOCK", "APPROVED", "PACKED")},
        "verification": {"count": len(verified), "median_minutes": round(median(verified), 1) if verified else None,
                         "within_target_pct": round(100 * sum(v <= TARGET_MINUTES for v in verified) / len(verified)) if verified else None,
                         "target_minutes": TARGET_MINUTES},
        "rejections": {"orders": len(rejected_orders),
                       "rate_pct": round(100 * len(rejected_orders) / len(decided)) if decided else None,
                       "reasons": sorted(({"reason": r, "count": c} for r, c in reasons.items()), key=lambda x: -x["count"])[:5]},
        "by_store": by_store,
        "gate_violations": violations,
        "prescription_views": db.scalar(select(func.count()).select_from(AccessLog)),
    }
