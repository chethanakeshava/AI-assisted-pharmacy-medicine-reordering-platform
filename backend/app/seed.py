"""Seed realistic, fake data (no real personal data). Run: python -m app.seed"""
import io
import random
import sys
from datetime import datetime, timedelta, timezone

from PIL import Image, ImageDraw, ImageFont

from sqlalchemy import select

from .config import settings
from .db import Base, SessionLocal, engine
from .services import crypto, extractor, matcher
from .models import (FamilyProfile, Order, OrderItem, Prescription, Product, RefillSchedule, Rule, Stock, Store, User)

STORES = [("Salt Lake", 22.5867, 88.4171), ("Behala", 22.4985, 88.3118), ("Howrah Maidan", 22.5850, 88.3426),
          ("Park Street", 22.5524, 88.3516), ("Dum Dum", 22.6228, 88.4222)]
# name, generic, pack, units, schedule, price
PRODUCTS = [
    ("Metformin 500 mg", "Metformin", "strip of 15", 15, "H", 120),
    ("Telmisartan 40 mg", "Telmisartan", "strip of 10", 10, "H", 285),
    ("Levothyroxine 50 mcg", "Levothyroxine", "bottle of 100", 100, "H", 190),
    ("Amlodipine 5 mg", "Amlodipine", "strip of 15", 15, "H", 55),
    ("Glimepiride 2 mg", "Glimepiride", "strip of 15", 15, "H", 98),
    ("Atorvastatin 10 mg", "Atorvastatin", "strip of 15", 15, "H", 110),
    ("Alprazolam 0.25 mg", "Alprazolam", "strip of 10", 10, "H1", 42),
    ("Tramadol 50 mg", "Tramadol", "strip of 10", 10, "H1", 75),
    ("Morphine 10 mg", "Morphine", "strip of 10", 10, "NARCOTIC", 150),
    ("Paracetamol 500 mg", "Paracetamol", "strip of 15", 15, "OTC", 30),
    ("Metformin 500 mg (Generic)", "Metformin", "strip of 15", 15, "H", 65),
    ("Telmisartan 40 mg (Generic)", "Telmisartan", "strip of 10", 10, "H", 140),
    ("Amlodipine 5 mg (Generic)", "Amlodipine", "strip of 15", 15, "H", 30),
    ("ORS sachet", "ORS", "pack of 5", 5, "OTC", 40),
    ("Vitamin D3 60K", "Cholecalciferol", "pack of 4", 4, "OTC", 130),
]
RULES = [("OTC", 1, 0, 0), ("H", 1, 1, 0), ("H1", 1, 1, 1), ("X", 0, 1, 0), ("NARCOTIC", 0, 1, 0)]


def fake_rx_png(patient: str, lines: list[str]) -> bytes:
    """A typed, obviously fake prescription image for demos (no real patient data)."""
    img = Image.new("RGB", (900, 1100), (236, 233, 226))
    d, f = ImageDraw.Draw(img), ImageFont.load_default(size=32)
    d.line((50, 50, 850, 50), fill="black", width=3)
    for i, t in enumerate(["Dr. A. Sample, MBBS (FAKE - DEMO ONLY)", "Reg. No: WB-00000", f"Patient: {patient}", "", "Rx", *lines, "", "Sign: A. Sample"]):
        d.text((60, 80 + i * 80), t, fill="black", font=f)
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()


def add_history(db, stores, prods, pharma):
    """~30 past orders so the central dashboard has something real to show (deterministic)."""
    rng = random.Random(42)
    names = ["Meera Das", "Sanjay Roy", "Pooja Nandi", "Imran Sheikh", "Tapan Saha", "Sunita Paul"]
    custs = [User(phone=f"90000000{40 + i}", name=n, role="customer", lat=22.55 + i * 0.01, lng=88.35 + i * 0.01)
             for i, n in enumerate(names)]
    db.add_all(custs)
    db.flush()
    gated = [p for p in prods.values() if p.schedule == "H"]
    store_list = list(stores.values())
    reasons = ["Prescription expired", "Dose not on prescription", "Illegible, no new photo sent"]
    now = datetime.now(timezone.utc)
    for n in range(30):
        p, st = rng.choice(gated), store_list[n % len(store_list)]
        created = now - timedelta(days=rng.randint(1, 20), hours=rng.randint(0, 8))
        verified = created + timedelta(minutes=rng.randint(3, 16))
        rejected = n % 7 == 3
        o = Order(code=f"RX-4{9000 + n}", user_id=custs[n % len(custs)].id, created_at=created, verified_at=verified,
                  status="REJECTED" if rejected else "DISPATCHED", store_id=None if rejected else st.id)
        it = OrderItem(product_id=p.id, qty=rng.randint(1, 4), schedule=p.schedule, unit_price=p.price)
        if rejected:
            it.status, it.reject_reason = "REJECTED", rng.choice(reasons)
        else:
            it.status, it.approved_by, it.approved_at = "DISPATCHED", pharma.id, verified
            o.invoice_no, o.handover_to = f"H-{1000 + n}", "Delivery partner"
            o.packed_at = verified + timedelta(minutes=rng.randint(20, 90))
            o.dispatched_at = o.packed_at + timedelta(minutes=rng.randint(10, 60))
        o.items.append(it)
        db.add(o)


def run(force: bool = False):
    if settings.app_env != "dev" and not force:
        raise SystemExit("Refusing to wipe a non-dev database. Re-run with --force if you really mean it.")
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    db = SessionLocal()
    stores = {n: Store(name=n, lat=la, lng=lo) for n, la, lo in STORES}
    db.add_all(stores.values())
    db.add_all(Rule(schedule=s, sellable_online=a, needs_prescription=b, needs_register=c) for s, a, b, c in RULES)
    prods = {p[0]: Product(name=p[0], generic_name=p[1], pack=p[2], units_per_pack=p[3], schedule=p[4], price=p[5])
             for p in PRODUCTS}
    db.add_all(prods.values())
    db.flush()
    # Stock: Behala is out of Telmisartan on purpose so routing has something to do.
    for s in stores.values():
        for p in prods.values():
            if p.schedule in {"X", "NARCOTIC"}:
                continue
            qty = 0 if (s.name == "Behala" and p.name.startswith("Telmisartan")) else 40
            db.add(Stock(store_id=s.id, product_id=p.id, qty=qty))
    users = {
        "debasish": User(phone="9000000001", name="Debasish Ghosh", role="customer", lat=22.5800, lng=88.4100),
        "rina": User(phone="9000000002", name="Rina Sen", role="customer", lat=22.5000, lng=88.3200),
        "arif": User(phone="9000000003", name="Arif Mondal", role="customer", lat=22.5900, lng=88.3400),
        "pharma": User(phone="9000000010", name="Dr. Anita Roy (Pharmacist)", role="pharmacist"),
    }
    for i, name in enumerate(["Salt Lake", "Behala", "Howrah Maidan", "Park Street", "Dum Dum"]):
        users[f"store{i}"] = User(phone=f"90000000{20 + i}", name=f"{name} Store Staff", role="store_staff",
                                  store_id=stores[name].id)
    users["ops"] = User(phone="9000000030", name="Central Operations", role="ops")
    db.add_all(users.values())
    db.flush()
    mother = FamilyProfile(user_id=users["debasish"].id, name="Mother (Mrs. Ghosh)", relation="mother")
    db.add_all([FamilyProfile(user_id=users["debasish"].id, name="Debasish Ghosh", relation="self"), mother,
                FamilyProfile(user_id=users["rina"].id, name="Rina Sen", relation="self"),
                FamilyProfile(user_id=users["arif"].id, name="Arif Mondal", relation="self")])
    db.flush()

    def order(code, user, store, status, product, qty, item_status, approved, rx_status, scenario="", extra=()):
        p = prods[product]
        raw = extractor.mock_extract(scenario) if scenario else {"readable": True, "notes": "", "items": [
            {"name": product, "strength": None, "qty": qty, "doses_per_day": 1, "confidence": 0.93}]}
        draft = matcher.build_draft(db, extractor.sanitize(raw))
        png = fake_rx_png(users[user].name, [f"1. Tab {product}   x {qty}", *extra])
        rx = Prescription(user_id=users[user].id, enc_path=crypto.save_encrypted(png), status=rx_status,
                          ai_draft={**draft, "source": "mock"},
                          review_note="Image too blurry to read the dose" if rx_status == "REUPLOAD" else None)
        db.add(rx)
        db.flush()
        o = Order(code=code, user_id=users[user].id, store_id=stores[store].id if store else None, status=status,
                  profile_id=mother.id if user == "debasish" else None, prescription_id=rx.id)
        it = OrderItem(product_id=p.id, qty=qty, schedule=p.schedule, unit_price=p.price, status=item_status,
                       approved_by=users["pharma"].id if approved else None)
        o.items.append(it)
        db.add(o)

    order("RX-50211", "debasish", "Salt Lake", "PACKED", "Metformin 500 mg", 4, "PACKED", True, "APPROVED",
          extra=["2. Tab Amlodipine 5 mg   x 2"])
    order("RX-50214", "rina", None, "AWAITING_PHARMACIST", "Telmisartan 40 mg", 3, "PENDING", False, "PENDING")
    order("RX-50219", "arif", None, "ON_HOLD", "Levothyroxine 50 mcg", 1, "PENDING", False, "REUPLOAD", "unreadable")
    add_history(db, stores, prods, users["pharma"])
    db.flush()
    rx1 = db.scalars(select(Prescription).where(Prescription.user_id == users["debasish"].id)).first()
    db.add_all([
        RefillSchedule(user_id=users["debasish"].id, profile_id=mother.id, product_id=prods["Amlodipine 5 mg"].id,
                       qty=2, doses_per_day=1, last_order_at=datetime.now(timezone.utc) - timedelta(days=28),
                       prescription_id=rx1.id),
        RefillSchedule(user_id=users["debasish"].id, profile_id=mother.id, product_id=prods["Vitamin D3 60K"].id,
                       qty=1, doses_per_day=None, last_order_at=datetime.now(timezone.utc) - timedelta(days=5)),
    ])
    db.commit()
    db.close()
    print("Seeded. Demo phones: 9000000001-3 customers, 9000000010 pharmacist, 9000000020-24 store staff (one per store)")


if __name__ == "__main__":
    run(force="--force" in sys.argv)
