# Weekly Report - Season 2022, Week 9

_Generated at 2026-01-02T11:32:39.730839+00:00 (UTC)_

Data root: `data`

## Layer Shapes

| Layer | Artifact | Manifest | Rows | Columns | Status |
|-------|----------|----------|------|---------|--------|
| L1 Ingest | `data\l1\2022\9.parquet` | `data\l1\2022\9_manifest.json` | 2238 | 18 | ready |
| L2 Clean | `data\l2\2022\9.parquet` | `data\l2\2022\9_manifest.json` | 2238 | 24 | ready |
| L3 Team Week | `data\l3_team_week\2022\9.parquet` | `data\l3_team_week\2022\9_manifest.json` | 26 | 34 | ready |

## L2 Audit Snapshot

Last 3 entries from `data\l2_audit\2022\9_audit.jsonl`:

- {"step": "load", "details": "Loaded L1 parquet", "rows": 2238, "cols": 18, "timestamp": "2026-01-02T11:32:39.297713+00:00"}
- {"step": "prepare", "details": "Normalized team aliases, filtered season/week, deduplicated keys", "rows": 2238, "cols": 24, "rows_removed": 0, "timestamp": "2026-01-02T11:32:39.297713+00:00"}
- {"step": "validate", "details": "Validated against L2 contract and guardrails", "rows": 2238, "cols": 24, "timestamp": "2026-01-02T11:32:39.297713+00:00"}

## L3 Sanity

- Rows processed: 26
- Columns available: 34
- Artifact path: `data\l3_team_week\2022\9.parquet`

## Metrics Snapshot

### L4 Core12 Preview

- Artifact: `data\l4_core12\2022\9.parquet`
- Manifest: `data\l4_core12\2022\9_manifest.json`
- Rows: 26
- Columns: 27

| TEAM | core_epa_off | core_sr_off | core_sr_def |
| --- | --- | --- | --- |
| CIN | 0.2235205003901595 | 0.5806451612903226 | 0.3787878787878788 |
| MIA | 0.20398213493991907 | 0.43661971830985913 | 0.42696629213483145 |
| PHI | 0.12221494338274756 | 0.5443037974683544 | 0.43243243243243246 |
| BAL | 0.1212007033116207 | 0.4878048780487805 | 0.38571428571428573 |
| CHI | 0.08750499356433414 | 0.42696629213483145 | 0.43661971830985913 |

### PowerScore Rankings

- Artifact: `data\l4_powerscore\2022\9.parquet`
- Manifest: `data\l4_powerscore\2022\9_manifest.json`
- Rows: 26
- Columns: 4

| team | power_score |
| --- | --- |
| CHI | 1.9581647477692088 |
| BAL | 1.9566120004413725 |
| CIN | 1.9112755184306949 |
| NYJ | 1.8164503006601398 |
| GB | 1.8156250076528986 |
| BUF | 1.7897138600007945 |
| KC | 1.7622805884014037 |
| HOU | 1.7490832463141057 |
| LAC | 1.7458237573596607 |
| PHI | 1.742901296742481 |


## Visualizations

![PowerScore Top 10](2022_w9/assets/powerscore_top10.png)

