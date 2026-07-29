# Backtest - variant_m 2025 Week 2-18

This is a historical backtest screen, not prospective edge proof.

Scope:
- Season: 2025
- Weeks: 2-18
- Picks dir: `data\picks_variant_m`
- Market: ATS/spread pick grading using stored `handicap` from pick perspective
- Unit model: flat 1u risk at -110; win +0.9091u, loss -1u, push 0u

Important limitation:
- These historical pick files are backfilled research artifacts, not frozen before kickoff.
- Use this to select candidate filters only. Forward proof still requires prospective ledger.

## By Tag

| Bucket | Bets | W-L-P | Win% | Units | ROI |
|---|---:|---:|---:|---:|---:|
| GOM | 15 | 13-2-0 | 86.7% | +9.82u | 65.5% |
| GOW | 17 | 11-6-0 | 64.7% | +4.00u | 23.5% |
| GOY | 33 | 29-4-0 | 87.9% | +22.36u | 67.8% |
| NEUTRAL | 182 | 72-109-1 | 39.8% | -43.55u | -24.1% |
| VALUE PLAY | 9 | 8-1-0 | 88.9% | +6.27u | 69.7% |

## Action Tags vs Neutral

| Bucket | Bets | W-L-P | Win% | Units | ROI |
|---|---:|---:|---:|---:|---:|
| action_tags | 74 | 61-13-0 | 82.4% | +42.45u | 57.4% |
| neutral | 182 | 72-109-1 | 39.8% | -43.55u | -24.1% |

## By Confidence Bucket

| Bucket | Bets | W-L-P | Win% | Units | ROI |
|---|---:|---:|---:|---:|---:|
| 100-110 | 1 | 1-0-0 | 100.0% | +0.91u | 90.9% |
| 40-50 | 9 | 3-6-0 | 33.3% | -3.27u | -36.4% |
| 50-60 | 26 | 10-15-1 | 40.0% | -5.91u | -23.6% |
| 60-70 | 37 | 21-16-0 | 56.8% | +3.09u | 8.4% |
| 70-80 | 38 | 20-18-0 | 52.6% | +0.18u | 0.5% |
| 80-90 | 37 | 17-20-0 | 45.9% | -4.55u | -12.3% |
| 90-100 | 108 | 61-47-0 | 56.5% | +8.45u | 7.8% |

## By Edge Bucket

| Bucket | Bets | W-L-P | Win% | Units | ROI |
|---|---:|---:|---:|---:|---:|
| 0-2 | 38 | 19-19-0 | 50.0% | -1.73u | -4.5% |
| 10-12 | 30 | 21-9-0 | 70.0% | +10.09u | 33.6% |
| 12+ | 39 | 23-16-0 | 59.0% | +4.91u | 12.6% |
| 2-4 | 54 | 22-32-0 | 40.7% | -12.00u | -22.2% |
| 4-6 | 31 | 16-14-1 | 53.3% | +0.55u | 1.8% |
| 6-8 | 37 | 16-21-0 | 43.2% | -6.45u | -17.4% |
| 8-10 | 27 | 16-11-0 | 59.3% | +3.55u | 13.1% |

## Favorite vs Underdog

| Bucket | Bets | W-L-P | Win% | Units | ROI |
|---|---:|---:|---:|---:|---:|
| favorite | 195 | 97-98-0 | 49.7% | -9.82u | -5.0% |
| underdog | 61 | 36-24-1 | 60.0% | +8.73u | 14.5% |

## Practical Read

- The strongest historical signal is not all model picks. It is the non-NEUTRAL/action-tag subset.
- NEUTRAL was strongly negative in this 2025 screen and should not be treated as a bet category.
- The result is too strong to trust blindly as proof because the files are historical/backfilled, not a timestamped prospective ledger.
- Next useful test: repeat across 2021-2025 with train/holdout split and then promote only stable rules to 2026 forward tracking.
