# Weekly Report - Season 2025, Week 8

_Generated at 2025-10-28T18:25:48.967823+00:00 (UTC)_

Data root: `data`

## Layer Shapes

| Layer | Artifact | Manifest | Rows | Columns | Status |
|-------|----------|----------|------|---------|--------|
| L1 Ingest | `data\l1\2025\8.parquet` | `data\l1\2025\8_manifest.json` | 6 | 13 | ready |
| L2 Clean | `data\l2\2025\8.parquet` | `data\l2\2025\8_manifest.json` | 6 | 12 | ready |
| L3 Team Week | `data\l3_team_week\2025\8.parquet` | `data\l3_team_week\2025\8_manifest.json` | 2 | 10 | ready |

## L2 Audit Snapshot

Last 3 entries from `data\l2_audit\2025\8_audit.jsonl`:

- {"step": "load", "details": "Loaded L1 parquet", "rows": 6, "cols": 13, "timestamp": "2025-10-28T18:25:48.718585+00:00"}
- {"step": "prepare", "details": "Normalized team aliases, filtered season/week, deduplicated keys", "rows": 6, "cols": 12, "rows_removed": 0, "timestamp": "2025-10-28T18:25:48.718585+00:00"}
- {"step": "validate", "details": "Validated against L2 contract and guardrails", "rows": 6, "cols": 12, "timestamp": "2025-10-28T18:25:48.718585+00:00"}

## L3 Sanity

- Rows processed: 2
- Columns available: 10
- Artifact path: `data\l3_team_week\2025\8.parquet`

## Metrics Snapshot

### L4 Core12 Preview

- Artifact: `data\l4_core12\2025\8.parquet`
- Manifest: `data\l4_core12\2025\8_manifest.json`
- Rows: 2
- Columns: 9

| TEAM | core_epa_off | core_sr_off | core_sr_def |
| --- | --- | --- | --- |
| AAA | 0.06666666666666667 | 0.6666666666666666 | 0.5 |
| BBB | 0.05000000000000001 | 0.5 | 0.33333333333333337 |

### PowerScore Rankings

- Artifact: `data\l4_powerscore\2025\8.parquet`
- Manifest: `data\l4_powerscore\2025\8_manifest.json`
- Rows: 2
- Columns: 4

| team | power_score |
| --- | --- |
| AAA | 0.38 |
| BBB | 0.3291666666666667 |


## Visualizations

![PowerScore Top 10](2025_w8/assets/powerscore_top10.png)

