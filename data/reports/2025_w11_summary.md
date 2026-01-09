# Weekly Report - Season 2025, Week 11

_Generated at 2026-01-08T19:17:56.779289+00:00 (UTC)_

Data root: `data`

## Layer Shapes

| Layer | Artifact | Manifest | Rows | Columns | Status |
|-------|----------|----------|------|---------|--------|
| L1 Ingest | `data\l1\2025\11.parquet` | `data\l1\2025\11_manifest.json` | 2575 | 18 | ready |
| L2 Clean | `data\l2\2025\11.parquet` | `data\l2\2025\11_manifest.json` | 2575 | 24 | ready |
| L3 Team Week | `data\l3_team_week\2025\11.parquet` | `data\l3_team_week\2025\11_manifest.json` | 30 | 34 | ready |

## L2 Audit Snapshot

Last 3 entries from `data\l2_audit\2025\11_audit.jsonl`:

- {"step": "load", "details": "Loaded L1 parquet", "rows": 2575, "cols": 18, "timestamp": "2026-01-08T19:17:56.373727+00:00"}
- {"step": "prepare", "details": "Normalized team aliases, filtered season/week, deduplicated keys", "rows": 2575, "cols": 24, "rows_removed": 0, "timestamp": "2026-01-08T19:17:56.373727+00:00"}
- {"step": "validate", "details": "Validated against L2 contract and guardrails", "rows": 2575, "cols": 24, "timestamp": "2026-01-08T19:17:56.373727+00:00"}

## L3 Sanity

- Rows processed: 30
- Columns available: 34
- Artifact path: `data\l3_team_week\2025\11.parquet`

## Metrics Snapshot

### L4 Core12 Preview

- Artifact: `data\l4_core12\2025\11.parquet`
- Manifest: `data\l4_core12\2025\11_manifest.json`
- Rows: 30
- Columns: 27

| TEAM | core_epa_off | core_sr_off | core_sr_def |
| --- | --- | --- | --- |
| BUF | 0.3199538236690892 | 0.5416666666666666 | 0.4946236559139785 |
| GB | 0.29348152830018936 | 0.4852941176470588 | 0.47674418604651164 |
| SF | 0.24636443573478106 | 0.5540540540540541 | 0.4639175257731959 |
| PIT | 0.14815714723074142 | 0.49382716049382713 | 0.36904761904761907 |
| TB | 0.14189803484146313 | 0.4946236559139785 | 0.5416666666666666 |

### PowerScore Rankings

- Artifact: `data\l4_powerscore\2025\11.parquet`
- Manifest: `data\l4_powerscore\2025\11_manifest.json`
- Rows: 30
- Columns: 4

| team | power_score |
| --- | --- |
| WAS | 2.179704000653726 |
| PIT | 1.9502885463350244 |
| GB | 1.9483695459566843 |
| NYG | 1.9404554450414087 |
| ARI | 1.9052692659514434 |
| KC | 1.8870441161626625 |
| NE | 1.800075486385416 |
| DAL | 1.7971868743349082 |
| CIN | 1.7581026548994674 |
| JAX | 1.7475933525381948 |


## Visualizations

![PowerScore Top 10](2025_w11/assets/powerscore_top10.png)

