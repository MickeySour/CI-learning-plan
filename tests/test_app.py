from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_add():
    resp = client.get("/add?a=1&b=2")
    assert resp.status_code == 200
    assert resp.json() == {"result": 3}


def test_add_negative():
    resp = client.get("/add?a=-3&b=5")
    assert resp.status_code == 200
    assert resp.json() == {"result": 2}


def test_add_missing_param():
    resp = client.get("/add?a=1")
    assert resp.status_code == 422
