from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import AccessLog, FamilyProfile, Prescription, Product, User
from ..security import current_user, require_role
from ..services import crypto, extractor, matcher
from ..services.uploads import read_prescription_image

router = APIRouter(prefix="/prescriptions", tags=["prescriptions"])


@router.post("", status_code=201)
async def upload(file: UploadFile = File(...), profile_id: int | None = Form(None),
                 user: User = Depends(require_role("customer")), db: Session = Depends(get_db)):
    if profile_id is not None:
        prof = db.get(FamilyProfile, profile_id)
        if not prof or prof.user_id != user.id:
            raise HTTPException(404, "Profile not found")
    data, mime = await read_prescription_image(file)
    draft = matcher.build_draft(db, extractor.extract(data, mime, file.filename or ""))
    rx = Prescription(user_id=user.id, profile_id=profile_id, enc_path=crypto.save_encrypted(data), ai_draft=draft)
    db.add(rx)
    db.commit()
    return {"id": rx.id, "status": rx.status, "readable": draft["readable"], "item_count": len(draft["items"])}


@router.get("/{rx_id}/suggestions")
def suggestions(rx_id: int, user: User = Depends(require_role("customer")), db: Session = Depends(get_db)):
    """What the customer sees: a pre-filled cart to review. Generics are pharmacist-only; blocked items are hidden."""
    rx = db.get(Prescription, rx_id)
    if not rx or rx.user_id != user.id:
        raise HTTPException(404, "Prescription not found")
    d = rx.ai_draft or {"items": [], "readable": None}
    return {"readable": d.get("readable"),
            "message": "Suggested from your photo. A pharmacist will check every item before anything is sent.",
            "items": [{"product_id": i["product_id"], "name": i["product_name"], "qty": i["qty"],
                       "pack": p.pack, "price": p.price, "schedule": p.schedule,
                       "needs_check": i["low_confidence"]}
                      for i in d["items"] if i["product_id"] and not i["blocked"]
                      for p in [db.get(Product, i["product_id"])]]}


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
