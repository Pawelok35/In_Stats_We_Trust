# Weekly Report - Season 2025, Week 8

_Generated at 2025-11-10T14:28:54.721288+00:00 (UTC)_

Data root: `data`

## Layer Shapes

| Layer | Artifact | Manifest | Rows | Columns | Status |
|-------|----------|----------|------|---------|--------|
| L1 Ingest | `data\l1\2025\8.parquet` | `data\l1\2025\8_manifest.json` | 2142 | 18 | ready |
| L2 Clean | `data\l2\2025\8.parquet` | `data\l2\2025\8_manifest.json` | 2142 | 24 | ready |
| L3 Team Week | `data\l3_team_week\2025\8.parquet` | `data\l3_team_week\2025\8_manifest.json` | 26 | 34 | ready |

## L2 Audit Snapshot

Last 3 entries from `data\l2_audit\2025\8_audit.jsonl`:

- {"step": "load", "details": "Loaded L1 parquet", "rows": 2142, "cols": 18, "timestamp": "2025-11-10T14:28:54.303086+00:00"}
- {"step": "prepare", "details": "Normalized team aliases, filtered season/week, deduplicated keys", "rows": 2142, "cols": 24, "rows_removed": 0, "timestamp": "2025-11-10T14:28:54.303086+00:00"}
- {"step": "validate", "details": "Validated against L2 contract and guardrails", "rows": 2142, "cols": 24, "timestamp": "2025-11-10T14:28:54.303086+00:00"}

## L3 Sanity

- Rows processed: 26
- Columns available: 34
- Artifact path: `data\l3_team_week\2025\8.parquet`

## Metrics Snapshot

### L4 Core12 Preview

- Artifact: `data\l4_core12\2025\8.parquet`
- Manifest: `data\l4_core12\2025\8_manifest.json`
- Rows: 26
- Columns: 15

| TEAM | core_epa_off | core_sr_off | core_sr_def |
| --- | --- | --- | --- |
| DEN | 0.33052069837628284 | 0.5949367088607594 | 0.5531914893617021 |
| PHI | 0.3072478346868501 | 0.5822784810126582 | 0.4857142857142857 |
| IND | 0.2969749304118441 | 0.47761194029850745 | 0.4318181818181818 |
| BUF | 0.2825220279348425 | 0.5189873417721519 | 0.47435897435897434 |
| CIN | 0.24932262560009563 | 0.6578947368421053 | 0.5604395604395604 |

### PowerScore Rankings

- Artifact: `data\l4_powerscore\2025\8.parquet`
- Manifest: `data\l4_powerscore\2025\8_manifest.json`
- Rows: 26
- Columns: 4

| team | power_score |
| --- | --- |
| CIN | 0.3371989619679479 |
| NYJ | 0.3058290896840429 |
| PHI | 0.302786293905961 |
| DEN | 0.30242497454899786 |
| BAL | 0.25001858405787913 |
| IND | 0.24733406649455442 |
| DAL | 0.23937913957282694 |
| NYG | 0.23379631869347134 |
| HOU | 0.21438542826718573 |
| BUF | 0.2118661445479372 |


## Visualizations

![PowerScore Top 10](2025_w8/assets/powerscore_top10.png)

