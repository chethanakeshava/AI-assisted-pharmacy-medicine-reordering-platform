"""Parse and validate the daily stock CSV (columns: store, product, qty). All-or-nothing."""
import csv
import io

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Product, Stock, Store

MAX_ERRORS = 20


def apply_stock_csv(db: Session, text: str) -> tuple[int, list[str]]:
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames or {"store", "product", "qty"} - {f.strip().lower() for f in reader.fieldnames}:
        return 0, ["The file needs the columns: store, product, qty"]
    stores = {s.name.lower(): s for s in db.scalars(select(Store)).all()}
    products = {p.name.lower(): p for p in db.scalars(select(Product)).all()}
    updates, errors = {}, []
    for n, raw in enumerate(reader, start=2):
        row = {(k or "").strip().lower(): (v or "").strip() for k, v in raw.items()}
        store, prod = stores.get(row["store"].lower()), products.get(row["product"].lower())
        try:
            qty = int(row["qty"])
            if qty < 0 or qty > 100000:
                raise ValueError
        except ValueError:
            qty = None
        if not store:
            errors.append(f"Line {n}: unknown store '{row['store']}'")
        elif not prod:
            errors.append(f"Line {n}: unknown product '{row['product']}'")
        elif qty is None:
            errors.append(f"Line {n}: quantity must be a whole number from 0 to 100000")
        else:
            updates[(store.id, prod.id)] = qty
    if errors:
        return 0, errors[:MAX_ERRORS]
    existing = {(s.store_id, s.product_id): s for s in db.scalars(select(Stock)).all()}
    for key, qty in updates.items():
        if key in existing:
            existing[key].qty = qty
        else:
            db.add(Stock(store_id=key[0], product_id=key[1], qty=qty))
    return len(updates), []
