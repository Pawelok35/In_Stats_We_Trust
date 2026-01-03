# Weekly Report - Season 2022, Week 7

_Generated at 2026-01-02T11:31:11.743150+00:00 (UTC)_

Data root: `data`

## Layer Shapes

| Layer | Artifact | Manifest | Rows | Columns | Status |
|-------|----------|----------|------|---------|--------|
| L1 Ingest | `data\l1\2022\7.parquet` | `data\l1\2022\7_manifest.json` | 2390 | 18 | ready |
| L2 Clean | `data\l2\2022\7.parquet` | `data\l2\2022\7_manifest.json` | 2390 | 24 | ready |
| L3 Team Week | `data\l3_team_week\2022\7.parquet` | `data\l3_team_week\2022\7_manifest.json` | 28 | 34 | ready |

## L2 Audit Snapshot

Last 3 entries from `data\l2_audit\2022\7_audit.jsonl`:

- {"step": "load", "details": "Loaded L1 parquet", "rows": 2390, "cols": 18, "timestamp": "2026-01-02T11:31:11.316486+00:00"}
- {"step": "prepare", "details": "Normalized team aliases, filtered season/week, deduplicated keys", "rows": 2390, "cols": 24, "rows_removed": 0, "timestamp": "2026-01-02T11:31:11.316486+00:00"}
- {"step": "validate", "details": "Validated against L2 contract and guardrails", "rows": 2390, "cols": 24, "timestamp": "2026-01-02T11:31:11.316486+00:00"}

## L3 Sanity

- Rows processed: 28
- Columns available: 34
- Artifact path: `data\l3_team_week\2022\7.parquet`

## Metrics Snapshot

### L4 Core12 Preview

- Artifact: `data\l4_core12\2022\7.parquet`
- Manifest: `data\l4_core12\2022\7_manifest.json`
- Rows: 28
- Columns: 27

| TEAM | core_epa_off | core_sr_off | core_sr_def |
| --- | --- | --- | --- |
| KC | 0.37206446240306834 | 0.55 | 0.44329896907216493 |
| CIN | 0.23769714580183582 | 0.5357142857142857 | 0.3870967741935484 |
| LV | 0.23703312496277126 | 0.5405405405405406 | 0.4375 |
| NYG | 0.15709496142991472 | 0.5168539325842697 | 0.42045454545454547 |
| SEA | 0.11816163225209012 | 0.4823529411764706 | 0.37362637362637363 |

### PowerScore Rankings

- Artifact: `data\l4_powerscore\2022\7.parquet`
- Manifest: `data\l4_powerscore\2022\7_manifest.json`
- Rows: 28
- Columns: 4

| team | power_score |
| --- | --- |
| NYG | 2.4222686655996357 |
| JAX | 2.114964089623097 |
| CIN | 2.082534025181189 |
| SF | 1.966737209267127 |
| HOU | 1.9330122494290976 |
| KC | 1.8779301109165645 |
| LV | 1.8616570856929868 |
| WAS | 1.7358986672848016 |
| ARI | 1.7126472369430712 |
| NO | 1.6858731577325115 |


## Visualizations

![PowerScore Top 10](2022_w7/assets/powerscore_top10.png)

