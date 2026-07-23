"""FastAPI application for the operations KPI automation demo."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.pipeline import build_kpis, load_rows

STATIC_DIR = Path(__file__).parent / "static"


class KpiValues(BaseModel):
    orders: int
    revenue_eur: float
    on_time_rate: float
    avg_processing_hours: float
    incidents: int


class TeamKpis(KpiValues):
    team: str


class MonthKpis(KpiValues):
    month: str


class QualityMetadata(BaseModel):
    rows_processed: int
    rows_rejected: int
    validation_errors: int
    validation_messages: list[str]
    source: str
    data_classification: str


class KpiResponse(BaseModel):
    summary: KpiValues
    teams: list[TeamKpis]
    months: list[MonthKpis]
    quality: QualityMetadata


class TraceStep(BaseModel):
    step: str
    status: str
    detail: str


class RefreshResponse(BaseModel):
    run_id: str
    status: str
    finished_at: str
    trace: list[TraceStep]
    result: KpiResponse


app = FastAPI(
    title="Operations KPI Automation Demo",
    version="1.0.0",
    description=(
        "Synthetic portfolio demo: CSV validation, Python KPI aggregation, "
        "Power BI-ready API and n8n automation."
    ),
)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def dashboard() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/favicon.ico", include_in_schema=False)
def favicon() -> FileResponse:
    return FileResponse(STATIC_DIR / "favicon.svg", media_type="image/svg+xml")


@app.get("/api/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok", "mode": "portfolio-demo", "data": "synthetic"}


@app.get("/api/kpis", tags=["analytics"], response_model=KpiResponse)
def kpis() -> dict:
    return build_kpis()


@app.post("/api/refresh", tags=["automation"], response_model=RefreshResponse)
def refresh() -> dict:
    rows, errors = load_rows()
    result = build_kpis(rows, errors)
    team_count = len(result["teams"])
    month_count = len(result["months"])
    return {
        "run_id": f"run-{uuid4().hex[:8]}",
        "status": "completed",
        "finished_at": datetime.now(UTC).isoformat(),
        "trace": [
            {
                "step": "Extract",
                "status": "ok",
                "detail": f"{len(rows) + len(errors)} rows read from CSV",
            },
            {
                "step": "Validate",
                "status": "ok",
                "detail": f"{len(rows)} passed, {len(errors)} quarantined",
            },
            {
                "step": "Transform",
                "status": "ok",
                "detail": f"KPIs aggregated for {team_count} teams, {month_count} months",
            },
            {"step": "Publish", "status": "ok", "detail": "API payload refreshed"},
        ],
        "result": result,
    }
