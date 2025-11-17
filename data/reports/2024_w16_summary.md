# Weekly Report - Season 2024, Week 16

_Generated at 2025-11-10T17:51:19.311836+00:00 (UTC)_

Data root: `data`

## Layer Shapes

| Layer | Artifact | Manifest | Rows | Columns | Status |
|-------|----------|----------|------|---------|--------|
| L1 Ingest | `data\l1\2024\16.parquet` | `data\l1\2024\16_manifest.json` | 2764 | 18 | ready |
| L2 Clean | `data\l2\2024\16.parquet` | `data\l2\2024\16_manifest.json` | 2764 | 24 | ready |
| L3 Team Week | `data\l3_team_week\2024\16.parquet` | `data\l3_team_week\2024\16_manifest.json` | 32 | 34 | ready |

## L2 Audit Snapshot

Last 3 entries from `data\l2_audit\2024\16_audit.jsonl`:

- {"step": "load", "details": "Loaded L1 parquet", "rows": 2764, "cols": 18, "timestamp": "2025-11-10T17:51:18.818309+00:00"}
- {"step": "prepare", "details": "Normalized team aliases, filtered season/week, deduplicated keys", "rows": 2764, "cols": 24, "rows_removed": 0, "timestamp": "2025-11-10T17:51:18.818309+00:00"}
- {"step": "validate", "details": "Validated against L2 contract and guardrails", "rows": 2764, "cols": 24, "timestamp": "2025-11-10T17:51:18.818309+00:00"}

## L3 Sanity

- Rows processed: 32
- Columns available: 34
- Artifact path: `data\l3_team_week\2024\16.parquet`

## Metrics Snapshot

### L4 Core12 Preview

- Artifact: `data\l4_core12\2024\16.parquet`
- Manifest: `data\l4_core12\2024\16_manifest.json`
- Rows: N/A
- Columns: N/A

| TEAM | core_epa_off | core_sr_off | core_sr_def |
| --- | --- | --- | --- |
| DET | 0.2762668057367569 | 0.573170731707317 | 0.46987951807228917 |
| GB | 0.2464010525823516 | 0.5058823529411764 | 0.35714285714285715 |
| LAC | 0.2093985794503012 | 0.5308641975308642 | 0.4939759036144578 |
| MIA | 0.1945277580784427 | 0.5679012345679012 | 0.5058823529411764 |
| CAR | 0.17573967646393512 | 0.45555555555555555 | 0.5111111111111111 |

### PowerScore Rankings

- Artifact: `data\l4_powerscore\2024\16.parquet`
- Manifest: `data\l4_powerscore\2024\16_manifest.json`
- Rows: 32
- Columns: 4

| team | power_score |
| --- | --- |
| DET | 0.2686005678865867 |
| LAC | 0.262055353047117 |
| DEN | 0.23279744897505414 |
| MIA | 0.2268396146953939 |
| ARI | 0.22482673462143998 |
| CAR | 0.22378566098192498 |
| BAL | 0.2100128447281746 |
| IND | 0.2015511179730917 |
| CHI | 0.1980851327324992 |
| SEA | 0.19773143696520717 |


## Visualizations

![PowerScore Top 10](2024_w16/assets/powerscore_top10.png)

