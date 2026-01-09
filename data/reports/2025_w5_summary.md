# Weekly Report - Season 2025, Week 5

_Generated at 2026-01-08T19:13:14.897604+00:00 (UTC)_

Data root: `data`

## Layer Shapes

| Layer | Artifact | Manifest | Rows | Columns | Status |
|-------|----------|----------|------|---------|--------|
| L1 Ingest | `data\l1\2025\5.parquet` | `data\l1\2025\5_manifest.json` | 2454 | 18 | ready |
| L2 Clean | `data\l2\2025\5.parquet` | `data\l2\2025\5_manifest.json` | 2454 | 24 | ready |
| L3 Team Week | `data\l3_team_week\2025\5.parquet` | `data\l3_team_week\2025\5_manifest.json` | 28 | 34 | ready |

## L2 Audit Snapshot

Last 3 entries from `data\l2_audit\2025\5_audit.jsonl`:

- {"step": "load", "details": "Loaded L1 parquet", "rows": 2454, "cols": 18, "timestamp": "2026-01-08T19:13:14.487315+00:00"}
- {"step": "prepare", "details": "Normalized team aliases, filtered season/week, deduplicated keys", "rows": 2454, "cols": 24, "rows_removed": 0, "timestamp": "2026-01-08T19:13:14.487315+00:00"}
- {"step": "validate", "details": "Validated against L2 contract and guardrails", "rows": 2454, "cols": 24, "timestamp": "2026-01-08T19:13:14.487315+00:00"}

## L3 Sanity

- Rows processed: 28
- Columns available: 34
- Artifact path: `data\l3_team_week\2025\5.parquet`

## Metrics Snapshot

### L4 Core12 Preview

- Artifact: `data\l4_core12\2025\5.parquet`
- Manifest: `data\l4_core12\2025\5_manifest.json`
- Rows: 28
- Columns: 27

| TEAM | core_epa_off | core_sr_off | core_sr_def |
| --- | --- | --- | --- |
| TB | 0.33884341191304357 | 0.5394736842105263 | 0.5714285714285714 |
| HOU | 0.31254115817958816 | 0.611764705882353 | 0.43548387096774194 |
| DAL | 0.25794387863176627 | 0.47560975609756095 | 0.5 |
| SEA | 0.24349613059554007 | 0.5714285714285714 | 0.5394736842105263 |
| IND | 0.2424103805422783 | 0.5066666666666667 | 0.5 |

### PowerScore Rankings

- Artifact: `data\l4_powerscore\2025\5.parquet`
- Manifest: `data\l4_powerscore\2025\5_manifest.json`
- Rows: 28
- Columns: 4

| team | power_score |
| --- | --- |
| SF | 2.1097036337804633 |
| IND | 2.0418975657640193 |
| WAS | 2.040342783181571 |
| LV | 1.9176320136688993 |
| HOU | 1.9122343111878963 |
| KC | 1.8694727802689235 |
| DEN | 1.8693394455977588 |
| SEA | 1.8358494709481907 |
| TB | 1.822162841341305 |
| NYJ | 1.8188294896970167 |


## Visualizations

![PowerScore Top 10](2025_w5/assets/powerscore_top10.png)

