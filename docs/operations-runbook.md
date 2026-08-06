# ETL operations runbook

## Normal refresh

1. Call `POST /api/refresh`.
2. Record `run_id`, source checksum, contract version and quality score.
3. Confirm the quality gate is `pass`.
4. Compare row, team and month counts with the previous successful run.
5. Refresh the Power BI dataset only after the API result is available.

## Quality gate failure

1. Do not replace the last known-good data product.
2. Open `/api/quality` and identify failed checks.
3. Review the quarantined line numbers in `quality.validation_messages`.
4. Compare the current source SHA-256 with the last successful run.
5. Correct the producer or contract through a reviewed change; never edit output KPIs manually.
6. Rerun and attach before/after gate evidence to the incident or change ticket.

## Duplicate-key incident

The business key is `(date, team)`. A duplicate would inflate orders, revenue and incidents.
Quarantine or deduplicate at the source, document the chosen winner and rerun the complete period.

## Contract change

A new team, column or reporting cadence requires a contract-version update, tests, and a consumer
impact review for the API, Power Query and DAX assets.

