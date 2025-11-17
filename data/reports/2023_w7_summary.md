# Weekly Report - Season 2023, Week 7

_Generated at 2025-11-10T20:38:11.289916+00:00 (UTC)_

Data root: `data`

## Layer Shapes

| Layer | Artifact | Manifest | Rows | Columns | Status |
|-------|----------|----------|------|---------|--------|
| L1 Ingest | `data\l1\2023\7.parquet` | `data\l1\2023\7_manifest.json` | 2252 | 18 | ready |
| L2 Clean | `data\l2\2023\7.parquet` | `data\l2\2023\7_manifest.json` | 2252 | 24 | ready |
| L3 Team Week | `data\l3_team_week\2023\7.parquet` | `data\l3_team_week\2023\7_manifest.json` | 26 | 34 | ready |

## L2 Audit Snapshot

Last 3 entries from `data\l2_audit\2023\7_audit.jsonl`:

- {"step": "load", "details": "Loaded L1 parquet", "rows": 2252, "cols": 18, "timestamp": "2025-11-10T20:38:10.855767+00:00"}
- {"step": "prepare", "details": "Normalized team aliases, filtered season/week, deduplicated keys", "rows": 2252, "cols": 24, "rows_removed": 0, "timestamp": "2025-11-10T20:38:10.855767+00:00"}
- {"step": "validate", "details": "Validated against L2 contract and guardrails", "rows": 2252, "cols": 24, "timestamp": "2025-11-10T20:38:10.855767+00:00"}

## L3 Sanity

- Rows processed: 26
- Columns available: 34
- Artifact path: `data\l3_team_week\2023\7.parquet`

## Metrics Snapshot

### L4 Core12 Preview

- Artifact: `data\l4_core12\2023\7.parquet`
- Manifest: `data\l4_core12\2023\7_manifest.json`
- Rows: N/A
- Columns: N/A

| TEAM | core_epa_off | core_sr_off | core_sr_def |
| --- | --- | --- | --- |
| BAL | 0.3589953155007581 | 0.5211267605633803 | 0.38636363636363635 |
| KC | 0.20110538348286267 | 0.46987951807228917 | 0.3625 |
| CHI | 0.08810231488579037 | 0.45454545454545453 | 0.3717948717948718 |
| DEN | 0.08807561664204848 | 0.40789473684210525 | 0.43209876543209874 |
| NE | 0.07688988115344393 | 0.4868421052631579 | 0.4772727272727273 |

### PowerScore Rankings

- Artifact: `data\l4_powerscore\2023\7.parquet`
- Manifest: `data\l4_powerscore\2023\7_manifest.json`
- Rows: 26
- Columns: 4

| team | power_score |
| --- | --- |
| BAL | 0.2673077183155666 |
| KC | 0.22003754866741462 |
| NE | 0.18597189352399798 |
| DEN | 0.17877776966405434 |
| GB | 0.17305971336433915 |
| BUF | 0.17224749367206213 |
| LAC | 0.16749377562587306 |
| SF | 0.16019933490941327 |
| MIN | 0.14853084944763506 |
| DET | 0.14012547461944647 |


## Visualizations

![PowerScore Top 10](2023_w7/assets/powerscore_top10.png)

