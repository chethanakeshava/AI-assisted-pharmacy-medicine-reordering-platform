"""Seed realistic, fake data (no real personal data). Run: python -m app.seed"""
from .db import Base, SessionLocal, engine
from .models import (FamilyProfile, Order, OrderItem, Product, Rule, Stock, Store, User)

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


def run():
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
        "store": User(phone="9000000020", name="Salt Lake Store Staff", role="store_staff",
                      store_id=stores["Salt Lake"].id),
    }
    db.add_all(users.values())
    db.flush()
    mother = FamilyProfile(user_id=users["debasish"].id, name="Mother (Mrs. Ghosh)", relation="mother")
    db.add_all([FamilyProfile(user_id=users["debasish"].id, name="Debasish Ghosh", relation="self"), mother,
                FamilyProfile(user_id=users["rina"].id, name="Rina Sen", relation="self"),
                FamilyProfile(user_id=users["arif"].id, name="Arif Mondal", relation="self")])
    db.flush()

    def order(code, user, store, status, product, qty, item_status, approved):
        p = prods[product]
        o = Order(code=code, user_id=users[user].id, store_id=stores[store].id, status=status,
                  profile_id=mother.id if user == "debasish" else None)
        it = OrderItem(product_id=p.id, qty=qty, schedule=p.schedule, unit_price=p.price, status=item_status,
                       approved_by=users["pharma"].id if approved else None)
        o.items.append(it)
        db.add(o)

    order("RX-50211", "debasish", "Salt Lake", "PACKED", "Metformin 500 mg", 4, "PACKED", True)
    order("RX-50214", "rina", "Behala", "AWAITING_PHARMACIST", "Telmisartan 40 mg", 3, "PENDING", False)
    order("RX-50219", "arif", "Howrah Maidan", "ON_HOLD", "Levothyroxine 50 mcg", 1, "PENDING", False)
    db.commit()
    db.close()
    print("Seeded. Demo phones: 9000000001-3 customers, 9000000010 pharmacist, 9000000020 store staff")


if __name__ == "__main__":
    run()
