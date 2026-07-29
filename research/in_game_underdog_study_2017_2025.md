# In-Game Pregame Underdog Study - 2017_2025

Scope: regular season games only when local schedule data is available.

Important limitation: nfl_data_py does not provide historical executable live moneyline odds. The `fair ML` columns below are converted from nflfastR win probability / vegas win probability proxies.

## Summary

| Snapshot | Cases Led | Avg Lead | SU W-L | SU Win% | ATS W-L | ATS Cover% | Median WP | Median Fair ML | Median Vegas WP | Median Vegas Fair ML |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Q1 | 750 | 6.1 | 397-353 | 52.9% | 532-218 | 70.9% | 66.1% | -195 | 51.9% | -108 |
| H1 | 832 | 8.0 | 527-305 | 63.3% | 667-165 | 80.2% | 73.1% | -272 | 62.5% | -167 |
| Q3 | 802 | 9.1 | 584-218 | 72.8% | 716-86 | 89.3% | 81.0% | -427 | 74.0% | -285 |

## Q3 Live Trigger Map

This table is the closest we can get without true historical live odds. `Break-even live ML` is the worst live moneyline price you could accept based on historical SU win rate for that state. Example: if break-even is `-150`, you need better than -150. If it is `+120`, you need +120 or better.

| Spread Bucket | Lead Bucket | Location | Fair ML Bucket | Cases | SU W-L | SU Win% | Break-even Live ML | Pregame ATS Cover% | Median WP | Median Fair ML | Live Decision Note |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| <=3 | 1-3 | home dog | favorite fair | 32 | 15-17 | 46.9% | +113 | 50.0% | 69.8% | -231 | NO ML - historical win rate too low |
| <=3 | 1-3 | away dog | favorite fair | 30 | 27-3 | 90.0% | -900 | 93.3% | 61.4% | -159 | ML WATCH - only better than -900 |
| <=3 | 1-3 | away dog | plus-money fair | 15 | 7-8 | 46.7% | +114 | 53.3% | 41.4% | +142 | NO BET - sample <30 |
| <=3 | 1-3 | home dog | plus-money fair | 2 | 1-1 | 50.0% | -100 | 100.0% | 44.8% | +123 | NO BET - sample <30 |
| <=3 | 4-7 | away dog | favorite fair | 52 | 36-16 | 69.2% | -225 | 76.9% | 73.8% | -281 | PRICE SENSITIVE ML - only better than -225 |
| <=3 | 4-7 | home dog | favorite fair | 41 | 33-8 | 80.5% | -413 | 82.9% | 76.1% | -318 | ML WATCH - only better than -413 |
| <=3 | 4-7 | away dog | plus-money fair | 1 | 0-1 | 0.0% | n/a | 0.0% | 46.3% | +116 | NO BET - sample <30 |
| <=3 | 8+ | away dog | favorite fair | 101 | 91-10 | 90.1% | -910 | 95.0% | 91.7% | -1099 | ML WATCH - only better than -910 |
| <=3 | 8+ | home dog | favorite fair | 95 | 88-7 | 92.6% | -1257 | 94.7% | 96.3% | -2584 | ML WATCH - only better than -1257 |
| 3.5-7 | 1-3 | away dog | favorite fair | 31 | 16-15 | 51.6% | -107 | 83.9% | 64.0% | -178 | NO ML - historical win rate too low |
| 3.5-7 | 1-3 | home dog | favorite fair | 25 | 13-12 | 52.0% | -108 | 92.0% | 67.6% | -208 | NO BET - sample <30 |
| 3.5-7 | 1-3 | away dog | plus-money fair | 11 | 4-7 | 36.4% | +175 | 63.6% | 41.6% | +140 | NO BET - sample <30 |
| 3.5-7 | 1-3 | home dog | plus-money fair | 3 | 0-3 | 0.0% | n/a | 33.3% | 46.5% | +115 | NO BET - sample <30 |
| 3.5-7 | 4-7 | away dog | favorite fair | 50 | 29-21 | 58.0% | -138 | 88.0% | 70.9% | -244 | PRICE SENSITIVE ML - only better than -138 |
| 3.5-7 | 4-7 | home dog | favorite fair | 37 | 29-8 | 78.4% | -362 | 91.9% | 76.8% | -331 | ML WATCH - only better than -362 |
| 3.5-7 | 4-7 | away dog | plus-money fair | 4 | 1-3 | 25.0% | +300 | 75.0% | 45.7% | +119 | NO BET - sample <30 |
| 3.5-7 | 8+ | away dog | favorite fair | 85 | 75-10 | 88.2% | -750 | 98.8% | 91.7% | -1110 | ML WATCH - only better than -750 |
| 3.5-7 | 8+ | home dog | favorite fair | 50 | 41-9 | 82.0% | -456 | 96.0% | 92.1% | -1164 | ML WATCH - only better than -456 |
| 7.5+ | 1-3 | away dog | favorite fair | 21 | 9-12 | 42.9% | +133 | 95.2% | 61.1% | -157 | NO BET - sample <30 |
| 7.5+ | 1-3 | home dog | favorite fair | 13 | 9-4 | 69.2% | -225 | 100.0% | 62.1% | -164 | NO BET - sample <30 |
| 7.5+ | 1-3 | away dog | plus-money fair | 11 | 3-8 | 27.3% | +267 | 81.8% | 39.6% | +152 | NO BET - sample <30 |
| 7.5+ | 1-3 | home dog | plus-money fair | 2 | 1-1 | 50.0% | -100 | 50.0% | 46.2% | +116 | NO BET - sample <30 |
| 7.5+ | 4-7 | away dog | favorite fair | 31 | 17-14 | 54.8% | -121 | 96.8% | 71.9% | -256 | NO ML - historical win rate too low |
| 7.5+ | 4-7 | home dog | favorite fair | 10 | 3-7 | 30.0% | +233 | 100.0% | 77.3% | -343 | NO BET - sample <30 |
| 7.5+ | 4-7 | away dog | plus-money fair | 2 | 0-2 | 0.0% | n/a | 100.0% | 45.2% | +121 | NO BET - sample <30 |
| 7.5+ | 8+ | away dog | favorite fair | 32 | 25-7 | 78.1% | -357 | 100.0% | 91.7% | -1114 | ML WATCH - only better than -357 |
| 7.5+ | 8+ | home dog | favorite fair | 15 | 11-4 | 73.3% | -275 | 100.0% | 88.8% | -791 | NO BET - sample <30 |

## Interpretation

- `Q1`, `H1`, and `Q3` mean the underdog was leading at the end of that game segment.
- `SU Win%` shows how often the pregame underdog finished the upset after leading.
- `ATS Cover%` shows how often the pregame underdog covered the original pregame spread.
- `Median Fair ML` is not a historical live book line. It is the no-vig fair moneyline implied by the model win probability.
- `Break-even live ML` is based on realized historical SU win rate in that bucket, not on available book prices.
- `Live Decision Note` is intentionally conservative: it only marks a moneyline watch state when the bucket has at least 30 historical cases.
- This does not choose a live spread because archived live spread lines are not present in nfl_data_py.
- This report can identify live states worth monitoring; it cannot prove live betting profit without archived live odds.

## Detail Export

CSV detail: `research\in_game_underdog_study_2017_2025.csv`
