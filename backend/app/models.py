from datetime import datetime, timezone

from sqlalchemy import (JSON, CheckConstraint, DateTime, Float, ForeignKey,
                        Integer, String, Text, UniqueConstraint)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def now():
    return datetime.now(timezone.utc)


class Store(Base):
    __tablename__ = "stores"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True)
    lat: Mapped[float] = mapped_column(Float)
    lng: Mapped[float] = mapped_column(Float)


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    phone: Mapped[str] = mapped_column(String(15), unique=True)
    name: Mapped[str] = mapped_column(String(80))
    role: Mapped[str] = mapped_column(String(20))  # customer | pharmacist | store_staff
    store_id: Mapped[int | None] = mapped_column(ForeignKey("stores.id"), nullable=True)
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    __table_args__ = (CheckConstraint("role IN ('customer','pharmacist','store_staff')", name="ck_user_role"),)


class FamilyProfile(Base):
    __tablename__ = "family_profiles"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String(80))
    relation: Mapped[str] = mapped_column(String(30), default="self")


class Product(Base):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    generic_name: Mapped[str] = mapped_column(String(120))
    pack: Mapped[str] = mapped_column(String(60))
    units_per_pack: Mapped[int] = mapped_column(Integer)
    schedule: Mapped[str] = mapped_column(String(8))  # OTC | H | H1 | X | NARCOTIC
    price: Mapped[float] = mapped_column(Float)


class Stock(Base):
    __tablename__ = "stock"
    id: Mapped[int] = mapped_column(primary_key=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    qty: Mapped[int] = mapped_column(Integer, default=0)
    __table_args__ = (UniqueConstraint("store_id", "product_id"),)


class Rule(Base):
    """Configurable schedule rules; regulations are not final, so no hard-coding."""
    __tablename__ = "rules"
    schedule: Mapped[str] = mapped_column(String(8), primary_key=True)
    sellable_online: Mapped[int] = mapped_column(Integer, default=1)
    needs_prescription: Mapped[int] = mapped_column(Integer, default=0)
    needs_register: Mapped[int] = mapped_column(Integer, default=0)


class Prescription(Base):
    __tablename__ = "prescriptions"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    profile_id: Mapped[int | None] = mapped_column(ForeignKey("family_profiles.id"), nullable=True)
    enc_path: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(20), default="PENDING")  # PENDING|APPROVED|REUPLOAD|REJECTED
    ai_draft: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    review_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Order(Base):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(12), unique=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    profile_id: Mapped[int | None] = mapped_column(ForeignKey("family_profiles.id"), nullable=True)
    store_id: Mapped[int | None] = mapped_column(ForeignKey("stores.id"), nullable=True)
    prescription_id: Mapped[int | None] = mapped_column(ForeignKey("prescriptions.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(24), default="AWAITING_PHARMACIST")
    invoice_no: Mapped[str | None] = mapped_column(String(30), nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    items: Mapped[list["OrderItem"]] = relationship(back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    qty: Mapped[int] = mapped_column(Integer)
    schedule: Mapped[str] = mapped_column(String(8))  # snapshot at order time
    unit_price: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(12), default="PENDING")  # PENDING|APPROVED|REJECTED|PACKED|DISPATCHED
    approved_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reject_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    order: Mapped[Order] = relationship(back_populates="items")
    __table_args__ = (
        # Last line of defence: even buggy code cannot pack/dispatch an unapproved H/H1 item.
        CheckConstraint(
            "NOT (schedule IN ('H','H1') AND status IN ('PACKED','DISPATCHED') AND approved_by IS NULL)",
            name="ck_h_items_need_approval"),
        CheckConstraint("NOT (status = 'APPROVED' AND approved_by IS NULL)", name="ck_approved_has_approver"),
        CheckConstraint("schedule NOT IN ('X','NARCOTIC')", name="ck_no_x_online"),
    )


class H1Register(Base):
    __tablename__ = "h1_register"
    id: Mapped[int] = mapped_column(primary_key=True)
    order_item_id: Mapped[int] = mapped_column(ForeignKey("order_items.id"), unique=True)
    patient_name: Mapped[str] = mapped_column(String(80))
    prescriber_name: Mapped[str] = mapped_column(String(80))
    prescriber_reg_no: Mapped[str] = mapped_column(String(40))
    logged_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    logged_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class RefillSchedule(Base):
    __tablename__ = "refill_schedules"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    profile_id: Mapped[int | None] = mapped_column(ForeignKey("family_profiles.id"), nullable=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    qty: Mapped[int] = mapped_column(Integer)
    doses_per_day: Mapped[float] = mapped_column(Float, default=1)
    last_order_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Notification(Base):
    """Mock SMS/WhatsApp outbox."""
    __tablename__ = "notifications"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    channel: Mapped[str] = mapped_column(String(12), default="sms")
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class OtpCode(Base):
    __tablename__ = "otp_codes"
    id: Mapped[int] = mapped_column(primary_key=True)
    phone: Mapped[str] = mapped_column(String(15), index=True)
    code_hash: Mapped[str] = mapped_column(String(64))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    used: Mapped[int] = mapped_column(Integer, default=0)


class AccessLog(Base):
    """DPDP: every view of a prescription is logged."""
    __tablename__ = "access_log"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    prescription_id: Mapped[int] = mapped_column(ForeignKey("prescriptions.id"))
    action: Mapped[str] = mapped_column(String(20))
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
