# Weekly Report - Season 2023, Week 11

_Generated at 2025-11-10T20:38:56.217284+00:00 (UTC)_

Data root: `data`

## Layer Shapes

| Layer | Artifact | Manifest | Rows | Columns | Status |
|-------|----------|----------|------|---------|--------|
| L1 Ingest | `data\l1\2023\11.parquet` | `data\l1\2023\11_manifest.json` | 2410 | 18 | ready |
| L2 Clean | `data\l2\2023\11.parquet` | `data\l2\2023\11_manifest.json` | 2410 | 24 | ready |
| L3 Team Week | `data\l3_team_week\2023\11.parquet` | `data\l3_team_week\2023\11_manifest.json` | 28 | 34 | ready |

## L2 Audit Snapshot

Last 3 entries from `data\l2_audit\2023\11_audit.jsonl`:

- {"step": "load", "details": "Loaded L1 parquet", "rows": 2410, "cols": 18, "timestamp": "2025-11-10T20:38:55.760798+00:00"}
- {"step": "prepare", "details": "Normalized team aliases, filtered season/week, deduplicated keys", "rows": 2410, "cols": 24, "rows_removed": 0, "timestamp": "2025-11-10T20:38:55.760798+00:00"}
- {"step": "validate", "details": "Validated against L2 contract and guardrails", "rows": 2410, "cols": 24, "timestamp": "2025-11-10T20:38:55.760798+00:00"}

## L3 Sanity

- Rows processed: 28
- Columns available: 34
- Artifact path: `data\l3_team_week\2023\11.parquet`

## Metrics Snapshot

### L4 Core12 Preview

- Artifact: `data\l4_core12\2023\11.parquet`
- Manifest: `data\l4_core12\2023\11_manifest.json`
- Rows: N/A
- Columns: N/A

| TEAM | core_epa_off | core_sr_off | core_sr_def |
| --- | --- | --- | --- |
| JAX | 0.31209720766526605 | 0.4880952380952381 | 0.38333333333333336 |
| DAL | 0.16022337277302112 | 0.4367816091954023 | 0.3815789473684211 |
| BAL | 0.15139809104961804 | 0.4939759036144578 | 0.39285714285714285 |
| SF | 0.13321212241174402 | 0.5405405405405406 | 0.4642857142857143 |
| BUF | 0.06484686397016048 | 0.3695652173913043 | 0.2602739726027397 |

### PowerScore Rankings

- Artifact: `data\l4_powerscore\2023\11.parquet`
- Manifest: `data\l4_powerscore\2023\11_manifest.json`
- Rows: 28
- Columns: 4

| team | power_score |
| --- | --- |
| JAX | 0.2592946743346485 |
| SF | 0.20119197909205438 |
| BAL | 0.19414792681581486 |
| TEN | 0.18731724859037927 |
| DET | 0.15493725253750776 |
| CHI | 0.14732227620279825 |
| DAL | 0.1445430239031505 |
| GB | 0.1434983386389149 |
| CIN | 0.1423387141602995 |
| LAC | 0.13831459058079942 |


## Visualizations

![PowerScore Top 10](2023_w11/assets/powerscore_top10.png)

