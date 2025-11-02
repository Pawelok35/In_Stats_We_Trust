# Weekly Report - Season 2025, Week 9

_Generated at 2025-11-02T11:58:32.673246+00:00 (UTC)_

Data root: `data`

## Layer Shapes

| Layer | Artifact | Manifest | Rows | Columns | Status |
|-------|----------|----------|------|---------|--------|
| L1 Ingest | `data\l1\2025\9.parquet` | `data\l1\2025\9_manifest.json` | 159 | 18 | ready |
| L2 Clean | `data\l2\2025\9.parquet` | `data\l2\2025\9_manifest.json` | 159 | 14 | ready |
| L3 Team Week | `data\l3_team_week\2025\9.parquet` | `data\l3_team_week\2025\9_manifest.json` | 2 | 10 | ready |

## L2 Audit Snapshot

Last 3 entries from `data\l2_audit\2025\9_audit.jsonl`:

- {"step": "load", "details": "Loaded L1 parquet", "rows": 159, "cols": 18, "timestamp": "2025-11-02T11:58:32.301118+00:00"}
- {"step": "prepare", "details": "Normalized team aliases, filtered season/week, deduplicated keys", "rows": 159, "cols": 14, "rows_removed": 0, "timestamp": "2025-11-02T11:58:32.301118+00:00"}
- {"step": "validate", "details": "Validated against L2 contract and guardrails", "rows": 159, "cols": 14, "timestamp": "2025-11-02T11:58:32.301118+00:00"}

## L3 Sanity

- Rows processed: 2
- Columns available: 10
- Artifact path: `data\l3_team_week\2025\9.parquet`

## Metrics Snapshot

### L4 Core12 Preview

- Artifact: `data\l4_core12\2025\9.parquet`
- Manifest: `data\l4_core12\2025\9_manifest.json`
- Rows: 2
- Columns: 15

| TEAM | core_epa_off | core_sr_off | core_sr_def |
| --- | --- | --- | --- |
| BAL | 0.13702889081930192 | 0.5211267605633803 | 0.4230769230769231 |
| MIA | -0.19530646457599524 | 0.4230769230769231 | 0.5211267605633803 |

### PowerScore Rankings

- Artifact: `data\l4_powerscore\2025\9.parquet`
- Manifest: `data\l4_powerscore\2025\9_manifest.json`
- Rows: 2
- Columns: 4

| team | power_score |
| --- | --- |
| BAL | 0.13918050901240167 |
| MIA | 0.06481774633149283 |


## Visualizations

![PowerScore Top 10](2025_w9/assets/powerscore_top10.png)

