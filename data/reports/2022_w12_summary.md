# Weekly Report - Season 2022, Week 12

_Generated at 2026-01-02T11:35:10.465173+00:00 (UTC)_

Data root: `data`

## Layer Shapes

| Layer | Artifact | Manifest | Rows | Columns | Status |
|-------|----------|----------|------|---------|--------|
| L1 Ingest | `data\l1\2022\12.parquet` | `data\l1\2022\12_manifest.json` | 2791 | 18 | ready |
| L2 Clean | `data\l2\2022\12.parquet` | `data\l2\2022\12_manifest.json` | 2791 | 24 | ready |
| L3 Team Week | `data\l3_team_week\2022\12.parquet` | `data\l3_team_week\2022\12_manifest.json` | 32 | 34 | ready |

## L2 Audit Snapshot

Last 3 entries from `data\l2_audit\2022\12_audit.jsonl`:

- {"step": "load", "details": "Loaded L1 parquet", "rows": 2791, "cols": 18, "timestamp": "2026-01-02T11:35:10.062684+00:00"}
- {"step": "prepare", "details": "Normalized team aliases, filtered season/week, deduplicated keys", "rows": 2791, "cols": 24, "rows_removed": 0, "timestamp": "2026-01-02T11:35:10.062684+00:00"}
- {"step": "validate", "details": "Validated against L2 contract and guardrails", "rows": 2791, "cols": 24, "timestamp": "2026-01-02T11:35:10.063681+00:00"}

## L3 Sanity

- Rows processed: 32
- Columns available: 34
- Artifact path: `data\l3_team_week\2022\12.parquet`

## Metrics Snapshot

### L4 Core12 Preview

- Artifact: `data\l4_core12\2022\12.parquet`
- Manifest: `data\l4_core12\2022\12_manifest.json`
- Rows: 32
- Columns: 27

| TEAM | core_epa_off | core_sr_off | core_sr_def |
| --- | --- | --- | --- |
| NYJ | 0.1907340570622565 | 0.5 | 0.3333333333333333 |
| GB | 0.16771963954141195 | 0.5 | 0.5252525252525253 |
| PHI | 0.16729860054799403 | 0.5252525252525253 | 0.5 |
| KC | 0.12761683001854393 | 0.5348837209302325 | 0.3194444444444444 |
| LV | 0.11787803180287687 | 0.47959183673469385 | 0.5176470588235295 |

### PowerScore Rankings

- Artifact: `data\l4_powerscore\2022\12.parquet`
- Manifest: `data\l4_powerscore\2022\12_manifest.json`
- Rows: 32
- Columns: 4

| team | power_score |
| --- | --- |
| KC | 2.3113591797541115 |
| PHI | 2.0234115694132115 |
| BUF | 2.0050560464394143 |
| DAL | 1.9472518451121676 |
| WAS | 1.8655527730814614 |
| PIT | 1.8287717510110635 |
| MIN | 1.7889740313845452 |
| SF | 1.7883457349813408 |
| BAL | 1.755442263263928 |
| DET | 1.737219740556532 |


## Visualizations

![PowerScore Top 10](2022_w12/assets/powerscore_top10.png)

