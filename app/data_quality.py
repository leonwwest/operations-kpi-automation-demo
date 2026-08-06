"""Versioned data-contract checks and lineage for the operations pipeline."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Any

CONTRACT_FILE = Path(__file__).resolve().parent.parent / "data" / "contract.json"


@dataclass(frozen=True)
class QualityCheck:
    check_id: str
    dimension: str
    status: str
    observed: str
    expected: str


def load_contract(path: Path = CONTRACT_FILE) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _check(
    check_id: str,
    dimension: str,
    passed: bool,
    observed: str,
    expected: str,
) -> QualityCheck:
    return QualityCheck(
        check_id=check_id,
        dimension=dimension,
        status="pass" if passed else "fail",
        observed=observed,
        expected=expected,
    )


def evaluate_quality(
    rows: Iterable[Any],
    validation_errors: Iterable[Any],
    source: Path,
    contract: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Evaluate rows against the checked-in contract without mutating the dataset."""
    materialized = list(rows)
    errors = list(validation_errors)
    contract = contract or load_contract()
    total_read = len(materialized) + len(errors)
    rejected_rate = (len(errors) / total_read * 100) if total_read else 100.0
    teams = sorted({row.team for row in materialized})
    months = sorted({row.date.strftime("%Y-%m") for row in materialized})
    keys = [(row.date.isoformat(), row.team) for row in materialized]
    duplicates = len(keys) - len(set(keys))
    latest = max((row.date for row in materialized), default=None)
    expected_end = date.fromisoformat(contract["expected_period_end"])
    lag_days = (expected_end - latest).days if latest else 999999

    checks = [
        _check(
            "volume.minimum_rows",
            "completeness",
            len(materialized) >= contract["minimum_rows"],
            str(len(materialized)),
            f">={contract['minimum_rows']}",
        ),
        _check(
            "coverage.minimum_months",
            "completeness",
            len(months) >= contract["minimum_months"],
            str(len(months)),
            f">={contract['minimum_months']}",
        ),
        _check(
            "validity.rejected_rate",
            "validity",
            rejected_rate <= contract["maximum_rejected_rate_pct"],
            f"{rejected_rate:.2f}%",
            f"<={contract['maximum_rejected_rate_pct']:.2f}%",
        ),
        _check(
            "uniqueness.date_team",
            "uniqueness",
            duplicates == 0,
            str(duplicates),
            "0 duplicate keys",
        ),
        _check(
            "domain.allowed_teams",
            "validity",
            set(teams) <= set(contract["allowed_teams"]),
            ", ".join(teams),
            ", ".join(contract["allowed_teams"]),
        ),
        _check(
            "freshness.expected_period",
            "freshness",
            0 <= lag_days <= contract["maximum_period_lag_days"],
            latest.isoformat() if latest else "no rows",
            (
                f"within {contract['maximum_period_lag_days']} days before "
                f"{contract['expected_period_end']}"
            ),
        ),
    ]
    failed = [check for check in checks if check.status == "fail"]
    score = round((len(checks) - len(failed)) / len(checks) * 100)
    return {
        "gate_status": "pass" if not failed else "fail",
        "score": score,
        "contract_version": contract["contract_version"],
        "dataset": contract["dataset"],
        "owner": contract["owner"],
        "source_sha256": file_sha256(source),
        "checks": [asdict(check) for check in checks],
    }


def build_lineage(source: Path, contract: dict[str, Any] | None = None) -> dict[str, Any]:
    contract = contract or load_contract()
    return {
        "contract_version": contract["contract_version"],
        "nodes": [
            {
                "id": "source.operations_csv",
                "type": "source",
                "name": source.name,
                "sha256": file_sha256(source),
            },
            {
                "id": "transform.validation",
                "type": "transform",
                "name": "schema and business-rule validation",
            },
            {
                "id": "transform.kpi_aggregation",
                "type": "transform",
                "name": "team and monthly KPI aggregation",
            },
            {
                "id": "product.kpi_api",
                "type": "data_product",
                "name": "/api/kpis",
            },
            {
                "id": "consumer.power_bi",
                "type": "consumer",
                "name": "Power BI / Power Query",
            },
        ],
        "edges": [
            {"from": "source.operations_csv", "to": "transform.validation"},
            {"from": "transform.validation", "to": "transform.kpi_aggregation"},
            {"from": "transform.kpi_aggregation", "to": "product.kpi_api"},
            {"from": "product.kpi_api", "to": "consumer.power_bi"},
        ],
    }
