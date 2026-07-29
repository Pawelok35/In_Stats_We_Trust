# Edge Proof Dossier

Generated from local pick ledgers under `data`.

## Verdict

**Classification:** strong search-adjusted holdout evidence

This dossier is an empirical audit, not financial advice. The selected rule was ranked using train-period performance only; holdout results are reported after selection.

Key holdout facts:
- holdout bets=234, W-L-P=170-62-2
- holdout ROI=39.9%, units=+92.55
- one-sided binomial p=0.0000, Bonferroni-adjusted p=0.0000
- 95% Wilson CI win-rate=67.2%-78.6%

## Protocol

- Train seasons: 2021, 2022, 2023
- Holdout seasons: 2024, 2025
- Variant directories searched: picks, picks_variant_a_high_conf, picks_variant_b_edge_focus, picks_variant_c_psdiff, picks_variant_d_balanced, picks_variant_e_loose, picks_variant_f, picks_variant_g, picks_variant_h, picks_variant_i, picks_variant_j, picks_variant_k, picks_variant_l, picks_variant_m, picks_variant_n, picks_variant_o
- Tested rule grid size: 186624
- Train eligibility gate: at least 3 bets and positive flat-stake units in every train season.
- Selection criterion: train profit, then train ROI, then train sample size.
- Holdout was not used for selecting the champion rule.
- Profit model: flat 1u risk per non-push ATS decision at -110; win = +0.9091u, loss = -1u, push = 0u.
- Statistical screen: one-sided binomial test against 52.38% break-even win rate, plus Bonferroni adjustment over the searched grid.

## Champion Rule

`variant_e_loose | tags=GOY+GOM+GOW+VALUE PLAY | confidence>=0 | edge>=0 | any`

| Split | Bets | W-L-P | Win Rate | Units | ROI | Max DD | p-value | Adj. p | 95% CI |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Train | 348 | 231-105-12 | 68.8% | +105.00u | 31.2% | -10.82u | 0.0000 | 0.0000 | 63.6%-73.5% |
| Holdout | 234 | 170-62-2 | 73.3% | +92.55u | 39.9% | -4.45u | 0.0000 | 0.0000 | 67.2%-78.6% |

## Season Breakdown

| Season | Split | Bets | W-L-P | Win Rate | Units | ROI | Max DD |
|---:|---|---:|---:|---:|---:|---:|---:|
| 2021 | train | 111 | 57-51-3 | 52.8% | +0.82u | 0.8% | -10.82u |
| 2022 | train | 108 | 74-30-4 | 71.2% | +37.27u | 35.8% | -4.00u |
| 2023 | train | 129 | 100-24-5 | 80.6% | +66.91u | 54.0% | -2.00u |
| 2024 | holdout | 139 | 106-32-1 | 76.8% | +64.36u | 46.6% | -4.09u |
| 2025 | holdout | 95 | 64-30-1 | 68.1% | +28.18u | 30.0% | -4.45u |

## Top Train-Selected Candidates

| Rank | Rule | Train Units | Train ROI | Holdout Units | Holdout ROI | Holdout Bets |
|---:|---|---:|---:|---:|---:|---:|
| 1 | `variant_e_loose / tags=GOY+GOM+GOW+VALUE PLAY / confidence>=0 / edge>=0 / any` | +105.00u | 31.2% | +92.55u | 39.9% | 234 |
| 2 | `baseline / tags=GOY+GOM+GOW+VALUE PLAY / confidence>=0 / edge>=0 / any` | +104.64u | 32.4% | +93.73u | 41.3% | 229 |
| 3 | `variant_g / tags=GOY+GOM+GOW+VALUE PLAY / confidence>=0 / edge>=0 / any` | +104.64u | 32.4% | +93.73u | 41.3% | 229 |
| 4 | `variant_i / tags=GOY+GOM+GOW+VALUE PLAY / confidence>=0 / edge>=0 / any` | +104.64u | 32.4% | +93.73u | 41.3% | 229 |
| 5 | `variant_e_loose / tags=GOY+GOM+GOW+VALUE PLAY / confidence>=70 / edge>=0 / any` | +104.55u | 32.2% | +88.09u | 39.2% | 227 |
| 6 | `baseline / tags=GOY+GOM+GOW+VALUE PLAY / confidence>=70 / edge>=0 / any` | +104.09u | 33.1% | +89.27u | 40.6% | 222 |
| 7 | `variant_g / tags=GOY+GOM+GOW+VALUE PLAY / confidence>=70 / edge>=0 / any` | +104.09u | 33.1% | +89.27u | 40.6% | 222 |
| 8 | `variant_i / tags=GOY+GOM+GOW+VALUE PLAY / confidence>=70 / edge>=0 / any` | +104.09u | 33.1% | +89.27u | 40.6% | 222 |
| 9 | `variant_h / tags=GOY+GOM+GOW+VALUE PLAY / confidence>=0 / edge>=0 / any` | +101.36u | 32.6% | +89.36u | 41.0% | 220 |
| 10 | `variant_h / tags=GOY+GOM+GOW+VALUE PLAY / confidence>=70 / edge>=0 / any` | +101.36u | 32.6% | +89.36u | 41.0% | 220 |
| 11 | `variant_e_loose / tags=GOY+GOM+GOW+VALUE PLAY / confidence>=0 / edge>=0 / any / week>=3` | +101.18u | 32.1% | +82.73u | 38.1% | 218 |
| 12 | `variant_a_high_conf / tags=GOY+GOM+GOW+VALUE PLAY / confidence>=0 / edge>=0 / any` | +101.09u | 36.8% | +96.55u | 51.9% | 188 |
| 13 | `variant_a_high_conf / tags=GOY+GOM+GOW+VALUE PLAY / confidence>=70 / edge>=0 / any` | +101.09u | 36.8% | +96.55u | 51.9% | 188 |
| 14 | `variant_f / tags=GOY+GOM+GOW+VALUE PLAY / confidence>=0 / edge>=0 / any` | +101.09u | 36.8% | +96.55u | 51.9% | 188 |
| 15 | `variant_f / tags=GOY+GOM+GOW+VALUE PLAY / confidence>=70 / edge>=0 / any` | +101.09u | 36.8% | +96.55u | 51.9% | 188 |
| 16 | `baseline / tags=GOY+GOM+GOW+VALUE PLAY / confidence>=0 / edge>=0 / any / week>=3` | +100.82u | 33.4% | +83.91u | 39.6% | 213 |
| 17 | `variant_g / tags=GOY+GOM+GOW+VALUE PLAY / confidence>=0 / edge>=0 / any / week>=3` | +100.82u | 33.4% | +83.91u | 39.6% | 213 |
| 18 | `variant_i / tags=GOY+GOM+GOW+VALUE PLAY / confidence>=0 / edge>=0 / any / week>=3` | +100.82u | 33.4% | +83.91u | 39.6% | 213 |
| 19 | `variant_n / tags=GOY+GOM+GOW+VALUE PLAY / confidence>=0 / edge>=0 / any` | +99.82u | 41.6% | +90.09u | 56.3% | 162 |
| 20 | `variant_n / tags=GOY+GOM+GOW+VALUE PLAY / confidence>=70 / edge>=0 / any` | +99.82u | 41.6% | +90.09u | 56.3% | 162 |

## Interpretation

- A positive holdout is evidence only if the rule was selected without looking at holdout outcomes.
- A search-adjusted proof is much harder than a positive ROI table because the grid contains many variants, thresholds and subgroups.
- If adjusted p-value is not significant, the correct label is a candidate edge, not a proven edge.
- The next stronger test is prospective paper-trading with immutable timestamps before kickoff.

## Next Gate

Promote the champion rule to prospective watch only if holdout ROI is positive, sample size is adequate, and drawdown is operationally tolerable. The prospective ledger must record decision-time line, price, source, timestamp, model version and no-bet reasons before kickoff.
