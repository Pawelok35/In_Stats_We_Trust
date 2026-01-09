# Weekly Report - Season 2025, Week 2

_Generated at 2026-01-08T19:11:21.301137+00:00 (UTC)_

Data root: `data`

## Layer Shapes

| Layer | Artifact | Manifest | Rows | Columns | Status |
|-------|----------|----------|------|---------|--------|
| L1 Ingest | `data\l1\2025\2.parquet` | `data\l1\2025\2_manifest.json` | 2789 | 18 | ready |
| L2 Clean | `data\l2\2025\2.parquet` | `data\l2\2025\2_manifest.json` | 2789 | 24 | ready |
| L3 Team Week | `data\l3_team_week\2025\2.parquet` | `data\l3_team_week\2025\2_manifest.json` | 32 | 34 | ready |

## L2 Audit Snapshot

Last 3 entries from `data\l2_audit\2025\2_audit.jsonl`:

- {"step": "load", "details": "Loaded L1 parquet", "rows": 2789, "cols": 18, "timestamp": "2026-01-08T19:11:20.859489+00:00"}
- {"step": "prepare", "details": "Normalized team aliases, filtered season/week, deduplicated keys", "rows": 2789, "cols": 24, "rows_removed": 0, "timestamp": "2026-01-08T19:11:20.859489+00:00"}
- {"step": "validate", "details": "Validated against L2 contract and guardrails", "rows": 2789, "cols": 24, "timestamp": "2026-01-08T19:11:20.859489+00:00"}

## L3 Sanity

- Rows processed: 32
- Columns available: 34
- Artifact path: `data\l3_team_week\2025\2.parquet`

## Metrics Snapshot

### L4 Core12 Preview

- Artifact: `data\l4_core12\2025\2.parquet`
- Manifest: `data\l4_core12\2025\2_manifest.json`
- Rows: 32
- Columns: 27

| TEAM | core_epa_off | core_sr_off | core_sr_def |
| --- | --- | --- | --- |
| DET | 0.3040654425775366 | 0.5714285714285714 | 0.40229885057471265 |
| LA | 0.19871598221007972 | 0.5189873417721519 | 0.4659090909090909 |
| NYG | 0.18632809716192159 | 0.48863636363636365 | 0.48717948717948717 |
| NE | 0.18303553731758385 | 0.4430379746835443 | 0.46153846153846156 |
| BUF | 0.17734567434268278 | 0.45555555555555555 | 0.421875 |

### PowerScore Rankings

- Artifact: `data\l4_powerscore\2025\2.parquet`
- Manifest: `data\l4_powerscore\2025\2_manifest.json`
- Rows: 32
- Columns: 4

| team | power_score |
| --- | --- |
| CAR | 2.0997021463302517 |
| TB | 2.0709850736839885 |
| MIA | 1.9107422751357919 |
| DEN | 1.8922079430597654 |
| IND | 1.8176560573236449 |
| BUF | 1.7783384949637395 |
| NE | 1.7693460568487984 |
| DAL | 1.7657901380597394 |
| KC | 1.7527049332998594 |
| TEN | 1.747668250874036 |


## Visualizations

![PowerScore Top 10](2025_w2/assets/powerscore_top10.png)

