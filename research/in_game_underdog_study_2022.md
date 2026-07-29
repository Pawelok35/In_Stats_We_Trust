# In-Game Pregame Underdog Study - 2022

Scope: regular season games only when local schedule data is available.

Important limitation: nfl_data_py does not provide historical executable live moneyline odds. The `fair ML` columns below are converted from nflfastR win probability / vegas win probability proxies.

## Summary

| Snapshot | Cases Led | Avg Lead | SU W-L | SU Win% | ATS W-L | ATS Cover% | Median WP | Median Fair ML | Median Vegas WP | Median Vegas Fair ML |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Q1 | 95 | 5.9 | 41-54 | 43.2% | 62-33 | 65.3% | 66.4% | -198 | 54.4% | -119 |
| H1 | 102 | 7.2 | 55-47 | 53.9% | 75-27 | 73.5% | 72.4% | -262 | 60.7% | -154 |
| Q3 | 91 | 8.4 | 56-35 | 61.5% | 78-13 | 85.7% | 76.6% | -328 | 70.6% | -240 |

## Interpretation

- `Q1`, `H1`, and `Q3` mean the underdog was leading at the end of that game segment.
- `SU Win%` shows how often the pregame underdog finished the upset after leading.
- `ATS Cover%` shows how often the pregame underdog covered the original pregame spread.
- `Median Fair ML` is not a historical live book line. It is the no-vig fair moneyline implied by the model win probability.

## Detail Export

CSV detail: `research\in_game_underdog_study_2022.csv`
