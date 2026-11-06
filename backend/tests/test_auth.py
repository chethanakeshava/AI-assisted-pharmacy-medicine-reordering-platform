from .conftest import login


def test_otp_login_and_me(client):
    h = login(client, "9000000001")
    me = client.get("/auth/me", headers=h).json()
    assert me["role"] == "customer" and len(me["profiles"]) == 2


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
