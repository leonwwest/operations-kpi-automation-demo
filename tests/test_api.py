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
    payload = response.json()
    assert payload["summary"]["orders"] == 6039
    assert len(payload["months"]) == 12
    assert payload["quality"]["validation_errors"] == 0


def test_kpi_response_schema() -> None:
    payload = client.get("/api/kpis").json()
    kpi_keys = {
        "orders",
        "revenue_eur",
        "on_time_rate",
        "avg_processing_hours",
        "incidents",
    }
    assert kpi_keys <= payload["summary"].keys()
    assert kpi_keys | {"team"} <= payload["teams"][0].keys()
    assert kpi_keys | {"month"} <= payload["months"][0].keys()


def test_refresh_endpoint_returns_trace() -> None:
    response = client.post("/api/refresh")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "completed"
    assert payload["run_id"].startswith("run-")
    assert [step["step"] for step in payload["trace"]] == [
        "Extract",
        "Validate",
        "Transform",
        "Publish",
    ]


def test_refresh_result_matches_kpi_endpoint() -> None:
    refresh_payload = client.post("/api/refresh").json()
    kpi_payload = client.get("/api/kpis").json()
    assert refresh_payload["result"]["summary"] == kpi_payload["summary"]


def test_dashboard_is_served() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "Operations KPI" in response.text
