
You are helping me prepare a 19-point NFL betting model audit called Variant B.

IMPORTANT:
- I do not want picks.
- I do not want a betting recommendation.
- I do not want you to decide whether to bet.
- I want a structured research/audit package for one NFL game.
- If data is unavailable, mark it as MISSING, UNKNOWN, NOT_ASSESSABLE, PENDING_NOT_DUE, or POST_EVENT_ONLY.
- Do not invent facts.
- Do not call movement "sharp", "steam", "public", or "respected" unless the source supports that exact claim.
- Separate confirmed facts from assumptions, risks, missing data, and pending-not-due items.
- Use direct primary sources where possible.
- If you use secondary sources, label them as context, not final proof.
- A language model may summarize, but deterministic calculations should be left to Python/rule engine.
- Do not calculate EV, CLV, no-chase status, price quality, or final operator gate if required inputs are missing.
- For any spread, keep both the exact value and the nearest 0.5 rounded display value.
- For whole-number spreads such as -3, +3, -7, +7, explicitly preserve push logic.

GAME_INPUT:
  season:
  week:
  game_date_local:
  game_date_usa:
  scheduled_kickoff_local:
  scheduled_kickoff_utc:
  away_team:
  home_team:
  venue:
  venue_city_country:
  neutral_site: true/false/unknown
  international_game: true/false/unknown
  designated_home_team:
  market: full-game spread
  selected_team:
  current_spread_selected_team:
  current_price:
  book_or_source:
  quote_timestamp_utc:
  executable_status: confirmed_executable / displayed_unverified / manual_consensus / unknown
  model_version:
  model_run_id:
  model_generated_at_utc:
  model_fair_margin_selected_team_raw:
  model_fair_margin_selected_team_rounded_to_0_5:
  edge_vs_line_points_raw:
  edge_vs_line_points_rounded_to_0_5:
  model_tag: VALUE PLAY / GOW / GOM / GOY / NEUTRAL / unknown
  p_cover:
  p_push:
  p_loss:
  margin_pmf_available: true/false/unknown
  acceptable_quote_frontier_available: true/false/unknown
```

## Output format

Return one structured YAML-style report with this exact top-level structure:

```yaml
audit_metadata:
  game_identity:
  research_timestamp_utc:
  research_cutoff_utc:
  source_policy:
  warnings:

points:
  - point_number:
    point_name:
    purpose:
    automation_level: FULL | SEMI | MANUAL | HYBRID | INTERNAL_ONLY
    due_status: DUE | NOT_DUE | POST_EVENT_ONLY | UNKNOWN
    criticality: HARD_REQUIRED | HARD_WHEN_DUE | SOFT_REQUIRED | CONTEXT_ONLY | POST_EVENT
    confirmed_facts:
    missing_data:
    pending_not_due:
    not_assessable:
    source_evidence:
      - source_name:
        source_url:
        source_tier: PRIMARY | SECONDARY | CONTEXT_ONLY | INTERNAL_REQUIRED
        captured_or_accessed_at:
        supports_claim:
    deterministic_checks:
    manual_review_needed:
    recommended_machine_fields:
    test_game_output:
    reason_codes:

summary:
  hard_blockers:
  warnings:
  pending_not_due:
  internal_inputs_required_from_me:
  data_to_capture_manually:
  next_best_action:
```

## 19 audit points and source instructions

### 1. argument_against

Purpose: strongest argument against the model pick.

Use mainly internal model artifacts:
- model run id, model version, commit/input hash
- fair margin, edge formula, model tag
- margin PMF, p_cover, p_push, p_loss
- calibration/uncertainty report
- model-generation market snapshot
- neutral-site/home-field adjustment logs
- sportsbook house rules for push/OT/settlement

Do not treat a raw fair-margin edge as full EV. If p_cover, p_push and p_loss are missing, mark full EV as NOT_ASSESSABLE.

### 2. market_move_notes

Purpose: describe movement from opener, model-generation quote and current executable quote.

Preferred sources:
- own append-only model-generation quote snapshot
- direct sportsbook/betslip confirmation
- OpticOdds
- Betstamp PRO / SpotOdds / Unabated
- The Odds API as budget source
- SportsDataIO
- Don Best as secondary validation
- OddsPortal/Covers only as sanity check

Track separately:
- opener
- model-generation quote
- current executable quote

Do not assign no-chase status yourself unless deterministic data exists.

### 3. injury_role_notes

Purpose: identify injury/status/role risks that could affect the edge.

Sources:
- NFL official injury report
- NFL official inactives
- official team injury reports
- official team transactions/roster designations
- official team PR/communications accounts
- official gamebooks, participation, snap counts
- 32BeatWriters and original beat reporters as context only
- RotoWire / Footballguys / SICScore / Fantasy Life / ETR / Rotoworld / FantasyPros as secondary context

Before injury reports/inactives are published, return PENDING_NOT_DUE. Do not infer that teams are healthy.

### 4. schedule_spot_notes

Purpose: schedule, travel, rest, timezone, international/neutral-site and acclimation context.

Sources:
- NFL official schedule
- NFL Football Operations / International Games
- official team schedules
- official venue/event page
- nflverse/nflreadpy schedule
- IANA timezone database
- audited venue registry
- GeographicLib/geodesic distance
- official team travel/practice/acclimation info if available
- team PR, coach press conferences, official transcripts
- AP/Reuters/credentialed beat reporters as context

Do not claim a travel advantage unless itinerary/acclimation evidence exists.

### 5. weather_notes

Purpose: game-window weather and venue/field operation risk.

Sources:
- official weather service for the venue jurisdiction
- for USA: NOAA / National Weather Service
- for Australia: Bureau of Meteorology, BOM MetEye, BOM ADFD, BOM observations/radar/warnings
- official venue operating notices
- NFL/team PR for roof, surface and field operations
- licensed weather provider if available
- Open-Meteo only as budget secondary source

If the official forecast does not yet cover the game window, return PENDING_NOT_DUE.

### 6. key_number_check

Purpose: check if the spread is on, off, through or near key numbers.

Sources:
- own quote event ledger
- market snapshot and model-generation quote path
- model margin PMF
- internal key-number config
- sportsbook house rules
- OpticOdds/SportsDataIO for quote path validation
- nflverse/nflreadpy for historical validation

Any integer spread can push. Treat 3 and 7 as primary key numbers unless our policy says otherwise.

### 7. no_chase_limit

Purpose: determine if the current quote is still playable under frozen limits.

Sources:
- immutable model-generation quote
- versioned no-chase policy
- model PMF and p_cover/p_push/p_loss
- acceptable quote frontier generated at model run
- direct sportsbook/betslip confirmation
- eligible-books policy
- house rules
- OpticOdds/SportsDataIO/Betstamp/Unabated

Do not recreate a missing model-generation quote manually after the fact.

### 8. price_quality

Purpose: evaluate whether the available price is executable and sufficient for positive expected value.

Sources:
- model PMF
- p_cover, p_push, p_loss
- acceptable quote frontier
- direct sportsbook/betslip confirmation at target stake
- house rules
- OpticOdds/SportsDataIO/The Odds API/Betstamp/Unabated

If only manual consensus exists, return NOT_ASSESSABLE. Preserve push-aware logic.

### 9. market_snapshot

Purpose: capture the exact decision/execution quote.

Evidence grades:
- EXECUTED_GRADE: accepted ticket/digital receipt
- DIRECT_BOOK_GRADE: direct book betslip checked at target stake
- PROVIDER_GRADE: named-book provider quote with timestamp
- PREVIEW_ONLY: manual consensus or unverified screen
- INVALID: inconsistent or fabricated evidence

Required:
- event, side, market, market scope
- book/source
- spread and price from same atomic quote
- timestamp
- quote id if available
- executable status
- target stake check if direct-book grade

### 10. public_bias / tickets_handle

Purpose: context for public betting concentration, not sharp-money proof.

Sources:
- DraftKings direct betting splits
- VSiN Pro with DK/Circa separated
- Sports Insights
- Action Network
- official BetMGM/FanDuel/Caesars market-specific publications
- ScoresAndOdds secondary
- Covers Consensus only as community sentiment

Do not average percentages from different providers without denominator and sample rules.

### 11. power_rankings_check

Purpose: sanity check internal team-strength view against external benchmarks.

Sources:
- internal neutral-field PowerScore / internal_neutral_power_gap
- ESPN FPI
- PFF Point Spread Team Ratings
- FTN DVOA/DAVE
- nfelo
- internal market-implied neutral rating
- SumerSports
- NFL.com/The Athletic/ESPN editorial only as narrative context

Prefer point-based neutral-field comparison over ordinal rank comparison.

### 12. roster_change_check

Purpose: detect whether roster/staff/role changes make the model baseline stale.

Sources:
- internal model roster baseline, role baseline, staff baseline
- official team roster pages
- official team transactions
- NFL official transactions
- official coaching announcements/staff pages
- NFL Draft Tracker
- gamebooks/starters/inactives
- nflverse/nflreadpy rosters and snap counts
- Sportradar/SportsDataIO/PFF/Ourlads/Over The Cap/Spotrac as context or automation

Without an internal frozen baseline, return NOT_ASSESSABLE.

### 13. matchup_specific_risk

Purpose: test the model edge against matchup conflicts.

Sources:
- internal matchup dependency report
- internal feature contribution / sensitivity report
- nflverse/nflreadpy EPA, success, pace, xpass, split queries
- injuries/rosters/roles/gamebooks from points 3 and 12
- ESPN Analytics win rates
- Next Gen Stats / NFL Pro
- PFF Premium
- FTN, SumerSports, SIS, TruMedia

Start from the internal model edge drivers. Do not invent random matchup narratives.

### 14. game_script_risk

Purpose: stress-test the edge under plausible game-script scenarios.

Sources:
- internal play-by-play/possession simulator
- internal PMF and p_cover/p_push/p_loss
- frozen scenario policy
- nflverse/nflreadpy/nflfastR play-by-play
- Next Gen Stats/NFL Pro
- SIS/TruMedia
- SumerSports
- current roster/injury/weather/market inputs

If no simulator/PMF exists, return NOT_ASSESSABLE.

### 15. closing_line

Purpose: capture the final pregame closing spread.

Sources:
- internal append-only quote ledger
- direct sportsbook close capture
- OpticOdds full quote history
- SportsDataIO provider-declared close
- The Odds API fallback snapshots
- Betstamp/Unabated manual QA
- manual screenshot only as fallback

Before market close, return POST_EVENT_ONLY or PENDING_NOT_DUE. Do not use scheduled kickoff as close timestamp unless the market actually closed then.

### 16. closing_price

Purpose: capture the closing price tied to the same close snapshot as point 15.

Sources:
- same close_snapshot_id as point 15
- internal quote ledger
- direct sportsbook close capture
- OpticOdds/SportsDataIO/The Odds API
- Betstamp/Unabated
- full closing ladder and both sides when available

Do not separate closing price from closing line.

### 17. clv_points

Purpose: calculate CLV from decision snapshot and close snapshot.

Sources:
- point 9 decision snapshot
- point 15/16 close snapshot
- internal quote ledger
- full closing ladder
- point 6 key-number context
- internal selected-team spread convention
- Python rule engine

Do not calculate CLV if point 15/16 are missing. Do not combine spread CLV and price CLV into one fake number.

### 18. process_quality

Purpose: internal quality gate for points 1-17.

Sources:
- immutable audit bundle
- process policy registry
- event clock/due window engine
- evidence manifest
- calculation manifest
- model lineage
- manual override log

Return:
- run_status
- domain_status
- due_status
- criticality
- gate_effect
- effective_status
- readiness by phase

Not-due items should not count as failures. Due hard blockers override any numeric score.

### 19. final_operator_decision

Purpose: deterministic action router based on point 18.

Sources:
- frozen process_quality snapshot
- operator decision policy
- audit phase state
- blocker classification registry
- action routing registry
- manual override log
- append-only operator decision ledger

Return separately:

```yaml
gate_state: OPEN | HOLD | INVALID
operator_action: HOLD_PENDING_DATA | RETURN_FOR_DATA_CORRECTION | RETURN_FOR_MODEL_RERUN | READY_FOR_NEXT_AUDIT_STAGE | AUDIT_COMPLETE | INVALID_AUDIT
hold_type:
required_actions:
nonblocking_pending_items:
prohibited_transitions:
decision_provenance:
```

Do not say PLAY/PASS as a betting recommendation.

## Final summary required

At the end, provide:

```yaml
final_summary:
  audit_readiness_now:
  due_hard_blockers:
  not_due_items:
  post_event_only_items:
  data_i_must_enter_manually:
  data_gpt_found_with_sources:
  data_that_requires_internal_python:
  next_step_for_me:
  safe_to_advance_to_next_audit_stage: true/false
```
```