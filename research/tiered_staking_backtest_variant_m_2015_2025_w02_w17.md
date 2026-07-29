# Tiered Staking Backtest

This is a historical backtest screen, not prospective edge proof.

Scope:
- Seasons: 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025
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
| flat_1u | 804 | 529-260-15 | 67.0% | 804.00u | +220.91u | 27.5% | -23.00u |
| conservative_0.5_1_1.5_2 | 804 | 529-260-15 | 67.0% | 1253.00u | +336.00u | 26.8% | -37.18u |
| aggressive_1_2_3_4 | 804 | 529-260-15 | 67.0% | 2506.00u | +672.00u | 26.8% | -74.36u |

## By Tag - Action Staking, NEUTRAL 0u

| Bucket | Bets | W-L-P | Win% | Risk | Units | ROI | Max DD |
|---|---:|---:|---:|---:|---:|---:|---:|
| GOM | 136 | 96-38-2 | 71.6% | 136.00u | +49.27u | 36.2% | -5.36u |
| GOW | 173 | 114-56-3 | 67.1% | 173.00u | +47.64u | 27.5% | -10.82u |
| GOY | 419 | 268-142-9 | 65.4% | 419.00u | +101.64u | 24.3% | -17.91u |
| NEUTRAL | 1833 | 820-953-60 | 46.2% | 0.00u | +0.00u | 0.0% | +0.00u |
| VALUE PLAY | 76 | 51-24-1 | 68.0% | 76.00u | +22.36u | 29.4% | -5.18u |

## By Tag - If Every Tag Was Staked 1u

| Bucket | Bets | W-L-P | Win% | Risk | Units | ROI | Max DD |
|---|---:|---:|---:|---:|---:|---:|---:|
| GOM | 136 | 96-38-2 | 71.6% | 136.00u | +49.27u | 36.2% | -5.36u |
| GOW | 173 | 114-56-3 | 67.1% | 173.00u | +47.64u | 27.5% | -10.82u |
| GOY | 419 | 268-142-9 | 65.4% | 419.00u | +101.64u | 24.3% | -17.91u |
| NEUTRAL | 1833 | 820-953-60 | 46.2% | 1833.00u | -207.55u | -11.3% | -212.55u |
| VALUE PLAY | 76 | 51-24-1 | 68.0% | 76.00u | +22.36u | 29.4% | -5.18u |

## By Season - Action Tags Flat 1u

| Bucket | Bets | W-L-P | Win% | Risk | Units | ROI | Max DD |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2015 | 79 | 40-35-4 | 53.3% | 79.00u | +1.36u | 1.7% | -13.55u |
| 2016 | 78 | 43-35-0 | 55.1% | 78.00u | +4.09u | 5.2% | -10.27u |
| 2017 | 80 | 68-12-0 | 85.0% | 80.00u | +49.82u | 62.3% | -1.27u |
| 2018 | 77 | 33-41-3 | 44.6% | 77.00u | -11.00u | -14.3% | -12.91u |
| 2019 | 65 | 30-34-1 | 46.9% | 65.00u | -6.73u | -10.3% | -8.09u |
| 2020 | 83 | 43-37-3 | 53.8% | 83.00u | +2.09u | 2.5% | -8.09u |
| 2021 | 74 | 39-34-1 | 53.4% | 74.00u | +1.45u | 2.0% | -9.27u |
| 2022 | 54 | 46-8-0 | 85.2% | 54.00u | +33.82u | 62.6% | -2.00u |
| 2023 | 79 | 69-7-3 | 90.8% | 79.00u | +55.73u | 70.5% | -1.09u |
| 2024 | 66 | 61-5-0 | 92.4% | 66.00u | +50.45u | 76.4% | -1.00u |
| 2025 | 69 | 57-12-0 | 82.6% | 69.00u | +39.82u | 57.7% | -2.00u |

## By Season - Action Tags Aggressive 1/2/3/4

| Bucket | Bets | W-L-P | Win% | Risk | Units | ROI | Max DD |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2015 | 79 | 40-35-4 | 53.3% | 263.00u | -0.73u | -0.3% | -46.73u |
| 2016 | 78 | 43-35-0 | 55.1% | 233.00u | +5.64u | 2.4% | -31.00u |
| 2017 | 80 | 68-12-0 | 85.0% | 240.00u | +162.82u | 67.8% | -5.27u |
| 2018 | 77 | 33-41-3 | 44.6% | 256.00u | -29.27u | -11.4% | -41.27u |
| 2019 | 65 | 30-34-1 | 46.9% | 216.00u | -26.91u | -12.5% | -32.64u |
| 2020 | 83 | 43-37-3 | 53.8% | 261.00u | +13.27u | 5.1% | -26.45u |
| 2021 | 74 | 39-34-1 | 53.4% | 232.00u | -8.45u | -3.6% | -34.73u |
| 2022 | 54 | 46-8-0 | 85.2% | 148.00u | +86.82u | 58.7% | -6.00u |
| 2023 | 79 | 69-7-3 | 90.8% | 246.00u | +181.09u | 73.6% | -4.00u |
| 2024 | 66 | 61-5-0 | 92.4% | 208.00u | +166.18u | 79.9% | -3.00u |
| 2025 | 69 | 57-12-0 | 82.6% | 203.00u | +121.55u | 59.9% | -6.00u |

## Practical Read

- Compare staking plans by max drawdown, not only total units.
- Aggressive staking can look better when GOY/GOM are hot, but it concentrates risk in the highest tier.
- NEUTRAL is treated as 0u stake in tier plans and should remain a no-bet category.
- A staking plan should not be promoted to 2026 real tracking until it survives train/holdout review.
