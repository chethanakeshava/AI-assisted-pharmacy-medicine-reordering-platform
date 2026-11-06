import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import settings
from .db import get_db
from .models import OtpCode, User

bearer = HTTPBearer(auto_error=False)


def hash_otp(phone: str, code: str) -> str:
    return hmac.new(settings.otp_secret.encode(), f"{phone}:{code}".encode(), hashlib.sha256).hexdigest()


def issue_otp(db: Session, phone: str) -> str:
    code = f"{secrets.randbelow(10**6):06d}"
    db.add(OtpCode(phone=phone, code_hash=hash_otp(phone, code),
                   expires_at=datetime.now(timezone.utc) + timedelta(seconds=settings.otp_ttl_seconds)))
    db.commit()
    return code


def check_otp(db: Session, phone: str, code: str) -> bool:
    row = db.scalars(select(OtpCode).where(OtpCode.phone == phone, OtpCode.used == 0)
                     .order_by(OtpCode.id.desc())).first()
    if not row or row.attempts >= settings.otp_max_attempts:
        return False
    exp = row.expires_at if row.expires_at.tzinfo else row.expires_at.replace(tzinfo=timezone.utc)
    if exp < datetime.now(timezone.utc):
        return False
    row.attempts += 1
    ok = hmac.compare_digest(row.code_hash, hash_otp(phone, code))
    if ok:
        row.used = 1
    db.commit()
    return ok


def make_token(user: User) -> str:
    payload = {"sub": str(user.id), "role": user.role,
               "exp": datetime.now(timezone.utc) + timedelta(hours=12)}
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def current_user(cred: HTTPAuthorizationCredentials = Depends(bearer), db: Session = Depends(get_db)) -> User:
    if not cred:
        raise HTTPException(401, "Not signed in")
    try:
        data = jwt.decode(cred.credentials, settings.jwt_secret, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(401, "Session expired")
    user = db.get(User, int(data["sub"]))
    if not user:
        raise HTTPException(401, "Unknown user")
    return user


def require_role(*roles: str):
    def dep(user: User = Depends(current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(403, "Not allowed for your role")
        return user
    return dep
