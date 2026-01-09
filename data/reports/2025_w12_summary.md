# Weekly Report - Season 2025, Week 12

_Generated at 2026-01-08T19:18:53.166552+00:00 (UTC)_

Data root: `data`

## Layer Shapes

| Layer | Artifact | Manifest | Rows | Columns | Status |
|-------|----------|----------|------|---------|--------|
| L1 Ingest | `data\l1\2025\12.parquet` | `data\l1\2025\12_manifest.json` | 2445 | 18 | ready |
| L2 Clean | `data\l2\2025\12.parquet` | `data\l2\2025\12_manifest.json` | 2445 | 24 | ready |
| L3 Team Week | `data\l3_team_week\2025\12.parquet` | `data\l3_team_week\2025\12_manifest.json` | 28 | 34 | ready |

## L2 Audit Snapshot

Last 3 entries from `data\l2_audit\2025\12_audit.jsonl`:

- {"step": "load", "details": "Loaded L1 parquet", "rows": 2445, "cols": 18, "timestamp": "2026-01-08T19:18:52.735711+00:00"}
- {"step": "prepare", "details": "Normalized team aliases, filtered season/week, deduplicated keys", "rows": 2445, "cols": 24, "rows_removed": 0, "timestamp": "2026-01-08T19:18:52.735711+00:00"}
- {"step": "validate", "details": "Validated against L2 contract and guardrails", "rows": 2445, "cols": 24, "timestamp": "2026-01-08T19:18:52.735711+00:00"}

## L3 Sanity

- Rows processed: 28
- Columns available: 34
- Artifact path: `data\l3_team_week\2025\12.parquet`

## Metrics Snapshot

### L4 Core12 Preview

- Artifact: `data\l4_core12\2025\12.parquet`
- Manifest: `data\l4_core12\2025\12_manifest.json`
- Rows: 28
- Columns: 27

| TEAM | core_epa_off | core_sr_off | core_sr_def |
| --- | --- | --- | --- |
| DET | 0.15410611207286518 | 0.5333333333333333 | 0.41836734693877553 |
| NYG | 0.11145007308116373 | 0.41836734693877553 | 0.5333333333333333 |
| SEA | 0.10045876206857139 | 0.4927536231884058 | 0.4111111111111111 |
| GB | 0.09718927070952771 | 0.5 | 0.46551724137931033 |
| BAL | 0.08521220073677026 | 0.41025641025641024 | 0.3918918918918919 |

### PowerScore Rankings

- Artifact: `data\l4_powerscore\2025\12.parquet`
- Manifest: `data\l4_powerscore\2025\12_manifest.json`
- Rows: 28
- Columns: 4

| team | power_score |
| --- | --- |
| TEN | 2.110274643947321 |
| KC | 2.0240689365813314 |
| NYG | 1.8077539180610076 |
| SF | 1.7155550212829151 |
| NO | 1.7149519172919223 |
| PIT | 1.6946331871840128 |
| NE | 1.6857700400515352 |
| ARI | 1.6558556441293186 |
| CIN | 1.6448234421601269 |
| PHI | 1.6270853253685345 |


## Visualizations

![PowerScore Top 10](2025_w12/assets/powerscore_top10.png)

