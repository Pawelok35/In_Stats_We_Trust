# Weekly Report - Season 2023, Week 16

_Generated at 2025-11-10T20:39:52.540621+00:00 (UTC)_

Data root: `data`

## Layer Shapes

| Layer | Artifact | Manifest | Rows | Columns | Status |
|-------|----------|----------|------|---------|--------|
| L1 Ingest | `data\l1\2023\16.parquet` | `data\l1\2023\16_manifest.json` | 2844 | 18 | ready |
| L2 Clean | `data\l2\2023\16.parquet` | `data\l2\2023\16_manifest.json` | 2844 | 24 | ready |
| L3 Team Week | `data\l3_team_week\2023\16.parquet` | `data\l3_team_week\2023\16_manifest.json` | 32 | 34 | ready |

## L2 Audit Snapshot

Last 3 entries from `data\l2_audit\2023\16_audit.jsonl`:

- {"step": "load", "details": "Loaded L1 parquet", "rows": 2844, "cols": 18, "timestamp": "2025-11-10T20:39:52.018971+00:00"}
- {"step": "prepare", "details": "Normalized team aliases, filtered season/week, deduplicated keys", "rows": 2844, "cols": 24, "rows_removed": 0, "timestamp": "2025-11-10T20:39:52.018971+00:00"}
- {"step": "validate", "details": "Validated against L2 contract and guardrails", "rows": 2844, "cols": 24, "timestamp": "2025-11-10T20:39:52.018971+00:00"}

## L3 Sanity

- Rows processed: 32
- Columns available: 34
- Artifact path: `data\l3_team_week\2023\16.parquet`

## Metrics Snapshot

### L4 Core12 Preview

- Artifact: `data\l4_core12\2023\16.parquet`
- Manifest: `data\l4_core12\2023\16_manifest.json`
- Rows: N/A
- Columns: N/A

| TEAM | core_epa_off | core_sr_off | core_sr_def |
| --- | --- | --- | --- |
| GB | 0.24581403524747916 | 0.5 | 0.4642857142857143 |
| CAR | 0.1895457417593293 | 0.4642857142857143 | 0.5 |
| SEA | 0.16559620554509916 | 0.4605263157894737 | 0.4819277108433735 |
| PIT | 0.15321898190925518 | 0.4533333333333333 | 0.38961038961038963 |
| MIA | 0.1256160243760749 | 0.5 | 0.43902439024390244 |

### PowerScore Rankings

- Artifact: `data\l4_powerscore\2023\16.parquet`
- Manifest: `data\l4_powerscore\2023\16_manifest.json`
- Rows: 32
- Columns: 4

| team | power_score |
| --- | --- |
| GB | 0.27751548925991215 |
| CAR | 0.264908578570023 |
| MIA | 0.21709127900028805 |
| SEA | 0.20754551943397465 |
| TEN | 0.19611887799508895 |
| DAL | 0.18861142087830002 |
| CHI | 0.17172718702508014 |
| DET | 0.1706849747173695 |
| ATL | 0.16663433427920601 |
| MIN | 0.15730729052883288 |


## Visualizations

![PowerScore Top 10](2023_w16/assets/powerscore_top10.png)

