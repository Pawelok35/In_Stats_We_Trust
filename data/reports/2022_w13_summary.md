# Weekly Report - Season 2022, Week 13

_Generated at 2026-01-02T11:36:03.905178+00:00 (UTC)_

Data root: `data`

## Layer Shapes

| Layer | Artifact | Manifest | Rows | Columns | Status |
|-------|----------|----------|------|---------|--------|
| L1 Ingest | `data\l1\2022\13.parquet` | `data\l1\2022\13_manifest.json` | 2633 | 18 | ready |
| L2 Clean | `data\l2\2022\13.parquet` | `data\l2\2022\13_manifest.json` | 2633 | 24 | ready |
| L3 Team Week | `data\l3_team_week\2022\13.parquet` | `data\l3_team_week\2022\13_manifest.json` | 30 | 34 | ready |

## L2 Audit Snapshot

Last 3 entries from `data\l2_audit\2022\13_audit.jsonl`:

- {"step": "load", "details": "Loaded L1 parquet", "rows": 2633, "cols": 18, "timestamp": "2026-01-02T11:36:03.482350+00:00"}
- {"step": "prepare", "details": "Normalized team aliases, filtered season/week, deduplicated keys", "rows": 2633, "cols": 24, "rows_removed": 0, "timestamp": "2026-01-02T11:36:03.482350+00:00"}
- {"step": "validate", "details": "Validated against L2 contract and guardrails", "rows": 2633, "cols": 24, "timestamp": "2026-01-02T11:36:03.482350+00:00"}

## L3 Sanity

- Rows processed: 30
- Columns available: 34
- Artifact path: `data\l3_team_week\2022\13.parquet`

## Metrics Snapshot

### L4 Core12 Preview

- Artifact: `data\l4_core12\2022\13.parquet`
- Manifest: `data\l4_core12\2022\13_manifest.json`
- Rows: 30
- Columns: 27

| TEAM | core_epa_off | core_sr_off | core_sr_def |
| --- | --- | --- | --- |
| DET | 0.2436284928884521 | 0.5494505494505495 | 0.3424657534246575 |
| KC | 0.17789364923069725 | 0.5522388059701493 | 0.5232558139534884 |
| DAL | 0.16346647962927818 | 0.45348837209302323 | 0.36666666666666664 |
| CIN | 0.16027272355114652 | 0.5232558139534884 | 0.5522388059701493 |
| PHI | 0.15193768515018746 | 0.4583333333333333 | 0.2916666666666667 |

### PowerScore Rankings

- Artifact: `data\l4_powerscore\2022\13.parquet`
- Manifest: `data\l4_powerscore\2022\13_manifest.json`
- Rows: 30
- Columns: 4

| team | power_score |
| --- | --- |
| CIN | 2.3724881365774126 |
| DET | 2.223286483939147 |
| PIT | 2.0395709390310444 |
| BUF | 1.9155281315102721 |
| KC | 1.9073770234335108 |
| ATL | 1.8943977352374177 |
| PHI | 1.875091479873876 |
| TB | 1.7993450625765368 |
| GB | 1.7960000594941843 |
| LA | 1.7667730141747182 |


## Visualizations

![PowerScore Top 10](2022_w13/assets/powerscore_top10.png)

