# Tiered Staking Backtest

This is a historical backtest screen, not prospective edge proof.

Scope:
- Seasons: 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025
- Weeks: 12-17
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
| flat_1u | 299 | 209-83-7 | 71.6% | 299.00u | +107.00u | 35.8% | -10.45u |
| conservative_0.5_1_1.5_2 | 299 | 209-83-7 | 71.6% | 441.50u | +157.95u | 35.8% | -16.59u |
| aggressive_1_2_3_4 | 299 | 209-83-7 | 71.6% | 883.00u | +315.91u | 35.8% | -33.18u |

## By Tag - Action Staking, NEUTRAL 0u

| Bucket | Bets | W-L-P | Win% | Risk | Units | ROI | Max DD |
|---|---:|---:|---:|---:|---:|---:|---:|
| GOM | 56 | 39-17-0 | 69.6% | 56.00u | +18.45u | 33.0% | -4.45u |
| GOW | 70 | 48-20-2 | 70.6% | 70.00u | +23.64u | 33.8% | -5.09u |
| GOY | 134 | 94-36-4 | 72.3% | 134.00u | +49.45u | 36.9% | -4.73u |
| NEUTRAL | 728 | 342-363-23 | 48.5% | 0.00u | +0.00u | 0.0% | +0.00u |
| VALUE PLAY | 39 | 28-10-1 | 73.7% | 39.00u | +15.45u | 39.6% | -3.36u |

## By Tag - If Every Tag Was Staked 1u

| Bucket | Bets | W-L-P | Win% | Risk | Units | ROI | Max DD |
|---|---:|---:|---:|---:|---:|---:|---:|
| GOM | 56 | 39-17-0 | 69.6% | 56.00u | +18.45u | 33.0% | -4.45u |
| GOW | 70 | 48-20-2 | 70.6% | 70.00u | +23.64u | 33.8% | -5.09u |
| GOY | 134 | 94-36-4 | 72.3% | 134.00u | +49.45u | 36.9% | -4.73u |
| NEUTRAL | 728 | 342-363-23 | 48.5% | 728.00u | -52.09u | -7.2% | -53.36u |
| VALUE PLAY | 39 | 28-10-1 | 73.7% | 39.00u | +15.45u | 39.6% | -3.36u |

## By Season - Action Tags Flat 1u

| Bucket | Bets | W-L-P | Win% | Risk | Units | ROI | Max DD |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2015 | 25 | 17-7-1 | 70.8% | 25.00u | +8.45u | 33.8% | -2.09u |
| 2016 | 31 | 17-14-0 | 54.8% | 31.00u | +1.45u | 4.7% | -4.09u |
| 2017 | 32 | 26-6-0 | 81.2% | 32.00u | +17.64u | 55.1% | -1.27u |
| 2018 | 26 | 13-13-0 | 50.0% | 26.00u | -1.18u | -4.5% | -4.55u |
| 2019 | 19 | 8-11-0 | 42.1% | 19.00u | -3.73u | -19.6% | -5.55u |
| 2020 | 32 | 17-12-3 | 58.6% | 32.00u | +3.45u | 10.8% | -3.00u |
| 2021 | 19 | 12-6-1 | 66.7% | 19.00u | +4.91u | 25.8% | -2.00u |
| 2022 | 26 | 24-2-0 | 92.3% | 26.00u | +19.82u | 76.2% | -1.00u |
| 2023 | 34 | 28-4-2 | 87.5% | 34.00u | +21.45u | 63.1% | -1.09u |
| 2024 | 30 | 27-3-0 | 90.0% | 30.00u | +21.55u | 71.8% | -1.00u |
| 2025 | 25 | 20-5-0 | 80.0% | 25.00u | +13.18u | 52.7% | -1.09u |

## By Season - Action Tags Aggressive 1/2/3/4

| Bucket | Bets | W-L-P | Win% | Risk | Units | ROI | Max DD |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2015 | 25 | 17-7-1 | 70.8% | 77.00u | +18.64u | 24.2% | -5.36u |
| 2016 | 31 | 17-14-0 | 54.8% | 90.00u | -4.09u | -4.5% | -13.00u |
| 2017 | 32 | 26-6-0 | 81.2% | 92.00u | +53.09u | 57.7% | -5.27u |
| 2018 | 26 | 13-13-0 | 50.0% | 79.00u | +3.09u | 3.9% | -9.45u |
| 2019 | 19 | 8-11-0 | 42.1% | 60.00u | -16.09u | -26.8% | -21.27u |
| 2020 | 32 | 17-12-3 | 58.6% | 98.00u | +15.91u | 16.2% | -10.00u |
| 2021 | 19 | 12-6-1 | 66.7% | 51.00u | +14.09u | 27.6% | -5.00u |
| 2022 | 26 | 24-2-0 | 92.3% | 71.00u | +49.27u | 69.4% | -4.00u |
| 2023 | 34 | 28-4-2 | 87.5% | 98.00u | +70.27u | 71.7% | -2.00u |
| 2024 | 30 | 27-3-0 | 90.0% | 98.00u | +73.82u | 75.3% | -3.00u |
| 2025 | 25 | 20-5-0 | 80.0% | 69.00u | +37.91u | 54.9% | -4.00u |

## Practical Read

- Compare staking plans by max drawdown, not only total units.
- Aggressive staking can look better when GOY/GOM are hot, but it concentrates risk in the highest tier.
- NEUTRAL is treated as 0u stake in tier plans and should remain a no-bet category.
- A staking plan should not be promoted to 2026 real tracking until it survives train/holdout review.
