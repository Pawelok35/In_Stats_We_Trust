# Weekly Report - Season 2025, Week 1

_Generated at 2025-11-11T13:52:38.893626+00:00 (UTC)_

Data root: `data`

## Layer Shapes

| Layer | Artifact | Manifest | Rows | Columns | Status |
|-------|----------|----------|------|---------|--------|
| L1 Ingest | `data\l1\2025\1.parquet` | `data\l1\2025\1_manifest.json` | 2738 | 18 | ready |
| L2 Clean | `data\l2\2025\1.parquet` | `data\l2\2025\1_manifest.json` | 2738 | 24 | ready |
| L3 Team Week | `data\l3_team_week\2025\1.parquet` | `data\l3_team_week\2025\1_manifest.json` | 32 | 34 | ready |

## L2 Audit Snapshot

Last 3 entries from `data\l2_audit\2025\1_audit.jsonl`:

- {"step": "load", "details": "Loaded L1 parquet", "rows": 2738, "cols": 18, "timestamp": "2025-11-11T13:52:38.507392+00:00"}
- {"step": "prepare", "details": "Normalized team aliases, filtered season/week, deduplicated keys", "rows": 2738, "cols": 24, "rows_removed": 0, "timestamp": "2025-11-11T13:52:38.507392+00:00"}
- {"step": "validate", "details": "Validated against L2 contract and guardrails", "rows": 2738, "cols": 24, "timestamp": "2025-11-11T13:52:38.507392+00:00"}

## L3 Sanity

- Rows processed: 32
- Columns available: 34
- Artifact path: `data\l3_team_week\2025\1.parquet`

## Metrics Snapshot

### L4 Core12 Preview

- Artifact: `data\l4_core12\2025\1.parquet`
- Manifest: `data\l4_core12\2025\1_manifest.json`
- Rows: 32
- Columns: 15

| TEAM | core_epa_off | core_sr_off | core_sr_def |
| --- | --- | --- | --- |
| BAL | 0.3402929010236977 | 0.5633802816901409 | 0.48598130841121495 |
| IND | 0.2513866281246438 | 0.5529411764705883 | 0.47368421052631576 |
| LAC | 0.2110752395618661 | 0.5679012345679012 | 0.45569620253164556 |
| PIT | 0.20591976812907628 | 0.5064935064935064 | 0.55 |
| BUF | 0.20185621668558532 | 0.48598130841121495 | 0.5633802816901409 |

### PowerScore Rankings

- Artifact: `data\l4_powerscore\2025\1.parquet`
- Manifest: `data\l4_powerscore\2025\1_manifest.json`
- Rows: 32
- Columns: 4

| team | power_score |
| --- | --- |
| BAL | 0.3453892516531577 |
| BUF | 0.2845026485680589 |
| LAC | 0.2667936341130515 |
| NYJ | 0.26143171866025244 |
| PIT | 0.2510446676960239 |
| PHI | 0.23367640427821196 |
| DAL | 0.22966680873232953 |
| IND | 0.2279327236313058 |
| KC | 0.22486251747139746 |
| GB | 0.20200948169174965 |


## Visualizations

![PowerScore Top 10](2025_w1/assets/powerscore_top10.png)

