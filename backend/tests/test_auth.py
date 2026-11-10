from .conftest import login


def test_otp_login_and_me(client):
    h = login(client, "9000000001")
    me = client.get("/auth/me", headers=h).json()
    assert me["role"] == "customer" and len(me["profiles"]) == 2


def test_customer_registration_and_immediate_login(client):
    requested = client.post(
        "/auth/register/request-otp",
        json={"name": "  New Customer  ", "phone": "9000000099", "role": "ops"},
    )
    assert requested.status_code == 200
    response = client.post(
        "/auth/register/verify-otp",
        json={
            "name": "  New Customer  ",
            "phone": "9000000099",
            "code": requested.json()["dev_otp"],
            "role": "ops",
        },
    )
    assert response.status_code == 200
    account = response.json()
    assert account["role"] == "customer"
    assert account["name"] == "New Customer"
    assert account["token"]

    new_customer = login(client, "9000000099")
    me = client.get("/auth/me", headers=new_customer).json()
    assert me["name"] == "New Customer"


def test_registration_rejects_duplicate_phone(client):
    response = client.post(
        "/auth/register/request-otp",
        json={"name": "Duplicate", "phone": "9000000001"},
    )
    assert response.status_code == 409


def test_registration_uses_existing_otp_rate_limit(client):
    results = [
        client.post(
            "/auth/register/request-otp",
            json={"name": "New Customer", "phone": "9000000096"},
        ).status_code
        for _ in range(7)
    ]
    assert results == [200, 200, 200, 200, 200, 429, 429]


def test_registration_hides_dev_otp_outside_dev(client, monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "app_env", "prod")
    response = client.post(
        "/auth/register/request-otp",
        json={"name": "New Customer", "phone": "9000000095"},
    )
    assert response.status_code == 200
    assert response.json()["dev_otp"] is None


def test_registration_rejects_wrong_otp(client):
    requested = client.post(
        "/auth/register/request-otp",
        json={"name": "New Customer", "phone": "9000000099"},
    ).json()
    wrong_code = "000000" if requested["dev_otp"] != "000000" else "000001"
    response = client.post(
        "/auth/register/verify-otp",
        json={"name": "New Customer", "phone": "9000000099", "code": wrong_code},
    )
    assert response.status_code == 401


def test_registration_rejects_expired_and_reused_otp(client, db, monkeypatch):
    from app.config import settings
    from app.models import OtpCode
    from datetime import datetime, timedelta, timezone

    monkeypatch.setattr(settings, "otp_ttl_seconds", 0)
    expired = client.post(
        "/auth/register/request-otp",
        json={"name": "Expired User", "phone": "9000000098"},
    ).json()["dev_otp"]
    response = client.post(
        "/auth/register/verify-otp",
        json={"name": "Expired User", "phone": "9000000098", "code": expired},
    )
    assert response.status_code == 401

    monkeypatch.setattr(settings, "otp_ttl_seconds", 300)
    request = client.post(
        "/auth/register/request-otp",
        json={"name": "Reused User", "phone": "9000000097"},
    ).json()
    code = request["dev_otp"]
    otp = db.query(OtpCode).filter_by(phone="9000000097").one()
    otp.expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
    db.commit()

    payload = {"name": "Reused User", "phone": "9000000097", "code": code}
    assert client.post("/auth/register/verify-otp", json=payload).status_code == 200
    assert client.post("/auth/register/verify-otp", json=payload).status_code == 401


def test_wrong_otp_rejected(client):
    client.post("/auth/request-otp", json={"phone": "9000000001"})
    assert client.post("/auth/verify-otp", json={"phone": "9000000001", "code": "000000"}).status_code in (401,)


def test_otp_locks_after_max_attempts(client):
    client.post("/auth/request-otp", json={"phone": "9000000001"})
    for _ in range(5):
        client.post("/auth/verify-otp", json={"phone": "9000000001", "code": "111111"})
    assert client.post("/auth/verify-otp", json={"phone": "9000000001", "code": "111111"}).status_code == 401


def test_unknown_phone_and_bad_format(client):
    assert client.post("/auth/request-otp", json={"phone": "9999999999"}).status_code == 404
    assert client.post("/auth/request-otp", json={"phone": "abc"}).status_code == 422


def test_protected_route_needs_token(client):
    assert client.get("/catalog/search?q=met").status_code == 401


def test_search_flags_blocked_and_gated(client):
    h = login(client, "9000000001")
    r = client.get("/catalog/search?q=morphine", headers=h).json()
    assert r[0]["sellable"] is False
    r = client.get("/catalog/search?q=metformin", headers=h).json()
    assert r[0]["sellable"] and r[0]["needs_prescription"]
