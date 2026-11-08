import pytest

from app import seed
from app.config import assert_safe_config, settings
from app.services.metrics import minutes_between
from datetime import datetime, timedelta, timezone
from .conftest import login, upload_rx


# ---------- security ----------
def test_otp_requests_are_rate_limited(client):
    codes = [client.post("/auth/request-otp", json={"phone": "9000000002"}).status_code for _ in range(7)]
    assert codes[:5] == [200] * 5 and codes[5:] == [429, 429]
    assert client.post("/auth/request-otp", json={"phone": "9000000003"}).status_code == 200   # per-phone, not global


def test_security_headers_on_every_response(client):
    r = client.get("/health")
    assert r.headers["x-content-type-options"] == "nosniff" and r.headers["x-frame-options"] == "DENY"
    assert r.headers["referrer-policy"] == "no-referrer" and r.headers["cache-control"] == "no-store"


def test_production_refuses_default_secrets(monkeypatch):
    assert_safe_config()   # dev is fine
    monkeypatch.setattr(settings, "app_env", "prod")
    with pytest.raises(RuntimeError) as e:
        assert_safe_config()
    assert "JWT_SECRET" in str(e.value) and "FERNET_KEY" in str(e.value)
    monkeypatch.setattr(settings, "jwt_secret", "j" * 40)
    monkeypatch.setattr(settings, "otp_secret", "o" * 40)
    monkeypatch.setattr(settings, "fernet_key", "k")
    assert_safe_config()


def test_seed_will_not_wipe_a_non_dev_database(monkeypatch):
    monkeypatch.setattr(settings, "app_env", "prod")
    with pytest.raises(SystemExit):
        seed.run()


def test_dev_otp_hidden_outside_dev(client, monkeypatch):
    monkeypatch.setattr(settings, "app_env", "prod")
    assert client.post("/auth/request-otp", json={"phone": "9000000001"}).json()["dev_otp"] is None


# ---------- payments (test mode) ----------
def place(client, h, method="UPI_TEST"):
    rx = upload_rx(client, h).json()["id"]
    pid = client.get("/catalog/search?q=amlodipine", headers=h).json()[0]["id"]
    return client.post("/orders", headers=h, json={"prescription_id": rx, "payment_method": method,
                                                    "items": [{"product_id": pid, "qty": 1}]}).json()


def approve(client, o):
    ph = login(client, "9000000010")
    for i in o["items"]:
        client.post(f"/pharmacist/orders/{o['id']}/items/{i['id']}/approve", headers=ph)
    client.post(f"/pharmacist/orders/{o['id']}/finalize", headers=ph)


def test_upi_test_payment_only_after_approval_and_only_once(client):
    h = login(client, "9000000001")
    o = place(client, h)
    assert o["payment_method"] == "UPI_TEST" and o["payment_status"] == "PENDING"
    assert client.post(f"/orders/{o['id']}/pay", headers=h).status_code == 409      # not approved yet
    approve(client, o)
    assert client.post(f"/orders/{o['id']}/pay", headers=h).json()["payment_status"] == "PAID_TEST"
    assert client.post(f"/orders/{o['id']}/pay", headers=h).status_code == 409      # no double payment


def test_cod_orders_cannot_be_paid_online_and_others_cannot_pay(client):
    h = login(client, "9000000001")
    cod = place(client, h, "COD")
    approve(client, cod)
    assert client.post(f"/orders/{cod['id']}/pay", headers=h).status_code == 409
    assert client.post(f"/orders/{cod['id']}/pay", headers=login(client, "9000000002")).status_code == 404


def test_invalid_payment_method_rejected(client):
    h = login(client, "9000000001")
    rx = upload_rx(client, h).json()["id"]
    pid = client.get("/catalog/search?q=amlodipine", headers=h).json()[0]["id"]
    r = client.post("/orders", headers=h, json={"prescription_id": rx, "payment_method": "BITCOIN", "items": [{"product_id": pid, "qty": 1}]})
    assert r.status_code == 422


# ---------- central dashboard ----------
def test_dashboard_is_ops_only(client):
    for phone in ("9000000001", "9000000010", "9000000020"):
        assert client.get("/dashboard", headers=login(client, phone)).status_code == 403
    assert client.get("/dashboard").status_code == 401


def test_dashboard_numbers_are_consistent(client):
    d = client.get("/dashboard", headers=login(client, "9000000030")).json()
    assert d["gate_violations"] == 0                      # the headline safety KPI
    assert d["orders"] >= 30 and len(d["by_store"]) == 5
    v = d["verification"]
    assert v["median_minutes"] is not None and 0 <= v["within_target_pct"] <= 100 and v["target_minutes"] == 10
    assert d["rejections"]["orders"] > 0 and d["rejections"]["reasons"]
    assert sum(s["orders"] for s in d["by_store"]) <= d["orders"]


def test_dashboard_window_validated_and_counts_live_orders(client):
    ops = login(client, "9000000030")
    assert client.get("/dashboard?days=0", headers=ops).status_code == 422
    before = client.get("/dashboard", headers=ops).json()["open"]["AWAITING_PHARMACIST"]
    place(client, login(client, "9000000001"))
    assert client.get("/dashboard", headers=ops).json()["open"]["AWAITING_PHARMACIST"] == before + 1


def test_minutes_between_handles_naive_and_aware():
    a = datetime(2026, 11, 1, 10, 0, tzinfo=timezone.utc)
    assert minutes_between(a, a + timedelta(minutes=7)) == 7
    assert minutes_between(a.replace(tzinfo=None), a + timedelta(minutes=7)) == 7
