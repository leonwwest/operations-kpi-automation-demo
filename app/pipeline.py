"""Validation and KPI aggregation for the synthetic operations dataset."""

from __future__ import annotations

import csv
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "operations.csv"


@dataclass(frozen=True)
class OperationRow:
    date: date
    team: str
    orders: int
    revenue_eur: float
    fulfilled_on_time: int
    processing_hours: float
    incidents: int


@dataclass(frozen=True)
class ValidationError:
    line: int
    message: str


def _positive_int(value: str, field: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise ValueError(f"{field} must not be negative")
    return parsed


def _positive_float(value: str, field: str) -> float:
    parsed = float(value)
    if parsed < 0:
        raise ValueError(f"{field} must not be negative")
    return parsed


def parse_row(raw: dict[str, str]) -> OperationRow:
    required = {
        "date",
        "team",
        "orders",
        "revenue_eur",
        "fulfilled_on_time",
        "processing_hours",
        "incidents",
    }
    missing = required.difference(raw)
    if missing:
        raise ValueError(f"missing columns: {', '.join(sorted(missing))}")

    team = raw["team"].strip()
    if not team:
        raise ValueError("team must not be empty")

    orders = _positive_int(raw["orders"], "orders")
    fulfilled = _positive_int(raw["fulfilled_on_time"], "fulfilled_on_time")
    if fulfilled > orders:
        raise ValueError("fulfilled_on_time must not exceed orders")

    return OperationRow(
        date=date.fromisoformat(raw["date"]),
        team=team,
        orders=orders,
        revenue_eur=_positive_float(raw["revenue_eur"], "revenue_eur"),
        fulfilled_on_time=fulfilled,
        processing_hours=_positive_float(raw["processing_hours"], "processing_hours"),
        incidents=_positive_int(raw["incidents"], "incidents"),
    )


def load_rows(
    path: Path = DATA_FILE,
) -> tuple[list[OperationRow], list[ValidationError]]:
    """Load rows and quarantine invalid ones instead of aborting the run."""
    rows: list[OperationRow] = []
    errors: list[ValidationError] = []
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for line_number, raw in enumerate(reader, start=2):
            try:
                rows.append(parse_row(raw))
            except ValueError as exc:
                errors.append(ValidationError(line=line_number, message=str(exc)))
    return rows, errors


def _aggregate(rows: Iterable[OperationRow]) -> dict[str, float | int]:
    materialized = list(rows)
    total_orders = sum(row.orders for row in materialized)
    fulfilled = sum(row.fulfilled_on_time for row in materialized)
    weighted_hours = sum(row.processing_hours * row.orders for row in materialized)
    return {
        "orders": total_orders,
        "revenue_eur": round(sum(row.revenue_eur for row in materialized), 2),
        "on_time_rate": round((fulfilled / total_orders * 100) if total_orders else 0, 1),
        "avg_processing_hours": round(
            (weighted_hours / total_orders) if total_orders else 0,
            1,
        ),
        "incidents": sum(row.incidents for row in materialized),
    }


def build_kpis(
    rows: list[OperationRow] | None = None,
    validation_errors: list[ValidationError] | None = None,
) -> dict:
    if rows is None:
        rows, validation_errors = load_rows()
    elif validation_errors is None:
        validation_errors = []
    if not rows:
        raise ValueError("dataset must contain at least one row")

    by_team: dict[str, list[OperationRow]] = defaultdict(list)
    by_month: dict[str, list[OperationRow]] = defaultdict(list)
    for row in rows:
        by_team[row.team].append(row)
        by_month[row.date.strftime("%Y-%m")].append(row)

    return {
        "summary": _aggregate(rows),
        "teams": [
            {"team": team, **_aggregate(team_rows)}
            for team, team_rows in sorted(by_team.items())
        ],
        "months": [
            {"month": month, **_aggregate(month_rows)}
            for month, month_rows in sorted(by_month.items())
        ],
        "quality": {
            "rows_processed": len(rows),
            "rows_rejected": len(validation_errors),
            "validation_errors": len(validation_errors),
            "validation_messages": [
                f"line {error.line}: {error.message}"
                for error in validation_errors[:5]
            ],
            "source": "data/operations.csv",
            "data_classification": "synthetic",
        },
    }
