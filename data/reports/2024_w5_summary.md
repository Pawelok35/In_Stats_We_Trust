# Weekly Report - Season 2024, Week 5

_Generated at 2025-12-28T14:27:51.539842+00:00 (UTC)_

Data root: `data`

## Layer Shapes

| Layer | Artifact | Manifest | Rows | Columns | Status |
|-------|----------|----------|------|---------|--------|
| L1 Ingest | `data\l1\2024\5.parquet` | `data\l1\2024\5_manifest.json` | 2522 | 18 | ready |
| L2 Clean | `data\l2\2024\5.parquet` | `data\l2\2024\5_manifest.json` | 2522 | 24 | ready |
| L3 Team Week | `data\l3_team_week\2024\5.parquet` | `data\l3_team_week\2024\5_manifest.json` | 28 | 34 | ready |

## L2 Audit Snapshot

Last 3 entries from `data\l2_audit\2024\5_audit.jsonl`:

- {"step": "load", "details": "Loaded L1 parquet", "rows": 2522, "cols": 18, "timestamp": "2025-12-28T14:27:51.092998+00:00"}
- {"step": "prepare", "details": "Normalized team aliases, filtered season/week, deduplicated keys", "rows": 2522, "cols": 24, "rows_removed": 0, "timestamp": "2025-12-28T14:27:51.092998+00:00"}
- {"step": "validate", "details": "Validated against L2 contract and guardrails", "rows": 2522, "cols": 24, "timestamp": "2025-12-28T14:27:51.092998+00:00"}

## L3 Sanity

- Rows processed: 28
- Columns available: 34
- Artifact path: `data\l3_team_week\2024\5.parquet`

## Metrics Snapshot

### L4 Core12 Preview

- Artifact: `data\l4_core12\2024\5.parquet`
- Manifest: `data\l4_core12\2024\5_manifest.json`
- Rows: 28
- Columns: 27

| TEAM | core_epa_off | core_sr_off | core_sr_def |
| --- | --- | --- | --- |
| BAL | 0.25153988001770095 | 0.5894736842105263 | 0.4891304347826087 |
| JAX | 0.23499713759673269 | 0.5263157894736842 | 0.4946236559139785 |
| TB | 0.20195647701621056 | 0.5522388059701493 | 0.5 |
| CIN | 0.1892393207906381 | 0.4891304347826087 | 0.5894736842105263 |
| IND | 0.17155197020419824 | 0.4946236559139785 | 0.5263157894736842 |

### PowerScore Rankings

- Artifact: `data\l4_powerscore\2024\5.parquet`
- Manifest: `data\l4_powerscore\2024\5_manifest.json`
- Rows: 28
- Columns: 4

| team | power_score |
| --- | --- |
| DAL | 2.230431707729905 |
| KC | 2.115689536564556 |
| ATL | 2.0474647712493033 |
| LA | 1.9299555430515933 |
| BAL | 1.734793704755416 |
| MIA | 1.70744889132177 |
| IND | 1.6614677618385416 |
| CIN | 1.6542089623605312 |
| SF | 1.6477680290301948 |
| ARI | 1.620536507741133 |


## Visualizations

![PowerScore Top 10](2024_w5/assets/powerscore_top10.png)

