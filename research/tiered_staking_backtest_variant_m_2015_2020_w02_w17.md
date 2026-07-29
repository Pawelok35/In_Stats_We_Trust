# Tiered Staking Backtest

This is a historical backtest screen, not prospective edge proof.

Scope:
- Seasons: 2015, 2016, 2017, 2018, 2019, 2020
- Weeks: 2-17
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
| flat_1u | 462 | 257-194-11 | 57.0% | 462.00u | +39.64u | 8.6% | -23.00u |
| conservative_0.5_1_1.5_2 | 462 | 257-194-11 | 57.0% | 734.50u | +62.41u | 8.5% | -36.23u |
| aggressive_1_2_3_4 | 462 | 257-194-11 | 57.0% | 1469.00u | +124.82u | 8.5% | -72.45u |

## By Tag - Action Staking, NEUTRAL 0u

| Bucket | Bets | W-L-P | Win% | Risk | Units | ROI | Max DD |
|---|---:|---:|---:|---:|---:|---:|---:|
| GOM | 71 | 46-24-1 | 65.7% | 71.00u | +17.82u | 25.1% | -5.27u |
| GOW | 88 | 47-39-2 | 54.7% | 88.00u | +3.73u | 4.2% | -10.82u |
| GOY | 259 | 140-112-7 | 55.6% | 259.00u | +15.27u | 5.9% | -15.45u |
| NEUTRAL | 976 | 443-501-32 | 46.9% | 0.00u | +0.00u | 0.0% | +0.00u |
| VALUE PLAY | 44 | 24-19-1 | 55.8% | 44.00u | +2.82u | 6.4% | -3.36u |

## By Tag - If Every Tag Was Staked 1u

| Bucket | Bets | W-L-P | Win% | Risk | Units | ROI | Max DD |
|---|---:|---:|---:|---:|---:|---:|---:|
| GOM | 71 | 46-24-1 | 65.7% | 71.00u | +17.82u | 25.1% | -5.27u |
| GOW | 88 | 47-39-2 | 54.7% | 88.00u | +3.73u | 4.2% | -10.82u |
| GOY | 259 | 140-112-7 | 55.6% | 259.00u | +15.27u | 5.9% | -15.45u |
| NEUTRAL | 976 | 443-501-32 | 46.9% | 976.00u | -98.27u | -10.1% | -109.45u |
| VALUE PLAY | 44 | 24-19-1 | 55.8% | 44.00u | +2.82u | 6.4% | -3.36u |

## By Season - Action Tags Flat 1u

| Bucket | Bets | W-L-P | Win% | Risk | Units | ROI | Max DD |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2015 | 79 | 40-35-4 | 53.3% | 79.00u | +1.36u | 1.7% | -13.55u |
| 2016 | 78 | 43-35-0 | 55.1% | 78.00u | +4.09u | 5.2% | -10.27u |
| 2017 | 80 | 68-12-0 | 85.0% | 80.00u | +49.82u | 62.3% | -1.27u |
| 2018 | 77 | 33-41-3 | 44.6% | 77.00u | -11.00u | -14.3% | -12.91u |
| 2019 | 65 | 30-34-1 | 46.9% | 65.00u | -6.73u | -10.3% | -8.09u |
| 2020 | 83 | 43-37-3 | 53.8% | 83.00u | +2.09u | 2.5% | -8.09u |

## By Season - Action Tags Aggressive 1/2/3/4

| Bucket | Bets | W-L-P | Win% | Risk | Units | ROI | Max DD |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2015 | 79 | 40-35-4 | 53.3% | 263.00u | -0.73u | -0.3% | -46.73u |
| 2016 | 78 | 43-35-0 | 55.1% | 233.00u | +5.64u | 2.4% | -31.00u |
| 2017 | 80 | 68-12-0 | 85.0% | 240.00u | +162.82u | 67.8% | -5.27u |
| 2018 | 77 | 33-41-3 | 44.6% | 256.00u | -29.27u | -11.4% | -41.27u |
| 2019 | 65 | 30-34-1 | 46.9% | 216.00u | -26.91u | -12.5% | -32.64u |
| 2020 | 83 | 43-37-3 | 53.8% | 261.00u | +13.27u | 5.1% | -26.45u |

## Practical Read

- Compare staking plans by max drawdown, not only total units.
- Aggressive staking can look better when GOY/GOM are hot, but it concentrates risk in the highest tier.
- NEUTRAL is treated as 0u stake in tier plans and should remain a no-bet category.
- A staking plan should not be promoted to 2026 real tracking until it survives train/holdout review.
