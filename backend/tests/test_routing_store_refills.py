from datetime import date, timedelta

from sqlalchemy import select

from app.models import Notification, Order, OrderItem, Product, Stock, Store
from app.services.reminders import days_supply, send_due_reminders
from app.services.routing import haversine_km
from .conftest import login


def ph(client):
    return login(client, "9000000010")


def approve_all(client, code):
    """Pharmacist approves every item of an order (by code) and finishes the review."""
    h = ph(client)
    o = next(x for x in client.get("/pharmacist/queue", headers=h).json() if x["code"] == code)
    for i in o["items"]:
        assert client.post(f"/pharmacist/orders/{o['id']}/items/{i['id']}/approve", headers=h).status_code == 200
    return client.post(f"/pharmacist/orders/{o['id']}/finalize", headers=h).json()


def debasish_reorder(client):
    h = login(client, "9000000001")
    o = client.post("/orders/1/reorder", headers=h).json()
    return h, o


def stock_of(db, store_name, product_name):
    return db.scalars(select(Stock).join(Store).join(Product, Stock.product_id == Product.id)
                      .where(Store.name == store_name, Product.name == product_name)).one()


# ---------- routing ----------
def test_haversine_is_sane():
    assert 0 < haversine_km(22.5867, 88.4171, 22.4985, 88.3118) < 20
    assert haversine_km(22.5, 88.3, 22.5, 88.3) == 0


def test_routes_to_nearest_store_and_reserves_stock(client, db):
    _, o = debasish_reorder(client)
    r = approve_all(client, o["code"])
    assert r["status"] == "APPROVED" and r["store_name"] == "Salt Lake" and r["distance_km"] is not None
    assert stock_of(db, "Salt Lake", "Metformin 500 mg").qty == 40 - 4


def test_skips_nearest_store_that_is_out_of_stock(client, db):
    r = approve_all(client, "RX-50214")  # Rina lives near Behala, which has no Telmisartan
    assert r["status"] == "APPROVED" and r["store_name"] not in (None, "Behala")


def test_no_stock_anywhere_waits_then_reroutes_after_csv(client, db):
    for s in db.scalars(select(Stock).join(Product).where(Product.name == "Telmisartan 40 mg")).all():
        s.qty = 0
    db.commit()
    r = approve_all(client, "RX-50214")
    assert r["status"] == "NO_STOCK" and r["store_name"] is None and "stock" in r["routing_note"]
    csv = b"store,product,qty\nPark Street,Telmisartan 40 mg,10\n"
    up = client.post("/stock/upload", headers=ph(client), files={"file": ("s.csv", csv, "text/csv")})
    assert up.json() == {"applied": 1, "rerouted": 1}
    rina = login(client, "9000000002")
    o = client.get("/orders", headers=rina).json()[0]
    assert o["status"] == "APPROVED" and o["store_name"] == "Park Street"


def test_stock_csv_is_all_or_nothing(client, db):
    bad = b"store,product,qty\nPark Street,Metformin 500 mg,5\nNowhere,Metformin 500 mg,5\nBehala,Metformin 500 mg,-2\nBehala,Nothing,1\n"
    r = client.post("/stock/upload", headers=ph(client), files={"file": ("s.csv", bad, "text/csv")})
    assert r.status_code == 422 and len(r.json()["detail"]["errors"]) == 3
    assert stock_of(db, "Park Street", "Metformin 500 mg").qty == 40   # the valid line was NOT applied


def test_stock_csv_rejects_wrong_columns_role_and_encoding(client):
    h = ph(client)
    assert client.post("/stock/upload", headers=h, files={"file": ("s.csv", b"a,b\n1,2\n", "text/csv")}).status_code == 422
    assert client.post("/stock/upload", headers=h, files={"file": ("s.csv", b"\xff\xfe\x00bad", "text/csv")}).status_code == 422
    cust = login(client, "9000000001")
    assert client.post("/stock/upload", headers=cust, files={"file": ("s.csv", b"store,product,qty\n", "text/csv")}).status_code == 403


def test_stock_csv_updates_quantities(client, db):
    ok = b"store,product,qty\nPark Street,Metformin 500 mg,7\nbehala,metformin 500 mg,9\n"
    assert client.post("/stock/upload", headers=ph(client), files={"file": ("s.csv", ok, "text/csv")}).json()["applied"] == 2
    db.expire_all()
    assert stock_of(db, "Park Street", "Metformin 500 mg").qty == 7


# ---------- store flow ----------
def routed_order(client):
    _, o = debasish_reorder(client)
    approve_all(client, o["code"])
    return o


def test_store_sees_only_its_own_orders(client):
    o = routed_order(client)
    mine = client.get("/store/orders", headers=login(client, "9000000020")).json()
    assert [x["code"] for x in mine if x["code"] == o["code"]] and all(x["customer"] for x in mine)
    other = client.get("/store/orders", headers=login(client, "9000000021")).json()
    assert o["code"] not in [x["code"] for x in other]
    assert client.post(f"/store/orders/{o['id']}/pack", headers=login(client, "9000000021"), json={"invoice_no": "INV-1"}).status_code == 404


def test_pack_then_handover_and_refill_clock(client, db):
    o = routed_order(client)
    st = login(client, "9000000020")
    assert client.post(f"/store/orders/{o['id']}/pack", headers=st, json={"invoice_no": "!!"}).status_code == 422
    assert client.post(f"/store/orders/{o['id']}/handover", headers=st, json={"handed_to": "Ravi"}).status_code == 409
    p = client.post(f"/store/orders/{o['id']}/pack", headers=st, json={"invoice_no": "SL/2026/001"}).json()
    assert p["status"] == "PACKED" and p["invoice_no"] == "SL/2026/001"
    assert client.post(f"/store/orders/{o['id']}/pack", headers=st, json={"invoice_no": "SL/2026/002"}).status_code == 409
    d = client.post(f"/store/orders/{o['id']}/handover", headers=st, json={"handed_to": "Ravi (delivery)"}).json()
    assert d["status"] == "DISPATCHED" and all(i["status"] == "DISPATCHED" for i in d["items"])
    assert db.scalars(select(Notification).where(Notification.body.like("%on its way%"))).first()
    cust = login(client, "9000000001")
    met = next(r for r in client.get("/refills", headers=cust).json() if r["product_name"] == "Metformin 500 mg")
    assert met["days_left"] == 60     # 4 packs x 15 / 1 a day (dose read from the prescription), clock restarted at dispatch


def test_duplicate_invoice_blocked_within_store(client):
    a = routed_order(client)
    b = routed_order(client)
    st = login(client, "9000000020")
    assert client.post(f"/store/orders/{a['id']}/pack", headers=st, json={"invoice_no": "SAME-1"}).status_code == 200
    assert client.post(f"/store/orders/{b['id']}/pack", headers=st, json={"invoice_no": "SAME-1"}).status_code == 409


def test_cannot_pack_order_still_awaiting_pharmacist(client):
    h, o = debasish_reorder(client)
    assert client.post(f"/store/orders/{o['id']}/pack", headers=login(client, "9000000020"), json={"invoice_no": "INV-9"}).status_code == 404


def test_pack_refuses_unapproved_h_item_even_if_order_status_is_tampered(client, db):
    """Defence in depth: an APPROVED order with a PENDING Schedule H item still cannot be packed."""
    o = routed_order(client)
    item = db.scalars(select(OrderItem).where(OrderItem.order_id == o["id"])).first()
    item.status, item.approved_by = "PENDING", None
    db.commit()
    r = client.post(f"/store/orders/{o['id']}/pack", headers=login(client, "9000000020"), json={"invoice_no": "INV-7"})
    assert r.status_code == 409 and "approved" in r.json()["detail"]
    db.expire_all()
    assert db.get(Order, o["id"]).status == "APPROVED"


# ---------- refills ----------
def test_refill_math():
    assert days_supply(15, 4, 2) == 30 and days_supply(100, 1, 1) == 100
    assert days_supply(15, 4, None) is None and days_supply(15, 4, 0) is None


def test_refill_list_orders_due_first_and_flags_missing_dose(client):
    r = client.get("/refills", headers=login(client, "9000000001")).json()
    assert [x["state"] for x in r] == ["due", "needs_dose"] and r[0]["days_left"] == 2 and r[1]["days_left"] is None


def test_reminder_sent_once_per_cycle_and_skips_needs_dose(client, db):
    assert send_due_reminders(db) == 1
    assert send_due_reminders(db) == 0
    body = client.get("/notifications", headers=login(client, "9000000001")).json()[0]["body"]
    assert "Amlodipine 5 mg" in body and "Refills" in body
    assert send_due_reminders(db, today=date.today() + timedelta(days=60)) == 0   # same cycle: not repeated


def test_no_reminder_while_an_order_is_open(client, db):
    h = login(client, "9000000001")
    amlo = client.get("/refills", headers=h).json()[0]
    assert client.post(f"/refills/{amlo['id']}/reorder", headers=h).status_code == 201   # now an order is open
    assert send_due_reminders(db) == 0


def test_refill_dose_can_be_set_and_is_validated(client):
    h = login(client, "9000000001")
    vit = next(r for r in client.get("/refills", headers=h).json() if r["state"] == "needs_dose")
    assert client.patch(f"/refills/{vit['id']}", headers=h, json={"doses_per_day": 0}).status_code == 422
    r = client.patch(f"/refills/{vit['id']}", headers=h, json={"doses_per_day": 1}).json()
    assert r["days_supply"] == 4 and r["state"] == "due"


def test_refill_one_tap_reorder_uses_saved_prescription(client):
    h = login(client, "9000000001")
    first = client.get("/refills", headers=h).json()[0]
    o = client.post(f"/refills/{first['id']}/reorder", headers=h).json()
    assert o["status"] == "AWAITING_PHARMACIST" and o["prescription_id"] and o["items"][0]["qty"] == 2
    vit = client.get("/refills", headers=h).json()[1]
    assert client.post(f"/refills/{vit['id']}/reorder", headers=h).status_code == 201   # OTC needs no prescription


def test_refill_belongs_to_its_owner_and_can_be_stopped(client):
    h, other = login(client, "9000000001"), login(client, "9000000002")
    rid = client.get("/refills", headers=h).json()[0]["id"]
    assert client.post(f"/refills/{rid}/reorder", headers=other).status_code == 404
    assert client.delete(f"/refills/{rid}", headers=other).status_code == 404
    assert client.delete(f"/refills/{rid}", headers=h).status_code == 204
    assert all(r["id"] != rid for r in client.get("/refills", headers=h).json())
