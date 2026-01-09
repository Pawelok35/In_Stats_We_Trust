# Weekly Report - Season 2025, Week 9

_Generated at 2026-01-08T19:16:13.789793+00:00 (UTC)_

Data root: `data`

## Layer Shapes

| Layer | Artifact | Manifest | Rows | Columns | Status |
|-------|----------|----------|------|---------|--------|
| L1 Ingest | `data\l1\2025\9.parquet` | `data\l1\2025\9_manifest.json` | 2385 | 18 | ready |
| L2 Clean | `data\l2\2025\9.parquet` | `data\l2\2025\9_manifest.json` | 2385 | 24 | ready |
| L3 Team Week | `data\l3_team_week\2025\9.parquet` | `data\l3_team_week\2025\9_manifest.json` | 28 | 34 | ready |

## L2 Audit Snapshot

Last 3 entries from `data\l2_audit\2025\9_audit.jsonl`:

- {"step": "load", "details": "Loaded L1 parquet", "rows": 2385, "cols": 18, "timestamp": "2026-01-08T19:16:13.406776+00:00"}
- {"step": "prepare", "details": "Normalized team aliases, filtered season/week, deduplicated keys", "rows": 2385, "cols": 24, "rows_removed": 0, "timestamp": "2026-01-08T19:16:13.407775+00:00"}
- {"step": "validate", "details": "Validated against L2 contract and guardrails", "rows": 2385, "cols": 24, "timestamp": "2026-01-08T19:16:13.407775+00:00"}

## L3 Sanity

- Rows processed: 28
- Columns available: 34
- Artifact path: `data\l3_team_week\2025\9.parquet`

## Metrics Snapshot

### L4 Core12 Preview

- Artifact: `data\l4_core12\2025\9.parquet`
- Manifest: `data\l4_core12\2025\9_manifest.json`
- Rows: 28
- Columns: 27

| TEAM | core_epa_off | core_sr_off | core_sr_def |
| --- | --- | --- | --- |
| SEA | 0.3334855174359221 | 0.6 | 0.4878048780487805 |
| CHI | 0.30640623176141696 | 0.5588235294117647 | 0.5568181818181818 |
| SF | 0.27939457879457846 | 0.5301204819277109 | 0.5454545454545454 |
| CIN | 0.24712779783559116 | 0.5568181818181818 | 0.5588235294117647 |
| LA | 0.17170099496919042 | 0.53125 | 0.4074074074074074 |

### PowerScore Rankings

- Artifact: `data\l4_powerscore\2025\9.parquet`
- Manifest: `data\l4_powerscore\2025\9_manifest.json`
- Rows: 28
- Columns: 4

| team | power_score |
| --- | --- |
| JAX | 2.3797350460228968 |
| CAR | 2.174953644574574 |
| LA | 2.070728209112249 |
| GB | 2.0381193359495673 |
| CHI | 1.9963736230365554 |
| LV | 1.8081735979112539 |
| IND | 1.797901141070315 |
| WAS | 1.7945156145924404 |
| BUF | 1.7913990177067773 |
| NYG | 1.7704203966426177 |


## Visualizations

![PowerScore Top 10](2025_w9/assets/powerscore_top10.png)

