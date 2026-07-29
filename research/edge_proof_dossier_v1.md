# Edge Proof Dossier

Generated from local pick ledgers under `data`.

## Verdict

**Proof status:** not a full edge proof: statistically strong historical backtest with integrity red flags
**Statistical classification before integrity gates:** strong search-adjusted holdout evidence

This dossier is an empirical audit, not financial advice. The selected rule was ranked using train-period performance only; holdout results are reported after selection.

Key holdout facts:
- holdout bets=139, W-L-P=122-17-0
- holdout ROI=67.6%, units=+93.91
- one-sided binomial p=0.0000, Bonferroni-adjusted p=0.0000
- 95% Wilson CI win-rate=81.3%-92.2%

## Protocol

- Train seasons: 2021, 2022, 2023
- Holdout seasons: 2024, 2025
- Variant directories searched: picks_variant_b_edge_focus, picks_variant_c_psdiff, picks_variant_d_balanced, picks_variant_j, picks_variant_k, picks_variant_m
- Tested rule grid size: 69984
- Train eligibility gate: at least 3 bets and positive flat-stake units in every train season.
- Selection criterion: train profit, then train ROI, then train sample size.
- Holdout was not used for selecting the champion rule.
- Profit model: flat 1u risk per non-push ATS decision at -110; win = +0.9091u, loss = -1u, push = 0u.
- Statistical screen: one-sided binomial test against 52.38% break-even win rate, plus Bonferroni adjustment over the searched grid.

## Data Integrity Gate

- Pick records scanned: 7746
- Records generated after season year: 7746
- Records generated from dirty worktree: 7674
- Records missing decision-time odds timestamp: 7746
- Distinct `generated_at` timestamps: 62

Red flags:
- pick files were generated after the season year; this is historical backfill, not prospective proof
- records were generated from a dirty git worktree
- records do not contain immutable decision-time odds timestamps
- some records do not contain commit_sha

Integrity verdict: the numeric result can be treated as a historical backtest screen, but not as a completed proof of a tradable edge. The next required gate is a prospective, immutable paper-trading ledger.

## Champion Rule

`variant_m | tags=GOY+GOM+GOW+VALUE PLAY | confidence>=0 | edge>=0 | any | week>=3`

| Split | Bets | W-L-P | Win Rate | Units | ROI | Max DD | p-value | Adj. p | 95% CI |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Train | 206 | 153-49-4 | 75.7% | +90.09u | 44.6% | -9.27u | 0.0000 | 0.0000 | 69.4%-81.1% |
| Holdout | 139 | 122-17-0 | 87.8% | +93.91u | 67.6% | -2.00u | 0.0000 | 0.0000 | 81.3%-92.2% |

## Season Breakdown

| Season | Split | Bets | W-L-P | Win Rate | Units | ROI | Max DD |
|---:|---|---:|---:|---:|---:|---:|---:|
| 2021 | train | 73 | 38-34-1 | 52.8% | +0.55u | 0.8% | -9.27u |
| 2022 | train | 55 | 47-8-0 | 85.5% | +34.73u | 63.1% | -2.00u |
| 2023 | train | 78 | 68-7-3 | 90.7% | +54.82u | 73.1% | -1.09u |
| 2024 | holdout | 68 | 63-5-0 | 92.6% | +52.27u | 76.9% | -1.00u |
| 2025 | holdout | 71 | 59-12-0 | 83.1% | +41.64u | 58.6% | -2.00u |

## Top Train-Selected Candidates

| Rank | Rule | Train Units | Train ROI | Holdout Units | Holdout ROI | Holdout Bets |
|---:|---|---:|---:|---:|---:|---:|
| 1 | `variant_m / tags=GOY+GOM+GOW+VALUE PLAY / confidence>=0 / edge>=0 / any / week>=3` | +90.09u | 44.6% | +93.91u | 67.6% | 139 |
| 2 | `variant_m / tags=GOY+GOM+GOW+VALUE PLAY / confidence>=70 / edge>=0 / any / week>=3` | +90.09u | 44.6% | +93.91u | 67.6% | 139 |
| 3 | `variant_m / tags=GOY+GOM+GOW / confidence>=0 / edge>=0 / any` | +83.64u | 42.5% | +88.55u | 67.6% | 131 |
| 4 | `variant_m / tags=GOY+GOM+GOW / confidence>=70 / edge>=0 / any` | +83.64u | 42.5% | +88.55u | 67.6% | 131 |
| 5 | `variant_m / tags=GOY+GOM+GOW+VALUE PLAY / confidence>=80 / edge>=0 / any` | +83.45u | 41.5% | +89.45u | 67.8% | 132 |
| 6 | `variant_m / tags=GOY+GOM+GOW+VALUE PLAY / confidence>=0 / edge>=0 / any / week>=3 / abs(handicap)<=10` | +81.64u | 52.0% | +83.45u | 71.3% | 117 |
| 7 | `variant_m / tags=GOY+GOM+GOW+VALUE PLAY / confidence>=70 / edge>=0 / any / week>=3 / abs(handicap)<=10` | +81.64u | 52.0% | +83.45u | 71.3% | 117 |
| 8 | `variant_k / tags=GOY+GOM+GOW+VALUE PLAY / confidence>=0 / edge>=4 / any / abs(handicap)<=10` | +81.64u | 41.0% | +84.27u | 52.0% | 163 |
| 9 | `variant_k / tags=GOY+GOM+GOW+VALUE PLAY / confidence>=70 / edge>=4 / any / abs(handicap)<=10` | +81.64u | 41.0% | +84.27u | 52.0% | 163 |
| 10 | `variant_m / tags=GOY+GOM+GOW / confidence>=0 / edge>=0 / any / week>=3` | +81.36u | 44.2% | +84.00u | 66.7% | 126 |
| 11 | `variant_m / tags=GOY+GOM+GOW / confidence>=70 / edge>=0 / any / week>=3` | +81.36u | 44.2% | +84.00u | 66.7% | 126 |
| 12 | `variant_m / tags=GOY+GOM+GOW+VALUE PLAY / confidence>=80 / edge>=0 / any / week>=3` | +81.18u | 43.2% | +84.91u | 66.9% | 127 |
| 13 | `variant_c_psdiff / tags=GOY+GOM+GOW+VALUE PLAY / confidence>=0 / edge>=0 / any / week>=5 / abs(handicap)<=10` | +78.91u | 51.2% | +77.45u | 53.8% | 144 |
| 14 | `variant_k / tags=GOY+GOM+GOW+VALUE PLAY / confidence>=0 / edge>=0 / any / week>=5 / abs(handicap)<=10` | +78.73u | 44.0% | +71.09u | 45.0% | 158 |
| 15 | `variant_k / tags=GOY+GOM+GOW+VALUE PLAY / confidence>=70 / edge>=0 / any / week>=5 / abs(handicap)<=10` | +78.73u | 44.0% | +71.09u | 45.0% | 158 |
| 16 | `variant_m / tags=GOY+GOM+GOW / confidence>=80 / edge>=0 / any` | +78.27u | 41.4% | +83.18u | 67.6% | 123 |
| 17 | `variant_k / tags=GOY+GOM+GOW+VALUE PLAY / confidence>=0 / edge>=4 / any / week>=3 / abs(handicap)<=10` | +77.64u | 42.7% | +77.09u | 50.7% | 152 |
| 18 | `variant_k / tags=GOY+GOM+GOW+VALUE PLAY / confidence>=70 / edge>=4 / any / week>=3 / abs(handicap)<=10` | +77.64u | 42.7% | +77.09u | 50.7% | 152 |
| 19 | `variant_c_psdiff / tags=GOY+GOM+GOW+VALUE PLAY / confidence>=70 / edge>=0 / any / week>=5 / abs(handicap)<=10` | +77.09u | 50.7% | +75.73u | 54.1% | 140 |
| 20 | `variant_m / tags=GOY+GOM+GOW+VALUE PLAY / confidence>=0 / edge>=0 / favorite / week>=3` | +76.73u | 42.4% | +80.36u | 65.9% | 122 |

## Interpretation

- A positive holdout is evidence only if the rule was selected without looking at holdout outcomes.
- A search-adjusted proof is much harder than a positive ROI table because the grid contains many variants, thresholds and subgroups.
- If adjusted p-value is not significant, the correct label is a candidate edge, not a proven edge.
- The next stronger test is prospective paper-trading with immutable timestamps before kickoff.

## Next Gate

Promote the champion rule to prospective watch only if holdout ROI is positive, sample size is adequate, and drawdown is operationally tolerable. The prospective ledger must record decision-time line, price, source, timestamp, model version and no-bet reasons before kickoff.
