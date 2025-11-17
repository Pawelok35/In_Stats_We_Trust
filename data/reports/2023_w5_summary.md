# Weekly Report - Season 2023, Week 5

_Generated at 2025-11-10T20:37:48.826424+00:00 (UTC)_

Data root: `data`

## Layer Shapes

| Layer | Artifact | Manifest | Rows | Columns | Status |
|-------|----------|----------|------|---------|--------|
| L1 Ingest | `data\l1\2023\5.parquet` | `data\l1\2023\5_manifest.json` | 2430 | 18 | ready |
| L2 Clean | `data\l2\2023\5.parquet` | `data\l2\2023\5_manifest.json` | 2430 | 24 | ready |
| L3 Team Week | `data\l3_team_week\2023\5.parquet` | `data\l3_team_week\2023\5_manifest.json` | 28 | 34 | ready |

## L2 Audit Snapshot

Last 3 entries from `data\l2_audit\2023\5_audit.jsonl`:

- {"step": "load", "details": "Loaded L1 parquet", "rows": 2430, "cols": 18, "timestamp": "2025-11-10T20:37:48.297056+00:00"}
- {"step": "prepare", "details": "Normalized team aliases, filtered season/week, deduplicated keys", "rows": 2430, "cols": 24, "rows_removed": 0, "timestamp": "2025-11-10T20:37:48.297056+00:00"}
- {"step": "validate", "details": "Validated against L2 contract and guardrails", "rows": 2430, "cols": 24, "timestamp": "2025-11-10T20:37:48.297056+00:00"}

## L3 Sanity

- Rows processed: 28
- Columns available: 34
- Artifact path: `data\l3_team_week\2023\5.parquet`

## Metrics Snapshot

### L4 Core12 Preview

- Artifact: `data\l4_core12\2023\5.parquet`
- Manifest: `data\l4_core12\2023\5_manifest.json`
- Rows: N/A
- Columns: N/A

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
| JAX | 0.21630110665228688 |
| DET | 0.21388261674643289 |
| BUF | 0.21184313675420907 |
| CHI | 0.20299454235109587 |
| IND | 0.20087665365375712 |
| TEN | 0.18494546480240048 |
| PHI | 0.1844652242355323 |
| MIA | 0.1725423805166275 |
| KC | 0.16996827857622743 |
| MIN | 0.1552539840085993 |


## Visualizations

![PowerScore Top 10](2023_w5/assets/powerscore_top10.png)

