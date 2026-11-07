from pathlib import Path

from sqlalchemy import select

from app.models import AccessLog
from .conftest import PNG, login, upload_rx


def pid(client, h, q):
    return client.get(f"/catalog/search?q={q}", headers=h).json()[0]["id"]


def test_upload_is_encrypted_on_disk_and_roundtrips(client, db):
    h = login(client, "9000000001")
    rx = upload_rx(client, h).json()
    stored = [p.read_bytes() for p in Path("test_uploads").glob("*.enc")]
    assert stored and all(PNG not in b for b in stored)
    pharm = login(client, "9000000010")
    r = client.get(f"/prescriptions/{rx['id']}/image", headers=pharm)
    assert r.status_code == 200 and r.content == PNG and r.headers["content-type"] == "image/png"


def test_every_view_is_access_logged(client, db):
    h = login(client, "9000000001")
    rid = upload_rx(client, h).json()["id"]
    client.get(f"/prescriptions/{rid}/image", headers=h)
    client.get(f"/prescriptions/{rid}/image", headers=login(client, "9000000010"))
    assert len(db.scalars(select(AccessLog)).all()) == 2


def test_upload_validation(client):
    h = login(client, "9000000001")
    assert upload_rx(client, h, data=b"not an image at all", name="rx.png").status_code == 415
    assert upload_rx(client, h, data=b"").status_code == 422
    assert upload_rx(client, h, data=PNG + b"0" * (5 * 1024 * 1024)).status_code == 413


def test_prescription_access_control(client):
    owner, other = login(client, "9000000001"), login(client, "9000000002")
    rid = upload_rx(client, owner).json()["id"]
    assert client.get(f"/prescriptions/{rid}/image", headers=other).status_code == 404
    assert client.get(f"/prescriptions/{rid}/image", headers=login(client, "9000000020")).status_code == 404
    assert client.get(f"/prescriptions/{rid}/image").status_code == 401


def test_h_item_without_prescription_rejected(client):
    h = login(client, "9000000001")
    r = client.post("/orders", headers=h, json={"items": [{"product_id": pid(client, h, "metformin"), "qty": 2}]})
    assert r.status_code == 422


def test_blocked_and_invalid_items_rejected(client):
    h = login(client, "9000000001")
    rx = upload_rx(client, h).json()["id"]
    morphine = pid(client, h, "morphine")
    assert client.post("/orders", headers=h, json={"prescription_id": rx, "items": [{"product_id": morphine, "qty": 1}]}).status_code == 422
    met = pid(client, h, "metformin")
    for qty in (0, -1, 21):
        assert client.post("/orders", headers=h, json={"prescription_id": rx, "items": [{"product_id": met, "qty": qty}]}).status_code == 422
    assert client.post("/orders", headers=h, json={"prescription_id": rx, "items": []}).status_code == 422


def test_cannot_use_someone_elses_prescription_or_profile(client):
    owner, other = login(client, "9000000001"), login(client, "9000000002")
    rx = upload_rx(client, owner).json()["id"]
    met = pid(client, other, "metformin")
    assert client.post("/orders", headers=other, json={"prescription_id": rx, "items": [{"product_id": met, "qty": 1}]}).status_code == 404
    assert client.post("/orders", headers=other, json={"profile_id": 2, "items": [{"product_id": met, "qty": 1}]}).status_code == 404


def test_order_created_and_scoped_to_owner(client):
    h, other = login(client, "9000000001"), login(client, "9000000002")
    rx = upload_rx(client, h).json()["id"]
    o = client.post("/orders", headers=h, json={"prescription_id": rx, "profile_id": 2,
                    "items": [{"product_id": pid(client, h, "metformin"), "qty": 4}]}).json()
    assert o["status"] == "AWAITING_PHARMACIST" and o["total"] == 480
    assert client.get(f"/orders/{o['id']}", headers=other).status_code == 404
    assert client.get("/pharmacist/queue", headers=h).status_code == 403
