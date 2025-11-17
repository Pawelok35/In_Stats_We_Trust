# Weekly Report - Season 2024, Week 12

_Generated at 2025-11-10T17:50:34.484199+00:00 (UTC)_

Data root: `data`

## Layer Shapes

| Layer | Artifact | Manifest | Rows | Columns | Status |
|-------|----------|----------|------|---------|--------|
| L1 Ingest | `data\l1\2024\12.parquet` | `data\l1\2024\12_manifest.json` | 2291 | 18 | ready |
| L2 Clean | `data\l2\2024\12.parquet` | `data\l2\2024\12_manifest.json` | 2291 | 24 | ready |
| L3 Team Week | `data\l3_team_week\2024\12.parquet` | `data\l3_team_week\2024\12_manifest.json` | 26 | 34 | ready |

## L2 Audit Snapshot

Last 3 entries from `data\l2_audit\2024\12_audit.jsonl`:

- {"step": "load", "details": "Loaded L1 parquet", "rows": 2291, "cols": 18, "timestamp": "2025-11-10T17:50:33.997054+00:00"}
- {"step": "prepare", "details": "Normalized team aliases, filtered season/week, deduplicated keys", "rows": 2291, "cols": 24, "rows_removed": 0, "timestamp": "2025-11-10T17:50:33.997054+00:00"}
- {"step": "validate", "details": "Validated against L2 contract and guardrails", "rows": 2291, "cols": 24, "timestamp": "2025-11-10T17:50:33.997054+00:00"}

## L3 Sanity

- Rows processed: 26
- Columns available: 34
- Artifact path: `data\l3_team_week\2024\12.parquet`

## Metrics Snapshot

### L4 Core12 Preview

- Artifact: `data\l4_core12\2024\12.parquet`
- Manifest: `data\l4_core12\2024\12_manifest.json`
- Rows: N/A
- Columns: N/A

| TEAM | core_epa_off | core_sr_off | core_sr_def |
| --- | --- | --- | --- |
| PHI | 0.2749450840212907 | 0.5168539325842697 | 0.5063291139240507 |
| KC | 0.244472243646526 | 0.5955056179775281 | 0.5060240963855421 |
| BAL | 0.22892420626940985 | 0.4810126582278481 | 0.5057471264367817 |
| TB | 0.21140016321288913 | 0.5 | 0.4246575342465753 |
| GB | 0.1462588829833061 | 0.5465116279069767 | 0.38235294117647056 |

### PowerScore Rankings

- Artifact: `data\l4_powerscore\2024\12.parquet`
- Manifest: `data\l4_powerscore\2024\12_manifest.json`
- Rows: 26
- Columns: 4

| team | power_score |
| --- | --- |
| KC | 0.28396122802038726 |
| BAL | 0.24551231020347566 |
| PHI | 0.24499363708193597 |
| CAR | 0.24201093049980846 |
| LAC | 0.22316452936168663 |
| MIN | 0.2058843685275254 |
| LA | 0.19671002257033302 |
| TB | 0.18981313640567343 |
| CHI | 0.18008281795222444 |
| DET | 0.15866526163356345 |


## Visualizations

![PowerScore Top 10](2024_w12/assets/powerscore_top10.png)

