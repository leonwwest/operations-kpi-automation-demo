from pathlib import Path

import pytest

from app.pipeline import build_kpis, load_rows, parse_row


def test_dataset_is_loaded() -> None:
    rows = load_rows()
    assert len(rows) == 12
    assert {row.team for row in rows} == {"North", "South", "Central"}


def test_kpis_are_aggregated() -> None:
    payload = build_kpis()
    assert payload["summary"]["orders"] == 1674
    assert payload["summary"]["revenue_eur"] == 248380.0
    assert payload["summary"]["on_time_rate"] > 94
    assert len(payload["months"]) == 3


def test_quality_metadata_is_explicit() -> None:
    payload = build_kpis()
    assert payload["quality"] == {
        "rows_processed": 12,
        "validation_errors": 0,
        "source": "data/operations.csv",
        "data_classification": "synthetic",
    }


def test_fulfilled_orders_cannot_exceed_total() -> None:
    with pytest.raises(ValueError, match="must not exceed"):
        parse_row(
            {
                "date": "2026-01-01",
                "team": "Demo",
                "orders": "3",
                "revenue_eur": "100",
                "fulfilled_on_time": "4",
                "processing_hours": "2",
                "incidents": "0",
            }
        )


def test_empty_dataset_is_rejected(tmp_path: Path) -> None:
    empty = tmp_path / "empty.csv"
    empty.write_text(
        "date,team,orders,revenue_eur,fulfilled_on_time,processing_hours,incidents\n",
        encoding="utf-8",
    )
    assert load_rows(empty) == []
    with pytest.raises(ValueError, match="at least one row"):
        build_kpis([])
