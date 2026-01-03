# Weekly Report - Season 2023, Week 4

_Generated at 2026-01-02T10:18:31.576047+00:00 (UTC)_

Data root: `data`

## Layer Shapes

| Layer | Artifact | Manifest | Rows | Columns | Status |
|-------|----------|----------|------|---------|--------|
| L1 Ingest | `data\l1\2023\4.parquet` | `data\l1\2023\4_manifest.json` | 2730 | 18 | ready |
| L2 Clean | `data\l2\2023\4.parquet` | `data\l2\2023\4_manifest.json` | 2730 | 24 | ready |
| L3 Team Week | `data\l3_team_week\2023\4.parquet` | `data\l3_team_week\2023\4_manifest.json` | 32 | 34 | ready |

## L2 Audit Snapshot

Last 3 entries from `data\l2_audit\2023\4_audit.jsonl`:

- {"step": "load", "details": "Loaded L1 parquet", "rows": 2730, "cols": 18, "timestamp": "2026-01-02T10:18:31.162886+00:00"}
- {"step": "prepare", "details": "Normalized team aliases, filtered season/week, deduplicated keys", "rows": 2730, "cols": 24, "rows_removed": 0, "timestamp": "2026-01-02T10:18:31.162886+00:00"}
- {"step": "validate", "details": "Validated against L2 contract and guardrails", "rows": 2730, "cols": 24, "timestamp": "2026-01-02T10:18:31.162886+00:00"}

## L3 Sanity

- Rows processed: 32
- Columns available: 34
- Artifact path: `data\l3_team_week\2023\4.parquet`

## Metrics Snapshot

### L4 Core12 Preview

- Artifact: `data\l4_core12\2023\4.parquet`
- Manifest: `data\l4_core12\2023\4_manifest.json`
- Rows: 32
- Columns: 27

| TEAM | core_epa_off | core_sr_off | core_sr_def |
| --- | --- | --- | --- |
| SF | 0.40122498620463454 | 0.5942028985507246 | 0.4418604651162791 |
| BUF | 0.3663669531862881 | 0.5405405405405406 | 0.4268292682926829 |
| PHI | 0.18713169984435768 | 0.47191011235955055 | 0.3979591836734694 |
| DEN | 0.17004734858432236 | 0.4411764705882353 | 0.4444444444444444 |
| TEN | 0.16445115114314646 | 0.4936708860759494 | 0.4696969696969697 |

### PowerScore Rankings

- Artifact: `data\l4_powerscore\2023\4.parquet`
- Manifest: `data\l4_powerscore\2023\4_manifest.json`
- Rows: 32
- Columns: 4

| team | power_score |
| --- | --- |
| ARI | 2.6751542741680585 |
| WAS | 2.1480229296798914 |
| SF | 2.02958021466942 |
| CHI | 1.96621123356419 |
| TEN | 1.9002867505807188 |
| HOU | 1.8398382114100786 |
| PHI | 1.830859323384461 |
| LA | 1.8040658415301867 |
| CAR | 1.794395184795517 |
| DET | 1.6861894626902472 |


## Visualizations

![PowerScore Top 10](2023_w4/assets/powerscore_top10.png)

