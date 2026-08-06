from pathlib import Path

from app.data_quality import build_lineage, evaluate_quality, load_contract
from app.pipeline import DATA_FILE, load_rows


def test_contract_is_versioned_and_owned() -> None:
    contract = load_contract()
    assert contract["contract_version"] == "2.0.0"
    assert contract["owner"] == "operations-analytics"
    assert contract["unique_key"] == ["date", "team"]


def test_valid_dataset_passes_every_check() -> None:
    rows, errors = load_rows()
    report = evaluate_quality(rows, errors, DATA_FILE)
    assert report["gate_status"] == "pass"
    assert report["score"] == 100
    assert all(check["status"] == "pass" for check in report["checks"])


def test_rejected_rate_can_stop_publication() -> None:
    rows, errors = load_rows(Path(__file__).parents[1] / "data" / "operations-broken.csv")
    report = evaluate_quality(rows, errors, DATA_FILE)
    assert report["gate_status"] == "fail"
    failed = {check["check_id"] for check in report["checks"] if check["status"] == "fail"}
    assert "validity.rejected_rate" in failed
    assert "volume.minimum_rows" in failed


def test_lineage_is_complete_and_checksum_based() -> None:
    lineage = build_lineage(DATA_FILE)
    assert len(lineage["nodes"]) == 5
    assert len(lineage["edges"]) == 4
    assert len(lineage["nodes"][0]["sha256"]) == 64

