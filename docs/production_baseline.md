# Production Baseline - Main NFL Pick Pipeline

Generated: 2026-07-29

Status: `PRODUCTION_READY` for the main pick pipeline only.

## Production Scope

The production-ready claim applies only to:

```text
L2
-> L3
-> rolling/Core12
-> report/analyzer
-> preflight
-> matchup_batch
-> pick
```

It does not apply to research tools, Live Scenario, experimental GUI files, or ad hoc backtest utilities outside this path.

## Data Sources

| Source | Provider | Local files | Consumer |
| --- | --- | --- | --- |
| Play-by-play | nflverse/nfl_data_py filesystem cache | `data/l1`, `data/l2` | L2/L3 ETL |
| Team-week metrics | Local ETL | `data/l3_team_week/{season}/{week}.parquet` | rolling windows, Core12, preflight |
| Rolling/Core12 | Local metrics pipeline | `data/rolling_core12`, `data/l4_core12` | reports, analyzer, PowerScore |
| PowerScore | Local Core12 + config weights | `data/l4_powerscore` | report/analyzer |
| Market lines | Manual/book snapshot converted to config | `config/lines/{season}/week{week}_lines.yaml` | matchup reports, batch |
| Model reports | Local markdown reports | `data/reports/comparisons/...` | `scripts/matchup_analyzer.py` |

See also `config/data_sources.yaml`.

## Required Metrics

Required L3 model metrics:

- `epa_off_mean`
- `epa_def_mean`
- `success_rate_off`
- `success_rate_def`
- `ypp_off`
- `ypp_def`
- `ypp_diff`
- `tempo`

Required Core12/model metrics:

- `core_epa_off`
- `core_epa_def`
- `core_sr_off`
- `core_sr_def`
- `core_ypp_diff`

Required analyzer inputs:

- PowerScore model components
- Success Rate Offense
- Turnover Margin
- Pressure Rate

Missing required metrics block pick generation.

## Optional Metrics

Optional/context metrics may warn and be omitted without creating a fake neutral value:

- pass/rush success splits
- pressure allowed / pressure context
- explosive play rates
- third-down rates
- red-zone rates
- points-per-drive rates/diff
- field-position metrics
- trend summary
- analog context

## Cutoff Policy

- Source weeks must satisfy `source_week < analysis_week`.
- Safe rolling snapshots must not include the analysis week or future weeks.
- Preflight validates L3 source files for weeks before the analysis week and validates the selected rolling snapshot.
- Timestamp cutoff support exists in `utils.data_cutoff.validate_pre_game_cutoff`, but the current main model workflow primarily enforces week-based cutoff.
- Unsafe bypass is only available as `--unsafe-test-only-bypass`; such output is never production eligible.

## Missing Data Policy

Null means unavailable/missing and must not become a neutral model value.

Valid zero examples:

- event flags such as no turnover on a valid play,
- counts such as zero conversions on five valid attempts,
- a true rate of `0 / n = 0.0` when `n > 0`.

Invalid zero examples:

- missing EPA -> `0.0`,
- missing success rate -> `0.0`,
- missing yards-per-play side -> zeroed diff,
- `0 / 0 -> 0.0`,
- missing required report value -> neutral component.

Third-down policy:

- `down == 3` and valid positive `distance` -> eligible attempt,
- missing/null/invalid `distance` -> not eligible,
- no eligible attempts -> third-down rate is `null`, not `0.0`.

## Production Backtest Baseline

Champion CORE:

```text
variant_d_balanced
confidence >= 85
edge_vs_line >= 4
week >= 3
abs(handicap) <= 7
seasons 2017-2025
```

Baseline and current confirmed result:

```text
74 bets
61-12-1
+128.70u
Risk 222.00u
ROI 58.0%
Max DD -6.30u
Worst season +2.1u
```

## Test Baseline

Commands:

```powershell
.\.venv\Scripts\python.exe -m pytest --collect-only
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check <production changed files>
.\.venv\Scripts\python.exe -m ruff check .
```

Current discovery:

```text
237 tests collected
237 passed
0 skipped
0 deselected
```

Full `ruff check .` still reports six pre-existing import-order issues outside the production changes:

- `scripts/analyze_quarter_paths.py`
- `scripts/argument_against_auto.py`
- `scripts/build_edge_proof_dossier.py`
- `scripts/live_watch_card.py`
- `scripts/variant_b_learning_ledger.py`
- `scripts/variant_b_post_event_evaluation.py`

## Exclusions

Not covered by this production baseline:

- `live_scenario/*`
- `tests/test_live_scenario_forum_formatter.py`
- `research/live_scenario_v2/gui/*`
- research/backtest exploration scripts not called by the main pick pipeline
- GUI-only operator tooling unless it directly invokes the production batch

## Known Technical Debt

- Six old Ruff import-order issues listed above.
- No configured mypy/pyright type-checking gate.
- Some research/backtest/Live Scenario scripts still contain fallback zeros for counts, samples, or historical summaries; these are outside the production pick pipeline.
- Market lines remain manual/book-snapshot inputs.
