# Tiered Staking Backtest

This is a historical backtest screen, not prospective edge proof.

Scope:
- Seasons: 2021, 2022, 2023, 2024, 2025
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
| flat_1u | 365 | 289-72-4 | 80.1% | 365.00u | +190.73u | 52.3% | -9.27u |
| conservative_0.5_1_1.5_2 | 365 | 289-72-4 | 80.1% | 556.00u | +290.50u | 52.2% | -17.36u |
| aggressive_1_2_3_4 | 365 | 289-72-4 | 80.1% | 1112.00u | +581.00u | 52.2% | -34.73u |

## By Tag - Action Staking, NEUTRAL 0u

| Bucket | Bets | W-L-P | Win% | Risk | Units | ROI | Max DD |
|---|---:|---:|---:|---:|---:|---:|---:|
| GOM | 69 | 54-14-1 | 79.4% | 69.00u | +35.09u | 50.9% | -4.27u |
| GOW | 90 | 69-20-1 | 77.5% | 90.00u | +42.73u | 47.5% | -2.00u |
| GOY | 173 | 138-33-2 | 80.7% | 173.00u | +92.45u | 53.4% | -9.91u |
| NEUTRAL | 914 | 397-488-29 | 44.9% | 0.00u | +0.00u | 0.0% | +0.00u |
| VALUE PLAY | 33 | 28-5-0 | 84.8% | 33.00u | +20.45u | 62.0% | -2.09u |

## By Tag - If Every Tag Was Staked 1u

| Bucket | Bets | W-L-P | Win% | Risk | Units | ROI | Max DD |
|---|---:|---:|---:|---:|---:|---:|---:|
| GOM | 69 | 54-14-1 | 79.4% | 69.00u | +35.09u | 50.9% | -4.27u |
| GOW | 90 | 69-20-1 | 77.5% | 90.00u | +42.73u | 47.5% | -2.00u |
| GOY | 173 | 138-33-2 | 80.7% | 173.00u | +92.45u | 53.4% | -9.91u |
| NEUTRAL | 914 | 397-488-29 | 44.9% | 914.00u | -127.09u | -13.9% | -128.00u |
| VALUE PLAY | 33 | 28-5-0 | 84.8% | 33.00u | +20.45u | 62.0% | -2.09u |

## By Season - Action Tags Flat 1u

| Bucket | Bets | W-L-P | Win% | Risk | Units | ROI | Max DD |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2021 | 82 | 42-39-1 | 51.9% | 82.00u | -0.82u | -1.0% | -9.27u |
| 2022 | 56 | 48-8-0 | 85.7% | 56.00u | +35.64u | 63.6% | -2.00u |
| 2023 | 82 | 72-7-3 | 91.1% | 82.00u | +58.45u | 71.3% | -1.09u |
| 2024 | 71 | 66-5-0 | 93.0% | 71.00u | +55.00u | 77.5% | -1.00u |
| 2025 | 74 | 61-13-0 | 82.4% | 74.00u | +42.45u | 57.4% | -2.00u |

## By Season - Action Tags Aggressive 1/2/3/4

| Bucket | Bets | W-L-P | Win% | Risk | Units | ROI | Max DD |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2021 | 82 | 42-39-1 | 51.9% | 256.00u | -17.18u | -6.7% | -34.73u |
| 2022 | 56 | 48-8-0 | 85.7% | 156.00u | +94.09u | 60.3% | -6.00u |
| 2023 | 82 | 72-7-3 | 91.1% | 256.00u | +190.18u | 74.3% | -4.00u |
| 2024 | 71 | 66-5-0 | 93.0% | 224.00u | +180.73u | 80.7% | -3.00u |
| 2025 | 74 | 61-13-0 | 82.4% | 220.00u | +133.18u | 60.5% | -6.00u |

## Practical Read

- Compare staking plans by max drawdown, not only total units.
- Aggressive staking can look better when GOY/GOM are hot, but it concentrates risk in the highest tier.
- NEUTRAL is treated as 0u stake in tier plans and should remain a no-bet category.
- A staking plan should not be promoted to 2026 real tracking until it survives train/holdout review.
