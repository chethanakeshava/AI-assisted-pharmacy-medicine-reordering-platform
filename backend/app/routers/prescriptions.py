from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import AccessLog, FamilyProfile, Prescription, User
from ..security import current_user, require_role
from ..services import crypto
from ..services.uploads import read_image

router = APIRouter(prefix="/prescriptions", tags=["prescriptions"])


@router.post("", status_code=201)
async def upload(file: UploadFile = File(...), profile_id: int | None = Form(None),
                 user: User = Depends(require_role("customer")), db: Session = Depends(get_db)):
    if profile_id is not None:
        prof = db.get(FamilyProfile, profile_id)
        if not prof or prof.user_id != user.id:
            raise HTTPException(404, "Profile not found")
    data, _ = await read_image(file)
    rx = Prescription(user_id=user.id, profile_id=profile_id, enc_path=crypto.save_encrypted(data),
                      ai_draft={"readable": None, "items": [], "source": "not_run"})
    db.add(rx)
    db.commit()
    return {"id": rx.id, "status": rx.status}


@router.get("")
def mine(user: User = Depends(require_role("customer")), db: Session = Depends(get_db)):
    rows = db.scalars(select(Prescription).where(Prescription.user_id == user.id)
                      .order_by(Prescription.id.desc())).all()
    return [{"id": r.id, "status": r.status, "review_note": r.review_note,
             "created_at": r.created_at.isoformat()} for r in rows]


@router.get("/{rx_id}/image")
def image(rx_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    rx = db.get(Prescription, rx_id)
    # 404 (not 403) for other people's files so ids cannot be probed.
    if not rx or (user.role == "customer" and rx.user_id != user.id) or user.role == "store_staff":
        raise HTTPException(404, "Prescription not found")
    db.add(AccessLog(user_id=user.id, prescription_id=rx.id, action="view"))
    db.commit()
    data = crypto.read_decrypted(rx.enc_path)
    from ..services.uploads import sniff
    return Response(data, media_type=sniff(data) or "application/octet-stream",
                    headers={"Cache-Control": "no-store"})
