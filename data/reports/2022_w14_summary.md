# Weekly Report - Season 2022, Week 14

_Generated at 2025-11-11T12:25:19.890262+00:00 (UTC)_

Data root: `data`

## Layer Shapes

| Layer | Artifact | Manifest | Rows | Columns | Status |
|-------|----------|----------|------|---------|--------|
| L1 Ingest | `data\l1\2022\14.parquet` | `data\l1\2022\14_manifest.json` | 2274 | 18 | ready |
| L2 Clean | `data\l2\2022\14.parquet` | `data\l2\2022\14_manifest.json` | 2274 | 24 | ready |
| L3 Team Week | `data\l3_team_week\2022\14.parquet` | `data\l3_team_week\2022\14_manifest.json` | 26 | 34 | ready |

## L2 Audit Snapshot

Last 3 entries from `data\l2_audit\2022\14_audit.jsonl`:

- {"step": "load", "details": "Loaded L1 parquet", "rows": 2274, "cols": 18, "timestamp": "2025-11-11T12:25:19.296628+00:00"}
- {"step": "prepare", "details": "Normalized team aliases, filtered season/week, deduplicated keys", "rows": 2274, "cols": 24, "rows_removed": 0, "timestamp": "2025-11-11T12:25:19.296628+00:00"}
- {"step": "validate", "details": "Validated against L2 contract and guardrails", "rows": 2274, "cols": 24, "timestamp": "2025-11-11T12:25:19.296628+00:00"}

## L3 Sanity

- Rows processed: 26
- Columns available: 34
- Artifact path: `data\l3_team_week\2022\14.parquet`

## Metrics Snapshot

### L4 Core12 Preview

- Artifact: `data\l4_core12\2022\14.parquet`
- Manifest: `data\l4_core12\2022\14_manifest.json`
- Rows: N/A
- Columns: N/A

| TEAM | core_epa_off | core_sr_off | core_sr_def |
| --- | --- | --- | --- |
| PHI | 0.3348179808434318 | 0.5411764705882353 | 0.43902439024390244 |
| DET | 0.15596478726630184 | 0.4431818181818182 | 0.4074074074074074 |
| JAX | 0.13906876374449995 | 0.4777777777777778 | 0.47560975609756095 |
| CAR | 0.12233923228232416 | 0.5054945054945055 | 0.4084507042253521 |
| SF | 0.11570523087030803 | 0.5384615384615384 | 0.3977272727272727 |

### PowerScore Rankings

- Artifact: `data\l4_powerscore\2022\14.parquet`
- Manifest: `data\l4_powerscore\2022\14_manifest.json`
- Rows: 26
- Columns: 4

| team | power_score |
| --- | --- |
| PHI | 0.2748450358593075 |
| DET | 0.1952944911011509 |
| CAR | 0.1874227192075792 |
| MIN | 0.17428559455620785 |
| NYG | 0.17360527657409341 |
| JAX | 0.172105561464187 |
| SF | 0.16687353311056632 |
| KC | 0.1641993890430757 |
| SEA | 0.14922038325996848 |
| LV | 0.14338816995655937 |


## Visualizations

![PowerScore Top 10](2022_w14/assets/powerscore_top10.png)

