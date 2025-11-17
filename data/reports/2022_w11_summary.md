# Weekly Report - Season 2022, Week 11

_Generated at 2025-11-11T12:24:48.673849+00:00 (UTC)_

Data root: `data`

## Layer Shapes

| Layer | Artifact | Manifest | Rows | Columns | Status |
|-------|----------|----------|------|---------|--------|
| L1 Ingest | `data\l1\2022\11.parquet` | `data\l1\2022\11_manifest.json` | 2423 | 18 | ready |
| L2 Clean | `data\l2\2022\11.parquet` | `data\l2\2022\11_manifest.json` | 2423 | 24 | ready |
| L3 Team Week | `data\l3_team_week\2022\11.parquet` | `data\l3_team_week\2022\11_manifest.json` | 28 | 34 | ready |

## L2 Audit Snapshot

Last 3 entries from `data\l2_audit\2022\11_audit.jsonl`:

- {"step": "load", "details": "Loaded L1 parquet", "rows": 2423, "cols": 18, "timestamp": "2025-11-11T12:24:48.220863+00:00"}
- {"step": "prepare", "details": "Normalized team aliases, filtered season/week, deduplicated keys", "rows": 2423, "cols": 24, "rows_removed": 0, "timestamp": "2025-11-11T12:24:48.220863+00:00"}
- {"step": "validate", "details": "Validated against L2 contract and guardrails", "rows": 2423, "cols": 24, "timestamp": "2025-11-11T12:24:48.220863+00:00"}

## L3 Sanity

- Rows processed: 28
- Columns available: 34
- Artifact path: `data\l3_team_week\2022\11.parquet`

## Metrics Snapshot

### L4 Core12 Preview

- Artifact: `data\l4_core12\2022\11.parquet`
- Manifest: `data\l4_core12\2022\11_manifest.json`
- Rows: N/A
- Columns: N/A

| TEAM | core_epa_off | core_sr_off | core_sr_def |
| --- | --- | --- | --- |
| SF | 0.29407165501568766 | 0.5405405405405406 | 0.37209302325581395 |
| DAL | 0.2711811473730075 | 0.5058823529411764 | 0.225 |
| BUF | 0.1910811235099157 | 0.5555555555555556 | 0.47368421052631576 |
| CIN | 0.18548137111698879 | 0.5176470588235295 | 0.4387755102040816 |
| KC | 0.16745441082705995 | 0.47560975609756095 | 0.5185185185185185 |

### PowerScore Rankings

- Artifact: `data\l4_powerscore\2022\11.parquet`
- Manifest: `data\l4_powerscore\2022\11_manifest.json`
- Rows: 28
- Columns: 4

| team | power_score |
| --- | --- |
| BUF | 0.23629765671411773 |
| SF | 0.229865519029933 |
| CIN | 0.2238757121977972 |
| KC | 0.2218911086067604 |
| LAC | 0.20505013847431952 |
| CLE | 0.18779772657509516 |
| DAL | 0.18168295705766307 |
| PIT | 0.1695271330412996 |
| LV | 0.16807692329979443 |
| TEN | 0.16707166412056215 |


## Visualizations

![PowerScore Top 10](2022_w11/assets/powerscore_top10.png)

