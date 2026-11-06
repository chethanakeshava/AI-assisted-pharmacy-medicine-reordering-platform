from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Product, User
from ..security import current_user
from ..services.gate import is_sellable

router = APIRouter(prefix="/catalog", tags=["catalog"])


@router.get("/search")
def search(q: str = Query(min_length=2, max_length=60), db: Session = Depends(get_db),
           _: User = Depends(current_user)):
    like = f"%{q}%"
    rows = db.scalars(select(Product).where(or_(Product.name.ilike(like),
                                                Product.generic_name.ilike(like))).limit(20)).all()
    return [{"id": p.id, "name": p.name, "pack": p.pack, "price": p.price, "schedule": p.schedule,
             "sellable": is_sellable(db, p.schedule),
             "needs_prescription": p.schedule in {"H", "H1"}} for p in rows]
