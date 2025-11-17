# Weekly Report - Season 2024, Week 15

_Generated at 2025-11-10T17:51:08.127401+00:00 (UTC)_

Data root: `data`

## Layer Shapes

| Layer | Artifact | Manifest | Rows | Columns | Status |
|-------|----------|----------|------|---------|--------|
| L1 Ingest | `data\l1\2024\15.parquet` | `data\l1\2024\15_manifest.json` | 2780 | 18 | ready |
| L2 Clean | `data\l2\2024\15.parquet` | `data\l2\2024\15_manifest.json` | 2780 | 24 | ready |
| L3 Team Week | `data\l3_team_week\2024\15.parquet` | `data\l3_team_week\2024\15_manifest.json` | 32 | 34 | ready |

## L2 Audit Snapshot

Last 3 entries from `data\l2_audit\2024\15_audit.jsonl`:

- {"step": "load", "details": "Loaded L1 parquet", "rows": 2780, "cols": 18, "timestamp": "2025-11-10T17:51:07.601887+00:00"}
- {"step": "prepare", "details": "Normalized team aliases, filtered season/week, deduplicated keys", "rows": 2780, "cols": 24, "rows_removed": 0, "timestamp": "2025-11-10T17:51:07.601887+00:00"}
- {"step": "validate", "details": "Validated against L2 contract and guardrails", "rows": 2780, "cols": 24, "timestamp": "2025-11-10T17:51:07.601887+00:00"}

## L3 Sanity

- Rows processed: 32
- Columns available: 34
- Artifact path: `data\l3_team_week\2024\15.parquet`

## Metrics Snapshot

### L4 Core12 Preview

- Artifact: `data\l4_core12\2024\15.parquet`
- Manifest: `data\l4_core12\2024\15_manifest.json`
- Rows: N/A
- Columns: N/A

| TEAM | core_epa_off | core_sr_off | core_sr_def |
| --- | --- | --- | --- |
| BUF | 0.3606015303591778 | 0.5934065934065934 | 0.5454545454545454 |
| BAL | 0.3064228371104659 | 0.5753424657534246 | 0.40476190476190477 |
| NYJ | 0.2914564291668403 | 0.45454545454545453 | 0.5773195876288659 |
| TB | 0.19357375647916003 | 0.5697674418604651 | 0.45714285714285713 |
| DET | 0.18292920374208027 | 0.5454545454545454 | 0.5934065934065934 |

### PowerScore Rankings

- Artifact: `data\l4_powerscore\2024\15.parquet`
- Manifest: `data\l4_powerscore\2024\15_manifest.json`
- Rows: 32
- Columns: 4

| team | power_score |
| --- | --- |
| BUF | 0.34411505769280953 |
| DET | 0.29675158798762424 |
| BAL | 0.27907933580654354 |
| NYJ | 0.274159669116514 |
| JAX | 0.2669692952815282 |
| NE | 0.22163212000866567 |
| DAL | 0.20965721391302233 |
| ARI | 0.19668192262701592 |
| TB | 0.19154272729834151 |
| CIN | 0.1697726947812782 |


## Visualizations

![PowerScore Top 10](2024_w15/assets/powerscore_top10.png)

