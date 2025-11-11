# Weekly Report - Season 2025, Week 6

_Generated at 2025-11-10T14:23:31.677554+00:00 (UTC)_

Data root: `data`

## Layer Shapes

| Layer | Artifact | Manifest | Rows | Columns | Status |
|-------|----------|----------|------|---------|--------|
| L1 Ingest | `data\l1\2025\6.parquet` | `data\l1\2025\6_manifest.json` | 2523 | 18 | ready |
| L2 Clean | `data\l2\2025\6.parquet` | `data\l2\2025\6_manifest.json` | 2523 | 24 | ready |
| L3 Team Week | `data\l3_team_week\2025\6.parquet` | `data\l3_team_week\2025\6_manifest.json` | 30 | 34 | ready |

## L2 Audit Snapshot

Last 3 entries from `data\l2_audit\2025\6_audit.jsonl`:

- {"step": "load", "details": "Loaded L1 parquet", "rows": 2523, "cols": 18, "timestamp": "2025-11-10T14:23:31.213093+00:00"}
- {"step": "prepare", "details": "Normalized team aliases, filtered season/week, deduplicated keys", "rows": 2523, "cols": 24, "rows_removed": 0, "timestamp": "2025-11-10T14:23:31.213093+00:00"}
- {"step": "validate", "details": "Validated against L2 contract and guardrails", "rows": 2523, "cols": 24, "timestamp": "2025-11-10T14:23:31.213093+00:00"}

## L3 Sanity

- Rows processed: 30
- Columns available: 34
- Artifact path: `data\l3_team_week\2025\6.parquet`

## Metrics Snapshot

### L4 Core12 Preview

- Artifact: `data\l4_core12\2025\6.parquet`
- Manifest: `data\l4_core12\2025\6_manifest.json`
- Rows: 30
- Columns: 15

| TEAM | core_epa_off | core_sr_off | core_sr_def |
| --- | --- | --- | --- |
| KC | 0.22661310429374376 | 0.56 | 0.5652173913043478 |
| GB | 0.21622707940638064 | 0.5866666666666667 | 0.5308641975308642 |
| DAL | 0.17656728941054173 | 0.4520547945205479 | 0.5647058823529412 |
| NYG | 0.17047508703758832 | 0.47126436781609193 | 0.5070422535211268 |
| IND | 0.16437398524660812 | 0.5657894736842105 | 0.5111111111111111 |

### PowerScore Rankings

- Artifact: `data\l4_powerscore\2025\6.parquet`
- Manifest: `data\l4_powerscore\2025\6_manifest.json`
- Rows: 30
- Columns: 4

| team | power_score |
| --- | --- |
| GB | 0.27363994552917137 |
| KC | 0.26203587265938955 |
| CAR | 0.2581734651179161 |
| IND | 0.2461414684553505 |
| DET | 0.23034574119797974 |
| ARI | 0.22618525994696503 |
| TB | 0.22393929229209153 |
| CIN | 0.22207129614931292 |
| DAL | 0.2163130069076587 |
| LAC | 0.203538439472317 |


## Visualizations

![PowerScore Top 10](2025_w6/assets/powerscore_top10.png)

