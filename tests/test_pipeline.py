from pathlib import Path

import pytest

from app.pipeline import build_kpis, load_rows, parse_row

HEADER = "date,team,orders,revenue_eur,fulfilled_on_time,processing_hours,incidents"


def test_dataset_is_loaded() -> None:
    rows, errors = load_rows()
    assert len(rows) == 52
    assert errors == []
    assert {row.team for row in rows} == {"North", "South", "Central"}


def test_kpis_are_aggregated() -> None:
    payload = build_kpis()
    assert payload["summary"] == {
        "orders": 6039,
        "revenue_eur": 895073.68,
        "on_time_rate": 95.1,
        "avg_processing_hours": 5.3,
        "incidents": 92,
    }
    assert len(payload["months"]) == 12
    assert len(payload["teams"]) == 3


def test_quality_metadata_is_explicit() -> None:
    payload = build_kpis()
    assert {
        "rows_processed": 52,
        "rows_rejected": 0,
        "validation_errors": 0,
        "validation_messages": [],
        "source": "data/operations.csv",
        "data_classification": "synthetic",
        "gate_status": "pass",
        "score": 100,
        "contract_version": "2.0.0",
    }.items() <= payload["quality"].items()
    assert len(payload["quality"]["source_sha256"]) == 64
    assert len(payload["quality"]["checks"]) == 6


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


def test_negative_values_are_rejected() -> None:
    with pytest.raises(ValueError, match="must not be negative"):
        parse_row(
            {
                "date": "2026-01-01",
                "team": "Demo",
                "orders": "-3",
                "revenue_eur": "100",
                "fulfilled_on_time": "0",
                "processing_hours": "2",
                "incidents": "0",
            }
        )


def test_missing_columns_are_rejected() -> None:
    with pytest.raises(ValueError, match="missing columns: incidents"):
        parse_row(
            {
                "date": "2026-01-01",
                "team": "Demo",
                "orders": "3",
                "revenue_eur": "100",
                "fulfilled_on_time": "2",
                "processing_hours": "2",
            }
        )


def test_invalid_date_is_rejected() -> None:
    with pytest.raises(ValueError, match="isoformat"):
        parse_row(
            {
                "date": "19.05.2026",
                "team": "Demo",
                "orders": "3",
                "revenue_eur": "100",
                "fulfilled_on_time": "2",
                "processing_hours": "2",
                "incidents": "0",
            }
        )


def test_truncated_row_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="missing values: fulfilled_on_time, incidents, processing_hours",
    ):
        parse_row(
            {
                "date": "2026-06-02",
                "team": "Central",
                "orders": "158",
                "revenue_eur": "24490.00",
                "fulfilled_on_time": None,
                "processing_hours": None,
                "incidents": None,
            }
        )


@pytest.mark.parametrize("value", ["nan", "inf", "-inf"])
def test_non_finite_floats_are_rejected(value: str) -> None:
    with pytest.raises(ValueError, match="must be a finite number"):
        parse_row(
            {
                "date": "2026-01-01",
                "team": "Demo",
                "orders": "3",
                "revenue_eur": value,
                "fulfilled_on_time": "2",
                "processing_hours": "2",
                "incidents": "0",
            }
        )


def test_invalid_rows_are_quarantined(tmp_path: Path) -> None:
    broken = tmp_path / "broken.csv"
    broken.write_text(
        f"{HEADER}\n"
        "2026-01-01,North,10,1000,9,5.0,1\n"
        "2026-01-02,South,-2,500,0,4.0,0\n"
        "not-a-date,Central,7,800,6,3.5,0\n"
        "2026-01-04,North,5,600,7,4.2,1\n",
        encoding="utf-8",
    )
    rows, errors = load_rows(broken)
    assert len(rows) == 1
    assert len(errors) == 3
    assert [error.line for error in errors] == [3, 4, 5]

    payload = build_kpis(rows, errors)
    assert payload["quality"]["rows_processed"] == 1
    assert payload["quality"]["rows_rejected"] == 3
    assert len(payload["quality"]["validation_messages"]) == 3


def test_broken_example_file_is_quarantined() -> None:
    broken = Path(__file__).parent.parent / "data" / "operations-broken.csv"
    rows, errors = load_rows(broken)
    assert len(rows) == 5
    assert len(errors) == 7
    messages = " ".join(error.message for error in errors)
    assert "missing values" in messages
    assert "must be a finite number" in messages


def test_empty_dataset_is_rejected(tmp_path: Path) -> None:
    empty = tmp_path / "empty.csv"
    empty.write_text(f"{HEADER}\n", encoding="utf-8")
    rows, errors = load_rows(empty)
    assert rows == []
    assert errors == []
    with pytest.raises(ValueError, match="at least one row"):
        build_kpis([])


def test_duplicate_date_and_team_fails_quality_gate() -> None:
    rows, errors = load_rows()
    payload = build_kpis([*rows, rows[0]], errors)
    uniqueness = next(
        check
        for check in payload["quality"]["checks"]
        if check["check_id"] == "uniqueness.date_team"
    )
    assert payload["quality"]["gate_status"] == "fail"
    assert uniqueness["status"] == "fail"
