from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["data"] == "synthetic"


def test_kpi_endpoint() -> None:
    response = client.get("/api/kpis")
    assert response.status_code == 200
    assert response.json()["summary"]["orders"] == 1674


def test_refresh_endpoint_returns_trace() -> None:
    response = client.post("/api/refresh")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "completed"
    assert [step["step"] for step in payload["trace"]] == [
        "Extract",
        "Validate",
        "Transform",
        "Publish",
    ]
