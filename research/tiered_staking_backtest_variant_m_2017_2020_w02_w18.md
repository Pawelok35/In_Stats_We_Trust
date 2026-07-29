# Tiered Staking Backtest

This is a historical backtest screen, not prospective edge proof.

Scope:
- Seasons: 2017, 2018, 2019, 2020
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
| flat_1u | 305 | 174-124-7 | 58.4% | 305.00u | +34.18u | 11.2% | -23.00u |
| conservative_0.5_1_1.5_2 | 305 | 174-124-7 | 58.4% | 486.50u | +59.95u | 12.3% | -36.23u |
| aggressive_1_2_3_4 | 305 | 174-124-7 | 58.4% | 973.00u | +119.91u | 12.3% | -72.45u |

## By Tag - Action Staking, NEUTRAL 0u

| Bucket | Bets | W-L-P | Win% | Risk | Units | ROI | Max DD |
|---|---:|---:|---:|---:|---:|---:|---:|
| GOM | 51 | 32-18-1 | 64.0% | 51.00u | +11.09u | 21.7% | -5.27u |
| GOW | 59 | 30-27-2 | 52.6% | 59.00u | +0.27u | 0.5% | -10.82u |
| GOY | 169 | 98-68-3 | 59.0% | 169.00u | +21.09u | 12.5% | -15.45u |
| NEUTRAL | 653 | 291-339-23 | 46.2% | 0.00u | +0.00u | 0.0% | +0.00u |
| VALUE PLAY | 26 | 14-11-1 | 56.0% | 26.00u | +1.73u | 6.6% | -3.36u |

## By Tag - If Every Tag Was Staked 1u

| Bucket | Bets | W-L-P | Win% | Risk | Units | ROI | Max DD |
|---|---:|---:|---:|---:|---:|---:|---:|
| GOM | 51 | 32-18-1 | 64.0% | 51.00u | +11.09u | 21.7% | -5.27u |
| GOW | 59 | 30-27-2 | 52.6% | 59.00u | +0.27u | 0.5% | -10.82u |
| GOY | 169 | 98-68-3 | 59.0% | 169.00u | +21.09u | 12.5% | -15.45u |
| NEUTRAL | 653 | 291-339-23 | 46.2% | 653.00u | -74.45u | -11.4% | -81.55u |
| VALUE PLAY | 26 | 14-11-1 | 56.0% | 26.00u | +1.73u | 6.6% | -3.36u |

## By Season - Action Tags Flat 1u

| Bucket | Bets | W-L-P | Win% | Risk | Units | ROI | Max DD |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2017 | 80 | 68-12-0 | 85.0% | 80.00u | +49.82u | 62.3% | -1.27u |
| 2018 | 77 | 33-41-3 | 44.6% | 77.00u | -11.00u | -14.3% | -12.91u |
| 2019 | 65 | 30-34-1 | 46.9% | 65.00u | -6.73u | -10.3% | -8.09u |
| 2020 | 83 | 43-37-3 | 53.8% | 83.00u | +2.09u | 2.5% | -8.09u |

## By Season - Action Tags Aggressive 1/2/3/4

| Bucket | Bets | W-L-P | Win% | Risk | Units | ROI | Max DD |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2017 | 80 | 68-12-0 | 85.0% | 240.00u | +162.82u | 67.8% | -5.27u |
| 2018 | 77 | 33-41-3 | 44.6% | 256.00u | -29.27u | -11.4% | -41.27u |
| 2019 | 65 | 30-34-1 | 46.9% | 216.00u | -26.91u | -12.5% | -32.64u |
| 2020 | 83 | 43-37-3 | 53.8% | 261.00u | +13.27u | 5.1% | -26.45u |

## Practical Read

- Compare staking plans by max drawdown, not only total units.
- Aggressive staking can look better when GOY/GOM are hot, but it concentrates risk in the highest tier.
- NEUTRAL is treated as 0u stake in tier plans and should remain a no-bet category.
- A staking plan should not be promoted to 2026 real tracking until it survives train/holdout review.
