"""Route an approved order to the nearest store that has every approved item in stock."""
from math import asin, cos, radians, sin, sqrt

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Order, Stock, Store, User

DEFAULT_LOCATION = (22.5726, 88.3639)  # Kolkata centre, used when a customer has no saved location


def haversine_km(lat1, lng1, lat2, lng2) -> float:
    dlat, dlng = radians(lat2 - lat1), radians(lng2 - lng1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng / 2) ** 2
    return 6371 * 2 * asin(sqrt(a))


def route_order(db: Session, order: Order) -> bool:
    """Reserve stock at the nearest store that can fill the whole order. Returns False if none can."""
    if order.store_id:
        return True
    need: dict[int, int] = {}
    for it in order.items:
        if it.status == "APPROVED":
            need[it.product_id] = need.get(it.product_id, 0) + it.qty
    if not need:
        return False
    user = db.get(User, order.user_id)
    lat, lng = (user.lat, user.lng) if user.lat is not None and user.lng is not None else DEFAULT_LOCATION
    ranked = sorted(db.scalars(select(Store)).all(), key=lambda s: haversine_km(lat, lng, s.lat, s.lng))
    for store in ranked:
        # FOR UPDATE on PostgreSQL stops two orders reserving the same last pack (ignored by SQLite).
        rows = db.scalars(select(Stock).where(Stock.store_id == store.id, Stock.product_id.in_(need))
                          .with_for_update()).all()
        have = {r.product_id: r for r in rows}
        if all(pid in have and have[pid].qty >= q for pid, q in need.items()):
            for pid, q in need.items():
                have[pid].qty -= q
            order.store_id = store.id
            order.distance_km = round(haversine_km(lat, lng, store.lat, store.lng), 1)
            order.routing_note = None
            return True
    order.routing_note = "No single store has every item in stock"
    return False


def reroute_waiting(db: Session) -> int:
    """After a new stock file, retry orders that were waiting for stock."""
    n = 0
    for o in db.scalars(select(Order).where(Order.status == "NO_STOCK")).all():
        if route_order(db, o):
            o.status = "APPROVED"
            n += 1
    return n
