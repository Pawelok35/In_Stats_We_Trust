# Season Phase Staking Backtest

This is a historical backtest screen, not prospective edge proof.

Seasons: 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025
Phases:
- early_w2_w5
- middle_w6_w11
- late_w12_w17

## Staking Plans

| Plan | Early W2-5 | Middle W6-11 | Late W12-17 |
|---|---|---|---|
| tracking | VP 0.0, GOW 0.0, GOM 0.0, GOY 0.0 | VP 0.5, GOW 0.5, GOM 0.5, GOY 0.5 | VP 0.5, GOW 1.0, GOM 1.0, GOY 1.0 |
| flat_by_phase | VP 0.5, GOW 0.5, GOM 0.5, GOY 0.5 | VP 1.0, GOW 1.0, GOM 1.0, GOY 1.0 | VP 1.0, GOW 1.0, GOM 1.0, GOY 1.0 |
| conservative_phase | VP 0.0, GOW 0.5, GOM 0.5, GOY 0.5 | VP 0.5, GOW 0.75, GOM 1.0, GOY 1.0 | VP 0.5, GOW 1.0, GOM 1.5, GOY 2.0 |
| balanced_phase | VP 0.25, GOW 0.5, GOM 0.75, GOY 1.0 | VP 0.5, GOW 1.0, GOM 1.25, GOY 1.5 | VP 0.75, GOW 1.0, GOM 1.5, GOY 2.0 |
| late_aggressive | VP 0.0, GOW 0.0, GOM 0.0, GOY 0.0 | VP 0.5, GOW 1.0, GOM 1.0, GOY 1.0 | VP 1.0, GOW 2.0, GOM 3.0, GOY 4.0 |
| selected_phase_tier | VP 0.25, GOW 0.5, GOM 0.75, GOY 1.0 | VP 0.5, GOW 1.0, GOM 1.25, GOY 1.5 | VP 1.0, GOW 2.0, GOM 3.0, GOY 4.0 |

## Overall By Plan

| Plan | Bets | W-L-P | Win% | Risk | Units | ROI | Max DD | Max Loss Streak |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| tracking | 585 | 398-174-13 | 69.6% | 422.50u | +139.68u | 33.1% | -10.45u | 7 |
| flat_by_phase | 804 | 529-260-15 | 67.0% | 694.50u | +204.36u | 29.4% | -15.73u | 7 |
| conservative_phase | 791 | 521-255-15 | 67.1% | 802.25u | +246.86u | 30.8% | -18.23u | 8 |
| balanced_phase | 804 | 529-260-15 | 67.0% | 994.00u | +290.09u | 29.2% | -23.61u | 7 |
| late_aggressive | 585 | 398-174-13 | 69.6% | 1157.00u | +394.41u | 34.1% | -31.82u | 7 |
| selected_phase_tier | 804 | 529-260-15 | 67.0% | 1425.75u | +444.18u | 31.2% | -35.86u | 7 |

## early_w2_w5

| Plan | Bets | W-L-P | Win% | Risk | Units | ROI | Max DD | Max Loss Streak |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| tracking | 0 | 0-0-0 | 0.0% | 0.00u | +0.00u | 0.0% | +0.00u | 0 |
| flat_by_phase | 219 | 131-86-2 | 60.4% | 109.50u | +16.55u | 15.1% | -9.14u | 6 |
| conservative_phase | 206 | 123-81-2 | 60.3% | 103.00u | +15.41u | 15.0% | -9.09u | 8 |
| balanced_phase | 219 | 131-86-2 | 60.4% | 183.00u | +26.61u | 14.5% | -17.05u | 6 |
| late_aggressive | 0 | 0-0-0 | 0.0% | 0.00u | +0.00u | 0.0% | +0.00u | 0 |
| selected_phase_tier | 219 | 131-86-2 | 60.4% | 183.00u | +26.61u | 14.5% | -17.05u | 6 |

## middle_w6_w11

| Plan | Bets | W-L-P | Win% | Risk | Units | ROI | Max DD | Max Loss Streak |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| tracking | 286 | 189-91-6 | 67.5% | 143.00u | +40.41u | 28.3% | -6.32u | 7 |
| flat_by_phase | 286 | 189-91-6 | 67.5% | 286.00u | +80.82u | 28.3% | -12.64u | 7 |
| conservative_phase | 286 | 189-91-6 | 67.5% | 257.75u | +73.50u | 28.5% | -12.05u | 7 |
| balanced_phase | 286 | 189-91-6 | 67.5% | 359.75u | +101.66u | 28.3% | -17.27u | 7 |
| late_aggressive | 286 | 189-91-6 | 67.5% | 274.00u | +78.50u | 28.6% | -12.59u | 7 |
| selected_phase_tier | 286 | 189-91-6 | 67.5% | 359.75u | +101.66u | 28.3% | -17.27u | 7 |

## late_w12_w17

| Plan | Bets | W-L-P | Win% | Risk | Units | ROI | Max DD | Max Loss Streak |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| tracking | 299 | 209-83-7 | 71.6% | 279.50u | +99.27u | 35.5% | -10.82u | 4 |
| flat_by_phase | 299 | 209-83-7 | 71.6% | 299.00u | +107.00u | 35.8% | -10.45u | 4 |
| conservative_phase | 299 | 209-83-7 | 71.6% | 441.50u | +157.95u | 35.8% | -16.59u | 4 |
| balanced_phase | 299 | 209-83-7 | 71.6% | 451.25u | +161.82u | 35.9% | -16.16u | 4 |
| late_aggressive | 299 | 209-83-7 | 71.6% | 883.00u | +315.91u | 35.8% | -33.18u | 4 |
| selected_phase_tier | 299 | 209-83-7 | 71.6% | 883.00u | +315.91u | 35.8% | -33.18u | 4 |

## Practical Recommendation

- Use phase-aware staking only as forward tracking until prospective ledger confirms it.
- The main risk control is not only unit size, but also max weekly exposure and skipping NEUTRAL.
- Late-season aggressive looks attractive historically, but it still creates larger drawdowns when a bad cluster appears.
