from pathlib import Path

import pytest
from sqlalchemy import select

from app.config import settings
from app.models import OrderItem, Prescription
from app.services import extractor
from .conftest import PNG, login, upload_rx

SAMPLES = Path("sample_prescriptions")


def draft_of(db, rx_id):
    return db.get(Prescription, rx_id).ai_draft


def test_clear_upload_gets_matched_draft(client, db):
    h = login(client, "9000000001")
    r = upload_rx(client, h).json()
    assert r["readable"] is True and r["item_count"] == 2
    items = draft_of(db, r["id"])["items"]
    assert [i["product_name"] for i in items] == ["Metformin 500 mg", "Telmisartan 40 mg"]
    assert all(not i["low_confidence"] for i in items) and items[0]["qty"] == 4


def test_pharmacist_sees_generics_with_saving(client, db):
    h = login(client, "9000000001")
    rx = upload_rx(client, h).json()["id"]
    met = client.get("/catalog/search?q=metformin", headers=h).json()[0]["id"]
    client.post("/orders", headers=h, json={"prescription_id": rx, "items": [{"product_id": met, "qty": 4}]})
    q = client.get("/pharmacist/queue", headers=login(client, "9000000010")).json()
    mine = next(o for o in q if o["prescription_id"] == rx)
    generic = mine["ai_draft"]["items"][0]["generic_options"]
    assert generic and generic[0]["name"].endswith("(Generic)") and generic[0]["saving"] == 55


def test_customer_suggestions_hide_generics(client):
    h = login(client, "9000000001")
    rx = upload_rx(client, h).json()["id"]
    s = client.get(f"/prescriptions/{rx}/suggestions", headers=h).json()
    assert len(s["items"]) == 2 and "generic_options" not in str(s)
    assert client.get(f"/prescriptions/{rx}/suggestions", headers=login(client, "9000000002")).status_code == 404


def test_unreadable_draft_is_flagged_not_guessed(client, db):
    h = login(client, "9000000001")
    r = upload_rx(client, h, name="unreadable.png").json()
    assert r["readable"] is False and r["item_count"] == 0


def test_blocked_drug_flagged_and_hidden_from_customer(client, db):
    h = login(client, "9000000001")
    r = upload_rx(client, h, name="blocked.png").json()
    item = draft_of(db, r["id"])["items"][0]
    assert item["blocked"] is True and item["generic_options"] == []
    assert client.get(f"/prescriptions/{r['id']}/suggestions", headers=h).json()["items"] == []


def test_messy_read_is_low_confidence_and_qty_never_filled(client, db):
    h = login(client, "9000000001")
    r = upload_rx(client, h, name="messy.png").json()
    tel = draft_of(db, r["id"])["items"][0]
    assert tel["low_confidence"] is True and tel["qty"] is None
    sug = client.get(f"/prescriptions/{r['id']}/suggestions", headers=h).json()["items"]
    assert all(i["needs_check"] for i in sug) and sug[0]["qty"] is None


def test_ai_failure_gives_empty_draft_not_a_crash(client, db, monkeypatch):
    monkeypatch.setattr(extractor, "mock_extract", lambda f: (_ for _ in ()).throw(RuntimeError("boom")))
    r = upload_rx(client, login(client, "9000000001"))
    assert r.status_code == 201
    d = draft_of(db, r.json()["id"])
    assert d["source"] == "failed" and d["items"] == [] and d["readable"] is None


def test_gemini_path_and_timeout(client, db, monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "gemini")

    class Resp:
        def raise_for_status(self): pass
        def json(self):
            return {"candidates": [{"content": {"parts": [{"text":
                '```json\n{"readable": true, "items": [{"name": "Metformin", "strength": "500 mg", "qty": 2, "confidence": 0.9}]}\n```'}]}}]}

    monkeypatch.setattr(extractor.httpx, "post", lambda *a, **k: Resp())
    h = login(client, "9000000001")
    d = draft_of(db, upload_rx(client, h).json()["id"])
    assert d["source"] == "gemini" and d["items"][0]["product_name"] == "Metformin 500 mg"

    def timeout(*a, **k):
        raise extractor.httpx.TimeoutException("slow")
    monkeypatch.setattr(extractor.httpx, "post", timeout)
    d = draft_of(db, upload_rx(client, h).json()["id"])
    assert d["source"] == "failed" and d["items"] == []


@pytest.mark.parametrize("name,reason", [("blurry", "blurry"), ("dark", "dark"), ("tiny", "small")])
def test_bad_photos_rejected_before_ai_and_not_stored(client, name, reason):
    before = len(list(Path("test_uploads").glob("*.enc"))) if Path("test_uploads").exists() else 0
    data = (SAMPLES / f"rx_{name}.png").read_bytes()
    r = upload_rx(client, login(client, "9000000001"), data=data)
    assert r.status_code == 422
    body = r.json()["detail"]
    assert body["code"] == "unreadable_image" and any(reason in x for x in body["reasons"]) and body["tips"]
    after = len(list(Path("test_uploads").glob("*.enc"))) if Path("test_uploads").exists() else 0
    assert after == before


def test_ai_draft_never_approves_anything(client, db):
    h = login(client, "9000000001")
    rx = upload_rx(client, h).json()["id"]
    sug = client.get(f"/prescriptions/{rx}/suggestions", headers=h).json()["items"]
    client.post("/orders", headers=h, json={"prescription_id": rx,
               "items": [{"product_id": i["product_id"], "qty": 1} for i in sug]})
    items = db.scalars(select(OrderItem).order_by(OrderItem.id.desc()).limit(2)).all()
    assert all(i.status == "PENDING" and i.approved_by is None for i in items)


def test_parse_and_sanitize():
    assert extractor.parse_model_json('```json\n{"a": 1}\n```') == {"a": 1}
    with pytest.raises(extractor.ExtractionError):
        extractor.parse_model_json("sorry, I cannot read this")
    out = extractor.sanitize({"readable": "yes", "items": [
        {"name": "  ", "qty": 2}, "junk", {"name": "Metformin", "qty": 500, "confidence": 7, "doses_per_day": "2"},
        {"name": "Amlodipine", "qty": "4", "confidence": 0.8}]})
    assert out["readable"] is None and len(out["items"]) == 2
    assert out["items"][0]["qty"] is None and out["items"][0]["confidence"] == 0.0 and out["items"][0]["doses_per_day"] == 2.0
    assert out["items"][1]["qty"] == 4
