# Tiered Staking Backtest

This is a historical backtest screen, not prospective edge proof.

Scope:
- Seasons: 2018
- Weeks: 2-18
- Picks dir: `data\picks_variant_m`
- Market: ATS/spread grading using stored `handicap` from pick perspective
- Price model: -110

Staking plans:
- `flat_1u`: all action tags 1u risk
- `conservative_0.5_1_1.5_2`: VALUE PLAY 0.5u, GOW 1u, GOM 1.5u, GOY 2u
- `aggressive_1_2_3_4`: VALUE PLAY 1u, GOW 2u, GOM 3u, GOY 4u

Important limitation:
- These historical pick files are research/backfilled artifacts, not frozen before kickoff.
- Use this to select candidate staking rules only. Forward proof still requires prospective ledger.

## Action Tags Only

| Staking | Bets | W-L-P | Win% | Risk | Units | ROI | Max DD |
|---|---:|---:|---:|---:|---:|---:|---:|
| flat_1u | 77 | 33-41-3 | 44.6% | 77.00u | -11.00u | -14.3% | -12.91u |
| conservative_0.5_1_1.5_2 | 77 | 33-41-3 | 44.6% | 128.00u | -14.64u | -11.4% | -20.64u |
| aggressive_1_2_3_4 | 77 | 33-41-3 | 44.6% | 256.00u | -29.27u | -11.4% | -41.27u |

## By Tag - Action Staking, NEUTRAL 0u

| Bucket | Bets | W-L-P | Win% | Risk | Units | ROI | Max DD |
|---|---:|---:|---:|---:|---:|---:|---:|
| GOM | 10 | 6-3-1 | 66.7% | 10.00u | +2.45u | 24.5% | -1.00u |
| GOW | 12 | 2-10-0 | 16.7% | 12.00u | -8.18u | -68.2% | -8.18u |
| GOY | 49 | 22-25-2 | 46.8% | 49.00u | -5.00u | -10.2% | -8.18u |
| NEUTRAL | 163 | 81-77-5 | 51.3% | 0.00u | +0.00u | 0.0% | +0.00u |
| VALUE PLAY | 6 | 3-3-0 | 50.0% | 6.00u | -0.27u | -4.5% | -1.18u |

## By Tag - If Every Tag Was Staked 1u

| Bucket | Bets | W-L-P | Win% | Risk | Units | ROI | Max DD |
|---|---:|---:|---:|---:|---:|---:|---:|
| GOM | 10 | 6-3-1 | 66.7% | 10.00u | +2.45u | 24.5% | -1.00u |
| GOW | 12 | 2-10-0 | 16.7% | 12.00u | -8.18u | -68.2% | -8.18u |
| GOY | 49 | 22-25-2 | 46.8% | 49.00u | -5.00u | -10.2% | -8.18u |
| NEUTRAL | 163 | 81-77-5 | 51.3% | 163.00u | -3.36u | -2.1% | -10.27u |
| VALUE PLAY | 6 | 3-3-0 | 50.0% | 6.00u | -0.27u | -4.5% | -1.18u |

## By Season - Action Tags Flat 1u

| Bucket | Bets | W-L-P | Win% | Risk | Units | ROI | Max DD |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2018 | 77 | 33-41-3 | 44.6% | 77.00u | -11.00u | -14.3% | -12.91u |

## By Season - Action Tags Aggressive 1/2/3/4

| Bucket | Bets | W-L-P | Win% | Risk | Units | ROI | Max DD |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2018 | 77 | 33-41-3 | 44.6% | 256.00u | -29.27u | -11.4% | -41.27u |

## Practical Read

- Compare staking plans by max drawdown, not only total units.
- Aggressive staking can look better when GOY/GOM are hot, but it concentrates risk in the highest tier.
- NEUTRAL is treated as 0u stake in tier plans and should remain a no-bet category.
- A staking plan should not be promoted to 2026 real tracking until it survives train/holdout review.
