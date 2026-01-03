# Weekly Report - Season 2023, Week 5

_Generated at 2026-01-02T10:19:59.083275+00:00 (UTC)_

Data root: `data`

## Layer Shapes

| Layer | Artifact | Manifest | Rows | Columns | Status |
|-------|----------|----------|------|---------|--------|
| L1 Ingest | `data\l1\2023\5.parquet` | `data\l1\2023\5_manifest.json` | 2430 | 18 | ready |
| L2 Clean | `data\l2\2023\5.parquet` | `data\l2\2023\5_manifest.json` | 2430 | 24 | ready |
| L3 Team Week | `data\l3_team_week\2023\5.parquet` | `data\l3_team_week\2023\5_manifest.json` | 28 | 34 | ready |

## L2 Audit Snapshot

Last 3 entries from `data\l2_audit\2023\5_audit.jsonl`:

- {"step": "load", "details": "Loaded L1 parquet", "rows": 2430, "cols": 18, "timestamp": "2026-01-02T10:19:58.698232+00:00"}
- {"step": "prepare", "details": "Normalized team aliases, filtered season/week, deduplicated keys", "rows": 2430, "cols": 24, "rows_removed": 0, "timestamp": "2026-01-02T10:19:58.698232+00:00"}
- {"step": "validate", "details": "Validated against L2 contract and guardrails", "rows": 2430, "cols": 24, "timestamp": "2026-01-02T10:19:58.698232+00:00"}

## L3 Sanity

- Rows processed: 28
- Columns available: 34
- Artifact path: `data\l3_team_week\2023\5.parquet`

## Metrics Snapshot

### L4 Core12 Preview

- Artifact: `data\l4_core12\2023\5.parquet`
- Manifest: `data\l4_core12\2023\5_manifest.json`
- Rows: 28
- Columns: 27

| TEAM | core_epa_off | core_sr_off | core_sr_def |
| --- | --- | --- | --- |
| CHI | 0.2424921473061823 | 0.43373493975903615 | 0.38372093023255816 |
| DET | 0.20039923658425157 | 0.5194805194805194 | 0.45555555555555555 |
| IND | 0.15470334372402708 | 0.3950617283950617 | 0.410958904109589 |
| JAX | 0.14161947665824776 | 0.4666666666666667 | 0.47297297297297297 |
| SF | 0.1358082417071193 | 0.5714285714285714 | 0.36507936507936506 |

### PowerScore Rankings

- Artifact: `data\l4_powerscore\2023\5.parquet`
- Manifest: `data\l4_powerscore\2023\5_manifest.json`
- Rows: 28
- Columns: 4

| team | power_score |
| --- | --- |
| PHI | 2.4396850044553124 |
| MIN | 2.2889749142411575 |
| KC | 2.207773156625008 |
| IND | 2.196247024024127 |
| TEN | 1.9907673826106198 |
| JAX | 1.9396344399856202 |
| CAR | 1.93279151037687 |
| NYG | 1.9115358618473575 |
| LA | 1.816912980707129 |
| CHI | 1.6879890658998364 |


## Visualizations

![PowerScore Top 10](2023_w5/assets/powerscore_top10.png)

