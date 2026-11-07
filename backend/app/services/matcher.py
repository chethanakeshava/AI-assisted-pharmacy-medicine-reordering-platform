"""Match AI-read names to the catalog and attach confidence flags. Pure logic, easy to test."""
import re
from difflib import SequenceMatcher

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import settings
from ..models import Product
from .gate import BLOCKED_ONLINE


def _norm(s: str) -> str:
    s = re.sub(r"\(generic\)", "", s.lower())
    return re.sub(r"[^a-z0-9 ]+", " ", s).strip()


def _is_generic(p: Product) -> bool:
    return "(generic)" in p.name.lower()


def best_match(products: list[Product], raw_name: str, strength: str | None):
    query = _norm(f"{raw_name} {strength or ''}")
    best, score = None, 0.0
    for p in sorted(products, key=_is_generic):  # on ties the branded entry wins
        s = SequenceMatcher(None, query, _norm(p.name)).ratio()
        if s > score:
            best, score = p, s
    return (best, round(score, 2)) if score >= settings.match_threshold else (None, round(score, 2))


def build_draft(db: Session, extracted: dict) -> dict:
    products = db.scalars(select(Product)).all()
    items = []
    for it in extracted["items"]:
        prod, score = best_match(products, it["raw_name"], it["strength"])
        conf = round(min(it["confidence"], score), 2)
        row = {**it, "match_score": score, "confidence": conf, "product_id": None, "product_name": None,
               "schedule": None, "blocked": False, "generic_options": [],
               "low_confidence": conf < settings.ai_confidence_threshold or prod is None}
        if prod:
            row.update(product_id=prod.id, product_name=prod.name, schedule=prod.schedule,
                       blocked=prod.schedule in BLOCKED_ONLINE)
            if not row["blocked"]:
                row["generic_options"] = [
                    {"product_id": g.id, "name": g.name, "price": g.price, "saving": round(prod.price - g.price, 2)}
                    for g in products if g.id != prod.id and g.generic_name == prod.generic_name
                    and g.schedule == prod.schedule and g.price < prod.price]
        items.append(row)
    return {**extracted, "items": items}
