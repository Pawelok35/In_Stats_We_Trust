# Current System Audit - 2026-08-01

Scope: audit only. No code or pipeline logic was changed.

Repository state checked on 2026-08-01:

- Current branch/head: `main` at `e5338c25dea74f07fd7097ebf501b1b3efd22288` (`updatebot`).
- Frozen production tag: `production-pipeline-baseline-2026-07-29` at `5216a330d8c23d11fd7acc67ee11cfb2ab390c88`.
- Working tree: one modified generated/research artifact: `research/live_scenario_v2/gui/2015_2025_CHI_vs_CAR_after_q2.json`.
- Current test status: `244 passed`.
- Current lint status: `ruff check .` fails on 6 pre-existing import-order issues listed in `docs/production_baseline.md`.

## 1. Repository Map

Main directories:

| Area | Purpose | Key files |
| --- | --- | --- |
| `app/` | CLI, reports, sync commands, API | `app/cli.py`, `app/reports.py`, `app/nfl_data_sync.py`, `app/api.py` |
| `etl/` | L1/L2/L3 data pipeline | `etl/l1_ingest.py`, `etl/l2_clean.py`, `etl/l3_aggregate.py`, `etl/mappers.py` |
| `metrics/` | Core12, PowerScore, rolling/backtest/research metrics | `metrics/core12.py`, `metrics/power_score.py`, `metrics/ats_features.py`, `metrics/strategy_search.py` |
| `utils/` | contracts, paths, config, guards, manifests, cutoff/preflight | `utils/data_cutoff.py`, `utils/preflight.py`, `utils/model_metrics.py` |
| `scripts/` | operational scripts and research workflows | `scripts/matchup_batch.py`, `scripts/prospective_week_flow.py`, `scripts/variant_b_week_flow.py`, `scripts/variant_b_daily_bot_gui.py` |
| `live_scenario/` | Live Scenario V2 backend, week game selector and formatter | `live_scenario/service.py`, `live_scenario/dataset.py`, `live_scenario/week_games.py`, `live_scenario/forum_formatter.py` |
| `config/` | settings, contracts, bot config, lines, strategy/tag rules | `config/settings.yaml`, `config/contracts.yaml`, `config/data_sources.yaml`, `config/variant_b_daily_bot.yaml` |
| `data/` | local source cache and generated artifacts | `data/l1`, `data/l2`, `data/l3_team_week`, `data/l4_core12`, `data/picks_*`, `data/live_scenario` |
| `research/` | GPT snapshots, Variant B audits, daily bot reports, simulations | `research/gpt_snapshots`, `research/variant_b_week_flow`, `research/daily_bot` |
| `tests/` | unit, integration and workflow tests | 48 test files, 244 tests collected |

## 2. Production Pick Pipeline

Production scope is explicitly frozen in `docs/production_baseline.md` as:

```text
L2 -> L3 -> rolling/Core12 -> report/analyzer -> preflight -> matchup_batch -> pick output
```

Implementation path:

1. L1 ingest:
   - `etl/l1_ingest.py:42` defines `run(season, week, source_override=None)`.
   - Current default provider in `config/settings.yaml:5` is `filesystem`.
   - Optional nfl_data_py adapter exists in `etl/sources/nfl_data_py.py:76`, using `nfl_data_py.import_pbp_data([season])` at `etl/sources/nfl_data_py.py:95`.

2. L2 clean:
   - `etl/l2_clean.py:21` defines `run`.
   - It calls `prepare_l2` from `etl/mappers.py:244`.
   - It validates `L2` with `validate_df`, `check_no_nan_in_keys`, `check_no_inf` at `etl/l2_clean.py:50-52`.

3. L3 aggregate:
   - `etl/l3_aggregate.py:512` defines `run`.
   - `_aggregate` builds team-week offense/defense metrics.
   - `_safe_div` is defined at `etl/l3_aggregate.py:21`.
   - `_quality_report` is defined at `etl/l3_aggregate.py:477`.
   - Required L3 model metrics are enforced later by `utils/model_metrics.py`.

4. Core12:
   - `metrics/core12.py` imports required/optional Core12 metrics from `utils.model_metrics`.
   - It writes `missing_required_metrics`, `model_input_complete`, `data_quality_status` at `metrics/core12.py:129-143`.

5. PowerScore:
   - `metrics/power_score.py:79` computes PowerScore from Core12 and config weights.
   - Validates `L4_POWERSCORE` at `metrics/power_score.py:153`.

6. Reports/analyzer:
   - `app/reports.py:1213` builds weekly team reports.
   - `scripts/matchup_analyzer.py:47` parses numeric report cells.
   - Required report components are checked at `scripts/matchup_analyzer.py:165-166`.
   - Required diffs are handled at `scripts/matchup_analyzer.py:339`.
   - Optional diffs return `None`/warning behavior at `scripts/matchup_analyzer.py:346`.

7. Preflight:
   - `scripts/matchup_batch.py:20` imports `require_model_preflight`.
   - `scripts/matchup_batch.py:163` runs preflight before batch analysis.
   - Outputs include `production_eligible` at `scripts/matchup_batch.py:170-174`.
   - Unsafe bypass is explicit and non-production at `scripts/matchup_batch.py:176-181`.

8. Pick output:
   - `scripts/matchup_batch.py:329-334` writes JSONL pick files under `data/picks.../{season}/week_XX.jsonl`.
   - `config/contracts.yaml` defines the `PICK_OUTPUT` required schema.

Status: production baseline is frozen and tested. Current `HEAD` is after the baseline, but the latest commit touches Live Scenario/forum formatter artifacts, not the frozen main production pick path.

## 3. DataCutoff And Production Safeguards

Core cutoff/preflight files:

- `utils/data_cutoff.py:22` - `DataCutoff`.
- `utils/data_cutoff.py:46` - `PreflightValidationResult`.
- `utils/data_cutoff.py:89` - `validate_pre_game_cutoff`.
- `utils/data_cutoff.py:144` - `resolve_safe_snapshot`.
- `utils/preflight.py:32` - `validate_model_preflight`.
- `utils/preflight.py:128` - `require_model_preflight`.

Current policy:

- Main model cutoff is primarily week-based: source weeks must be `< analysis_week`.
- Timestamp cutoff support exists in `validate_pre_game_cutoff`, but the main weekly workflow mostly enforces week-based cutoff.
- Safe rolling snapshot fallback only moves backward.
- Missing required metrics block production pick generation.
- Optional metrics create warnings and should not become fake neutral zeroes.
- Unsafe bypass exists only as `--unsafe-test-only-bypass` and is marked non-production.

Relevant tests:

- `tests/test_data_cutoff_policy.py`: 18 tests.
- Covers rolling last3/last5 leakage, safe snapshot fallback, week 1 insufficient history, duplicate team-week records, missing EPA, third-down denominator policy, controlled workflow preflight, and data source registry.

Status: production safeguards are strong for week-level pregame workflow. Timestamp-level enforcement is present as an API, but not yet the default driver of every production run.

## 4. Backtest And Champion CORE

Champion CORE is documented in `docs/production_baseline.md:114-123` and implemented in `metrics/ats_features.py`.

Rule:

```text
variant_d_balanced
tag == GOM
confidence >= 85
edge_vs_line >= 4
week >= 3
abs(handicap) <= 7
seasons 2017-2025
```

Implementation references:

- `metrics/ats_features.py:14` - `PAYOUT_WIN = 2.7`.
- `metrics/ats_features.py:106` - `load_core_gom_picks`.
- `metrics/ats_features.py:130-134` - tag/week/confidence/edge/handicap filters.
- `metrics/ats_features.py:675-679` - drawdown calculation.
- `metrics/strategy_search.py:296` - generic max drawdown helper.

Frozen baseline result:

```text
74 bets
61-12-1
+128.70u
Risk 222.00u
ROI 58.0%
Max DD -6.30u
Worst season +2.1u
```

Status: CORE is the official historical champion. Shadow extensions exist in `metrics/gom_calibration.py`, but docs say they did not replace CORE.

## 5. Book Lines And Market Snapshots

Market source status:

- `config/data_sources.yaml` declares `market_lines` as `manual_book_snapshot`.
- Inputs:
  - `data/book_snapshots/{season}/week_XX_screen_snapshot.yaml`
  - `config/lines/{season}/weekX_lines.yaml`
  - `data/market_quotes/{season}/week_XX.jsonl`
- Automation status: `MANUAL`.

Conversion:

- `scripts/book_snapshot_to_week_lines.py:45` parses/normalizes American or decimal prices.
- `scripts/book_snapshot_to_week_lines.py:116-119` reads home spread, total and prices.
- `scripts/book_snapshot_to_week_lines.py:128-158` writes model-facing line and source metadata.
- Tests: `tests/test_book_snapshot_to_week_lines.py`.

Current 2026 artifacts:

- `data/book_snapshots/2026/week_01_screen_snapshot.yaml`
- `config/lines/2026/week1_lines.yaml`
- `data/market_quotes/2026/week_01.jsonl`

Important limitation:

- nfl_data_py/schedules can provide schedule and fallback spread-like fields, but market-grade executable quote still requires manual book snapshot or a real odds feed.
- Current manual sources are good enough for operator workflow, not fully market-grade automation.

## 6. matchup_batch And Candidate Generation

Candidate generation and weekly flow:

- `scripts/prospective_week_flow.py:40` is the prospective weekly model flow entry point.
- `scripts/matchup_batch.py:134` defines `run_batch`.
- `scripts/matchup_batch.py:140-141` controls preflight enforcement and unsafe bypass.
- `scripts/matchup_batch.py:273-276` writes pick fields including confidence, handicap and edge.

Model tags:

- `scripts/matchup_analyzer.py:34-37` defines thresholds for `GOY`, `GOM`, `GOW`, `VALUE PLAY`.
- `scripts/matchup_analyzer.py:396` classifies confidence/edge/PowerScore diff into tags.
- Watchlist for neutral high-edge games exists in GUI helper `scripts/variant_b_daily_bot_gui.py:101` and tests `tests/test_variant_b_daily_bot_watchlist.py`.

Status: candidate generation is operational and protected by preflight for production batch output. It still depends on line files being prepared correctly before the run.

## 7. GPT Variant B / 19-Point Workflow

Variant B audit code:

- `scripts/variant_b_audit.py` is the deterministic audit layer.
- `scripts/variant_b_audit.py:39` defines blocking risk `PXQ-02` for missing p_cover/p_push/p_loss/frontier.
- `scripts/variant_b_audit.py:464` builds no-chase.
- `scripts/variant_b_audit.py:570-581` maps due/not-due point statuses including injury, weather, no-chase, public bias, power rankings, roster and game script.
- `scripts/variant_b_audit.py:714` builds final operator decision.
- `scripts/variant_b_audit.py:912-929` writes audit schema/framework metadata and GPT 19-point completeness.

Week flow:

- `scripts/variant_b_week_flow.py:83-101` checks whether all 19 GPT sections are structurally present.
- `scripts/variant_b_week_flow.py:146-203` writes `summary.md`.
- `scripts/variant_b_week_flow.py:251-261` can generate model proof.
- `scripts/variant_b_week_flow.py:308-316` can append to the learning ledger.

Prompt/source docs:

- `docs/variant_b_final_gpt_research_prompt.md`
- `docs/variant_b_sources_by_point.md`
- `docs/variant_b_19_point_master_prompt.md`

Manual points remain:

- Injuries, roster, weather, public betting, power rankings, game script and some market interpretation remain GPT/operator assisted.
- Quote/price quality still requires real book/source/timestamp/executable status.

Status: Variant B is a structured operator audit workflow, not a fully automated betting engine.

## 8. GUI / Operator Bot

Main GUI:

- `scripts/variant_b_daily_bot_gui.py`.
- Start script: `scripts/Start-VariantBDailyBotGui.ps1`.
- Tkinter/ttk GUI starts at `scripts/variant_b_daily_bot_gui.py:131`.
- Main horizontal `PanedWindow` is at `scripts/variant_b_daily_bot_gui.py:164`.
- Left workflow scroll area is built at `scripts/variant_b_daily_bot_gui.py:185-194`.
- Right Live Scenario panel is built at `scripts/variant_b_daily_bot_gui.py:522+`.

Daily bot:

- `scripts/variant_b_daily_bot.py`.
- Config: `config/variant_b_daily_bot.yaml`.
- Manual gates are evaluated at `scripts/variant_b_daily_bot.py:236-265`.
- Execute mode pauses command execution after missing manual evidence at `scripts/variant_b_daily_bot.py:279-301`.
- Report generation starts at `scripts/variant_b_daily_bot.py:324`.

Day plan:

- Monday: MNF final quote/delta and Variant B refresh.
- Tuesday: previous week close, schedule sync, fallback lines, book snapshot, basic model, GPT full 19, market quotes, Variant B.
- Wednesday: TNF delta plus early Sunday/MNF monitoring.
- Thursday: final TNF plus Sunday/MNF snapshot.
- Friday/Saturday: Sunday/MNF refresh.
- Sunday: final Sunday, MNF refresh, live note.

Status: GUI is now an operator center, but still uses manual paste/save steps for book snapshots and GPT research.

## 9. Live Scenario

Core files:

- `live_scenario/dataset.py` - durable processed dataset builder/validator.
- `live_scenario/service.py` - V2 report service.
- `live_scenario/week_games.py` - current-week game selector.
- `live_scenario/forum_formatter.py` - Polish forum post formatter.
- `scripts/live_scenario_v2.py` - CLI.
- `scripts/sync_live_scenario_data.py` - sync/rebuild helper.

Processed dataset:

- Manifest: `data/live_scenario/manifest.json`.
- Current status: `READY`.
- Seasons: 2015-2025.
- Unique completed games: 2895.
- Team-game observations: 5790.
- Source provider: `local_raw`.
- PBP raw files: `data/nflverse/raw/pbp/play_by_play_2015.parquet` through `play_by_play_2025.parquet`.
- Schedule raw file: `data/nflverse/raw/schedules/schedules.parquet`.
- Score reconciliation warning: `score_reconciliation_mismatch_non_ot_observations=28`.

V2 contract:

- `live_scenario/service.py:98-106` contains schema/methodology/cutoff/sample metadata.
- `live_scenario/service.py:644-664` restricts play-level events to `play_level_events_eligible == true`.
- `live_scenario/service.py:854-888` builds broad league, Team A, opponent league reference and opponent recovery sections.
- `live_scenario/service.py:897-914` builds quarter-path context and exact combined match.
- `live_scenario/service.py:958-970` builds reliability blocks and spread-conditioned levels.
- `live_scenario/service.py:982-986` builds forum content summary.

Week games:

- `live_scenario/week_games.py:80` defines `load_week_games`.
- It does not use the historical processed scenario dataset for current game list.
- It reads local schedules and can refresh via nflreadpy if missing.
- Current local 2026 Week 1 diagnostic found 16 games from `data/schedules/2026.parquet`.
- Example labels loaded: `NE @ SEA`, `SF @ LA`, `ATL @ PIT`, `BAL @ IND`, `BUF @ HOU`, `MIA @ LV`, `DEN @ KC`.

Status: Live Scenario is now a separate, non-production live analysis tool. It is tested and data-backed, but not part of the frozen production pick pipeline.

## 10. Forum Formatter

File:

- `live_scenario/forum_formatter.py`.

Behavior:

- Deterministic Polish forum text generator.
- `live_scenario/forum_formatter.py:72` uses Polish label `Bilans`.
- `live_scenario/forum_formatter.py:88` ends with `Historyczna ciekawostka - nie automatyczny typ live` using em dash in generated text.
- `live_scenario/forum_formatter.py:98-105` cleans `None`, `null`, `UNKNOWN`, `nan`.
- `live_scenario/forum_formatter.py:344-345` outputs Team A `Bilans` and `Surowy wynik`.
- `live_scenario/forum_formatter.py:366-380` chooses opponent section label depending on game state.

Tests:

- `tests/test_live_scenario_forum_formatter.py`: 27 tests.
- Snapshot/format tests check Polish labels, decimal comma, en dash/em dash, no technical null tokens, opponent raw result, and no statistical value mutation.

Status: formatter is working and covered by tests. Current `HEAD` after production baseline mainly contains this formatter update and example GUI JSON reports.

## 11. Tests

Current collection:

- 48 test files.
- 244 tests collected.
- `pytest -q`: 244 passed.

Warnings:

- FastAPI/Starlette deprecation warning from `fastapi.testclient`.
- Polars `how='outer'` deprecation warning in `etl/l3_aggregate.py:387`.
- Pandas/NumPy deprecation warnings in Live Scenario tests.

xfail/skip:

- No `xfail` found.
- No `skip` found by `rg -n "xfail|skip|pytest.mark" tests`, only parametrization marks.

Lint:

- `ruff check .` fails with 6 import-order issues:
  - `scripts/analyze_quarter_paths.py`
  - `scripts/argument_against_auto.py`
  - `scripts/build_edge_proof_dossier.py`
  - `scripts/live_watch_card.py`
  - `scripts/variant_b_learning_ledger.py`
  - `scripts/variant_b_post_event_evaluation.py`
- These are the same known issues listed in `docs/production_baseline.md`.

Status: functional tests are green; full repo lint is not clean.

## 12. Data / Artifacts

Current artifact counts:

| Path | Files |
| --- | ---: |
| `data/l1` | 375 |
| `data/l2` | 374 |
| `data/l3_team_week` | 374 |
| `data/l4_core12` | 374 |
| `data/l4_powerscore` | 375 |
| `data/rolling_core12` | 189 |
| `data/reports` | 15786 |
| `data/picks_variant_m` | 185 |
| `data/picks_variant_d_balanced` | 184 |
| `data/book_snapshots` | 1 |
| `data/market_quotes` | 1 |
| `data/learning_ledger` | 15 |
| `data/live_scenario` | 3 |
| `data/nflverse` | 12 |

Important current files:

- `data/live_scenario/manifest.json`
- `data/live_scenario/processed/team_game_scenario_rows.parquet`
- `data/live_scenario/reports/score_reconciliation_non_ot_mismatches.md`
- `data/book_snapshots/2026/week_01_screen_snapshot.yaml`
- `config/lines/2026/week1_lines.yaml`
- `data/market_quotes/2026/week_01.jsonl`
- `data/picks_variant_m/2026/week_01.jsonl`

Status: there is substantial historical local cache. 2026 Week 1 operator simulation/test artifacts exist.

## 13. Module Status Table

| Module | Status | Evidence |
| --- | --- | --- |
| Config/path/contracts | WORKING | `utils/config.py`, `utils/paths.py`, `utils/contracts.py`; tests pass |
| L1 ingest | WORKING | `etl/l1_ingest.py:42`; filesystem default, nfl_data_py optional |
| L2 clean | WORKING | `etl/l2_clean.py:21`; L2 guards at `etl/l2_clean.py:50-52` |
| L3 aggregate | WORKING | `etl/l3_aggregate.py:512`; tests pass; one Polars deprecation warning |
| Core12 | WORKING | `metrics/core12.py`; missing metrics fields present |
| PowerScore | WORKING | `metrics/power_score.py:79`; contract validated |
| Preflight/cutoff | WORKING | `utils/preflight.py`, `utils/data_cutoff.py`; 18 tests |
| matchup_analyzer | WORKING | required/optional parsing split present |
| matchup_batch | WORKING | preflight and unsafe bypass present |
| Champion CORE | FROZEN_RESEARCH_BASELINE | `docs/production_baseline.md`, `metrics/ats_features.py` |
| Market snapshots | PARTIAL_MANUAL | conversion works; real quote remains manual |
| Variant B audit | WORKING_OPERATOR_LAYER | deterministic gates plus GPT structural evidence |
| Daily bot CLI | WORKING | manual gate tests pass |
| Daily bot GUI | WORKING_BUT_OPERATOR_TOOL | GUI is post-baseline, not production baseline |
| Live Scenario V2 | WORKING_RESEARCH_TOOL | dataset READY, tests pass |
| Forum formatter | WORKING | 27 formatter tests pass |
| Full repo lint | NOT_CLEAN | 6 known Ruff import-order issues |

## 14. Actual User Workflow Today

Current practical workflow:

1. Open GUI:
   - `.\scripts\Start-VariantBDailyBotGui.ps1`

2. Tuesday:
   - Sync schedule/results as applicable.
   - Paste Pregame/book screenshots into GPT using the bot prompt.
   - Save `book_snapshot`.
   - Convert snapshot to `config/lines/{season}/week{week}_lines.yaml`.
   - Run basic model via `prospective_week_flow`.
   - Load model picks and watchlist.
   - For VP/GOW/GOM/GOY, send GPT full 19-point prompt.
   - Paste and save GPT outputs.
   - Fill real market quotes.
   - Run Variant B with model proof and learning ledger.

3. Wednesday:
   - TNF delta refresh if TNF is a candidate.
   - Early quote/GPT monitoring for Sunday/MNF candidates.

4. Thursday:
   - Final TNF quote/GPT delta.
   - Fresh Sunday/MNF quote snapshot.

5. Friday/Saturday:
   - Refresh Sunday/MNF injuries, roster, weather, market move and quotes.
   - Run Variant B refresh.

6. Sunday:
   - Final Sunday quote/GPT delta.
   - MNF quote/GPT delta if needed.
   - Optional Live Scenario during games.

7. Monday:
   - MNF final check.

8. After week ends:
   - Sync results.
   - Run post-event evaluation.
   - Refresh learning report.

## 15. Gaps Before 2026

Open gaps:

1. Market-grade odds are not automated.
   - Current market lines are manual snapshots.
   - No paid/direct atomic odds feed is integrated.

2. Timestamp-level as-of enforcement is not universally applied.
   - Week-based cutoff is strong.
   - Timestamp cutoff exists but is not yet the default for all production artifacts.

3. Full repo lint is not clean.
   - 6 known Ruff import-order issues remain.

4. Variant B research inputs remain manual/semi-manual.
   - Injuries, weather, roster, public bias, power rankings and game script depend on GPT/operator evidence.

5. Live Scenario is not production pick logic.
   - It is tested and useful for live context, but it should remain separate from pregame production picks unless a future validated rule promotes it.

6. Current HEAD is not the frozen production tag.
   - The extra commit is mainly Live Scenario/forum formatter, but production release references should explicitly point to the frozen tag when needed.

7. There is one dirty research JSON artifact.
   - `research/live_scenario_v2/gui/2015_2025_CHI_vs_CAR_after_q2.json`.

## Summary

The system has two different maturity levels:

- Main pregame pick pipeline: production-ready at frozen tag `production-pipeline-baseline-2026-07-29`.
- Operator tooling, Variant B and Live Scenario: functional and tested, but still operational/research layers with manual evidence steps.

## Data Flow Map

```text
filesystem/nfl_data_py PBP
  -> L1
  -> L2 clean + audit
  -> L3 team-week
  -> rolling/Core12
  -> PowerScore + reports
  -> matchup_analyzer
  -> preflight
  -> matchup_batch
  -> pick JSONL
  -> Variant B audit / learning ledger

manual book/GPT snapshot
  -> book_snapshot_to_week_lines
  -> config/lines
  -> prospective_week_flow / matchup_batch / Variant B

nflreadpy/local nflverse PBP + schedules
  -> live_scenario processed dataset
  -> Live Scenario V2
  -> forum formatter
```

## Top 5 Gaps

1. No automated market-grade odds feed.
2. GPT/operator research still required for several Variant B points.
3. Timestamp cutoff exists but is not universal across every production step.
4. Full repo Ruff is not clean.
5. Live Scenario is separate and should not be mixed into production pick decisions without future validation.

## Top 5 Risks

1. Manual quote entry can introduce stale, non-executable or inconsistent prices.
2. Week 1/early season model output is structurally weaker because current-season rolling data is limited.
3. Operator can confuse production picks, Variant B audit status and Live Scenario context if reports are read without scope.
4. Current branch is post-baseline; production claims must reference the frozen tag, not simply `main`.
5. Research artifacts in `research/` and `data/` can look authoritative even when they are simulations or generated examples.

## Next Small Recommended Step

Create one operator checklist named `docs/2026_weekly_operator_runbook.md` that explicitly separates:

- production pick commands,
- manual quote/GPT evidence steps,
- Variant B audit gates,
- Live Scenario usage,
- post-week settlement.

That should be documentation-only first; no code change is needed until the workflow is stable in daily use.
