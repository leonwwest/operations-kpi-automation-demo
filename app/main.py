"""FastAPI application for the operations KPI automation demo."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

from app.pipeline import build_kpis

STATIC_DIR = Path(__file__).parent / "static"

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
def favicon() -> Response:
    return Response(status_code=204)


@app.get("/api/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok", "mode": "portfolio-demo", "data": "synthetic"}


@app.get("/api/kpis", tags=["analytics"])
def kpis() -> dict:
    return build_kpis()


@app.post("/api/refresh", tags=["automation"])
def refresh() -> dict:
    result = build_kpis()
    return {
        "run_id": f"run-{uuid4().hex[:8]}",
        "status": "completed",
        "finished_at": datetime.now(UTC).isoformat(),
        "trace": [
            {"step": "Extract", "status": "ok", "detail": "Synthetic CSV loaded"},
            {"step": "Validate", "status": "ok", "detail": "All rows passed rules"},
            {"step": "Transform", "status": "ok", "detail": "KPIs aggregated"},
            {"step": "Publish", "status": "ok", "detail": "API payload refreshed"},
        ],
        "result": result,
    }
