# Weekly Report - Season 2024, Week 13

_Generated at 2025-11-10T17:50:45.883324+00:00 (UTC)_

Data root: `data`

## Layer Shapes

| Layer | Artifact | Manifest | Rows | Columns | Status |
|-------|----------|----------|------|---------|--------|
| L1 Ingest | `data\l1\2024\13.parquet` | `data\l1\2024\13_manifest.json` | 2848 | 18 | ready |
| L2 Clean | `data\l2\2024\13.parquet` | `data\l2\2024\13_manifest.json` | 2848 | 24 | ready |
| L3 Team Week | `data\l3_team_week\2024\13.parquet` | `data\l3_team_week\2024\13_manifest.json` | 32 | 34 | ready |

## L2 Audit Snapshot

Last 3 entries from `data\l2_audit\2024\13_audit.jsonl`:

- {"step": "load", "details": "Loaded L1 parquet", "rows": 2848, "cols": 18, "timestamp": "2025-11-10T17:50:45.119791+00:00"}
- {"step": "prepare", "details": "Normalized team aliases, filtered season/week, deduplicated keys", "rows": 2848, "cols": 24, "rows_removed": 0, "timestamp": "2025-11-10T17:50:45.119791+00:00"}
- {"step": "validate", "details": "Validated against L2 contract and guardrails", "rows": 2848, "cols": 24, "timestamp": "2025-11-10T17:50:45.119791+00:00"}

## L3 Sanity

- Rows processed: 32
- Columns available: 34
- Artifact path: `data\l3_team_week\2024\13.parquet`

## Metrics Snapshot

### L4 Core12 Preview

- Artifact: `data\l4_core12\2024\13.parquet`
- Manifest: `data\l4_core12\2024\13_manifest.json`
- Rows: N/A
- Columns: N/A

| TEAM | core_epa_off | core_sr_off | core_sr_def |
| --- | --- | --- | --- |
| GB | 0.278299344677685 | 0.5138888888888888 | 0.5111111111111111 |
| PIT | 0.19026539296392803 | 0.6043956043956044 | 0.5783132530120482 |
| WAS | 0.14957151987755873 | 0.5742574257425742 | 0.3611111111111111 |
| BUF | 0.1430380254621721 | 0.5 | 0.35384615384615387 |
| IND | 0.11766690803641403 | 0.5675675675675675 | 0.5116279069767442 |

### PowerScore Rankings

- Artifact: `data\l4_powerscore\2024\13.parquet`
- Manifest: `data\l4_powerscore\2024\13_manifest.json`
- Rows: 32
- Columns: 4

| team | power_score |
| --- | --- |
| GB | 0.27194211103358407 |
| PIT | 0.26840732541456797 |
| CIN | 0.24019729761188663 |
| MIA | 0.22835715907367152 |
| IND | 0.2114095810994255 |
| NE | 0.20536222832691858 |
| LA | 0.19061704276932204 |
| WAS | 0.190367180093105 |
| MIN | 0.1872144921187594 |
| DEN | 0.1804901085165399 |


## Visualizations

![PowerScore Top 10](2024_w13/assets/powerscore_top10.png)

