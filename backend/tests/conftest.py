import os
# Use a SEPARATE, empty database for TEST_DATABASE_URL: the test seed wipes it.
os.environ["DATABASE_URL"] = os.environ.get("TEST_DATABASE_URL", "sqlite:///./test.db")
os.environ["UPLOAD_DIR"] = "./test_uploads"
import pytest
from fastapi.testclient import TestClient
from app.db import SessionLocal
from app.main import app
from app import seed


@pytest.fixture(autouse=True)
def fresh_db():
    seed.run()
    yield


@pytest.fixture
def db():
    s = SessionLocal()
    yield s
    s.close()


@pytest.fixture
def client():
    return TestClient(app)


def login(client, phone):
    otp = client.post("/auth/request-otp", json={"phone": phone}).json()["dev_otp"]
    return {"Authorization": "Bearer " + client.post("/auth/verify-otp", json={"phone": phone, "code": otp}).json()["token"]}


import io
from scripts.make_sample_prescriptions import page

_buf = io.BytesIO()
page().save(_buf, "PNG")
PNG = _buf.getvalue()  # a real, sharp, readable fake prescription image


def upload_rx(client, headers, data=PNG, name="rx.png"):
    return client.post("/prescriptions", headers=headers, files={"file": (name, data, "image/png")})
