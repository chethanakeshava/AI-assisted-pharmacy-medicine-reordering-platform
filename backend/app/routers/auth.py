from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..config import settings
from ..db import get_db
from datetime import datetime, timedelta, timezone

from sqlalchemy import func

from ..models import FamilyProfile, OtpCode, Store, User
from ..security import check_otp, current_user, issue_otp, make_token

router = APIRouter(prefix="/auth", tags=["auth"])


class PhoneIn(BaseModel):
    phone: str = Field(pattern=r"^\d{10}$")


class VerifyIn(PhoneIn):
    code: str = Field(pattern=r"^\d{6}$")


class RegisterIn(PhoneIn):
    name: str = Field(max_length=80)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 2:
            raise ValueError("Name must contain at least 2 characters")
        return value


class RegisterVerifyIn(RegisterIn):
    code: str = Field(pattern=r"^\d{6}$")


def _enforce_otp_rate_limit(db: Session, phone: str) -> None:
    since = datetime.now(timezone.utc) - timedelta(minutes=10)
    recent = db.scalar(
        select(func.count()).select_from(OtpCode).where(
            OtpCode.phone == phone, OtpCode.created_at > since
        )
    )
    if recent >= settings.otp_requests_per_10_min:
        raise HTTPException(429, "Too many code requests. Please wait a few minutes and try again.")


@router.post("/request-otp")
def request_otp(body: PhoneIn, db: Session = Depends(get_db)):
    if not db.scalars(select(User).where(User.phone == body.phone)).first():
        raise HTTPException(404, "No account for this number")
    _enforce_otp_rate_limit(db, body.phone)
    code = issue_otp(db, body.phone)
    # Test mode: no SMS provider, so the code is returned for the on-screen dev inbox.
    return {"sent": True, "dev_otp": code if settings.app_env == "dev" else None}


@router.post("/register/request-otp")
def request_registration_otp(body: RegisterIn, db: Session = Depends(get_db)):
    if db.scalars(select(User).where(User.phone == body.phone)).first():
        raise HTTPException(409, "An account already exists for this number")
    _enforce_otp_rate_limit(db, body.phone)
    code = issue_otp(db, body.phone)
    return {"sent": True, "dev_otp": code if settings.app_env == "dev" else None}


@router.post("/verify-otp")
def verify_otp(body: VerifyIn, db: Session = Depends(get_db)):
    if not check_otp(db, body.phone, body.code):
        raise HTTPException(401, "Wrong or expired code")
    user = db.scalars(select(User).where(User.phone == body.phone)).one()
    return {"token": make_token(user), "role": user.role, "name": user.name}


@router.post("/register/verify-otp")
def verify_registration_otp(body: RegisterVerifyIn, db: Session = Depends(get_db)):
    if not check_otp(db, body.phone, body.code):
        raise HTTPException(401, "Wrong or expired code")
    if db.scalars(select(User).where(User.phone == body.phone)).first():
        raise HTTPException(409, "An account already exists for this number")

    user = User(phone=body.phone, name=body.name, role="customer")
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        if db.scalars(select(User).where(User.phone == body.phone)).first():
            raise HTTPException(409, "An account already exists for this number")
        raise
    db.refresh(user)
    return {"token": make_token(user), "role": user.role, "name": user.name}


@router.get("/me")
def me(user: User = Depends(current_user), db: Session = Depends(get_db)):
    profiles = db.scalars(select(FamilyProfile).where(FamilyProfile.user_id == user.id)).all()
    return {"id": user.id, "name": user.name, "role": user.role, "store_id": user.store_id,
            "store_name": db.get(Store, user.store_id).name if user.store_id else None,
            "profiles": [{"id": p.id, "name": p.name, "relation": p.relation} for p in profiles]}
