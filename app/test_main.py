from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_list_streams():
    response = client.get("/streams")
    assert response.status_code == 200
    data = response.json()
    assert "streams" in data
    assert data["total"] == 4


def test_get_stream_found():
    response = client.get("/streams/s1")
    assert response.status_code == 200
    assert response.json()["title"] == "TF1 Direct"


def test_get_stream_not_found():
    response = client.get("/streams/unknown")
    assert response.status_code == 404


def test_metrics_endpoint():
    response = client.get("/metrics")
    assert response.status_code == 200
    assert b"streamops_requests_total" in response.content