# Weekly Report - Season 2025, Week 7

_Generated at 2026-01-08T19:14:41.223055+00:00 (UTC)_

Data root: `data`

## Layer Shapes

| Layer | Artifact | Manifest | Rows | Columns | Status |
|-------|----------|----------|------|---------|--------|
| L1 Ingest | `data\l1\2025\7.parquet` | `data\l1\2025\7_manifest.json` | 2614 | 18 | ready |
| L2 Clean | `data\l2\2025\7.parquet` | `data\l2\2025\7_manifest.json` | 2614 | 24 | ready |
| L3 Team Week | `data\l3_team_week\2025\7.parquet` | `data\l3_team_week\2025\7_manifest.json` | 30 | 34 | ready |

## L2 Audit Snapshot

Last 3 entries from `data\l2_audit\2025\7_audit.jsonl`:

- {"step": "load", "details": "Loaded L1 parquet", "rows": 2614, "cols": 18, "timestamp": "2026-01-08T19:14:40.775271+00:00"}
- {"step": "prepare", "details": "Normalized team aliases, filtered season/week, deduplicated keys", "rows": 2614, "cols": 24, "rows_removed": 0, "timestamp": "2026-01-08T19:14:40.775271+00:00"}
- {"step": "validate", "details": "Validated against L2 contract and guardrails", "rows": 2614, "cols": 24, "timestamp": "2026-01-08T19:14:40.775271+00:00"}

## L3 Sanity

- Rows processed: 30
- Columns available: 34
- Artifact path: `data\l3_team_week\2025\7.parquet`

## Metrics Snapshot

### L4 Core12 Preview

- Artifact: `data\l4_core12\2025\7.parquet`
- Manifest: `data\l4_core12\2025\7_manifest.json`
- Rows: 30
- Columns: 27

| TEAM | core_epa_off | core_sr_off | core_sr_def |
| --- | --- | --- | --- |
| IND | 0.3671692300688576 | 0.5540540540540541 | 0.4782608695652174 |
| PIT | 0.26228544445708396 | 0.5466666666666666 | 0.5368421052631579 |
| LA | 0.24519463220675444 | 0.5172413793103449 | 0.45652173913043476 |
| CIN | 0.21908684763077058 | 0.5368421052631579 | 0.5466666666666666 |
| KC | 0.19428311674756574 | 0.5 | 0.3333333333333333 |

### PowerScore Rankings

- Artifact: `data\l4_powerscore\2025\7.parquet`
- Manifest: `data\l4_powerscore\2025\7_manifest.json`
- Rows: 30
- Columns: 4

| team | power_score |
| --- | --- |
| LAC | 2.524410409082688 |
| KC | 2.215487679908378 |
| CIN | 2.163348011877976 |
| ARI | 2.116025907197049 |
| IND | 1.929416528869265 |
| SF | 1.8848838905966372 |
| ATL | 1.8030181438353288 |
| MIN | 1.8019717384788443 |
| JAX | 1.7958508068550054 |
| NE | 1.7860791641564222 |


## Visualizations

![PowerScore Top 10](2025_w7/assets/powerscore_top10.png)

