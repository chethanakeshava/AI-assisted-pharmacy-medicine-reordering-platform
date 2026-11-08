from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
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


@router.post("/request-otp")
def request_otp(body: PhoneIn, db: Session = Depends(get_db)):
    if not db.scalars(select(User).where(User.phone == body.phone)).first():
        raise HTTPException(404, "No account for this number")
    since = datetime.now(timezone.utc) - timedelta(minutes=10)
    recent = db.scalar(select(func.count()).select_from(OtpCode).where(OtpCode.phone == body.phone, OtpCode.created_at > since))
    if recent >= settings.otp_requests_per_10_min:
        raise HTTPException(429, "Too many code requests. Please wait a few minutes and try again.")
    code = issue_otp(db, body.phone)
    # Test mode: no SMS provider, so the code is returned for the on-screen dev inbox.
    return {"sent": True, "dev_otp": code if settings.app_env == "dev" else None}


@router.post("/verify-otp")
def verify_otp(body: VerifyIn, db: Session = Depends(get_db)):
    if not check_otp(db, body.phone, body.code):
        raise HTTPException(401, "Wrong or expired code")
    user = db.scalars(select(User).where(User.phone == body.phone)).one()
    return {"token": make_token(user), "role": user.role, "name": user.name}


@router.get("/me")
def me(user: User = Depends(current_user), db: Session = Depends(get_db)):
    profiles = db.scalars(select(FamilyProfile).where(FamilyProfile.user_id == user.id)).all()
    return {"id": user.id, "name": user.name, "role": user.role, "store_id": user.store_id,
            "store_name": db.get(Store, user.store_id).name if user.store_id else None,
            "profiles": [{"id": p.id, "name": p.name, "relation": p.relation} for p in profiles]}
