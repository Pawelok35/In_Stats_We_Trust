# Weekly Report - Season 2023, Week 14

_Generated at 2025-11-10T20:39:29.101244+00:00 (UTC)_

Data root: `data`

## Layer Shapes

| Layer | Artifact | Manifest | Rows | Columns | Status |
|-------|----------|----------|------|---------|--------|
| L1 Ingest | `data\l1\2023\14.parquet` | `data\l1\2023\14_manifest.json` | 2664 | 18 | ready |
| L2 Clean | `data\l2\2023\14.parquet` | `data\l2\2023\14_manifest.json` | 2664 | 24 | ready |
| L3 Team Week | `data\l3_team_week\2023\14.parquet` | `data\l3_team_week\2023\14_manifest.json` | 30 | 34 | ready |

## L2 Audit Snapshot

Last 3 entries from `data\l2_audit\2023\14_audit.jsonl`:

- {"step": "load", "details": "Loaded L1 parquet", "rows": 2664, "cols": 18, "timestamp": "2025-11-10T20:39:28.571817+00:00"}
- {"step": "prepare", "details": "Normalized team aliases, filtered season/week, deduplicated keys", "rows": 2664, "cols": 24, "rows_removed": 0, "timestamp": "2025-11-10T20:39:28.571817+00:00"}
- {"step": "validate", "details": "Validated against L2 contract and guardrails", "rows": 2664, "cols": 24, "timestamp": "2025-11-10T20:39:28.571817+00:00"}

## L3 Sanity

- Rows processed: 30
- Columns available: 34
- Artifact path: `data\l3_team_week\2023\14.parquet`

## Metrics Snapshot

### L4 Core12 Preview

- Artifact: `data\l4_core12\2023\14.parquet`
- Manifest: `data\l4_core12\2023\14_manifest.json`
- Rows: N/A
- Columns: N/A

| TEAM | core_epa_off | core_sr_off | core_sr_def |
| --- | --- | --- | --- |
| CIN | 0.1573409424038144 | 0.43037974683544306 | 0.3950617283950617 |
| BAL | 0.1297845631311445 | 0.40217391304347827 | 0.4215686274509804 |
| SF | 0.12426451868506977 | 0.4305555555555556 | 0.3918918918918919 |
| DAL | 0.1178323089213033 | 0.4791666666666667 | 0.3888888888888889 |
| LA | 0.06709845386007253 | 0.4215686274509804 | 0.40217391304347827 |

### PowerScore Rankings

- Artifact: `data\l4_powerscore\2023\14.parquet`
- Manifest: `data\l4_powerscore\2023\14_manifest.json`
- Rows: 30
- Columns: 4

| team | power_score |
| --- | --- |
| LA | 0.18228450873215626 |
| BAL | 0.18112689656356723 |
| SF | 0.17965133956967547 |
| MIA | 0.16667100168390037 |
| CIN | 0.15744209584343022 |
| NYG | 0.14946171888005585 |
| DAL | 0.14538661968278271 |
| SEA | 0.1441320441031546 |
| TEN | 0.14395134862785672 |
| GB | 0.1288291084766521 |


## Visualizations

![PowerScore Top 10](2023_w14/assets/powerscore_top10.png)

