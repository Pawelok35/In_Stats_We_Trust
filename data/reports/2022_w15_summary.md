# Weekly Report - Season 2022, Week 15

_Generated at 2025-11-11T12:25:30.469473+00:00 (UTC)_

Data root: `data`

## Layer Shapes

| Layer | Artifact | Manifest | Rows | Columns | Status |
|-------|----------|----------|------|---------|--------|
| L1 Ingest | `data\l1\2022\15.parquet` | `data\l1\2022\15_manifest.json` | 2853 | 18 | ready |
| L2 Clean | `data\l2\2022\15.parquet` | `data\l2\2022\15_manifest.json` | 2853 | 24 | ready |
| L3 Team Week | `data\l3_team_week\2022\15.parquet` | `data\l3_team_week\2022\15_manifest.json` | 32 | 34 | ready |

## L2 Audit Snapshot

Last 3 entries from `data\l2_audit\2022\15_audit.jsonl`:

- {"step": "load", "details": "Loaded L1 parquet", "rows": 2853, "cols": 18, "timestamp": "2025-11-11T12:25:29.989297+00:00"}
- {"step": "prepare", "details": "Normalized team aliases, filtered season/week, deduplicated keys", "rows": 2853, "cols": 24, "rows_removed": 0, "timestamp": "2025-11-11T12:25:29.989297+00:00"}
- {"step": "validate", "details": "Validated against L2 contract and guardrails", "rows": 2853, "cols": 24, "timestamp": "2025-11-11T12:25:29.989297+00:00"}

## L3 Sanity

- Rows processed: 32
- Columns available: 34
- Artifact path: `data\l3_team_week\2022\15.parquet`

## Metrics Snapshot

### L4 Core12 Preview

- Artifact: `data\l4_core12\2022\15.parquet`
- Manifest: `data\l4_core12\2022\15_manifest.json`
- Rows: N/A
- Columns: N/A

| TEAM | core_epa_off | core_sr_off | core_sr_def |
| --- | --- | --- | --- |
| MIA | 0.20231600057382088 | 0.4805194805194805 | 0.5154639175257731 |
| PIT | 0.17083898543690643 | 0.5 | 0.3548387096774194 |
| BUF | 0.13708390938790188 | 0.5154639175257731 | 0.4805194805194805 |
| JAX | 0.10259568769898679 | 0.5222222222222223 | 0.5531914893617021 |
| DAL | 0.06814040009804229 | 0.5531914893617021 | 0.5222222222222223 |

### PowerScore Rankings

- Artifact: `data\l4_powerscore\2022\15.parquet`
- Manifest: `data\l4_powerscore\2022\15_manifest.json`
- Rows: 32
- Columns: 4

| team | power_score |
| --- | --- |
| MIA | 0.2469286807797164 |
| BUF | 0.23792710448300405 |
| PIT | 0.2094461207889298 |
| JAX | 0.2089810151586983 |
| DAL | 0.20394274565921855 |
| KC | 0.1768181235186996 |
| NO | 0.16440656049776628 |
| CAR | 0.1603741460169355 |
| GB | 0.1569599394635411 |
| NYG | 0.1318556812640922 |


## Visualizations

![PowerScore Top 10](2022_w15/assets/powerscore_top10.png)

