# Weekly Report - Season 2024, Week 6

_Generated at 2025-11-10T17:49:27.440358+00:00 (UTC)_

Data root: `data`

## Layer Shapes

| Layer | Artifact | Manifest | Rows | Columns | Status |
|-------|----------|----------|------|---------|--------|
| L1 Ingest | `data\l1\2024\6.parquet` | `data\l1\2024\6_manifest.json` | 2450 | 18 | ready |
| L2 Clean | `data\l2\2024\6.parquet` | `data\l2\2024\6_manifest.json` | 2450 | 24 | ready |
| L3 Team Week | `data\l3_team_week\2024\6.parquet` | `data\l3_team_week\2024\6_manifest.json` | 28 | 34 | ready |

## L2 Audit Snapshot

Last 3 entries from `data\l2_audit\2024\6_audit.jsonl`:

- {"step": "load", "details": "Loaded L1 parquet", "rows": 2450, "cols": 18, "timestamp": "2025-11-10T17:49:26.964046+00:00"}
- {"step": "prepare", "details": "Normalized team aliases, filtered season/week, deduplicated keys", "rows": 2450, "cols": 24, "rows_removed": 0, "timestamp": "2025-11-10T17:49:26.964046+00:00"}
- {"step": "validate", "details": "Validated against L2 contract and guardrails", "rows": 2450, "cols": 24, "timestamp": "2025-11-10T17:49:26.964046+00:00"}

## L3 Sanity

- Rows processed: 28
- Columns available: 34
- Artifact path: `data\l3_team_week\2024\6.parquet`

## Metrics Snapshot

### L4 Core12 Preview

- Artifact: `data\l4_core12\2024\6.parquet`
- Manifest: `data\l4_core12\2024\6_manifest.json`
- Rows: N/A
- Columns: N/A

| TEAM | core_epa_off | core_sr_off | core_sr_def |
| --- | --- | --- | --- |
| DET | 0.2974708306408206 | 0.5 | 0.43529411764705883 |
| CHI | 0.26703515979461373 | 0.5375 | 0.4358974358974359 |
| SF | 0.25443719798721465 | 0.5180722891566265 | 0.4536082474226804 |
| ATL | 0.19900853200310684 | 0.5301204819277109 | 0.45348837209302323 |
| BAL | 0.18287929114220397 | 0.5357142857142857 | 0.5128205128205128 |

### PowerScore Rankings

- Artifact: `data\l4_powerscore\2024\6.parquet`
- Manifest: `data\l4_powerscore\2024\6_manifest.json`
- Rows: 28
- Columns: 4

| team | power_score |
| --- | --- |
| BAL | 0.2623884920736147 |
| CHI | 0.2602972094193459 |
| SF | 0.2460764954775829 |
| WAS | 0.2304568971224102 |
| DET | 0.2160765387001161 |
| ATL | 0.20627370549287724 |
| BUF | 0.20160351728104603 |
| NYJ | 0.19237457121860682 |
| GB | 0.18545277068471924 |
| SEA | 0.18478142938728986 |


## Visualizations

![PowerScore Top 10](2024_w6/assets/powerscore_top10.png)

