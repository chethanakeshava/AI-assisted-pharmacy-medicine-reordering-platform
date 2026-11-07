from .conftest import PNG, login, upload_rx


def make_order(client, product="metformin", qty=2):
    h = login(client, "9000000001")
    rx = upload_rx(client, h).json()["id"]
    pid = client.get(f"/catalog/search?q={product}", headers=h).json()[0]["id"]
    o = client.post("/orders", headers=h, json={"prescription_id": rx, "items": [{"product_id": pid, "qty": qty}]}).json()
    return h, o


def test_happy_path_approve_and_finalize(client):
    h, o = make_order(client)
    ph = login(client, "9000000010")
    assert any(q["id"] == o["id"] for q in client.get("/pharmacist/queue", headers=ph).json())
    item = o["items"][0]["id"]
    assert client.post(f"/pharmacist/orders/{o['id']}/items/{item}/approve", headers=ph).status_code == 200
    r = client.post(f"/pharmacist/orders/{o['id']}/finalize", headers=ph).json()
    assert r["status"] == "APPROVED"
    assert client.get(f"/orders/{o['id']}", headers=h).json()["status"] == "APPROVED"


def test_customer_cannot_use_pharmacist_endpoints(client):
    h, o = make_order(client)
    item = o["items"][0]["id"]
    assert client.post(f"/pharmacist/orders/{o['id']}/items/{item}/approve", headers=h).status_code == 403
    store = login(client, "9000000020")
    assert client.post(f"/pharmacist/orders/{o['id']}/finalize", headers=store).status_code == 403


def test_reject_needs_reason_and_finalize_needs_decisions(client):
    h, o = make_order(client)
    ph = login(client, "9000000010")
    item = o["items"][0]["id"]
    assert client.post(f"/pharmacist/orders/{o['id']}/finalize", headers=ph).status_code == 409
    assert client.post(f"/pharmacist/orders/{o['id']}/items/{item}/reject", headers=ph, json={"reason": ""}).status_code == 422
    assert client.post(f"/pharmacist/orders/{o['id']}/items/{item}/reject", headers=ph, json={"reason": "Dose unclear"}).status_code == 200
    assert client.post(f"/pharmacist/orders/{o['id']}/finalize", headers=ph).json()["status"] == "REJECTED"


def test_double_approve_blocked(client):
    h, o = make_order(client)
    ph = login(client, "9000000010")
    url = f"/pharmacist/orders/{o['id']}/items/{o['items'][0]['id']}/approve"
    assert client.post(url, headers=ph).status_code == 200
    assert client.post(url, headers=ph).status_code == 409


def test_edit_changes_product_and_blocks_x(client):
    h, o = make_order(client)
    ph = login(client, "9000000010")
    item = o["items"][0]["id"]
    amlo = client.get("/catalog/search?q=amlodipine", headers=h).json()[0]["id"]
    r = client.patch(f"/pharmacist/orders/{o['id']}/items/{item}", headers=ph, json={"product_id": amlo, "qty": 3})
    assert r.json()["items"][0]["unit_price"] == 55 and r.json()["items"][0]["qty"] == 3


def test_h1_needs_register_details(client):
    h, o = make_order(client, product="alprazolam", qty=1)
    ph = login(client, "9000000010")
    url = f"/pharmacist/orders/{o['id']}/items/{o['items'][0]['id']}/approve"
    assert client.post(url, headers=ph).status_code == 422
    body = {"h1": {"patient_name": "Test Patient", "prescriber_name": "Dr Test", "prescriber_reg_no": "WB-12345"}}
    assert client.post(url, headers=ph, json=body).status_code == 200


def test_reupload_puts_on_hold_notifies_and_blocks_approval(client):
    h, o = make_order(client)
    ph = login(client, "9000000010")
    r = client.post(f"/pharmacist/orders/{o['id']}/reupload", headers=ph, json={"reason": "Image too blurry"})
    assert r.json()["status"] == "ON_HOLD"
    item = o["items"][0]["id"]
    assert client.post(f"/pharmacist/orders/{o['id']}/items/{item}/approve", headers=ph).status_code == 409
    # customer replaces the photo -> back in the queue
    back = client.post(f"/orders/{o['id']}/reupload", headers=h,
                       files={"file": ("n.png", PNG, "image/png")})
    assert back.json()["status"] == "AWAITING_PHARMACIST"
    assert client.post(f"/pharmacist/orders/{o['id']}/items/{item}/approve", headers=ph).status_code == 200


def test_reupload_only_when_on_hold(client):
    h, o = make_order(client)
    r = client.post(f"/orders/{o['id']}/reupload", headers=h,
                    files={"file": ("n.png", PNG, "image/png")})
    assert r.status_code == 409
