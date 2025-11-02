# ISTW Validation – T21 (2025 Week 8)

| Layer | Artifact | Rows | Cols | Manifest |
| --- | --- | --- | --- | --- |
| L1 Ingest | `data/l1/2025/8.parquet` | 6 | 13 | `data/l1/2025/8_manifest.json` |
| L2 Clean | `data/l2/2025/8.parquet` | 6 | 12 | `data/l2/2025/8_manifest.json` |
| L3 TeamWeek | `data/l3_team_week/2025/8.parquet` | 2 | 10 | `data/l3_team_week/2025/8_manifest.json` |
| L4 Core12 | `data/l4_core12/2025/8.parquet` | 2 | 9 | `data/l4_core12/2025/8_manifest.json` |
| L4 PowerScore | `data/l4_powerscore/2025/8.parquet` | 2 | 4 | `data/l4_powerscore/2025/8/manifest.json` |

| Check | Result |
| --- | --- |
| `python -m pytest -q` | ✅ |
| `python -m ruff check .` | ✅ |
| `python -m black --check .` | ✅ |
| Weekly report (`data/reports/2025_w8_summary.md`) | includes PowerScore Rankings |

| Runtime | Duration (s) |
| --- | --- |
| `build-week --season 2025 --week 8` | 1.14 |
| Core12 compute | 0.85 |
| PowerScore compute | 0.80 |

- Report SHA-256: `94d351dda6b194ad7ba7fd06ff3e1c8dd8b46014b62b42446b06be22e6aa3ca1`
- Validation timestamp (UTC): `2025-10-27T18:45:35.274078+00:00`
- Final status: ✅ ISTW System validated through T21
