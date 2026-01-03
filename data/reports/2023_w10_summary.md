# Weekly Report - Season 2023, Week 10

_Generated at 2026-01-02T10:26:01.940465+00:00 (UTC)_

Data root: `data`

## Layer Shapes

| Layer | Artifact | Manifest | Rows | Columns | Status |
|-------|----------|----------|------|---------|--------|
| L1 Ingest | `data\l1\2023\10.parquet` | `data\l1\2023\10_manifest.json` | 2479 | 18 | ready |
| L2 Clean | `data\l2\2023\10.parquet` | `data\l2\2023\10_manifest.json` | 2479 | 24 | ready |
| L3 Team Week | `data\l3_team_week\2023\10.parquet` | `data\l3_team_week\2023\10_manifest.json` | 28 | 34 | ready |

## L2 Audit Snapshot

Last 3 entries from `data\l2_audit\2023\10_audit.jsonl`:

- {"step": "load", "details": "Loaded L1 parquet", "rows": 2479, "cols": 18, "timestamp": "2026-01-02T10:26:01.515729+00:00"}
- {"step": "prepare", "details": "Normalized team aliases, filtered season/week, deduplicated keys", "rows": 2479, "cols": 24, "rows_removed": 0, "timestamp": "2026-01-02T10:26:01.516732+00:00"}
- {"step": "validate", "details": "Validated against L2 contract and guardrails", "rows": 2479, "cols": 24, "timestamp": "2026-01-02T10:26:01.516732+00:00"}

## L3 Sanity

- Rows processed: 28
- Columns available: 34
- Artifact path: `data\l3_team_week\2023\10.parquet`

## Metrics Snapshot

### L4 Core12 Preview

- Artifact: `data\l4_core12\2023\10.parquet`
- Manifest: `data\l4_core12\2023\10_manifest.json`
- Rows: 28
- Columns: 27

| TEAM | core_epa_off | core_sr_off | core_sr_def |
| --- | --- | --- | --- |
| DET | 0.3248018369351218 | 0.524390243902439 | 0.4777777777777778 |
| DAL | 0.24529108367810246 | 0.5268817204301075 | 0.3333333333333333 |
| SF | 0.23170824700345596 | 0.4666666666666667 | 0.3013698630136986 |
| LAC | 0.21861676566509736 | 0.4777777777777778 | 0.524390243902439 |
| WAS | 0.10685103861615061 | 0.4375 | 0.4519230769230769 |

### PowerScore Rankings

- Artifact: `data\l4_powerscore\2023\10.parquet`
- Manifest: `data\l4_powerscore\2023\10_manifest.json`
- Rows: 28
- Columns: 4

| team | power_score |
| --- | --- |
| LAC | 2.0609206798142528 |
| DET | 1.9285015570359216 |
| CLE | 1.8800438305125393 |
| ATL | 1.82750674415291 |
| SEA | 1.7686069814961118 |
| NE | 1.7614145040631428 |
| DEN | 1.6907088001819743 |
| PIT | 1.6575103480237798 |
| CHI | 1.6537272013236666 |
| GB | 1.6439697181599238 |


## Visualizations

![PowerScore Top 10](2023_w10/assets/powerscore_top10.png)

