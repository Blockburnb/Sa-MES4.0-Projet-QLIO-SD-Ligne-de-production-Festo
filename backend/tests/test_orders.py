from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_health():
    r = client.get('/health')
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_get_orders():
    r = client.get('/orders')
    assert r.status_code == 200
    assert isinstance(r.json(), list)
