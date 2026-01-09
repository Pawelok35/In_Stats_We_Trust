# Weekly Report - Season 2025, Week 8

_Generated at 2026-01-08T19:15:27.476778+00:00 (UTC)_

Data root: `data`

## Layer Shapes

| Layer | Artifact | Manifest | Rows | Columns | Status |
|-------|----------|----------|------|---------|--------|
| L1 Ingest | `data\l1\2025\8.parquet` | `data\l1\2025\8_manifest.json` | 2142 | 18 | ready |
| L2 Clean | `data\l2\2025\8.parquet` | `data\l2\2025\8_manifest.json` | 2142 | 24 | ready |
| L3 Team Week | `data\l3_team_week\2025\8.parquet` | `data\l3_team_week\2025\8_manifest.json` | 26 | 34 | ready |

## L2 Audit Snapshot

Last 3 entries from `data\l2_audit\2025\8_audit.jsonl`:

- {"step": "load", "details": "Loaded L1 parquet", "rows": 2142, "cols": 18, "timestamp": "2026-01-08T19:15:27.041214+00:00"}
- {"step": "prepare", "details": "Normalized team aliases, filtered season/week, deduplicated keys", "rows": 2142, "cols": 24, "rows_removed": 0, "timestamp": "2026-01-08T19:15:27.041214+00:00"}
- {"step": "validate", "details": "Validated against L2 contract and guardrails", "rows": 2142, "cols": 24, "timestamp": "2026-01-08T19:15:27.041214+00:00"}

## L3 Sanity

- Rows processed: 26
- Columns available: 34
- Artifact path: `data\l3_team_week\2025\8.parquet`

## Metrics Snapshot

### L4 Core12 Preview

- Artifact: `data\l4_core12\2025\8.parquet`
- Manifest: `data\l4_core12\2025\8_manifest.json`
- Rows: 26
- Columns: 27

| TEAM | core_epa_off | core_sr_off | core_sr_def |
| --- | --- | --- | --- |
| DEN | 0.33052069837628284 | 0.5949367088607594 | 0.5531914893617021 |
| PHI | 0.3072478346868501 | 0.5822784810126582 | 0.4857142857142857 |
| IND | 0.2969749304118441 | 0.47761194029850745 | 0.4318181818181818 |
| BUF | 0.2825220279348425 | 0.5189873417721519 | 0.47435897435897434 |
| CIN | 0.24932262560009563 | 0.6578947368421053 | 0.5604395604395604 |

### PowerScore Rankings

- Artifact: `data\l4_powerscore\2025\8.parquet`
- Manifest: `data\l4_powerscore\2025\8_manifest.json`
- Rows: 26
- Columns: 4

| team | power_score |
| --- | --- |
| LAC | 2.100588976658951 |
| HOU | 2.0752364920969733 |
| PHI | 2.027962102626074 |
| BAL | 2.002796361835657 |
| CHI | 1.9769993181206305 |
| DAL | 1.9357040912169274 |
| NYJ | 1.9296053134602669 |
| KC | 1.9121177533411613 |
| MIA | 1.8300382412427474 |
| CIN | 1.82035685670479 |


## Visualizations

![PowerScore Top 10](2025_w8/assets/powerscore_top10.png)

