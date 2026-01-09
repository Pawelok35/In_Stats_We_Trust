# Weekly Report - Season 2025, Week 4

_Generated at 2026-01-08T19:12:35.784975+00:00 (UTC)_

Data root: `data`

## Layer Shapes

| Layer | Artifact | Manifest | Rows | Columns | Status |
|-------|----------|----------|------|---------|--------|
| L1 Ingest | `data\l1\2025\4.parquet` | `data\l1\2025\4_manifest.json` | 2761 | 18 | ready |
| L2 Clean | `data\l2\2025\4.parquet` | `data\l2\2025\4_manifest.json` | 2761 | 24 | ready |
| L3 Team Week | `data\l3_team_week\2025\4.parquet` | `data\l3_team_week\2025\4_manifest.json` | 32 | 34 | ready |

## L2 Audit Snapshot

Last 3 entries from `data\l2_audit\2025\4_audit.jsonl`:

- {"step": "load", "details": "Loaded L1 parquet", "rows": 2761, "cols": 18, "timestamp": "2026-01-08T19:12:35.399312+00:00"}
- {"step": "prepare", "details": "Normalized team aliases, filtered season/week, deduplicated keys", "rows": 2761, "cols": 24, "rows_removed": 0, "timestamp": "2026-01-08T19:12:35.399312+00:00"}
- {"step": "validate", "details": "Validated against L2 contract and guardrails", "rows": 2761, "cols": 24, "timestamp": "2026-01-08T19:12:35.399312+00:00"}

## L3 Sanity

- Rows processed: 32
- Columns available: 34
- Artifact path: `data\l3_team_week\2025\4.parquet`

## Metrics Snapshot

### L4 Core12 Preview

- Artifact: `data\l4_core12\2025\4.parquet`
- Manifest: `data\l4_core12\2025\4_manifest.json`
- Rows: 32
- Columns: 27

| TEAM | core_epa_off | core_sr_off | core_sr_def |
| --- | --- | --- | --- |
| NE | 0.24640026739375157 | 0.42424242424242425 | 0.47126436781609193 |
| GB | 0.24406399031480153 | 0.5238095238095238 | 0.5222222222222223 |
| DAL | 0.22845727754498107 | 0.5222222222222223 | 0.5238095238095238 |
| ATL | 0.20668628886120305 | 0.5357142857142857 | 0.5405405405405406 |
| KC | 0.1823907378129661 | 0.4659090909090909 | 0.49295774647887325 |

### PowerScore Rankings

- Artifact: `data\l4_powerscore\2025\4.parquet`
- Manifest: `data\l4_powerscore\2025\4_manifest.json`
- Rows: 32
- Columns: 4

| team | power_score |
| --- | --- |
| GB | 2.1711571421624667 |
| DEN | 2.033412024239973 |
| MIN | 1.9853581080420932 |
| KC | 1.9317426115848786 |
| ATL | 1.9198873340759333 |
| DAL | 1.8956920371228958 |
| WAS | 1.8797493200572162 |
| HOU | 1.870628253518176 |
| NYJ | 1.822959134903277 |
| MIA | 1.8184038176678679 |


## Visualizations

![PowerScore Top 10](2025_w4/assets/powerscore_top10.png)

