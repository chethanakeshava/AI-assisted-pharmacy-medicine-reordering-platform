"""Dispatch gate: the AI never decides; a pharmacist's approval is required for H/H1 items."""
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from ..models import OrderItem, Rule, User

GATED = {"H", "H1"}
BLOCKED_ONLINE = {"X", "NARCOTIC"}
ALLOWED_NEXT = {
    "PENDING": {"APPROVED", "REJECTED"},
    "APPROVED": {"PACKED"},
    "PACKED": {"DISPATCHED"},
}


class GateError(Exception):
    pass


def is_sellable(db: Session, schedule: str) -> bool:
    if schedule in BLOCKED_ONLINE:
        return False  # hard floor, even if the rules table is edited
    rule = db.get(Rule, schedule)
    return True if rule is None else bool(rule.sellable_online)


def approve_item(db: Session, item: OrderItem, pharmacist: User) -> None:
    if pharmacist.role != "pharmacist":
        raise GateError("Only a pharmacist can approve")
    if item.status != "PENDING":
        raise GateError(f"Cannot approve an item that is {item.status}")
    item.status, item.approved_by = "APPROVED", pharmacist.id
    item.approved_at = datetime.now(timezone.utc)
    db.flush()


def reject_item(db: Session, item: OrderItem, pharmacist: User, reason: str) -> None:
    if pharmacist.role != "pharmacist":
        raise GateError("Only a pharmacist can reject")
    if not reason or not reason.strip():
        raise GateError("A reason is required to reject")
    item.status, item.reject_reason = "REJECTED", reason.strip()
    db.flush()


def advance_item(db: Session, item: OrderItem, new_status: str) -> None:
    if new_status not in ALLOWED_NEXT.get(item.status, set()):
        raise GateError(f"{item.status} -> {new_status} is not allowed")
    if new_status in {"PACKED", "DISPATCHED"} and item.schedule in GATED and item.approved_by is None:
        raise GateError("Schedule H/H1 item needs pharmacist approval before it can move on")
    item.status = new_status
    db.flush()
