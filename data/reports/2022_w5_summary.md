# Weekly Report - Season 2022, Week 5

_Generated at 2025-11-11T12:23:46.145890+00:00 (UTC)_

Data root: `data`

## Layer Shapes

| Layer | Artifact | Manifest | Rows | Columns | Status |
|-------|----------|----------|------|---------|--------|
| L1 Ingest | `data\l1\2022\5.parquet` | `data\l1\2022\5_manifest.json` | 2802 | 18 | ready |
| L2 Clean | `data\l2\2022\5.parquet` | `data\l2\2022\5_manifest.json` | 2802 | 24 | ready |
| L3 Team Week | `data\l3_team_week\2022\5.parquet` | `data\l3_team_week\2022\5_manifest.json` | 32 | 34 | ready |

## L2 Audit Snapshot

Last 3 entries from `data\l2_audit\2022\5_audit.jsonl`:

- {"step": "load", "details": "Loaded L1 parquet", "rows": 2802, "cols": 18, "timestamp": "2025-11-11T12:23:45.586934+00:00"}
- {"step": "prepare", "details": "Normalized team aliases, filtered season/week, deduplicated keys", "rows": 2802, "cols": 24, "rows_removed": 0, "timestamp": "2025-11-11T12:23:45.586934+00:00"}
- {"step": "validate", "details": "Validated against L2 contract and guardrails", "rows": 2802, "cols": 24, "timestamp": "2025-11-11T12:23:45.586934+00:00"}

## L3 Sanity

- Rows processed: 32
- Columns available: 34
- Artifact path: `data\l3_team_week\2022\5.parquet`

## Metrics Snapshot

### L4 Core12 Preview

- Artifact: `data\l4_core12\2022\5.parquet`
- Manifest: `data\l4_core12\2022\5_manifest.json`
- Rows: N/A
- Columns: N/A

| TEAM | core_epa_off | core_sr_off | core_sr_def |
| --- | --- | --- | --- |
| NYG | 0.20945761496764853 | 0.5 | 0.49382716049382713 |
| LV | 0.19778582736661163 | 0.43037974683544306 | 0.4888888888888889 |
| BUF | 0.19741698489007023 | 0.4583333333333333 | 0.37362637362637363 |
| LAC | 0.1935794294642454 | 0.4431818181818182 | 0.4878048780487805 |
| NYJ | 0.15685633206978822 | 0.48717948717948717 | 0.4523809523809524 |

### PowerScore Rankings

- Artifact: `data\l4_powerscore\2022\5.parquet`
- Manifest: `data\l4_powerscore\2022\5_manifest.json`
- Rows: 32
- Columns: 4

| team | power_score |
| --- | --- |
| NYG | 0.24082103245941933 |
| CLE | 0.23854432109063967 |
| LAC | 0.2330827803874983 |
| KC | 0.2316695581314055 |
| LV | 0.22558984663469114 |
| GB | 0.22232030346283727 |
| PHI | 0.1974728475545855 |
| MIN | 0.19532697514569874 |
| NYJ | 0.17510516606322438 |
| BUF | 0.16847932012677783 |


## Visualizations

![PowerScore Top 10](2022_w5/assets/powerscore_top10.png)

