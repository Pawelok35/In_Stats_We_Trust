# Strategy Research

## Current Research Rule

`GOM Stable` is stored in `config/strategy_rules/gom_stable.yaml`.

Rule:

- variant: `variant_d_balanced`
- tags: `GOM`
- confidence: `>= 85`
- edge: `>= 0`
- weeks: `>= 3`
- spread filter: `abs(handicap) <= 7`

## Latest Backtest

Generated with:

```powershell
.venv\Scripts\python.exe -m app.cli strategy-report --start-season 2017 --end-season 2025 --output data/results/strategy_search/gom_stable_report.md
```

Summary for seasons 2017-2025:

- Bets: 74
- W-L-P: 61-12-1
- Profit: +128.7u
- ROI: 58.0%
- Worst season: +2.1u
- Max drawdown: -6.3u

## Additional GOM Candidates

Expanded GOM search output:

- `data/results/strategy_search/gom_expanded_candidates.md`

Added fixed strategy rules:

- `config/strategy_rules/gom_stable_edge.yaml`
- `config/strategy_rules/gom_stable_mirror_m.yaml`
- `config/strategy_rules/gom_volume_cap8.yaml`

Candidate comparison for 2017-2025:

| Rule | Bets | W-L-P | Profit | ROI | Worst Season | Max Drawdown |
|---|---:|---:|---:|---:|---:|---:|
| `gom_stable_edge` | 74 | 61-12-1 | +128.7u | 58.0% | +2.1u | -6.3u |
| `gom_stable_mirror_m` | 74 | 61-12-1 | +128.7u | 58.0% | +2.1u | -6.3u |
| `gom_volume_cap8` | 82 | 65-16-1 | +127.5u | 51.8% | +4.8u | -9.3u |

Interpretation:

- `gom_stable_edge` should replace the earlier loose description because `edge>=4` is explicit and does not change the selected historical pick set.
- `gom_stable_mirror_m` is a parity check; on current data it matches `variant_d_balanced`.
- `gom_volume_cap8` is an alternate volume profile, not a better default. It improves worst-season profit but lowers ROI and increases drawdown.

## Early-Down Feature Veto Research

Generated report:

- `data/results/strategy_search/gom_feature_veto_report.md`

Implemented no-leakage early-down features for the current `GOM Stable` champion:

- `early_down_matchup_edge`
- `off_early_down_success_edge`
- `def_early_down_epa_allowed_edge`

Baseline remains:

- Bets: 74
- W-L-P: 61-12-1
- Profit: +128.7u
- ROI: 58.0%
- Worst season: +2.1u
- Max drawdown: -6.3u

Initial veto test:

| Feature Veto | Removed W-L-P | Removed Profit | After Profit | After ROI | Result |
|---|---:|---:|---:|---:|---|
| `early_down_matchup_edge` low-third | 22-2-0 | +53.4u | +75.3u | 50.2% | reject |
| `off_early_down_success_edge` low-third | 23-4-0 | +50.1u | +78.6u | 55.7% | reject |
| `def_early_down_epa_allowed_edge` low-third | 18-2-0 | +42.6u | +86.1u | 53.1% | reject |

Interpretation:

- These features are useful as research columns, but the first simple veto direction is not useful.
- Low early-down feature values removed mostly winners, so they should not be used as a current filter.
- Next feature work should focus on regression/luck and pressure context rather than immediately promoting early-down vetoes.

Second veto round with fixed natural thresholds:

| Veto | Removed W-L-P | Removed Profit | After Profit | After ROI | Result |
|---|---:|---:|---:|---:|---|
| `fumble_recovery_luck_edge >= 0.20` | 3-0-0 | +8.1u | +120.6u | 56.6% | reject |
| `third_down_luck_support >= 0.12 and attempts >= 25` | 1-1-0 | -0.3u | +129.0u | 59.7% | reject |
| `red_zone_luck_support >= 0.20 and trips >= 12` | 0-0-0 | +0.0u | +128.7u | 58.0% | no signal |
| `pressure_matchup_disadvantage >= 0.08` | 0-0-0 | +0.0u | +128.7u | 58.0% | no signal |
| `sack_conversion >= 0.50 and pressure <= league median` | 24-5-1 | +49.8u | +78.9u | 59.8% | reject |

Interpretation:

- No natural-threshold veto beat the current champion profile.
- `third_down_luck_support` is directionally interesting but too small and worsens max drawdown.
- `fumble_recovery_luck_edge` and `sack_conversion` remove too many winners.
- Keep these as research diagnostics only; do not apply them to production picks.

## GOM Calibration Shadow

Generated report:

- `data/results/strategy_search/gom_calibration_shadow_report.md`

Command:

```powershell
.venv\Scripts\python.exe -m app.cli gom-calibration-shadow
```

Purpose:

- Keep `GOM Stable CORE` unchanged.
- Build a near-miss GOM pool outside CORE.
- Score near-miss picks using consensus, margin dispersion, pressure/third-down context, and model residual uncertainty.
- Test whether CORE plus selected near-miss additions can beat CORE.

Near-miss pool definition:

- variant D
- tag `GOM`
- week `>= 3`
- `abs(handicap) <= 8`
- outside CORE
- confidence `80-84` with edge `>= 3`, or edge `3-4` with confidence `>= 80`, or cap8 extension

Result:

| Strategy | Bets | W-L-P | Profit | ROI | Max DD | Decision |
|---|---:|---:|---:|---:|---:|---|
| CORE | 74 | 61-12-1 | +128.7u | 58.0% | -6.3u | champion |
| NEAR-MISS only | 16 | 9-7-0 | +3.3u | 6.9% | -12.3u | weak pool |
| CORE + score>=1.25 top1/season | 80 | 63-16-1 | +122.1u | 50.9% | -9.3u | reject |
| CORE + score>=1.00 top2/season | 84 | 66-17-1 | +127.2u | 50.5% | -6.6u | reject |

Interpretation:

- The current near-miss pool is not good enough.
- The transparent shadow score did not identify profitable additions.
- CORE remains the official champion.
- Keep calibration as a 2026 shadow/diagnostic workflow only.

## Research Rules

- Do not promote a rule based only on 2024-2025 performance.
- Prefer expanding walk-forward checks over one fixed train/holdout split.
- Require every historical season to stay profitable before treating a rule as stable.
- Avoid tiny-sample rules unless they are explicitly marked as exploratory.
- Keep strategy rules in YAML so reports are reproducible.
