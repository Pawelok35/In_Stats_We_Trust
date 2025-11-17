# Weekly Report - Season 2024, Week 2

_Generated at 2025-11-10T17:48:42.767025+00:00 (UTC)_

Data root: `data`

## Layer Shapes

| Layer | Artifact | Manifest | Rows | Columns | Status |
|-------|----------|----------|------|---------|--------|
| L1 Ingest | `data\l1\2024\2.parquet` | `data\l1\2024\2_manifest.json` | 2721 | 18 | ready |
| L2 Clean | `data\l2\2024\2.parquet` | `data\l2\2024\2_manifest.json` | 2721 | 24 | ready |
| L3 Team Week | `data\l3_team_week\2024\2.parquet` | `data\l3_team_week\2024\2_manifest.json` | 32 | 34 | ready |

## L2 Audit Snapshot

Last 3 entries from `data\l2_audit\2024\2_audit.jsonl`:

- {"step": "load", "details": "Loaded L1 parquet", "rows": 2721, "cols": 18, "timestamp": "2025-11-10T17:48:42.344453+00:00"}
- {"step": "prepare", "details": "Normalized team aliases, filtered season/week, deduplicated keys", "rows": 2721, "cols": 24, "rows_removed": 0, "timestamp": "2025-11-10T17:48:42.344453+00:00"}
- {"step": "validate", "details": "Validated against L2 contract and guardrails", "rows": 2721, "cols": 24, "timestamp": "2025-11-10T17:48:42.344453+00:00"}

## L3 Sanity

- Rows processed: 32
- Columns available: 34
- Artifact path: `data\l3_team_week\2024\2.parquet`

## Metrics Snapshot

### L4 Core12 Preview

- Artifact: `data\l4_core12\2024\2.parquet`
- Manifest: `data\l4_core12\2024\2_manifest.json`
- Rows: N/A
- Columns: N/A

| TEAM | core_epa_off | core_sr_off | core_sr_def |
| --- | --- | --- | --- |
| NO | 0.3328928588698172 | 0.589041095890411 | 0.45977011494252873 |
| ARI | 0.3216522908260231 | 0.5875 | 0.5223880597014925 |
| ATL | 0.1376739255171521 | 0.5 | 0.47674418604651164 |
| WAS | 0.13138500058816538 | 0.4666666666666667 | 0.45588235294117646 |
| BUF | 0.1114574812474798 | 0.4098360655737705 | 0.47191011235955055 |

### PowerScore Rankings

- Artifact: `data\l4_powerscore\2024\2.parquet`
- Manifest: `data\l4_powerscore\2024\2_manifest.json`
- Rows: 32
- Columns: 4

| team | power_score |
| --- | --- |
| NO | 0.27633495461207436 |
| ARI | 0.2685365538667801 |
| ATL | 0.22064187622190884 |
| WAS | 0.2117335344193613 |
| PHI | 0.2009976225506045 |
| NYG | 0.1952262613801529 |
| SEA | 0.1726702138952825 |
| DAL | 0.16705396296501912 |
| LA | 0.16012353736083212 |
| CIN | 0.15750549848275563 |


## Visualizations

![PowerScore Top 10](2024_w2/assets/powerscore_top10.png)

