# Backtesting

Backtesting is the first-class evaluation layer for pick outputs.

## Command

```powershell
python -m app.cli evaluate-picks `
  --season 2025 `
  --from-week 2 `
  --to-week 12 `
  --manual-results data/results/manual_results.jsonl
```

The command prints:

- performance by tag,
- performance by confidence bucket,
- wins, losses, pushes, pending picks,
- win rate,
- net units,
- ROI.

## Assumptions

Current pick files do not store market odds, so ROI uses a conservative default:

- win: `+0.9091u`, equivalent to -110 pricing,
- loss: `-1.0u`,
- push: `0.0u`.

When pick records gain explicit odds, `metrics.backtest` should use those odds per pick.

## Input Contract

Pick records are read from:

```text
data/picks*/<season>/week_<week>.jsonl
```

Minimum fields:

- `season`
- `week`
- `home`
- `away`
- `tag`
- `model_winner`
- `confidence`
- `handicap`

Manual results are read from JSONL with:

- `season`
- `week`
- `home_team`
- `away_team`
- `home_score`
- `away_score`

## Module

The reusable implementation lives in `metrics/backtest.py`.

