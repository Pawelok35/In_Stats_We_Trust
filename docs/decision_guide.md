# Decision Guide

This is the operational guide for running and judging In Stats We Trust.

## Standard Weekly Flow

Use `python -m app.cli` as the public entrypoint.

For a completed week:

```powershell
python -m app.cli build-week --season 2025 --week 8
```

For an upcoming week, use the latest completed week as the reference week to avoid future data leakage:

```powershell
python -m app.cli weekly-pipeline `
  --season 2025 `
  --week 12 `
  --reference-week 11 `
  --picks-start-week 12 `
  --run-convergence
```

Then open the dashboard:

```powershell
cd frontend
npm run dev -- --port 3000
```

Dashboard:

```text
http://localhost:3000/dashboard
```

## How To Judge A Week

Run the pick backtest:

```powershell
python -m app.cli evaluate-picks `
  --season 2025 `
  --from-week 2 `
  --to-week 12 `
  --manual-results data/results/manual_results.jsonl
```

Run the active variant comparison:

```powershell
python -m app.cli evaluate-variants `
  --season 2025 `
  --start-week 2 `
  --end-week 12 `
  --manual-results data/results/manual_results.jsonl
```

Minimum review checklist:

- Check win rate and ROI by tag.
- Check confidence buckets.
- Check champion vs challengers.
- Check pending games before trusting totals.
- Check whether the edge came from one outlier week or a repeatable signal.

## Source Of Truth

| Area | Source |
| --- | --- |
| CLI workflows | `app/cli.py`, `docs/cli_workflow.md` |
| Artifact policy | `docs/artifact_policy.md` |
| Paths | `utils/paths.py` |
| Runtime config | `config/settings.yaml` |
| Schema contracts | `config/contracts.yaml` |
| Variant registry | `config/tag_variants.yaml` |
| Variant rules | `config/tag_rules/*.yaml` |
| Betting lines | `config/lines/<season>/week<n>_lines.yaml` |
| Manual results | `data/results/manual_results.jsonl` |
| Backtesting | `metrics/backtest.py`, `docs/backtesting.md` |
| Metadata | `utils/run_metadata.py`, `docs/run_metadata.md` |
| Frontend dashboard | `frontend/src/app/dashboard/page.tsx`, `docs/frontend_dashboard.md` |

## Artifact Map

Generated artifacts are under `data/`.

| Artifact | Meaning |
| --- | --- |
| `data/l1/<season>/<week>.parquet` | Raw normalized ingest layer |
| `data/l2/<season>/<week>.parquet` | Clean play-level layer |
| `data/l2_audit/<season>/<week>_audit.jsonl` | L2 audit trail |
| `data/l3_team_week/<season>/<week>.parquet` | Team-week metrics |
| `data/l4_core12/<season>/<week>.parquet` | Core12 metrics |
| `data/l4_powerscore/<season>/<week>.parquet` | PowerScore output |
| `data/reports/...` | Markdown reports and assets |
| `data/picks*/*/week_*.jsonl` | Pick outputs by variant |

Generated artifacts should not be treated as source code. See `docs/artifact_policy.md`.

## Signal Interpretation

`PowerScore`:

- A compact team strength score derived from Core12.
- Useful for relative comparison, not as a standalone betting signal.
- Stronger when it agrees with matchup report, edge, and variant convergence.

`confidence`:

- Model-side confidence attached to a pick.
- Should be judged by bucket performance in backtesting.
- High confidence without positive historical bucket performance is not enough.

`edge_vs_line`:

- Difference between model view and market line.
- Large absolute edge can signal opportunity or model disagreement.
- Always check if the edge appears across active variants.

Variant status:

- `champion`: current production/default variant.
- `challenger`: active contender compared against champion.
- `experimental`: research only, excluded from default active comparison.
- `retired`: historical reference.

Decision labels in the dashboard:

- `bet`: strongest actionable tier.
- `lean`: worth review, not automatically a bet.
- `avoid`: do not use as actionable signal.
- `no bet`: insufficient signal.

## What Is Experimental

Treat these as experimental unless promoted through documented backtesting:

- variants marked `experimental`,
- ad hoc scripts not exposed through `python -m app.cli`,
- generated reports in `data/reports/generated`,
- manual weather/convergence helper outputs,
- any pick file missing model/version metadata.

## Promotion Criteria

A new signal or variant should only become operational after it has:

- enough graded picks to avoid one-week noise,
- positive ROI after pushes and pending games are handled,
- stable confidence bucket behavior,
- documented comparison against the champion,
- no contract violations,
- reproducible metadata in generated artifacts.

