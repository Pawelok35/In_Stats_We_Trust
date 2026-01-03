# Weekly Report - Season 2023, Week 1

_Generated at 2026-01-02T10:06:17.641889+00:00 (UTC)_

Data root: `data`

## Layer Shapes

| Layer | Artifact | Manifest | Rows | Columns | Status |
|-------|----------|----------|------|---------|--------|
| L1 Ingest | `data\l1\2023\1.parquet` | `data\l1\2023\1_manifest.json` | 2816 | 18 | ready |
| L2 Clean | `data\l2\2023\1.parquet` | `data\l2\2023\1_manifest.json` | 2816 | 24 | ready |
| L3 Team Week | `data\l3_team_week\2023\1.parquet` | `data\l3_team_week\2023\1_manifest.json` | 32 | 34 | ready |

## L2 Audit Snapshot

Last 3 entries from `data\l2_audit\2023\1_audit.jsonl`:

- {"step": "load", "details": "Loaded L1 parquet", "rows": 2816, "cols": 18, "timestamp": "2026-01-02T10:06:17.066339+00:00"}
- {"step": "prepare", "details": "Normalized team aliases, filtered season/week, deduplicated keys", "rows": 2816, "cols": 24, "rows_removed": 0, "timestamp": "2026-01-02T10:06:17.066339+00:00"}
- {"step": "validate", "details": "Validated against L2 contract and guardrails", "rows": 2816, "cols": 24, "timestamp": "2026-01-02T10:06:17.066339+00:00"}

## L3 Sanity

- Rows processed: 32
- Columns available: 34
- Artifact path: `data\l3_team_week\2023\1.parquet`

## Metrics Snapshot

### L4 Core12 Preview

- Artifact: `data\l4_core12\2023\1.parquet`
- Manifest: `data\l4_core12\2023\1_manifest.json`
- Rows: 32
- Columns: 27

| TEAM | core_epa_off | core_sr_off | core_sr_def |
| --- | --- | --- | --- |
| MIA | 0.21891781653366274 | 0.47619047619047616 | 0.54 |
| LA | 0.18930464133392183 | 0.5 | 0.5 |
| LAC | 0.1311960656568408 | 0.54 | 0.47619047619047616 |
| LV | 0.12183892158102769 | 0.36619718309859156 | 0.4675324675324675 |
| GB | 0.11037227725963804 | 0.3924050632911392 | 0.4065934065934066 |

### PowerScore Rankings

- Artifact: `data\l4_powerscore\2023\1.parquet`
- Manifest: `data\l4_powerscore\2023\1_manifest.json`
- Rows: 32
- Columns: 4

| team | power_score |
| --- | --- |
| DEN | 2.7297714553145 |
| LA | 2.357217759437347 |
| LAC | 2.2247021862866267 |
| LV | 2.1752522825842995 |
| MIA | 1.7491807952384966 |
| SEA | 1.6532929144651143 |
| BUF | 1.6004556830186085 |
| CHI | 1.5833055454362162 |
| HOU | 1.5525198199385506 |
| KC | 1.5345257331338795 |


## Visualizations

![PowerScore Top 10](2023_w1/assets/powerscore_top10.png)

