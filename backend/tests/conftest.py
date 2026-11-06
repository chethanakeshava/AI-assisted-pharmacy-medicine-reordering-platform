import os
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
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
