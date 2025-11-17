# Weekly Report - Season 2024, Week 9

_Generated at 2025-11-10T17:49:59.830551+00:00 (UTC)_

Data root: `data`

## Layer Shapes

| Layer | Artifact | Manifest | Rows | Columns | Status |
|-------|----------|----------|------|---------|--------|
| L1 Ingest | `data\l1\2024\9.parquet` | `data\l1\2024\9_manifest.json` | 2651 | 18 | ready |
| L2 Clean | `data\l2\2024\9.parquet` | `data\l2\2024\9_manifest.json` | 2651 | 24 | ready |
| L3 Team Week | `data\l3_team_week\2024\9.parquet` | `data\l3_team_week\2024\9_manifest.json` | 30 | 34 | ready |

## L2 Audit Snapshot

Last 3 entries from `data\l2_audit\2024\9_audit.jsonl`:

- {"step": "load", "details": "Loaded L1 parquet", "rows": 2651, "cols": 18, "timestamp": "2025-11-10T17:49:59.232696+00:00"}
- {"step": "prepare", "details": "Normalized team aliases, filtered season/week, deduplicated keys", "rows": 2651, "cols": 24, "rows_removed": 0, "timestamp": "2025-11-10T17:49:59.232696+00:00"}
- {"step": "validate", "details": "Validated against L2 contract and guardrails", "rows": 2651, "cols": 24, "timestamp": "2025-11-10T17:49:59.232696+00:00"}

## L3 Sanity

- Rows processed: 30
- Columns available: 34
- Artifact path: `data\l3_team_week\2024\9.parquet`

## Metrics Snapshot

### L4 Core12 Preview

- Artifact: `data\l4_core12\2024\9.parquet`
- Manifest: `data\l4_core12\2024\9_manifest.json`
- Rows: N/A
- Columns: N/A

| TEAM | core_epa_off | core_sr_off | core_sr_def |
| --- | --- | --- | --- |
| BAL | 0.3334259262742245 | 0.589041095890411 | 0.36046511627906974 |
| WAS | 0.21738633287449677 | 0.5866666666666667 | 0.48717948717948717 |
| BUF | 0.21488951051142066 | 0.5875 | 0.569620253164557 |
| MIA | 0.2097066447398142 | 0.569620253164557 | 0.5875 |
| KC | 0.13981103706219705 | 0.5346534653465347 | 0.4444444444444444 |

### PowerScore Rankings

- Artifact: `data\l4_powerscore\2024\9.parquet`
- Manifest: `data\l4_powerscore\2024\9_manifest.json`
- Rows: 30
- Columns: 4

| team | power_score |
| --- | --- |
| MIA | 0.2866283923181811 |
| BUF | 0.27902765762696013 |
| BAL | 0.27313686718813557 |
| WAS | 0.271826362285572 |
| NYG | 0.23992170758645695 |
| KC | 0.22709739410228272 |
| TB | 0.20242715476762616 |
| NYJ | 0.17584478155124247 |
| CIN | 0.1743072574788823 |
| DET | 0.1657702635912135 |


## Visualizations

![PowerScore Top 10](2024_w9/assets/powerscore_top10.png)

