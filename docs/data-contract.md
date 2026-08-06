# Data contract and quality gate

`data/contract.json` is the versioned agreement between the CSV producer and the KPI data
product. It captures ownership, classification, required schema, accepted team values, the
business key, expected volume and reporting period.

The quality engine evaluates six independent checks:

| Dimension | Check | Why it matters |
|---|---|---|
| Completeness | minimum rows | prevents publication of a partial extract |
| Completeness | minimum month coverage | protects trend calculations |
| Validity | rejected-row rate | makes quarantine volume visible |
| Uniqueness | date + team key | prevents double-counting |
| Validity | allowed teams | detects unexpected source domains |
| Freshness | expected reporting period | identifies late deliveries |

`/api/quality` returns the gate result, score, contract version, source SHA-256 and evidence for
every check. `/api/refresh` publishes KPIs only after running the same gate and records its result
in the pipeline trace.

The sample contract describes a closed synthetic reporting period. This avoids a permanently
moving “today” check while still proving how a real expected-delivery window is enforced.

