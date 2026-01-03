# Weekly Report - Season 2023, Week 13

_Generated at 2026-01-02T10:28:37.732698+00:00 (UTC)_

Data root: `data`

## Layer Shapes

| Layer | Artifact | Manifest | Rows | Columns | Status |
|-------|----------|----------|------|---------|--------|
| L1 Ingest | `data\l1\2023\13.parquet` | `data\l1\2023\13_manifest.json` | 2329 | 18 | ready |
| L2 Clean | `data\l2\2023\13.parquet` | `data\l2\2023\13_manifest.json` | 2329 | 24 | ready |
| L3 Team Week | `data\l3_team_week\2023\13.parquet` | `data\l3_team_week\2023\13_manifest.json` | 26 | 34 | ready |

## L2 Audit Snapshot

Last 3 entries from `data\l2_audit\2023\13_audit.jsonl`:

- {"step": "load", "details": "Loaded L1 parquet", "rows": 2329, "cols": 18, "timestamp": "2026-01-02T10:28:37.338712+00:00"}
- {"step": "prepare", "details": "Normalized team aliases, filtered season/week, deduplicated keys", "rows": 2329, "cols": 24, "rows_removed": 0, "timestamp": "2026-01-02T10:28:37.338712+00:00"}
- {"step": "validate", "details": "Validated against L2 contract and guardrails", "rows": 2329, "cols": 24, "timestamp": "2026-01-02T10:28:37.338712+00:00"}

## L3 Sanity

- Rows processed: 26
- Columns available: 34
- Artifact path: `data\l3_team_week\2023\13.parquet`

## Metrics Snapshot

### L4 Core12 Preview

- Artifact: `data\l4_core12\2023\13.parquet`
- Manifest: `data\l4_core12\2023\13_manifest.json`
- Rows: 26
- Columns: 27

| TEAM | core_epa_off | core_sr_off | core_sr_def |
| --- | --- | --- | --- |
| SF | 0.4227630359592376 | 0.5974025974025974 | 0.3595505617977528 |
| MIA | 0.35179308375242996 | 0.527027027027027 | 0.2602739726027397 |
| GB | 0.23253180336250806 | 0.475 | 0.4810126582278481 |
| DAL | 0.1899612019814196 | 0.5142857142857142 | 0.4367816091954023 |
| CIN | 0.13928279202017518 | 0.5 | 0.44680851063829785 |

### PowerScore Rankings

- Artifact: `data\l4_powerscore\2023\13.parquet`
- Manifest: `data\l4_powerscore\2023\13_manifest.json`
- Rows: 26
- Columns: 4

| team | power_score |
| --- | --- |
| GB | 2.226993398556273 |
| KC | 2.1887597431434056 |
| PHI | 2.175102695109718 |
| DAL | 2.13195766568844 |
| SF | 2.021505777156439 |
| SEA | 1.9358532305271938 |
| ARI | 1.7580943908401379 |
| JAX | 1.7312657977919144 |
| MIA | 1.7018397689170455 |
| CIN | 1.688057802956569 |


## Visualizations

![PowerScore Top 10](2023_w13/assets/powerscore_top10.png)

