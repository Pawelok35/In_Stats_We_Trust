# NFL 2026 Pregame Decision System - Architecture And Implementation Plan

Status: planning document only.
Date: 2026-08-01.
Scope: pregame decision system around the frozen NFL production model.
Out of scope: Live Scenario, halftime analysis, live betting model, forum formatter.

This document is based on the current repository state, especially:

- `docs/current_system_audit_2026-08-01.md`
- `docs/production_baseline.md`
- `docs/variant_b_final_gpt_research_prompt.md`
- `docs/variant_b_19_point_master_prompt.md`
- `docs/variant_b_sources_by_point.md`
- `config/variant_b_daily_bot.yaml`
- `scripts/prospective_week_flow.py`
- `scripts/matchup_batch.py`
- `scripts/matchup_analyzer.py`
- `scripts/variant_b_audit.py`
- `scripts/variant_b_week_flow.py`
- `scripts/variant_b_daily_bot.py`
- `scripts/variant_b_daily_bot_gui.py`
- `scripts/book_snapshot_to_week_lines.py`
- `utils/preflight.py`
- `utils/data_cutoff.py`
- `metrics/ats_features.py`

No production code, contracts, tests, GUI files, data files, model rules, tag thresholds, or Champion CORE logic are changed by this document.

## 1. Scope And System Definition

The target system guides the operator through the full NFL pregame decision process:

```text
schedule
-> first market snapshot
-> frozen statistical model
-> weekly candidate list
-> weekly monitoring
-> injury / roster / weather / public betting / line movement
-> GPT Variant B
-> final quote
-> final preflight
-> operator verdict
-> closing line
-> CLV
-> settlement
```

The system must distinguish three decision levels:

```text
MODEL_CANDIDATE
RESEARCH_APPROVED
FINAL_OPERATOR_PICK
```

Definitions:

- `MODEL_CANDIDATE`: model found a potential edge. This is not a bet.
- `RESEARCH_APPROVED`: structured research and deterministic Variant B checks found no active blocker.
- `FINAL_OPERATOR_PICK`: operator approved a final decision against a current valid quote.

The frozen production model baseline remains:

```text
commit: 5216a330d8c23d11fd7acc67ee11cfb2ab390c88
tag: production-pipeline-baseline-2026-07-29
scope: L2 -> L3 -> rolling/Core12 -> report/analyzer -> preflight -> matchup_batch -> pick output
```

The new system is an operator and audit layer around that pipeline. It must call the existing model path without modifying it.

Out of scope for this pregame system:

- `live_scenario/*`
- halftime prediction
- live betting model
- forum formatter
- automatic pick approval without operator

## 2. Current Repository Elements To Reuse

| Area | File / function | Current input | Current output | Status | New architecture use | Adapter needed |
| --- | --- | --- | --- | --- | --- | --- |
| Weekly model flow | `scripts/prospective_week_flow.py:main` | season, week, lines config, variant | generated reports, `data/picks_{variant}/{season}/week_XX.jsonl`, prospective ledger | working | frozen model adapter entry point | yes: wrap output into `MODEL_SCAN_COMPLETED` and `MODEL_CANDIDATE_CREATED` events |
| Matchup batch | `scripts/matchup_batch.py:run_batch` | YAML line config entries | report files, combined report, pick JSONL | working | candidate generation and preflight carrier | yes: normalize pick rows into `CandidateRecord` |
| Market fields | `scripts/matchup_batch.py:build_market_fields` | matchup config entry and namespace | market fields on pick record | working | model-generation market context | yes: map to `MarketSnapshot` and preserve snapshot identity |
| Process fields | `scripts/matchup_batch.py:build_process_fields` | config entry | process metadata fields | working | initial process evidence | yes: map to candidate/event payload |
| Analyzer | `scripts/matchup_analyzer.py:run` | report path, home, away, spread, total | rendered analysis and projection | working | model projection source | yes: extract projection fields into central record |
| Classification | `scripts/matchup_analyzer.py:classify` | confidence, edge, PowerScore diff | model tag | frozen behavior | source of model tag | no logic change allowed |
| Numeric parser | `scripts/matchup_analyzer.py:parse_numeric` | report table cell | float or error | working | required report value guard | no |
| Preflight | `utils/preflight.py:require_model_preflight` | season, analysis week, paths | PASS or RuntimeError | working | production eligibility gate | no |
| Cutoff policy | `utils/data_cutoff.py:validate_pre_game_cutoff` | DataFrame and cutoff | `SAFE`/`UNSAFE` payload | working | future timestamp/weekly cutoff reference | no |
| Safe snapshot | `utils/data_cutoff.py:resolve_safe_snapshot` | available rolling weeks, requested week | safe snapshot resolution | working | no-leak rolling selection | no |
| Champion CORE | `metrics/ats_features.py:load_core_gom_picks` | seasons and picks dir | filtered CORE GOM picks | frozen research baseline | regression test source | no logic change allowed |
| Book snapshot conversion | `scripts/book_snapshot_to_week_lines.py:load_snapshot` | YAML `book_snapshot + games` | Python mapping | working | snapshot ingestion | yes: emit append-only snapshot events before converting to lines |
| Week lines build | `scripts/book_snapshot_to_week_lines.py:build_lines` | parsed snapshot | `config/lines/...yaml` payload | working | model line adapter | yes: do not use line YAML as only history |
| Variant B audit | `scripts/variant_b_audit.py:build_audit` | pick record, rules, audit stage | structured audit JSON | working operator layer | deterministic research/audit evidence | yes: store audit as `RESEARCH_COMPLETED/UPDATED` events |
| Variant B market snapshot | `scripts/variant_b_audit.py:build_market_snapshot` | pick record | point 9 output | working | quote integrity evidence | yes: map fields into market gate |
| Variant B no-chase | `scripts/variant_b_audit.py:build_no_chase` | pick record | point 7 output | working | final quote/no-chase gate input | yes |
| Variant B price quality | `scripts/variant_b_audit.py:build_price_quality` | pick record | point 8 output | working | final quote gate input | yes |
| Variant B operator decision | `scripts/variant_b_audit.py:build_operator_decision` | process quality | gate state/operator action | working | research gate, not final operator pick | yes: keep separate from `FINAL_OPERATOR_PICK` |
| Variant B week flow | `scripts/variant_b_week_flow.py:main` | picks file, quotes file, stage | audit JSON, summary MD/JSON, optional ledger | working | current daily research batch | yes: consume events and write events later |
| GPT structure check | `scripts/variant_b_week_flow.py:attach_gpt_snapshot_status` | pick record and snapshots root | status plus present points | working | GPT research completeness | yes |
| Quote override | `scripts/variant_b_week_flow.py:apply_quote_override` | pick record, JSONL quote | enriched pick record | working | current manual quote merge | yes: replace/augment with event log source |
| Daily bot CLI | `scripts/variant_b_daily_bot.py:evaluate_tasks` | day config, filesystem state | rows with READY/NEEDS_OPERATOR/BLOCKED | working | operator schedule/checklist | yes: point it to central record status |
| Daily bot GUI | `scripts/variant_b_daily_bot_gui.py` handlers | user selections/pastes | files, commands, display | working operator UI | later frontend | yes after backend stabilizes |
| Daily bot config | `config/variant_b_daily_bot.yaml` | day definitions | manual/command task list | working | operational schedule | yes: add pregame event tasks later |

Files that must be treated as frozen for early implementation:

- `scripts/matchup_analyzer.py` model scoring/classification logic
- `scripts/matchup_batch.py` production pick generation behavior
- `metrics/ats_features.py` Champion CORE filters and payout assumptions
- `utils/preflight.py` production preflight behavior
- `utils/data_cutoff.py` cutoff behavior unless a separate production change is approved

## 3. Current Model + GPT Workflow

Current actual flow:

```text
book snapshot YAML
-> scripts/book_snapshot_to_week_lines.py
-> config/lines/{season}/week{week}_lines.yaml
-> scripts/prospective_week_flow.py
-> scripts/matchup_batch.py
-> data/picks_{variant}/{season}/week_XX.jsonl
-> GUI copies GPT prompt
-> operator sends GPT 19-point research
-> GUI saves research/gpt_snapshots/{season}/week_XX/{game_id}/full_19_points.md
-> operator fills data/market_quotes/{season}/week_XX.jsonl
-> scripts/variant_b_week_flow.py
-> research/variant_b_week_flow/{season}/week_XX/*.json and summary.md
```

Automatic today:

- schedule sync in daily bot command config: `python -m app.cli sync-nfl-schedule --season {season}`
- fallback line export: `python -m app.cli export-lines-from-nfl --season {season} --week {week}`
- book snapshot to lines conversion via `scripts/book_snapshot_to_week_lines.py`
- model scan via `scripts/prospective_week_flow.py`
- batch candidate output via `scripts/matchup_batch.py`
- Variant B deterministic audit via `scripts/variant_b_week_flow.py` and `scripts/variant_b_audit.py`
- daily task gating in `scripts/variant_b_daily_bot.py:evaluate_tasks`

Manual today:

- screenshot extraction from Pregame/book into YAML
- real quote confirmation: book, spread, price, timestamp, executable status
- GPT full 19-point research
- GPT delta refresh
- final operator judgment
- closing line/closing price capture, unless added later

Partially automated today:

- quote override is read from `data/market_quotes/{season}/week_XX.jsonl` by `scripts/variant_b_week_flow.py:load_quote_overrides`
- GPT structure is checked by `scripts/variant_b_week_flow.py:attach_gpt_snapshot_status`, but the content/evidence is still operator/GPT supplied
- model proof can be generated by `scripts/variant_b_week_flow.py --with-model-proof`

Files created today:

- `data/book_snapshots/{season}/week_XX_screen_snapshot.yaml`
- `config/lines/{season}/week{week}_lines.yaml`
- `data/picks_{variant}/{season}/week_XX.jsonl`
- `research/gpt_snapshots/{season}/week_XX/**/full_19_points.md`
- `research/gpt_snapshots/{season}/week_XX/**/delta_*.md`
- `data/market_quotes/{season}/week_XX.jsonl`
- `research/variant_b_week_flow/{season}/week_XX/summary.md`
- `research/variant_b_week_flow/{season}/week_XX/*.json`
- `data/learning_ledger/{season}/week_XX/*` when enabled

Current history risks:

- `config/lines/{season}/week{week}_lines.yaml` is a current model input file and may be overwritten by later snapshots.
- `data/market_quotes/{season}/week_XX.jsonl` is closer to append-only, but it is not yet the single authoritative event log.
- `research/gpt_snapshots` preserves files, but there is no unified event sequence across market, model, GPT, injury, final quote and settlement.
- GUI displays current state, but current state is inferred from multiple files, not projected from one event stream.

## 4. Target Architecture

Target layers:

```text
FrozenProductionModelAdapter
EventContracts
AppendOnlyEventStore
CurrentStateProjector
MarketSnapshotHistory
WeeklyCandidateRegistry
VariantBIntegration
StructuredInjuryRosterInput
WeatherSchedulePublicContext
LineMovementEngine
FinalQuoteGate
OperatorDecisionService
ClosingQuoteClvSettlement
```

Data flow:

```text
schedule source
  -> GAME_CREATED event

book/manual/odds snapshot
  -> INITIAL_MARKET_SNAPSHOT / MARKET_QUOTE_UPDATED events
  -> week lines adapter
  -> frozen model input

frozen model pipeline
  -> MODEL_SCAN_COMPLETED event
  -> MODEL_CANDIDATE_CREATED / MODEL_CANDIDATE_BLOCKED events
  -> WeeklyCandidateRegistry

GPT + Variant B
  -> RESEARCH_STARTED / RESEARCH_COMPLETED / RESEARCH_UPDATED events
  -> deterministic audit payload
  -> research status on PregameGameRecord

manual structured context
  -> INJURY_UPDATED / ROSTER_UPDATED / WEATHER_UPDATED / PUBLIC_BETTING_UPDATED events

final quote
  -> FINAL_QUOTE_CAPTURED event
  -> FinalQuoteGate

operator
  -> OPERATOR_PICK_APPROVED / OPERATOR_PICK_REJECTED events

post-game
  -> CLOSING_QUOTE_CAPTURED
  -> GAME_SETTLED
  -> CLV and learning ledger
```

The current `PregameGameRecord` is not a hand-edited master file. It is rebuilt from events.

## 5. Data Contracts

These contracts are design-level only in this phase. They should later be implemented as typed Python models plus tests.

### PregameEvent

Purpose: immutable append-only event envelope.

Required:

- `event_id`
- `game_id`
- `season`
- `week`
- `event_type`
- `created_at_utc`
- `effective_at_utc`
- `source`
- `schema_version`
- `payload`

Optional:

- `idempotency_key`
- `supersedes_event_id`
- `correction_reason`
- `operator`
- `source_file`
- `source_hash`

Keys: `event_id`; idempotency via `idempotency_key`.
Timestamps: created and effective UTC.
Source metadata: source, source file/hash, operator when manual.
Quality status: lives in payload where applicable.
Schema version: event envelope and payload version.

### PregameGameRecord

Purpose: current view of one game.

Required:

- `season`
- `week`
- `game_id`
- `away_team`
- `home_team`
- `kickoff_utc`
- `current_decision_level`
- `record_schema_version`

Optional:

- venue, neutral site, model fields, research status, injury status, weather status, public betting status, final quote status, operator verdict, settlement.

Keys: `season`, `week`, `game_id`.
Timestamps: last event time, model generated time, final quote time, verdict time.
Source metadata: current-state fields should preserve source event IDs.
Quality status: aggregate status derived from component statuses.
Schema version: `pregame_game_record.v1`.

### MarketSnapshot

Purpose: one market observation without overwriting previous observations.

Required:

- `snapshot_id`
- `game_id`
- `snapshot_type`
- `captured_at_utc`
- `book`
- `source`
- `market_type`
- `quality_status`
- `executable_status`

Optional:

- `team_or_side`, `spread`, `spread_price`, `total`, `total_price`, `moneyline`, `quote_id`, `source_url`, `operator_note`.

Keys: `snapshot_id`; also natural key `game_id + captured_at_utc + book + market_type + team_or_side`.
Quality statuses: `MARKET_GRADE`, `EXECUTABLE_CONFIRMED`, `DISPLAYED_UNVERIFIED`, `STALE`, `INCONSISTENT_DISPLAY`, `MISSING_TIMESTAMP`, `MISSING_PRICE`.
Schema version: `market_snapshot.v1`.

### CandidateRecord

Purpose: model output normalized into a weekly registry, not a final pick.

Required:

- `game_id`
- `season`
- `week`
- `model_variant`
- `candidate_status`
- `production_eligible`
- `preflight_status`

Optional:

- `selected_team`, `model_tag`, `model_margin`, `market_margin_at_scan`, `edge_vs_line`, `confidence`, `warnings`, `reason_codes`, `pick_record_path`.

Keys: `game_id + model_variant + model_run_id`.
Timestamps: `model_generated_at_utc`.
Source metadata: pick JSONL path, commit/config hashes if present.
Quality status: model input completeness/preflight.
Schema version: `candidate_record.v1`.

### ResearchRecord

Purpose: store GPT/Variant B research and deterministic audit state.

Required:

- `game_id`
- `research_type`
- `captured_at_utc`
- `source`
- `variant_b_framework_version`
- `status`

Optional:

- `gpt_snapshot_path`, `points_present`, `hard_blockers`, `warnings`, `evidence`, `confidence`, `impact`, `blocking`.

Keys: `game_id + research_type + captured_at_utc`.
Timestamps: research cutoff and captured/accessed times.
Quality status: `STRUCTURALLY_COMPLETE`, `INCOMPLETE`, `MISSING`, `PENDING`, `NOT_ASSESSABLE`.
Schema version: `research_record.v1`.

### InjuryRecord

Purpose: structured manual injury/practice input.

Required:

- `game_id`
- `team`
- `player`
- `reported_at_utc`
- `source`
- `practice_status`
- `game_status`
- `impact`

Optional:

- position, role, starter status, injury type, blocking, operator note, source URL.

Keys: `game_id + team + player + reported_at_utc`.
Quality status: source/timestamp completeness and impact confidence.
Schema version: `injury_record.v1`.

### RosterRecord

Purpose: structured roster/depth chart change.

Required:

- `game_id`
- `team`
- `change_type`
- `reported_at_utc`
- `source`
- `impact`

Optional:

- player, position, role, old status, new status, depth chart effect, blocking.

Keys: `game_id + team + change_type + reported_at_utc + player`.
Schema version: `roster_record.v1`.

### WeatherRecord

Purpose: game-window weather and venue operation context.

Required:

- `game_id`
- `captured_at_utc`
- `source`
- `forecast_horizon`
- `risk_status`

Optional:

- temperature, wind, gusts, precipitation, snow, surface, roof status, source URL.

Keys: `game_id + captured_at_utc + source`.
Quality status: forecast availability, official/source reliability, horizon.
Schema version: `weather_record.v1`.

### PublicBettingRecord

Purpose: optional public betting context.

Required:

- `game_id`
- `market_type`
- `side`
- `source`
- `captured_at_utc`
- `reliability_status`

Optional:

- bet percentage, money percentage, source scope, book count, interpretation status.

Keys: `game_id + market_type + side + source + captured_at_utc`.
Quality status: reliability and scope.
Schema version: `public_betting_record.v1`.

### FinalQuote

Purpose: quote used by final gate.

Required:

- `game_id`
- `captured_at_utc`
- `book`
- `source`
- `spread`
- `price`
- `quality_status`
- `executable_status`

Optional:

- total, moneyline, quote ID, betslip confirmation, target stake, house rules checked.

Keys: final quote event ID and quote ID if available.
Quality status: final quote gate status.
Schema version: `final_quote.v1`.

### OperatorDecision

Purpose: final auditable operator verdict.

Required:

- `game_id`
- `operator`
- `decision_timestamp_utc`
- `verdict`
- `reason_codes`
- `model_version`
- `variant_b_framework_version`

Optional:

- stake, comment, final quote ID, reduced stake reason.

Keys: `game_id + decision_timestamp_utc + operator`.
Quality status: valid only if final quote gate and required research gates pass.
Schema version: `operator_decision.v1`.

### ClosingQuote

Purpose: post-market close reference.

Required:

- `game_id`
- `captured_at_utc`
- `book_or_source`
- `market_type`
- `quality_status`

Optional:

- closing spread, closing price, exact decision-line closing price, source URL.

Keys: `game_id + market_type + book_or_source + captured_at_utc`.
Schema version: `closing_quote.v1`.

### SettlementRecord

Purpose: result, units and process review.

Required:

- `game_id`
- `settled_at_utc`
- `result`
- `units`
- `operator_verdict`

Optional:

- final score, spread result, price CLV, spread CLV, closing quote ID, notes.

Keys: `game_id + settled_at_utc`.
Schema version: `settlement_record.v1`.

## 6. Append-Only Event Model

Base event structure:

```yaml
event_id:
game_id:
season:
week:
event_type:
created_at_utc:
effective_at_utc:
source:
schema_version:
idempotency_key:
supersedes_event_id:
payload:
```

Event types:

```text
GAME_CREATED
INITIAL_MARKET_SNAPSHOT
MARKET_QUOTE_UPDATED
MODEL_SCAN_COMPLETED
MODEL_CANDIDATE_CREATED
MODEL_CANDIDATE_BLOCKED
RESEARCH_STARTED
RESEARCH_COMPLETED
RESEARCH_UPDATED
INJURY_UPDATED
ROSTER_UPDATED
WEATHER_UPDATED
PUBLIC_BETTING_UPDATED
FINAL_QUOTE_CAPTURED
RESEARCH_APPROVED
OPERATOR_PICK_APPROVED
OPERATOR_PICK_REJECTED
CLOSING_QUOTE_CAPTURED
GAME_SETTLED
CORRECTION_EVENT
```

Idempotency:

- For automated events, generate `idempotency_key` from event type, game ID, source file/hash, model run ID or snapshot ID.
- Re-processing the same file should not create duplicate logical events.
- If an event is intentionally re-sent with the same idempotency key, the writer should return the existing event ID.

Ordering:

- Sort projection by `effective_at_utc`, then `created_at_utc`, then `event_id`.
- Late-arriving events are allowed. The projector must rebuild state deterministically.

Corrections:

- Never delete a wrong event.
- Add `CORRECTION_EVENT` with `supersedes_event_id` and reason.
- Projector applies the latest valid correction while preserving history.

Duplicate avoidance:

- `event_id` unique.
- `idempotency_key` unique where present.
- Natural uniqueness rules per payload type, for example `snapshot_id` for `MarketSnapshot`.

Current state rebuild:

- Read all events for `game_id`.
- Validate envelope and payload schemas.
- Apply events in deterministic order.
- Derive `PregameGameRecord`.
- Preserve source event IDs for current fields.

Out-of-order behavior:

- Accept event if schema-valid.
- Rebuild projection.
- If event conflicts with a later final decision, record warning and require operator review.

## 7. Market Snapshot History

Market snapshot history must be append-only.

Snapshot categories:

```text
INITIAL
CURRENT
FINAL
CLOSING
```

Every snapshot must support:

```text
snapshot_id
game_id
captured_at_utc
book
source
market_type
spread
spread_price
total
total_price
moneyline
quality_status
executable_status
```

Quality statuses:

```text
MARKET_GRADE
EXECUTABLE_CONFIRMED
DISPLAYED_UNVERIFIED
STALE
INCONSISTENT_DISPLAY
MISSING_TIMESTAMP
MISSING_PRICE
```

Current implementation to reuse:

- `scripts/book_snapshot_to_week_lines.py:load_snapshot` validates top-level `book_snapshot` and `games`.
- `scripts/book_snapshot_to_week_lines.py:american_price_or_none` normalizes American/decimal odds.
- `scripts/book_snapshot_to_week_lines.py:build_lines` writes model-facing line YAML.

Required adapter:

- Convert every pasted book snapshot into `INITIAL_MARKET_SNAPSHOT` or `MARKET_QUOTE_UPDATED` events.
- Continue producing `config/lines/{season}/week{week}_lines.yaml` for existing model compatibility.
- Treat `config/lines` as model input, not historical truth.

## 8. Weekly Candidate Registry

The candidate registry is a normalized view of all games after model scan. It is not a final pick file.

Statuses:

```text
MODEL_CANDIDATE
WATCHLIST
BLOCKED
NO_PLAY
MISSING_DATA
```

Current source:

- `scripts/prospective_week_flow.py` validates lines, generates previews, runs `scripts/matchup_batch.py`, then writes picks.
- `scripts/matchup_batch.py:run_batch` writes `data/picks_{variant}/{season}/week_XX.jsonl`.
- `scripts/matchup_batch.py` currently filters/records production eligibility through `require_model_preflight`.

Difference between registry and pick output:

- Current pick output contains model-generated candidates and fields used by backtest/Variant B.
- Candidate registry should include all games and their current model status, including `NO_PLAY`, `BLOCKED`, and `MISSING_DATA`.
- Final operator decisions must not be written back into the model pick output as if they were model picks.

Adapter:

- Read current pick JSONL.
- Join with schedule/week games.
- Emit `MODEL_SCAN_COMPLETED`.
- Emit one candidate event per game.

## 9. Final Quote Gate

The final quote gate prevents a final operator pick on stale, incomplete, or unacceptable market data.

Required checks:

- quote freshness
- book/source present
- price present
- executable status
- atomic spread + price identity when available
- acceptable quote frontier
- no-chase limit
- key numbers
- injury blockers
- Variant B status
- model production eligibility

Statuses:

```text
FINAL_QUOTE_VALID
FINAL_QUOTE_STALE
FINAL_QUOTE_OUTSIDE_FRONTIER
FINAL_PRICE_REJECTED
KEY_NUMBER_REJECTED
QUOTE_MISSING
WAIT_FOR_MARKET
WAIT_FOR_INJURY_NEWS
```

Current code to reuse:

- `scripts/variant_b_audit.py:build_market_snapshot`
- `scripts/variant_b_audit.py:build_no_chase`
- `scripts/variant_b_audit.py:build_price_quality`
- `scripts/variant_b_audit.py:has_atomic_quote`
- `scripts/variant_b_audit.py:has_model_generation_quote`
- `scripts/variant_b_audit.py:has_frozen_frontier`

Important distinction:

- Variant B point 19 currently returns audit/operator action like `HOLD_PENDING_DATA` or `READY_FOR_NEXT_AUDIT_STAGE`.
- That is not the same thing as final operator approval.

## 10. Operator Verdict

Allowed final verdicts:

```text
APPROVED
APPROVED_REDUCED_STAKE
WAIT
PASS
REJECTED_MODEL_DATA
REJECTED_INJURY
REJECTED_PRICE
REJECTED_LINE_MOVE
REJECTED_MARKET_QUALITY
REJECTED_RESEARCH_RISK
REJECTED_OPERATOR
```

Minimum conditions for `APPROVED`:

- model candidate exists and is production eligible,
- final quote gate is `FINAL_QUOTE_VALID`,
- quote is fresh and has book/source/price/timestamp,
- Variant B deterministic audit has no active hard blockers,
- required injury/roster/weather fields are either complete or explicitly not due/not material,
- no no-chase/key-number blocker is active,
- operator supplies stake and reason code,
- decision timestamp is before kickoff.

The service should emit:

- `OPERATOR_PICK_APPROVED`
- `OPERATOR_PICK_REJECTED`
- or leave current state as `WAIT`

It must never rewrite the model pick output.

## 11. Variant B And GPT Integration

Existing Variant B stays the framework.

Relevant existing components:

- `docs/variant_b_final_gpt_research_prompt.md`: current final GPT prompt and output structure.
- `docs/variant_b_19_point_master_prompt.md`: older master prompt and implementation grouping.
- `docs/variant_b_sources_by_point.md`: source map for all 19 points.
- `scripts/variant_b_audit.py`: deterministic rule/audit builder.
- `scripts/variant_b_week_flow.py`: weekly audit runner.

Existing 19 points:

```text
1 argument_against
2 market_move_notes
3 injury_role_notes
4 schedule_spot_notes
5 weather_notes
6 key_number_check
7 no_chase_limit
8 price_quality
9 market_snapshot
10 public_bias / tickets_handle
11 power_rankings_check
12 roster_change_check
13 matchup_specific_risk
14 game_script_risk
15 closing_line
16 closing_price
17 clv_points
18 process_quality
19 final_operator_decision
```

Event mapping:

- full GPT 19-point output -> `RESEARCH_COMPLETED`
- GPT delta -> `RESEARCH_UPDATED`
- final prekick refresh -> `RESEARCH_UPDATED` with `research_type=FINAL_REFRESH`
- deterministic audit JSON -> payload evidence on same research event or a linked `VARIANT_B_AUDIT_COMPLETED` subtype if later added

Every research point should map to:

```text
point_id
status
evidence
source
captured_at_utc
confidence
impact
blocking
```

Rules:

- GPT may summarize and gather evidence.
- Python/rule engine calculates and gates.
- GPT cannot set `FINAL_OPERATOR_PICK`.
- Missing data remains `UNKNOWN`, `PENDING`, `MISSING`, or `NOT_ASSESSABLE`.

## 12. Injury, Roster, Weather And Public Betting

First version should use manual structured input. Do not begin with scraping.

Injury input:

```text
player
team
position
role
starter_status
practice_status
game_status
injury_type
source
reported_at_utc
impact
blocking
operator_note
```

Roster input:

```text
team
player
change_type
old_status
new_status
source
reported_at_utc
impact
blocking
```

Weather input:

```text
temperature
wind
wind_gusts
precipitation
snow
surface
roof_status
forecast_horizon
source
captured_at_utc
risk_status
```

Public betting input:

```text
market_type
side
bet_percentage
money_percentage
source
captured_at_utc
source_scope
book_count
reliability_status
```

Public betting is optional context in v1. Missing bet percentage or money percentage must not block the first version.

Forbidden automatic label:

```text
SHARP_MONEY_CONFIRMED
```

unless a future trusted source contract supports it.

## 13. Decision Log, Closing Quote And CLV

Decision log should support:

```text
model_line
initial_line
bet_line
bet_price
bet_timestamp
closing_line
closing_price
spread_clv
price_clv
result
units
operator_verdict
reason_codes
```

Post-game event sequence:

```text
CLOSING_QUOTE_CAPTURED
GAME_SETTLED
```

CLV should be computed only when a valid bet line and closing reference are present. If closing price is missing or not source-qualified, CLV price is `NOT_ASSESSABLE`.

Existing scripts to inspect later:

- `scripts/variant_b_post_event_evaluation.py`
- `scripts/variant_b_learning_ledger.py`
- `scripts/settle_prospective_ledger.py`

No CLV implementation is part of this stage.

## 14. Production Baseline Protection

Frozen production scope:

- L2/L3 ETL behavior.
- rolling/Core12 and PowerScore behavior.
- `scripts/matchup_analyzer.py` scoring/classification behavior.
- `scripts/matchup_batch.py` production pick output behavior.
- `utils/preflight.py` production gate behavior.
- Champion CORE filters in `metrics/ats_features.py`.

Champion CORE expected regression:

```text
74 bets
61-12-1
+128.70u
ROI 58.0%
Max DD -6.30u
```

Recommended first regression test location:

```text
tests/test_champion_core_regression.py
```

Recommended source:

- call `metrics.ats_features.load_core_gom_picks`
- summarize W-L-P/profit/risk/ROI/max drawdown using existing logic or a narrow local helper in the test
- assert exact frozen values with small float tolerances

New pregame layer must call frozen scripts as adapters. It must not edit their output semantics.

## 15. Proposed Files And Directory Structure

Files to create after this plan is approved:

```text
pregame/__init__.py
pregame/contracts.py
pregame/events.py
pregame/event_store.py
pregame/projector.py
pregame/market_snapshots.py
pregame/candidate_registry.py
pregame/final_quote_gate.py
pregame/operator_decision.py
pregame/clv.py
tests/test_champion_core_regression.py
tests/test_pregame_contracts.py
tests/test_pregame_event_model.py
tests/test_pregame_market_snapshots.py
tests/test_pregame_candidate_registry.py
tests/test_pregame_final_quote_gate.py
```

Files likely to change later:

```text
config/data_sources.yaml
config/contracts.yaml or new pregame schema config
scripts/book_snapshot_to_week_lines.py
scripts/prospective_week_flow.py
scripts/variant_b_week_flow.py
scripts/variant_b_daily_bot.py
scripts/variant_b_daily_bot_gui.py
```

Files not to change in early stages:

```text
metrics/ats_features.py
scripts/matchup_analyzer.py
scripts/matchup_batch.py
utils/preflight.py
utils/data_cutoff.py
live_scenario/*
```

If an early test reveals a baseline issue, stop and review rather than patching model logic.

## 16. Implementation Plan

### Accepted Starting Point

Stage 11.2 is complete and frozen as the accepted single-candidate operator workflow. See `docs/variant_b_stage_11_2_accepted_baseline.md`.

The approved next implementation sequence is Stage 11.3A, 11.3B, 11.4, 11.5, 11.6, 11.7, then 11.8. Weekly batch and GUI work must not begin before the preceding stages are accepted.

### Commit 1 - Champion CORE regression test

Goal: protect baseline.

Files:

- `tests/test_champion_core_regression.py`

Tests:

- assert 74 bets
- assert 61-12-1
- assert +128.70u
- assert ROI 58.0%
- assert max drawdown -6.30u
- assert filters: variant D balanced, GOM, confidence >= 85, edge >= 4, week >= 3, abs(handicap) <= 7

Acceptance:

- test passes without changing production code.

Dependencies: current data in `data/picks_variant_d_balanced`.
Baseline risk: low if test-only.

### Commit 2 - Data contracts

Goal: define typed contract models/enums.

Files:

- `pregame/contracts.py`
- `pregame/events.py`
- `tests/test_pregame_contracts.py`

Acceptance:

- schemas validate required fields,
- invalid timestamps/statuses fail,
- no model code touched.

Dependencies: Commit 1.
Baseline risk: low.

### Commit 3 - Append-only event model

Goal: event envelope, event IDs, idempotency and correction rules.

Files:

- `pregame/event_store.py`
- `tests/test_pregame_event_model.py`

Acceptance:

- duplicate idempotency key does not create duplicate logical event,
- correction event supersedes without deletion,
- event order is deterministic.

Dependencies: Commit 2.
Baseline risk: low.

### Commit 4 - Current-state projector

Goal: rebuild `PregameGameRecord` from events.

Files:

- `pregame/projector.py`
- `tests/test_pregame_projector.py`

Acceptance:

- late-arriving events rebuild current state,
- source event IDs are preserved,
- final decision remains distinct from model candidate.

Dependencies: Commit 3.
Baseline risk: low.

### Commit 5 - Market snapshot history

Goal: append-only market snapshot adapter.

Files:

- `pregame/market_snapshots.py`
- tests for snapshot quality/statuses
- later adapter touch to `scripts/book_snapshot_to_week_lines.py` only if needed

Acceptance:

- initial/current/final/closing snapshots are preserved,
- missing timestamp/price/source becomes quality status,
- line YAML remains compatibility output only.

Dependencies: Commit 4.
Baseline risk: medium if touching conversion script; keep adapter separate first.

### Commit 6 - Weekly Candidate Registry

Goal: normalize model output and all-games weekly state.

Files:

- `pregame/candidate_registry.py`
- tests

Acceptance:

- pick JSONL maps to candidate records,
- non-candidate games can be represented as `NO_PLAY` or `MISSING_DATA`,
- final operator status is not written to pick output.

Dependencies: Commit 4.
Baseline risk: low if read-only adapter.

### Commit 7 - Final Quote Gate

Goal: deterministic gate for final quote validity.

Files:

- `pregame/final_quote_gate.py`
- tests

Acceptance:

- stale/missing price/missing timestamp blocks,
- acceptable frontier and no-chase fields are respected when present,
- missing optional public betting does not block.

Dependencies: Commits 5 and 6.
Baseline risk: low.

### Stage 11.3A - Audit: One Candidate To Central Event Flow

Goal: audit the accepted Stage 11.2 single-candidate artifact against central event-flow contracts before wiring it into a central game state.

Acceptance:

- document exact input/output event mapping for one candidate,
- prove CandidateRecord and Variant B evidence authority boundaries remain intact,
- identify missing event payload or projector fields,
- do not add batch, GUI, discovery, or automatic GPT behavior.

Dependencies: accepted Stage 11.2 single-candidate baseline.

### Stage 11.3B - Central Workflow For One Game

Goal: implement the central event workflow for exactly one game, using the accepted single-candidate Variant B path as an explicit input.

Acceptance:

- one game progresses through authoritative candidate, market, research, quote, and current-state events,
- current state is rebuilt from the append-only event flow,
- no automatic weekly batch, file discovery, or GUI wiring is added.

Dependencies: Stage 11.3A.

### Stage 11.4 - Structured Manual Inputs

Goal: add structured manual inputs for injuries, roster, weather, and public betting.

Acceptance:

- every manual item has source and timestamp,
- impact and blocking status are validated,
- public betting remains optional context.

Dependencies: Stage 11.3B.

### Stage 11.5 - Operator Verdict, Quotes, Settlement And CLV

Goal: implement the final operator decision together with final quote, closing quote, settlement, and CLV lifecycle.

Acceptance:

- `APPROVED` requires valid final quote, research/model status, and required manual evidence,
- rejected/pass/wait decisions require reason codes,
- closing quote, settlement, and CLV remain event records and never mutate model pick output.

Dependencies: Stages 11.3B and 11.4.

### Stage 11.6 - Full Week 1 End-To-End Simulation

Goal: prove the complete central workflow using isolated Week 1 simulation fixtures.

Acceptance:

- schedule -> initial snapshot -> model candidate -> GPT research -> injury update -> market update -> final quote -> operator decision -> closing quote -> settlement -> CLV,
- no production data or production artifacts are created.

Dependencies: Stages 11.3B, 11.4, and 11.5.

### Stage 11.7 - Weekly Batch

Goal: extend the proven one-game workflow to an explicit weekly batch process.

Acceptance:

- batch reuses Stage 11.3B logic rather than duplicating it,
- candidate and evidence inputs remain explicit and auditable,
- no GUI business logic is introduced.

Dependencies: Stage 11.6.

### Stage 11.8 - GUI Reads Central State

Goal: connect the existing operator GUI to central current state only after backend and weekly batch are proven.

Acceptance:

- GUI reads central `PregameGameRecord`,
- no business logic lives only in GUI,
- old manual workflow remains available.

Dependencies: Stage 11.7.
Baseline risk: medium.

## 17. Week 1 End-To-End Simulation

Scenario:

```text
GAME_CREATED
INITIAL_MARKET_SNAPSHOT
MODEL_SCAN_COMPLETED
MODEL_CANDIDATE_CREATED
RESEARCH_STARTED
RESEARCH_COMPLETED
INJURY_UPDATED
MARKET_QUOTE_UPDATED
FINAL_QUOTE_CAPTURED
RESEARCH_UPDATED
RESEARCH_APPROVED
OPERATOR_PICK_APPROVED or OPERATOR_PICK_REJECTED
CLOSING_QUOTE_CAPTURED
GAME_SETTLED
```

Simulation checks:

- all records share one `game_id`,
- every external input has source and timestamp,
- no event overwrites an older event,
- out-of-order events project deterministically,
- stale quote blocks approval,
- missing required research blocks approval,
- public betting missing does not block v1,
- Champion CORE regression still passes,
- no Live Scenario files are used.

## 18. Risks And Open Decisions

Critical:

- Manual market quote can be stale or non-executable.
- Current branch is after frozen baseline; production claims must reference the tag, not generic `main`.
- `FINAL_OPERATOR_PICK` must not be confused with Variant B point 19 operator action.

High:

- Current `config/lines` can be overwritten; event log must become source of market history.
- GPT evidence is structural but not deterministic; Python gates must remain authority.
- Timestamp-level cutoff exists but is not universal across all current production artifacts.

Medium:

- Public betting source reliability is unknown.
- Injury/roster automation source choice is unresolved.
- Closing line source and exact close definition are unresolved.
- GUI may hide state complexity if backend contracts are not stable first.

Low:

- Existing Ruff import-order issues remain outside the production baseline.
- Some generated/research artifacts may look authoritative unless clearly labeled.

UNKNOWN_REQUIRES_REVIEW:

- exact odds provider for market-grade quote history,
- final closing-line source,
- official injury feed automation source,
- whether public betting will be paid-feed, manual, or omitted in v1,
- final storage format: JSONL only vs SQLite/DuckDB plus JSONL export.

## 19. First Small Implementation Commit

Recommended first implementation commit after this document is approved:

```text
Champion CORE regression test
+
basic pregame contract enums/models
+
event enums
+
contract tests
```

Exact proposed files:

```text
tests/test_champion_core_regression.py
pregame/__init__.py
pregame/contracts.py
pregame/events.py
tests/test_pregame_contracts.py
```

Do not include yet:

- event store,
- projector,
- GUI changes,
- automated injury scraping,
- public betting automation,
- market provider integration,
- Live Scenario changes.

Acceptance:

- Champion CORE regression passes.
- Contract tests pass.
- No production model file changes.
- No Champion CORE threshold changes.
- No Variant B logic changes.
