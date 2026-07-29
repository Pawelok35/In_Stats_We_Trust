# GPT Snapshot

season: 2026
week: 1
game_id: 2026_w01_MIA_at_LV
snapshot_type: full_19_points
created_at_local: 2026-07-28T18:06:13.873580+02:00
source_thread: GPT

## GPT Output

audit_metadata:
game_identity:
season: 2026
week: 1
game_id: "2026_w01_MIA_at_LV"
game_date_local: "2026-09-13"
game_date_usa: "2026-09-13"
scheduled_kickoff_local: "2026-09-13T13:25:00-07:00"
scheduled_kickoff_local_display: "Sunday, September 13, 2026 — 1:25 PM PDT"
scheduled_kickoff_utc: "2026-09-13T20:25:00Z"
away_team: "MIA"
home_team: "LV"
designated_home_team: "LV"
venue: "Allegiant Stadium"
venue_city_country: "Las Vegas, Nevada, USA"
venue_address: "3333 Al Davis Way, Las Vegas, NV 89118"
neutral_site: false
international_game: false
market: "full-game spread"
selected_team: "MIA"
current_spread_selected_team_exact: 3.5
current_spread_selected_team_rounded_to_0_5: 3.5
current_price_raw: 102
current_price_display: "+102"
current_price_format: "ASSUMED_AMERICAN; format was not explicitly declared"
book_or_source: "SIM_PREGAME_COM"
quote_timestamp_utc: "2026-09-08T18:00:00Z"
executable_status: "UNKNOWN"
total_exact: 40.5
model_version: "MISSING"
model_run_id: "MISSING"
model_generated_at_utc: "MISSING"
model_fair_margin_selected_team_raw: -9.21
model_fair_margin_selected_team_rounded_to_0_5: -9.0
edge_vs_line_points_raw: 12.71
edge_vs_line_points_rounded_to_0_5: 12.5
model_tag: "GOM"
p_cover: "MISSING"
p_push: "MISSING"
p_loss: "MISSING"
margin_pmf_available: "UNKNOWN"
acceptable_quote_frontier_available: "UNKNOWN"
official_schedule_confirmation: "Miami at Las Vegas, Sunday September 13, 2026, 1:25 PM Pacific / 4:25 PM Eastern. "
venue_confirmation: "Allegiant Stadium is the Raiders’ home venue in Las Vegas and is fully enclosed and climate-controlled. "

research_timestamp_utc: "2026-07-28T15:50:27Z"
research_cutoff_utc: "2026-07-28T15:50:27Z"

source_policy:
governing_framework: "Attached Variant B final research framework. "
hierarchy:
- "Primary official sources for schedule, venue, transactions and injury-report status."
- "Secondary sources only as context or sanity checks."
- "User-supplied model and quote fields retained as internal inputs, not independently verified facts."
- "No reconstruction of opener, model-generation quote or executable quote."
- "No sharp/public/steam characterization without provider-specific evidence."
- "No EV, no-chase, CLV or price-quality conclusion without required deterministic inputs."

warnings:
- code: "FUTURE_DATED_QUOTE"
detail: "The supplied quote timestamp, 2026-09-08T18:00:00Z, is 42 days 2 hours 9 minutes 33 seconds after the research cutoff. It cannot be an observed current quote in this audit."
- code: "SIMULATED_NON_MARKET_GRADE_SOURCE"
detail: "SIM_PREGAME_COM is presented as a simulated source, not a direct sportsbook or verified named-book provider."
- code: "EXECUTABILITY_UNKNOWN"
detail: "No direct betslip, quote ID, accepted stake, maximum stake, named sportsbook or executable-status field was supplied."
- code: "PRICE_FORMAT_ASSUMPTION"
detail: "Raw price 102 is preserved. Display +102 assumes an American-odds convention; this convention was not explicitly provided."
- code: "MODEL_LINEAGE_MISSING"
detail: "Model version, run ID, generation timestamp, input hash, commit hash and calibration artifacts are missing."
- code: "PROBABILITY_DISTRIBUTION_MISSING"
detail: "p_cover, p_push, p_loss and the margin PMF are missing; a 12.71-point raw fair-line discrepancy is not equivalent to verified positive EV."
- code: "SIGN_CONVENTION_NOT_DOCUMENTED"
detail: "The arithmetic is internally consistent, but the semantic sign convention for model margin has not been verified from a model schema."
- code: "MODEL_TAG_NOT_A_RECOMMENDATION"
detail: "GOM is recorded only as the supplied internal model tag and is not treated as a betting recommendation."

points:

point_number: 1
point_name: "argument_against"
purpose: "Identify the strongest evidence-based argument against relying on the model indication."
automation_level: "HYBRID"
due_status: "DUE"
criticality: "HARD_REQUIRED"

confirmed_facts:

"The supplied model values imply MIA +3.5 against a model fair figure of -9.21, producing a reported 12.71-point discrepancy."
"Miami enters 2026 with a new head coach, Jeff Hafley, and substantial offensive personnel turnover, including the departure of Tua Tagovailoa, Tyreek Hill and Jaylen Waddle and the addition of Malik Willis. Official team reporting still described Willis as the presumptive or in-line starter rather than a finalized Week 1 starter at the research cutoff. "
"Las Vegas also has a new head coach, Klint Kubiak, added Kirk Cousins and drafted Fernando Mendoza first overall, leaving material scheme and quarterback-role uncertainty during training camp. "
"Available secondary market context displayed Las Vegas -3.5 and a total of 40.5, but did not validate the supplied +102 price, timestamp or executability. "

missing_data:

"model_version"
"model_run_id"
"model_generated_at_utc"
"model_commit_hash"
"input_data_hash"
"model-generation market snapshot"
"p_cover"
"p_push"
"p_loss"
"margin PMF"
"calibration and uncertainty report"
"frozen 2026 roster, role and coaching baseline"
"feature-contribution or sensitivity report"
"selected-team margin sign-convention documentation"

pending_not_due:

"Official Week 1 injury reports and inactives."
"Final Week 1 quarterback and role confirmation."

not_assessable:

"Full expected value."
"Whether the GOM tag remains valid after 2026 roster and coaching changes."
"Whether the 12.71-point discrepancy represents genuine model information, stale inputs, sign/convention error or unmodelled regime change."

source_evidence:

source_name: "USER_GAME_INPUT"
source_url: "Conversation input; no external URL"
source_tier: "INTERNAL_REQUIRED"
captured_or_accessed_at: "2026-07-28T15:50:27Z"
supports_claim: "Supplied spread, price, model margin, edge and model tag."
source_name: "Miami Dolphins official coaching and transaction material"
source_url: "Official team sources "
source_tier: "PRIMARY"
captured_or_accessed_at: "2026-07-28T15:50:27Z"
supports_claim: "Miami coaching, quarterback and roster turnover."
source_name: "Las Vegas Raiders official coaching, roster and quarterback material"
source_url: "Official team sources "
source_tier: "PRIMARY"
captured_or_accessed_at: "2026-07-28T15:50:27Z"
supports_claim: "Las Vegas coaching and quarterback-room changes."
source_name: "TeamRankings matchup page"
source_url: "Secondary market context "
source_tier: "CONTEXT_ONLY"
captured_or_accessed_at: "2026-07-28T15:50:27Z"
supports_claim: "Context-only display of LV -3.5 and total 40.5."

deterministic_checks:
edge_arithmetic:
formula_tested: "market spread selected team - model fair figure selected team"
calculation: "3.50 - (-9.21) = 12.71"
result: "PASS_ARITHMETIC_ONLY"
semantic_convention_validation: "NOT_ASSESSABLE"
rounded_values:
model_fair_margin_nearest_0_5: -9.0
edge_nearest_0_5: 12.5
ev_calculation: "NOT_PERFORMED"

manual_review_needed:

"Confirm the model’s selected-team sign convention."
"Inspect whether the model run included Miami’s and Las Vegas’s 2026 coaching, quarterback and skill-position changes."
"Check model calibration for very large Week 1 fair-line disagreements."

recommended_machine_fields:

"model_lineage_complete"
"roster_baseline_cutoff_utc"
"staff_baseline_cutoff_utc"
"qb_role_baseline"
"margin_pmf_id"
"calibration_report_id"
"sign_convention_version"
"extreme_edge_outlier_flag"

test_game_output:
strongest_argument_against: "The very large reported discrepancy may be driven by stale or incorrectly mapped inputs during a two-team coaching/QB regime change. It cannot be validated without model lineage, probability outputs, calibration and a frozen 2026 baseline."
full_ev_status: "NOT_ASSESSABLE"
model_tag_validation: "NOT_ASSESSABLE"

reason_codes:

"MODEL_LINEAGE_MISSING"
"PMF_MISSING"
"CALIBRATION_MISSING"
"ROSTER_REGIME_CHANGE"
"SIGN_CONVENTION_UNVERIFIED"
"EXTREME_EDGE_REQUIRES_REVIEW"

point_number: 2
point_name: "market_move_notes"
purpose: "Separate the opener, model-generation quote and current executable quote."
automation_level: "SEMI"
due_status: "DUE"
criticality: "HARD_REQUIRED"

confirmed_facts:

"The user supplied MIA +3.5 at raw price 102 from SIM_PREGAME_COM, timestamped 2026-09-08T18:00:00Z."
"That timestamp is 42 days 2 hours 9 minutes 33 seconds after this audit’s research cutoff and 5 days 2 hours 25 minutes before scheduled kickoff."
"A secondary line-history page displayed anonymous or non-executable context around LV -3.0 and LV -3.5, but did not provide an attributable atomic quote with the required price and timestamp. "

missing_data:

"verified opener with source, timestamp, spread and price"
"model-generation quote"
"model-generation quote timestamp"
"current quote observable at the research cutoff"
"current executable named-book quote"
"append-only quote ledger"
"atomic quote IDs"
"full two-sided price ladder"

pending_not_due: []

not_assessable:

"Magnitude and direction of true movement."
"Whether the line reached, crossed or returned through +3."
"Any sharp, steam, respected-money or public-money characterization."
"No-chase status."

source_evidence:

source_name: "USER_GAME_INPUT"
source_url: "Conversation input; no external URL"
source_tier: "INTERNAL_REQUIRED"
captured_or_accessed_at: "2026-07-28T15:50:27Z"
supports_claim: "Future-dated simulated quote."
source_name: "TeamRankings line-movement page"
source_url: "Secondary contextual history "
source_tier: "CONTEXT_ONLY"
captured_or_accessed_at: "2026-07-28T15:50:27Z"
supports_claim: "Anonymous/contextual LV -3.0 and -3.5 displays only."

deterministic_checks:
chronology_check:
research_cutoff_utc: "2026-07-28T15:50:27Z"
supplied_quote_timestamp_utc: "2026-09-08T18:00:00Z"
result: "FAIL_FUTURE_TIMESTAMP_RELATIVE_TO_AUDIT"
quote_to_kickoff:
duration: "5 days 2 hours 25 minutes"
result: "TIMESTAMP_PRECEDES_SCHEDULED_KICKOFF"
movement_calculation: "NOT_PERFORMED"

manual_review_needed:

"Provide actual opener, model-generation and decision snapshots from the quote ledger."
"Verify each quote from one named book with spread and price captured atomically."

recommended_machine_fields:

"opener_snapshot_id"
"model_generation_snapshot_id"
"decision_snapshot_id"
"book_id"
"quote_id"
"captured_at_utc"
"provider_received_at_utc"
"spread"
"price"
"executable_status"

test_game_output:
opener: "MISSING"
model_generation_quote: "MISSING"
supplied_future_quote:
spread: "MIA +3.5"
price_raw: 102
source: "SIM_PREGAME_COM"
timestamp_utc: "2026-09-08T18:00:00Z"
usability_at_research_cutoff: "INVALID_FOR_CURRENT-MARKET_VERIFICATION"
current_executable_quote_at_cutoff: "MISSING"
movement_description: "NOT_ASSESSABLE"

reason_codes:

"OPENER_MISSING"
"MODEL_GENERATION_QUOTE_MISSING"
"CURRENT_EXECUTABLE_QUOTE_MISSING"
"FUTURE_DATED_QUOTE"
"NO_MARKET_CHARACTERIZATION"

point_number: 3
point_name: "injury_role_notes"
purpose: "Identify injury, status and role risks that could affect model applicability."
automation_level: "HYBRID"
due_status: "NOT_DUE"
criticality: "HARD_WHEN_DUE"

confirmed_facts:

"The official NFL game page did not yet have Week 1 injury reports available for either Miami or Las Vegas at the research cutoff. "
"For a Sunday game, regular practice-status reporting is expected during game week, with game-status designations ordinarily published Friday. "
"Miami had training-camp designations involving Darrell Baker Jr., Storm Duck and Chris Bell. These are July roster-status facts, not proof of Week 1 availability. "
"Las Vegas had players on reserve/injured, including Corey Rucker and Brodric Martin. These transactions do not by themselves determine the final Week 1 active roster. "

missing_data:

"Week 1 Wednesday practice report"
"Week 1 Thursday practice report"
"Week 1 Friday practice and game-status report"
"official inactives"
"final depth-chart and starting-role confirmation"
"snap-share expectations"
"replacement-quality and unit-chain-reaction assessment"

pending_not_due:

"Official practice reports."
"Final game-status designations."
"Official inactives, ordinarily released close to kickoff."

not_assessable:

"Game-specific injury advantage."
"Net injury adjustment to the spread."
"Whether current training-camp designations affect Week 1."
"Final quarterback and skill-position role impacts."

source_evidence:

source_name: "NFL official game center"
source_url: "Official injury-report status "
source_tier: "PRIMARY"
captured_or_accessed_at: "2026-07-28T15:50:27Z"
supports_claim: "Game-specific injury reports are not yet available."
source_name: "NFL 2026 important dates and reporting guidance"
source_url: "Official NFL source "
source_tier: "PRIMARY"
captured_or_accessed_at: "2026-07-28T15:50:27Z"
supports_claim: "Expected reporting cadence for Sunday games."
source_name: "Official team transactions"
source_url: "Miami and Las Vegas transaction records "
source_tier: "PRIMARY"
captured_or_accessed_at: "2026-07-28T15:50:27Z"
supports_claim: "Current training-camp roster designations only."

deterministic_checks:
injury_due_engine:
scheduled_game_day: "Sunday"
research_date: "2026-07-28"
game_week_started: false
result: "PENDING_NOT_DUE"
healthy_team_inference: "PROHIBITED"

manual_review_needed:

"Re-run after each official game-week injury report."
"Map each listed player to expected starter status, snap share, replacement and unit impact."
"Capture official inactives before any final pregame audit stage."

recommended_machine_fields:

"report_date"
"player_id"
"practice_status"
"game_status"
"active_inactive_status"
"projected_role"
"baseline_snap_share"
"replacement_player_id"
"unit_impact"
"source_timestamp"

test_game_output:
official_injury_report_status: "PENDING_NOT_DUE"
official_inactives_status: "PENDING_NOT_DUE"
current_transaction_context: "AVAILABLE_BUT_NOT_GAME_STATUS_PROOF"
injury_edge_adjustment: "NOT_ASSESSABLE"

reason_codes:

"GAME_WEEK_REPORT_NOT_DUE"
"INACTIVES_NOT_DUE"
"DO_NOT_INFER_HEALTH"
"ROLE_CONFIRMATION_PENDING"

point_number: 4
point_name: "schedule_spot_notes"
purpose: "Document schedule, travel, rest, timezone and venue context without unsupported advantage claims."
automation_level: "HYBRID"
due_status: "DUE"
criticality: "SOFT_REQUIRED"

confirmed_facts:

"The game is scheduled for Sunday, September 13, 2026 at 1:25 PM Pacific at Allegiant Stadium in Las Vegas. "
"Las Vegas is the designated home team; the game is neither neutral-site nor international."
"The UTC kickoff is 2026-09-13T20:25:00Z; the corresponding Miami/Eastern time is 4:25 PM."
"Miami’s listed final preseason game is August 28, while Las Vegas’s is August 27. Their regular-season opener is September 13. "
"Miami opens the regular season on the road in Las Vegas. "

missing_data:

"Miami travel departure and arrival itinerary"
"hotel and acclimation plan"
"practice-location and travel-day information"
"verified team-specific travel disruption"
"any model-specific Week 1 rest adjustment"

pending_not_due:

"Official team travel and practice communications nearer game week."

not_assessable:

"Travel advantage or disadvantage."
"Acclimation advantage."
"Whether the one-day difference between final preseason games has practical significance."
"Any claimed body-clock edge."

source_evidence:

source_name: "Las Vegas Raiders official 2026 schedule"
source_url: "Official schedule "
source_tier: "PRIMARY"
captured_or_accessed_at: "2026-07-28T15:50:27Z"
supports_claim: "Week, opponent, date, venue and Pacific kickoff."
source_name: "Miami Dolphins official 2026 schedule"
source_url: "Official schedule "
source_tier: "PRIMARY"
captured_or_accessed_at: "2026-07-28T15:50:27Z"
supports_claim: "Miami road opener and Eastern kickoff."
source_name: "Allegiant Stadium event page"
source_url: "Official venue event listing "
source_tier: "PRIMARY"
captured_or_accessed_at: "2026-07-28T15:50:27Z"
supports_claim: "Venue and local event time."

deterministic_checks:
kickoff_time_conversion:
pacific: "2026-09-13T13:25:00-07:00"
eastern: "2026-09-13T16:25:00-04:00"
utc: "2026-09-13T20:25:00Z"
result: "PASS"
final_preseason_to_kickoff:
MIA: "approximately 15 days 21 hours 25 minutes"
LV: "approximately 16 days 20 hours 25 minutes"
regular_season_rest_asymmetry: "NOT_APPLICABLE_WEEK_1"
travel_advantage_assignment: "NOT_PERFORMED"

manual_review_needed:

"Check official travel/acclimation reporting during game week."
"Confirm any unusual practice or travel disruption before assigning a schedule adjustment."

recommended_machine_fields:

"origin_city"
"destination_city"
"distance_km"
"time_zones_crossed"
"team_departure_utc"
"team_arrival_utc"
"acclimation_nights"
"previous_game_end_utc"
"rest_hours"
"neutral_site"
"international_game"

test_game_output:
schedule_spot: "WEEK_1_MIA_ROAD_AT_LV"
neutral_site: false
international_game: false
designated_home_team: "LV"
verified_travel_advantage: "NONE_CLAIMED"
schedule_risk_status: "PARTIALLY_ASSESSABLE"

reason_codes:

"WEEK_1"
"MIA_ROAD"
"LV_HOME"
"ITINERARY_MISSING"
"NO_TRAVEL_ADVANTAGE_CLAIM"

point_number: 5
point_name: "weather_notes"
purpose: "Assess game-window weather and venue-operation risk."
automation_level: "HYBRID"
due_status: "NOT_DUE"
criticality: "HARD_WHEN_DUE"

confirmed_facts:

"Allegiant Stadium is fully enclosed and climate-controlled, reducing direct exposure to ordinary outdoor temperature, rain and wind. "
"The Raiders identify the playing surface as grass. "
"The game is approximately 47 days after the research cutoff, beyond the normal official NWS local forecast horizon. NWS local forecast products generally cover roughly seven days. "

missing_data:

"official game-window forecast"
"stadium operations notice"
"game-day internal temperature and humidity plan"
"field-condition report"
"any abnormal smoke, air-quality, power or venue-operation advisory"

pending_not_due:

"Official NWS game-window forecast."
"Game-day venue and field-operation notices."

not_assessable:

"Game-specific weather adjustment."
"Field-condition impact."
"Whether exceptional external conditions affect stadium operations."

source_evidence:

source_name: "Allegiant Stadium official overview"
source_url: "Official venue page "
source_tier: "PRIMARY"
captured_or_accessed_at: "2026-07-28T15:50:27Z"
supports_claim: "Enclosed, climate-controlled venue."
source_name: "Las Vegas Raiders stadium information"
source_url: "Official team source "
source_tier: "PRIMARY"
captured_or_accessed_at: "2026-07-28T15:50:27Z"
supports_claim: "Grass playing surface."
source_name: "National Weather Service forecast guidance"
source_url: "Official weather-service material "
source_tier: "PRIMARY"
captured_or_accessed_at: "2026-07-28T15:50:27Z"
supports_claim: "Game date lies outside normal official forecast coverage."

deterministic_checks:
days_from_research_to_game: 47.19
official_forecast_window_reached: false
outdoor_weather_direct_exposure:
baseline: "LOWER_THAN_OPEN_AIR_VENUE"
final_status: "PENDING_GAME_DAY_OPERATIONS"
game_weather_adjustment: "NOT_PERFORMED"

manual_review_needed:

"Re-run NWS and official venue checks inside the seven-day window."
"Capture any stadium-operation or field-condition notice on game day."

recommended_machine_fields:

"forecast_issued_at_utc"
"forecast_valid_from_utc"
"forecast_valid_to_utc"
"temperature"
"wind_speed"
"wind_gust"
"precipitation_probability"
"air_quality"
"venue_enclosed"
"field_surface"
"field_operations_status"

test_game_output:
venue_weather_protection: "CONFIRMED_ENCLOSED_CLIMATE_CONTROLLED"
official_game_window_forecast: "PENDING_NOT_DUE"
weather_risk_assessment: "NOT_ASSESSABLE"

reason_codes:

"ENCLOSED_VENUE"
"FORECAST_NOT_DUE"
"FIELD_OPERATIONS_PENDING"
"NO_WEATHER_ADJUSTMENT"

point_number: 6
point_name: "key_number_check"
purpose: "Preserve exact spread and evaluate its relation to key numbers without inventing quote history."
automation_level: "HYBRID"
due_status: "DUE"
criticality: "HARD_REQUIRED"

confirmed_facts:

"The supplied selected-team spread is exactly MIA +3.5."
"A half-point spread cannot push on an integer final scoring margin."
"The supplied line is one half-point above the primary NFL key number of 3 under the framework policy. The attached framework requires explicit preservation of push logic at whole numbers such as +3 and -3. "
"The supplied model fair figure is -9.21, rounded to -9.0, and the reported edge is 12.71 points, rounded to 12.5."

missing_data:

"verified opener"
"model-generation quote"
"quote-event path"
"full price ladder around MIA +3, +3.5 and +4"
"sportsbook-specific settlement and overtime rules"
"internal key-number configuration version"
"margin PMF"

pending_not_due: []

not_assessable:

"Whether the market arrived at, moved off or crossed 3."
"Probability value of the half-point from +3 to +3.5."
"Push probability at alternative whole-number quotes."
"Whether the current quote breached an internal key-number limit."

source_evidence:

source_name: "USER_GAME_INPUT"
source_url: "Conversation input; no external URL"
source_tier: "INTERNAL_REQUIRED"
captured_or_accessed_at: "2026-07-28T15:50:27Z"
supports_claim: "Exact spread, model margin and reported edge."
source_name: "Variant B framework"
source_url: "Attached policy "
source_tier: "INTERNAL_REQUIRED"
captured_or_accessed_at: "2026-07-28T15:50:27Z"
supports_claim: "Primary treatment of 3 and 7 and preservation of integer push logic."

deterministic_checks:
current_spread:
exact: 3.5
nearest_0_5: 3.5
half_point_line_push_possible: false
nearest_primary_key_number:
key_number: 3
distance_points: 0.5
relation: "ABOVE_KEY_3_FROM_SELECTED_TEAM_PERSPECTIVE"
whole_number_counterfactual:
line: "MIA +3"
settlement_if_MIA_loses_by_exactly_3: "PUSH, subject to book rules"
model_fair:
exact: -9.21
nearest_0_5: -9.0
reported_edge:
exact: 12.71
nearest_0_5: 12.5
quote_path_check: "NOT_ASSESSABLE"

manual_review_needed:

"Load the actual quote path and full ladder."
"Attach source-specific house rules."
"Use the margin PMF to value +3 versus +3.5 rather than applying a generic average."

recommended_machine_fields:

"spread_exact"
"spread_rounded_0_5"
"nearest_key_number"
"distance_to_key"
"integer_push_possible"
"quote_path_crossed_key"
"key_number_policy_version"
"house_rules_id"
"pmf_probability_at_margin_3"

test_game_output:
exact_line: "MIA +3.5"
key_number_relation: "HALF_POINT_ABOVE_3"
current_line_push_possible: false
movement_through_key: "UNKNOWN"
key_number_value: "NOT_ASSESSABLE"

reason_codes:

"EXACT_LINE_PRESERVED"
"NEAR_KEY_3"
"HALF_POINT_NO_PUSH"
"QUOTE_PATH_MISSING"
"PMF_MISSING"
"HOUSE_RULES_MISSING"

point_number: 7
point_name: "no_chase_limit"
purpose: "Determine whether the supplied quote remains inside a frozen acceptable-quote frontier."
automation_level: "INTERNAL_ONLY"
due_status: "DUE"
criticality: "HARD_REQUIRED"

confirmed_facts:

"The supplied quote is MIA +3.5 at raw price 102."
"No frozen no-chase policy, acceptable-quote frontier or verified model-generation quote was supplied."

missing_data:

"immutable model-generation quote"
"versioned no-chase policy"
"acceptable quote frontier generated with the model run"
"margin PMF"
"p_cover"
"p_push"
"p_loss"
"eligible-books policy"
"direct executable quote"
"book settlement rules"

pending_not_due: []

not_assessable:

"No-chase status."
"Maximum acceptable line."
"Maximum acceptable price."
"Whether movement across +3 changes eligibility."

source_evidence:

source_name: "Variant B framework"
source_url: "Attached no-chase requirements "
source_tier: "INTERNAL_REQUIRED"
captured_or_accessed_at: "2026-07-28T15:50:27Z"
supports_claim: "A missing model-generation quote must not be reconstructed and frozen frontier inputs are required."
source_name: "USER_GAME_INPUT"
source_url: "Conversation input; no external URL"
source_tier: "INTERNAL_REQUIRED"
captured_or_accessed_at: "2026-07-28T15:50:27Z"
supports_claim: "Supplied line and price only."

deterministic_checks:
acceptable_quote_frontier_lookup: "FAILED_MISSING_FRONTIER"
model_generation_quote_lookup: "FAILED_MISSING_SNAPSHOT"
no_chase_computation: "NOT_PERFORMED"
manual_reconstruction: "PROHIBITED"

manual_review_needed:

"Provide the frontier produced at model-generation time."
"Provide the frozen no-chase policy version and model-generation snapshot."
"Confirm eligible sportsbook and executable quote."

recommended_machine_fields:

"frontier_id"
"frontier_generated_at_utc"
"frontier_model_run_id"
"max_spread_by_price"
"max_price_by_spread"
"no_chase_policy_version"
"decision_snapshot_id"
"eligible_book_status"

test_game_output:
no_chase_status: "NOT_ASSESSABLE"
fallback_manual_limit: "NOT_CREATED"
quote_eligibility: "UNKNOWN"

reason_codes:

"FRONTIER_MISSING"
"NO_CHASE_POLICY_MISSING"
"MODEL_GENERATION_QUOTE_MISSING"
"PMF_MISSING"
"EXECUTABLE_QUOTE_MISSING"

point_number: 8
point_name: "price_quality"
purpose: "Evaluate whether the exact spread-price combination is executable and sufficient under push-aware probability inputs."
automation_level: "HYBRID"
due_status: "DUE"
criticality: "HARD_REQUIRED"

confirmed_facts:

"The raw supplied price is 102; it is displayed as +102 only under an assumed American-odds convention."
"The source is simulated and no direct-book execution check was supplied."
"The current spread is +3.5, so the exact quoted spread itself has no push outcome; however p_cover and p_loss are still required for EV."

missing_data:

"explicit price format"
"p_cover"
"p_push"
"p_loss"
"margin PMF"
"acceptable quote frontier"
"direct sportsbook quote"
"target stake and accepted maximum"
"house rules"
"book eligibility status"

pending_not_due: []

not_assessable:

"Positive or negative expected value."
"Minimum required price."
"Price cushion."
"Executable price quality."
"Stake capacity."

source_evidence:

source_name: "USER_GAME_INPUT"
source_url: "Conversation input; no external URL"
source_tier: "INTERNAL_REQUIRED"
captured_or_accessed_at: "2026-07-28T15:50:27Z"
supports_claim: "Raw price 102 and simulated source."
source_name: "Variant B framework"
source_url: "Attached EV and price-quality policy "
source_tier: "INTERNAL_REQUIRED"
captured_or_accessed_at: "2026-07-28T15:50:27Z"
supports_claim: "Price quality must remain not assessable without probabilities and executable evidence."

deterministic_checks:
raw_price_preservation: 102
normalized_display: "+102_ASSUMING_AMERICAN"
implied_probability_calculation: "NOT_USED_FOR_PRICE_QUALITY"
ev_calculation: "NOT_PERFORMED"
acceptable_price_check: "NOT_PERFORMED"

manual_review_needed:

"Declare the price format."
"Supply push-aware probabilities and the acceptable quote frontier."
"Verify the line and price in a direct sportsbook betslip at the intended stake."

recommended_machine_fields:

"price_format"
"price_raw"
"decimal_price_normalized"
"p_cover"
"p_push"
"p_loss"
"ev_per_unit"
"minimum_acceptable_price"
"target_stake"
"max_accepted_stake"
"direct_betslip_checked_at_utc"

test_game_output:
supplied_price: 102
normalized_price: "+102_ASSUMED"
executable_status: "UNKNOWN"
price_quality_status: "NOT_ASSESSABLE"
ev_status: "NOT_ASSESSABLE"

reason_codes:

"PRICE_FORMAT_UNCONFIRMED"
"PMF_MISSING"
"PROBABILITIES_MISSING"
"FRONTIER_MISSING"
"NON_EXECUTABLE_SOURCE"

point_number: 9
point_name: "market_snapshot"
purpose: "Grade the exact decision or execution quote."
automation_level: "HYBRID"
due_status: "DUE"
criticality: "HARD_REQUIRED"

confirmed_facts:

"Event identity, selected team, market scope, spread, raw price, source label and supplied timestamp are present."
"Spread and price were supplied together in the same user input."
"The supplied timestamp lies after the audit cutoff and therefore cannot represent an observed quote available during this research run."
"Secondary context displayed LV -3.5 and total 40.5, but did not verify MIA +3.5 at +102 from a named sportsbook. "

missing_data:

"named sportsbook"
"quote ID"
"provider event ID"
"direct betslip"
"target-stake check"
"accepted maximum stake"
"explicit executable_status"
"provider capture timestamp"
"screenshotted or ledger-backed atomic quote evidence"

pending_not_due: []

not_assessable:

"Actual executability."
"Whether +102 was available from an eligible book."
"Whether the quote could be accepted at the intended stake."

source_evidence:

source_name: "USER_GAME_INPUT"
source_url: "Conversation input; no external URL"
source_tier: "INTERNAL_REQUIRED"
captured_or_accessed_at: "2026-07-28T15:50:27Z"
supports_claim: "Supplied simulated quote fields."
source_name: "TeamRankings matchup page"
source_url: "Secondary context only "
source_tier: "CONTEXT_ONLY"
captured_or_accessed_at: "2026-07-28T15:50:27Z"
supports_claim: "Contextual line and total, not exact price/execution validation."

deterministic_checks:
atomic_input_completeness:
event: true
selected_side: true
market_scope: true
spread: true
price: true
source_label: true
timestamp: true
named_market_grade_book: false
quote_id: false
executable_status: false
target_stake_check: false
chronology: "FAIL_FUTURE_RELATIVE_TO_RESEARCH_CUTOFF"
evidence_grade: "PREVIEW_ONLY"
evidence_validity_for_execution: "INSUFFICIENT"

manual_review_needed:

"Replace the simulated future snapshot with a timestamped direct-book or named-provider snapshot."
"Capture quote ID, exact target stake and accepted maximum."
"Record the explicit executable-status enum."

recommended_machine_fields:

"decision_snapshot_id"
"event_id"
"book_id"
"market_type"
"period"
"selected_team"
"spread"
"price"
"quote_id"
"captured_at_utc"
"executable_status"
"target_stake"
"max_accepted_stake"
"evidence_grade"

test_game_output:
event: "2026_w01_MIA_at_LV"
side: "MIA"
market: "full-game spread"
spread: 3.5
price_raw: 102
source: "SIM_PREGAME_COM"
timestamp_utc: "2026-09-08T18:00:00Z"
executable_status: "UNKNOWN"
evidence_grade: "PREVIEW_ONLY"
snapshot_status: "HARD_BLOCKER"

reason_codes:

"SIMULATED_SOURCE"
"FUTURE_DATED_SNAPSHOT"
"NAMED_BOOK_MISSING"
"EXECUTABLE_STATUS_MISSING"
"TARGET_STAKE_NOT_CHECKED"
"QUOTE_ID_MISSING"

point_number: 10
point_name: "public_bias_tickets_handle"
purpose: "Record provider-specific public betting concentration as context only."
automation_level: "MANUAL"
due_status: "NOT_DUE"
criticality: "CONTEXT_ONLY"

confirmed_facts:

"No provider-specific tickets or handle percentages were supplied or verified."
"No claim of sharp, public, steam or respected-money movement is supported."

missing_data:

"provider name"
"book or contributing-book universe"
"market scope"
"ticket percentage"
"handle percentage"
"sample size or denominator"
"capture timestamp"
"provider methodology"

pending_not_due:

"Meaningful game-week betting-split capture."
"Final pregame split snapshot, if included in the operating process."

not_assessable:

"Public concentration."
"Ticket-versus-money divergence."
"Whether any split is informative."
"Any sharp-money interpretation."

source_evidence:

source_name: "Variant B framework"
source_url: "Attached public-bias source policy "
source_tier: "INTERNAL_REQUIRED"
captured_or_accessed_at: "2026-07-28T15:50:27Z"
supports_claim: "Provider percentages must not be averaged or characterized without denominator and source rules."

deterministic_checks:
provider_specific_data_present: false
market_specific_data_present: false
percentage_aggregation: "NOT_PERFORMED"
sharp_public_label: "PROHIBITED"

manual_review_needed:

"Capture one or more named providers separately during game week."
"Preserve each provider’s denominator, market and timestamp."

recommended_machine_fields:

"provider"
"book_universe"
"market"
"tickets_pct"
"handle_pct"
"sample_size"
"captured_at_utc"
"methodology_note"

test_game_output:
tickets_pct: "MISSING"
handle_pct: "MISSING"
public_bias_status: "PENDING_NOT_DUE"
sharp_money_claim: "NONE"

reason_codes:

"SPLITS_MISSING"
"CONTEXT_ONLY"
"NO_SHARP_PUBLIC_LABEL"

point_number: 11
point_name: "power_rankings_check"
purpose: "Compare the internal neutral-field team-strength view with external point-based benchmarks."
automation_level: "HYBRID"
due_status: "DUE"
criticality: "SOFT_REQUIRED"

confirmed_facts:

"The internal model implies a very large selected-team view relative to the supplied market line, but no internal neutral-field PowerScore or team-strength decomposition was supplied."
"ESPN’s published 2026 FPI discussion described Miami as the lowest-rated team in its preseason view. "
"An ESPN roster-ranking article placed Miami 32nd and Las Vegas 27th. "
"Sharp Football’s preseason ordinal rankings placed Miami 32nd and Las Vegas 29th. "
"Those external results are ordinal or editorial context, not equivalent to a point-based neutral-field spread rating."

missing_data:

"internal neutral-field PowerScore for MIA"
"internal neutral-field PowerScore for LV"
"internal neutral power gap"
"home-field adjustment"
"exact current ESPN FPI point values"
"point-based PFF, DVOA/DAVE, nfelo or Sumer ratings captured on one date"
"market-implied neutral rating calculation policy"

pending_not_due:

"Updated ratings after final preseason roster and role decisions."

not_assessable:

"Exact external neutral-field point gap."
"Whether external ratings validate the model’s 12.71-point discrepancy."
"A comparable consensus power-rating difference."

source_evidence:

source_name: "ESPN preseason FPI discussion"
source_url: "Secondary benchmark context "
source_tier: "SECONDARY"
captured_or_accessed_at: "2026-07-28T15:50:27Z"
supports_claim: "Miami positioned at the bottom of ESPN’s preseason FPI discussion."
source_name: "ESPN roster rankings"
source_url: "Secondary roster benchmark "
source_tier: "SECONDARY"
captured_or_accessed_at: "2026-07-28T15:50:27Z"
supports_claim: "Ordinal MIA 32, LV 27 roster ranking."
source_name: "Sharp Football preseason rankings"
source_url: "Secondary ordinal context "
source_tier: "CONTEXT_ONLY"
captured_or_accessed_at: "2026-07-28T15:50:27Z"
supports_claim: "Ordinal MIA 32, LV 29 ranking."

deterministic_checks:
internal_neutral_power_gap: "MISSING"
comparable_external_point_ratings_count: 0
ordinal_to_points_conversion: "NOT_PERFORMED"
model_market_disagreement:
raw_points: 12.71
status: "EXTREME_OUTLIER_REQUIRING_INTERNAL_REVIEW"

manual_review_needed:

"Capture point-based ratings from multiple sources on the same date."
"Compare neutral-field gaps, not ordinal ranks."
"Explain which model features create a view opposite to current external context."

recommended_machine_fields:

"internal_mia_neutral_rating"
"internal_lv_neutral_rating"
"internal_neutral_power_gap"
"home_field_adjustment"
"external_source"
"external_rating_date"
"external_mia_point_rating"
"external_lv_point_rating"
"external_neutral_gap"

test_game_output:
internal_power_gap: "MISSING"
external_point_gap: "MISSING"
external_ordinal_context: "DOES_NOT_CORROBORATE_A_LARGE_MIA_ADVANTAGE"
power_rankings_check_status: "NOT_ASSESSABLE"

reason_codes:

"INTERNAL_POWER_GAP_MISSING"
"POINT_BASED_EXTERNAL_DATA_MISSING"
"ORDINAL_CONTEXT_ONLY"
"MODEL_VIEW_OUTLIER"

point_number: 12
point_name: "roster_change_check"
purpose: "Determine whether roster, staff and role changes make the model baseline stale."
automation_level: "HYBRID"
due_status: "DUE"
criticality: "HARD_REQUIRED"

confirmed_facts:

"Miami hired Jeff Hafley as head coach for 2026. "
"Miami’s official transaction material records major turnover including Tua Tagovailoa, Tyreek Hill and Jaylen Waddle leaving and Malik Willis joining. "
"Miami’s official reporting described Willis as in line or presumptive to start, while acknowledging ongoing evaluation rather than a fully settled game-week role. "
"Las Vegas has Klint Kubiak as head coach and added major personnel including Kirk Cousins, while drafting Fernando Mendoza first overall. "
"The Raiders’ quarterback hierarchy was still a live training-camp subject at the research cutoff. "

missing_data:

"internal frozen roster baseline"
"internal frozen role baseline"
"internal frozen staff and scheme baseline"
"baseline cutoff timestamp"
"model feature mapping for changed players and coaches"
"final Week 1 depth charts"
"expected snap shares"
"offensive-line and secondary role reconciliation"
"specialist baseline"

pending_not_due:

"Final roster reductions."
"Official Week 1 depth and inactive decisions."
"Final confirmation of starting quarterbacks and supporting roles."

not_assessable:

"Whether the model run includes all relevant 2026 changes."
"Whether the model requires rerunning."
"Quantitative spread impact of each change."
"Baseline staleness status."

source_evidence:

source_name: "Miami Dolphins official sources"
source_url: "Coaching, transactions and quarterback reporting "
source_tier: "PRIMARY"
captured_or_accessed_at: "2026-07-28T15:50:27Z"
supports_claim: "Material Miami staff, QB and skill-position turnover."
source_name: "Las Vegas Raiders official sources"
source_url: "Coaching, offseason moves and QB room "
source_tier: "PRIMARY"
captured_or_accessed_at: "2026-07-28T15:50:27Z"
supports_claim: "Material Las Vegas staff and quarterback changes."

deterministic_checks:
internal_baseline_present: false
external_change_events_present: true
baseline_staleness_comparison: "NOT_PERFORMED"
mandatory_rerun_status: "NOT_ASSESSABLE"

manual_review_needed:

"Compare official 2026 roster/staff state with the exact baseline embedded in the model run."
"Map each material change to affected model features."
"Rerun the model if the baseline predates material changes."

recommended_machine_fields:

"baseline_roster_snapshot_id"
"baseline_role_snapshot_id"
"baseline_staff_snapshot_id"
"baseline_cutoff_utc"
"current_roster_snapshot_id"
"material_change_count"
"changed_player_ids"
"changed_coach_ids"
"feature_recompute_required"
"model_rerun_required"

test_game_output:
external_roster_change_flag: true
internal_baseline_available: false
baseline_staleness: "NOT_ASSESSABLE"
model_rerun_requirement: "NOT_ASSESSABLE"
principal_risk: "MAJOR_TWO_TEAM_COACHING_AND_QB_REGIME_CHANGE"

reason_codes:

"FROZEN_BASELINE_MISSING"
"MIA_MAJOR_ROSTER_CHANGE"
"LV_MAJOR_ROSTER_CHANGE"
"BOTH_HEAD_COACHES_CHANGED"
"QB_ROLES_UNSETTLED"

point_number: 13
point_name: "matchup_specific_risk"
purpose: "Test the reported model discrepancy against matchup dependencies actually used by the model."
automation_level: "HYBRID"
due_status: "DUE"
criticality: "HARD_REQUIRED"

confirmed_facts:

"Both teams have material coaching and quarterback changes that may alter historical offensive and defensive tendencies. "
"No internal model edge drivers, feature contributions or matchup-dependency report were supplied."
"Official Week 1 injury and inactive information is not yet due. "

missing_data:

"internal feature-contribution report"
"matchup dependency report"
"sensitivity analysis"
"current projected starters and snap shares"
"offensive-line versus pass-rush data mapped to current personnel"
"receiver/coverage assignments"
"run-game and early-down dependencies"
"scheme-transition priors"
"current injury-adjusted roster inputs"

pending_not_due:

"Final Week 1 roles, injuries and inactives."
"Reliable 2026 regular-season scheme and usage evidence."

not_assessable:

"Pass-protection versus pass-rush mismatch."
"Run-game mismatch."
"Coverage matchup."
"Specific unit responsible for the model’s 12.71-point discrepancy."
"Whether the edge is robust to current personnel."

source_evidence:

source_name: "Official team coaching and quarterback sources"
source_url: "Miami and Las Vegas official material "
source_tier: "PRIMARY"
captured_or_accessed_at: "2026-07-28T15:50:27Z"
supports_claim: "Substantial scheme and quarterback uncertainty."
source_name: "NFL official game center"
source_url: "Injury-report status "
source_tier: "PRIMARY"
captured_or_accessed_at: "2026-07-28T15:50:27Z"
supports_claim: "Game-specific injury data is not yet available."
source_name: "USER_MODEL_ARTIFACTS"
source_url: "Not supplied"
source_tier: "INTERNAL_REQUIRED"
captured_or_accessed_at: "2026-07-28T15:50:27Z"
supports_claim: "Required source for starting from actual edge drivers."

deterministic_checks:
internal_edge_drivers_present: false
current_roster_roles_finalized: false
matchup_feature_recalculation: "NOT_PERFORMED"
random_narrative_generation: "PROHIBITED"

manual_review_needed:

"Begin with the model’s actual top positive and negative edge contributors."
"Recalculate those dependencies using current roster, role and injury inputs."
"Avoid adding generic matchup narratives not tied to model features."

recommended_machine_fields:

"feature_name"
"feature_contribution_points"
"dependency_unit"
"current_input_value"
"baseline_input_value"
"sensitivity_low"
"sensitivity_high"
"injury_dependency"
"matchup_risk_flag"

test_game_output:
matchup_specific_risk_status: "NOT_ASSESSABLE"
verified_model_edge_driver: "MISSING"
current_role_inputs: "PENDING_NOT_DUE_OR_MISSING"
unsupported_matchup_narratives_added: false

reason_codes:

"EDGE_DRIVERS_MISSING"
"MATCHUP_REPORT_MISSING"
"ROLES_UNSETTLED"
"INJURIES_NOT_DUE"
"NO_RANDOM_NARRATIVE"

point_number: 14
point_name: "game_script_risk"
purpose: "Stress-test the model result across plausible possession and scoring scenarios."
automation_level: "INTERNAL_ONLY"
due_status: "DUE"
criticality: "HARD_REQUIRED"

confirmed_facts:

"The supplied total is 40.5, but it comes from the same simulated/future input and is not sufficient to define a game script."
"No play-by-play simulator, margin PMF, possession model or frozen scenario policy was supplied."
"Both teams have unsettled 2026 coaching and quarterback contexts, increasing uncertainty about how historical tendencies should be transferred. "

missing_data:

"possession simulator"
"margin PMF"
"score-state scenario policy"
"pace distribution"
"pass-rate-over-expected distribution"
"turnover sensitivity"
"explosive-play sensitivity"
"current quarterback and offensive-role assumptions"
"weather and injury scenario inputs"

pending_not_due:

"Final injury, weather and role inputs."
"Any 2026 regular-season usage evidence."

not_assessable:

"Favored game script."
"Comeback-script resilience."
"Turnover-dependency risk."
"Low-possession fragility."
"Distribution of cover, push and loss outcomes."

source_evidence:

source_name: "USER_GAME_INPUT"
source_url: "Conversation input; no external URL"
source_tier: "INTERNAL_REQUIRED"
captured_or_accessed_at: "2026-07-28T15:50:27Z"
supports_claim: "Supplied total of 40.5."
source_name: "Official team sources"
source_url: "Coaching and quarterback uncertainty "
source_tier: "PRIMARY"
captured_or_accessed_at: "2026-07-28T15:50:27Z"
supports_claim: "Historical tendency transfer is uncertain."
source_name: "INTERNAL_SIMULATOR"
source_url: "MISSING"
source_tier: "INTERNAL_REQUIRED"
captured_or_accessed_at: "2026-07-28T15:50:27Z"
supports_claim: "Required source for deterministic game-script testing."

deterministic_checks:
simulator_available: false
margin_pmf_available: "UNKNOWN"
scenario_policy_available: false
scenario_stress_test: "NOT_PERFORMED"
total_based_narrative: "NOT_INFERRED"

manual_review_needed:

"Run frozen scenarios only after roster, injury, weather and role inputs are finalized."
"Report p_cover, p_push and p_loss by scenario."
"Identify whether model value depends excessively on turnovers or a narrow lead-state path."

recommended_machine_fields:

"simulation_run_id"
"scenario_policy_version"
"possessions_distribution"
"pace_distribution"
"turnover_margin_scenarios"
"lead_state_scenarios"
"p_cover_by_scenario"
"p_push_by_scenario"
"p_loss_by_scenario"
"fragility_score"

test_game_output:
game_script_risk_status: "NOT_ASSESSABLE"
simulator_status: "MISSING"
pmf_status: "MISSING_OR_UNKNOWN"
inferred_script_from_total: "NONE"

reason_codes:

"SIMULATOR_MISSING"
"PMF_MISSING"
"SCENARIO_POLICY_MISSING"
"ROLE_INPUTS_UNSETTLED"
"NO_TOTAL_ONLY_NARRATIVE"

point_number: 15
point_name: "closing_line"
purpose: "Capture the final pregame closing spread from an actual close snapshot."
automation_level: "HYBRID"
due_status: "POST_EVENT_ONLY"
criticality: "POST_EVENT"

confirmed_facts:

"The scheduled kickoff is 2026-09-13T20:25:00Z. "
"No market close has occurred as of the research cutoff."

missing_data:

"close_snapshot_id"
"closing spread"
"actual market-close timestamp"
"named book or provider"
"full closing ladder"

pending_not_due:

"Final pregame market close."

not_assessable:

"Closing line."

source_evidence:

source_name: "Official schedule and venue event page"
source_url: "Official kickoff confirmation "
source_tier: "PRIMARY"
captured_or_accessed_at: "2026-07-28T15:50:27Z"
supports_claim: "Game has not occurred and close is not available."
source_name: "Variant B framework"
source_url: "Attached closing-line policy "
source_tier: "INTERNAL_REQUIRED"
captured_or_accessed_at: "2026-07-28T15:50:27Z"
supports_claim: "Scheduled kickoff must not be substituted for actual market close."

deterministic_checks:
market_closed: false
closing_line_capture: "POST_EVENT_ONLY"
scheduled_kickoff_used_as_close: false

manual_review_needed:

"Capture the actual final pregame quote and market-close timestamp from the ledger or named provider."

recommended_machine_fields:

"close_snapshot_id"
"market_closed_at_utc"
"book_id"
"closing_spread"
"closing_ladder"
"provider_declared_close"

test_game_output:
closing_line: "POST_EVENT_ONLY"
close_snapshot_id: "MISSING"

reason_codes:

"GAME_NOT_CLOSED"
"CLOSING_LINE_NOT_DUE"
"DO_NOT_USE_KICKOFF_AS_CLOSE"

point_number: 16
point_name: "closing_price"
purpose: "Capture the closing price tied to the same atomic snapshot as the closing line."
automation_level: "HYBRID"
due_status: "POST_EVENT_ONLY"
criticality: "POST_EVENT"

confirmed_facts:

"No closing-line snapshot exists yet."
"The closing price must be tied to the same close_snapshot_id as point 15 under the framework policy. "

missing_data:

"close_snapshot_id"
"closing price"
"closing spread"
"closing timestamp"
"two-sided closing ladder"
"named book/provider"

pending_not_due:

"Final pregame closing-price capture."

not_assessable:

"Closing price."

source_evidence:

source_name: "Variant B framework"
source_url: "Attached closing-price policy "
source_tier: "INTERNAL_REQUIRED"
captured_or_accessed_at: "2026-07-28T15:50:27Z"
supports_claim: "Closing price and line must come from the same close snapshot."

deterministic_checks:
close_snapshot_present: false
line_price_atomicity_check: "PENDING_NOT_DUE"
closing_price_capture: "POST_EVENT_ONLY"

manual_review_needed:

"Capture line and price atomically at actual market close."

recommended_machine_fields:

"close_snapshot_id"
"closing_spread"
"closing_price"
"opposite_side_spread"
"opposite_side_price"
"closed_at_utc"

test_game_output:
closing_price: "POST_EVENT_ONLY"
close_snapshot_id: "MISSING"

reason_codes:

"GAME_NOT_CLOSED"
"CLOSING_PRICE_NOT_DUE"
"SAME_SNAPSHOT_REQUIRED"

point_number: 17
point_name: "clv_points"
purpose: "Calculate spread CLV and price CLV only from valid decision and close snapshots."
automation_level: "FULL"
due_status: "POST_EVENT_ONLY"
criticality: "POST_EVENT"

confirmed_facts:

"The supplied decision snapshot is not executable-grade and is future-dated relative to this audit."
"Points 15 and 16 have no close snapshot."
"The framework prohibits calculating CLV without both decision and close snapshots. "

missing_data:

"valid decision_snapshot_id"
"close_snapshot_id"
"closing line"
"closing price"
"selected-team spread convention"
"full line-price ladders"

pending_not_due:

"Market close and post-close CLV computation."

not_assessable:

"Spread CLV."
"Price CLV."
"Key-number-adjusted CLV."

source_evidence:

source_name: "Variant B framework"
source_url: "Attached CLV requirements "
source_tier: "INTERNAL_REQUIRED"
captured_or_accessed_at: "2026-07-28T15:50:27Z"
supports_claim: "CLV cannot be calculated with missing decision or closing snapshots."

deterministic_checks:
valid_decision_snapshot_present: false
close_snapshot_present: false
clv_points_calculation: "NOT_PERFORMED"
spread_and_price_clv_combined: false

manual_review_needed:

"Wait for an actual close."
"Validate both snapshots before running the CLV rule engine."

recommended_machine_fields:

"decision_snapshot_id"
"close_snapshot_id"
"decision_spread"
"decision_price"
"closing_spread"
"closing_price"
"spread_clv_points"
"price_clv"
"key_number_context"

test_game_output:
spread_clv_points: "POST_EVENT_ONLY"
price_clv: "POST_EVENT_ONLY"
combined_fake_clv_metric: "NOT_CREATED"

reason_codes:

"DECISION_SNAPSHOT_INVALID_FOR_CLV"
"CLOSE_NOT_AVAILABLE"
"CLV_NOT_CALCULATED"

point_number: 18
point_name: "process_quality"
purpose: "Apply a phase-aware internal quality gate across points 1–17."
automation_level: "INTERNAL_ONLY"
due_status: "DUE"
criticality: "HARD_REQUIRED"

confirmed_facts:

"Game identity, official schedule and venue are confirmed."
"External roster and coaching changes are documented."
"Official injury reports, game-window weather and close data are correctly classified as not due or post-event."
"The decision quote is simulated, future-dated relative to the audit and lacks executable evidence."
"Required model lineage, PMF, probabilities, quote frontier, frozen roster baseline, matchup drivers and simulator artifacts are missing."

missing_data:

"immutable audit bundle"
"process policy registry"
"event-clock/due-window engine output"
"evidence manifest"
"calculation manifest"
"model lineage bundle"
"manual override log"
"frozen final gate policy"
"all due hard-required inputs identified in points 1, 2, 7, 8, 9, 12, 13 and 14"

pending_not_due:

"Week 1 injury reports and inactives."
"Game-window weather and field-operation check."
"Optional game-week public splits."
"Closing line, closing price and CLV."

not_assessable:

"Final numeric process score."
"Policy-compliant final operator gate from the frozen rule engine."
"Decision-stage readiness."

source_evidence:

source_name: "Variant B framework"
source_url: "Attached process-quality specification "
source_tier: "INTERNAL_REQUIRED"
captured_or_accessed_at: "2026-07-28T15:50:27Z"
supports_claim: "Not-due items are not failures; due hard blockers override scores."
source_name: "Points 1–17 evidence manifest"
source_url: "This audit report"
source_tier: "INTERNAL_REQUIRED"
captured_or_accessed_at: "2026-07-28T15:50:27Z"
supports_claim: "Current domain statuses and blockers."

deterministic_checks:
run_status: "PARTIAL_RESEARCH_COMPLETE_INTERNAL_VALIDATION_BLOCKED"
domain_status:
game_identity: "COMPLETE"
schedule_and_venue: "COMPLETE"
model_lineage: "BLOCKED"
probability_and_calibration: "BLOCKED"
market_quote: "BLOCKED"
market_movement: "BLOCKED"
injuries: "PENDING_NOT_DUE"
weather: "PENDING_NOT_DUE"
key_number_static_check: "PARTIAL"
no_chase: "NOT_ASSESSABLE"
price_quality: "NOT_ASSESSABLE"
public_bias: "PENDING_NOT_DUE_CONTEXT_ONLY"
power_rankings: "PARTIAL_CONTEXT_ONLY"
roster_external_research: "COMPLETE"
roster_internal_baseline_check: "BLOCKED"
matchup_specific_risk: "BLOCKED"
game_script_risk: "BLOCKED"
close_and_clv: "POST_EVENT_ONLY"
due_status_logic:
not_due_counted_as_failure: false
post_event_counted_as_failure: false
due_hard_blockers_present: true
gate_effect: "HOLD"
effective_status: "NOT_READY_FOR_DECISION_OR_EXECUTION_STAGE"
readiness_by_phase:
identity_and_schedule_research: "READY"
early_roster_research: "PARTIAL"
model_validation: "NOT_READY"
decision_quote_validation: "NOT_READY"
game_week_injury_weather_update: "NOT_DUE"
execution_stage: "NOT_READY"
close_and_clv_stage: "POST_EVENT_ONLY"

manual_review_needed:

"Attach all internal model and policy artifacts."
"Replace the simulated future quote with an actually observed atomic snapshot."
"Run the frozen process-quality engine after due hard blockers are resolved."

recommended_machine_fields:

"run_status"
"domain_status"
"due_status"
"criticality"
"gate_effect"
"effective_status"
"readiness_by_phase"
"hard_blocker_ids"
"nonblocking_pending_ids"
"evidence_manifest_id"
"calculation_manifest_id"
"override_log_id"

test_game_output:
run_status: "PARTIAL_RESEARCH_COMPLETE_INTERNAL_VALIDATION_BLOCKED"
effective_status: "HOLD"
due_hard_blockers:
- "MODEL_LINEAGE_MISSING"
- "PMF_AND_PROBABILITIES_MISSING"
- "MODEL_GENERATION_QUOTE_MISSING"
- "CURRENT_EXECUTABLE_QUOTE_MISSING"
- "FUTURE_DATED_SIMULATED_SNAPSHOT"
- "ACCEPTABLE_QUOTE_FRONTIER_MISSING"
- "FROZEN_ROSTER_BASELINE_MISSING"
- "MATCHUP_EDGE_DRIVERS_MISSING"
- "GAME_SCRIPT_SIMULATOR_MISSING"
- "PROCESS_POLICY_AND_MANIFESTS_MISSING"
nonblocking_pending:
- "INJURIES_NOT_DUE"
- "WEATHER_NOT_DUE"
- "PUBLIC_SPLITS_NOT_DUE"
- "CLOSING_DATA_POST_EVENT_ONLY"

reason_codes:

"DUE_HARD_BLOCKERS_PRESENT"
"NOT_DUE_ITEMS_EXCLUDED_FROM_FAILURE"
"POST_EVENT_ITEMS_EXCLUDED_FROM_FAILURE"
"DECISION_STAGE_NOT_READY"
"FAIL_CLOSED_PROCESS"

point_number: 19
point_name: "final_operator_decision"
purpose: "Route the audit state without issuing a betting decision."
automation_level: "INTERNAL_ONLY"
due_status: "DUE"
criticality: "HARD_REQUIRED"

confirmed_facts:

"Point 18 identifies unresolved due hard blockers."
"A frozen deterministic operator policy and complete process snapshot were not supplied."
"The only safe procedural state is to hold the audit for required data; this is not a betting recommendation."

missing_data:

"frozen process_quality snapshot"
"operator decision policy version"
"blocker classification registry"
"action routing registry"
"manual override log"
"append-only operator decision ledger"

pending_not_due:

"Game-week injuries and weather."
"Post-event closing and CLV fields."

not_assessable:

"Final rule-engine operator decision provenance."
"Any transition to a decision or execution stage."

source_evidence:

source_name: "Variant B framework"
source_url: "Attached operator-routing specification "
source_tier: "INTERNAL_REQUIRED"
captured_or_accessed_at: "2026-07-28T15:50:27Z"
supports_claim: "Allowed gate states and non-betting operator actions."
source_name: "Point 18 process-quality output"
source_url: "This audit report"
source_tier: "INTERNAL_REQUIRED"
captured_or_accessed_at: "2026-07-28T15:50:27Z"
supports_claim: "Due hard blockers require a fail-closed procedural hold."

deterministic_checks:
frozen_router_executed: false
fallback_behavior: "FAIL_CLOSED_HOLD"
betting_recommendation_generated: false
play_pass_language_generated: false

manual_review_needed:

"Resolve due hard blockers and execute the frozen operator router."
"Record the resulting action and provenance in the append-only ledger."

recommended_machine_fields:

"gate_state"
"operator_action"
"hold_type"
"required_actions"
"nonblocking_pending_items"
"prohibited_transitions"
"decision_policy_version"
"decision_snapshot_hash"
"decision_provenance"
"override_log_id"

test_game_output:
gate_state: "HOLD"
operator_action: "HOLD_PENDING_DATA"
hold_type: "DATA_QUALITY_MODEL_LINEAGE_AND_QUOTE_CHRONOLOGY"
required_actions:
- "Provide model version, run ID, generation timestamp, hashes and sign-convention documentation."
- "Provide p_cover, p_push, p_loss, margin PMF and calibration report."
- "Provide immutable model-generation quote and acceptable quote frontier."
- "Replace the future-dated simulated quote with an actually observed named-book or provider snapshot."
- "Provide executable status, quote ID and target-stake check."
- "Provide the frozen roster/role/staff baseline and compare it with official 2026 changes."
- "Provide model edge drivers, sensitivity report and game-script simulator outputs."
- "Run the frozen process-quality and operator-routing engines."
nonblocking_pending_items:
- "Official Week 1 practice reports and inactives."
- "Official game-window weather and field-operation check."
- "Provider-specific public splits, if used."
- "Closing line, closing price and CLV after market close."
prohibited_transitions:
- "READY_FOR_NEXT_AUDIT_STAGE"
- "AUDIT_COMPLETE"
- "Any decision or execution stage"
- "Any PLAY/PASS or betting recommendation"
- "Manual reconstruction of missing market snapshots"
decision_provenance:
status: "PROVISIONAL_FAIL_CLOSED_STATE"
frozen_rule_engine_result: "NOT_ASSESSABLE"
basis: "Due hard blockers identified in point 18"
betting_decision: "NONE"

reason_codes:

"HOLD_PENDING_DATA"
"FROZEN_ROUTER_NOT_EXECUTED"
"DUE_HARD_BLOCKERS"
"NO_BETTING_DECISION"

summary:
hard_blockers:
- "The supplied quote is future-dated relative to the research cutoff."
- "SIM_PREGAME_COM is simulated and not market-grade execution evidence."
- "No named-book atomic quote, quote ID, target-stake check or executable status."
- "No opener or immutable model-generation quote."
- "Model version, run ID, generation timestamp, hashes and sign convention are missing."
- "p_cover, p_push, p_loss, margin PMF and calibration report are missing."
- "Acceptable quote frontier and frozen no-chase policy are missing."
- "Internal frozen roster, role and staff baseline is missing despite major 2026 changes."
- "Internal matchup edge drivers and sensitivity report are missing."
- "Game-script simulator and scenario policy are missing."
- "Process policy registry, evidence manifest and deterministic operator router output are missing."

warnings:
- "The arithmetic 3.5 - (-9.21) = 12.71 passes, but semantic model-sign validation does not."
- "External ordinal rankings and secondary market context do not validate a 12.71-point model disagreement."
- "Miami and Las Vegas both underwent significant head-coach, quarterback and roster changes. "
- "Raw price 102 is interpreted as +102 only provisionally."
- "GOM remains an internal supplied tag, not an audited recommendation."

pending_not_due:
- "Official Week 1 practice reports and game-status designations."
- "Official inactives."
- "Game-window NWS forecast and venue-operation check."
- "Final Week 1 roles and depth chart."
- "Provider-specific public splits, if the process uses them."
- "Closing line, closing price and CLV."

internal_inputs_required_from_me:
- "model_version"
- "model_run_id"
- "model_generated_at_utc"
- "commit_hash and input_hash"
- "selected-team sign-convention schema"
- "p_cover, p_push and p_loss"
- "margin PMF"
- "calibration/uncertainty report"
- "model-generation quote snapshot"
- "acceptable quote frontier"
- "no-chase policy version"
- "eligible-books policy and house rules"
- "internal neutral-field power ratings"
- "frozen roster, role and staff baseline"
- "feature-contribution and matchup-dependency report"
- "game-script simulator outputs"
- "process policy, evidence manifest and operator router"

data_to_capture_manually:
- "An actually observed named-book quote with spread and price from the same atomic snapshot."
- "Quote ID, timestamp, executable status and target-stake acceptance."
- "Official game-week injury reports and inactives."
- "Final quarterback and key role confirmation."
- "Official weather/venue operation status inside the forecast window."
- "Actual closing line and price from one close snapshot."

next_best_action:
- "Do not advance the audit on the supplied future simulated quote. First attach the internal model bundle and an actually observed market-grade decision snapshot; then rerun points 1, 2 and 6–14 through the frozen deterministic process."

final_summary:
audit_readiness_now: "HOLD — identity, date, venue and early external roster research are complete, but model validation and market-execution evidence are blocked."
due_hard_blockers:
- "model lineage and sign convention"
- "probability distribution and calibration"
- "model-generation quote"
- "current market-grade executable snapshot"
- "acceptable quote frontier and no-chase policy"
- "internal frozen roster/staff baseline"
- "matchup edge drivers"
- "game-script simulator"
- "process and operator policy artifacts"
not_due_items:
- "official Week 1 injury reports"
- "official inactives"
- "game-window weather"
- "final depth and role decisions"
- "game-week public splits"
post_event_only_items:
- "closing_line"
- "closing_price"
- "clv_points"
data_i_must_enter_manually:
- "Complete internal model lineage bundle."
- "PMF and p_cover/p_push/p_loss."
- "Frozen acceptable quote frontier."
- "Actual named-book/provider snapshot with executability evidence."
- "Frozen roster/role/staff baseline."
- "Internal matchup and game-script artifacts."
data_gpt_found_with_sources:
- "Game date: September 13, 2026. "
- "Kickoff: 1:25 PM Pacific / 4:25 PM Eastern / 20:25 UTC. "
- "Venue: Allegiant Stadium, Las Vegas; LV is the home team. "
- "Venue is fully enclosed and climate-controlled, with a grass field. "
- "Official game injury reports are not yet available. "
- "Both teams have significant 2026 coaching, quarterback and roster changes. "
- "Secondary context displayed LV -3.5 and total 40.5 but did not verify the supplied +102 price or executability. "
data_that_requires_internal_python:
- "Push-aware EV from p_cover, p_push and p_loss."
- "Acceptable quote frontier lookup."
- "No-chase classification."
- "Probability value of +3 versus +3.5 from the game-specific margin PMF."
- "Roster-baseline diff and model-rerun trigger."
- "Scenario and game-script stress tests."
- "Process-quality gate."
- "Post-close spread CLV and price CLV."
next_step_for_me: "Attach the model-run bundle and replace SIM_PREGAME_COM with a real timestamped atomic quote captured no earlier than the actual observation time. Injury, weather and closing fields should remain pending until their proper due windows."
safe_to_advance_to_next_audit_stage: false
