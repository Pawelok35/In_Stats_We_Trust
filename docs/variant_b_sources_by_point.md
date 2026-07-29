# Variant B - zrodla danych dla 19 punktow

Cel:

```text
Nie podajemy GPT Pro na stale linkow Rams/49ers.
Podajemy mu zasady wyboru zrodel, a on ma znalezc zrodla dla druzyn i meczu,
ktore aktualnie badamy.
```

## Zasada ogolna

GPT Pro / Deep Research ma pracowac w takiej kolejnosci:

```text
1. Official league / official team / official venue.
2. Licensed data provider albo sportsbook/feed, jesli potrzebny market.
3. Reputable media tylko jako context, nie jako confirmed fact.
4. Rumors/social/fantasy blurbs nigdy jako confirmed fact.
```

Kazde zrodlo musi miec status:

```yaml
source_status:
  - OFFICIAL
  - LICENSED_FEED
  - SPORTSBOOK
  - MEDIA_CONTEXT
  - UNCONFIRMED
  - INTERNAL_MODEL
  - INTERNAL_MANUAL
```

## Uniwersalny source-discovery prompt

Dodaj do promptu GPT Pro:

```text
Before analyzing the fields, discover the source set for this exact game.

Find and list:
1. official NFL game/schedule source;
2. official page for Team A;
3. official page for Team B;
4. official injury report source for each team;
5. official roster/depth/transactions source for each team;
6. official venue page or event page;
7. official weather source for the venue jurisdiction;
8. market/odds source, if available;
9. public betting splits source, if available;
10. independent power-rating/ranking sources, if available.

For every source, return:
- source_name
- url
- source_status: OFFICIAL / LICENSED_FEED / SPORTSBOOK / MEDIA_CONTEXT / UNCONFIRMED
- what fields it can support
- what fields it cannot support
- timestamp/date available on source

Rules:
- Team-specific links must be discovered for the actual teams in the matchup.
- Do not use an old team page from another matchup.
- Do not use betting movement as injury evidence.
- Do not use public splits as proof of sharp/public cause.
- If no reliable source exists, mark the field MISSING or NOT_ASSESSABLE.
```

## Punkt po punkcie

### 1. argument_against

Zrodla:

```yaml
primary:
  - INTERNAL_MODEL: model output, fair line, edge, tag
  - INTERNAL_MODEL: feature attribution, home-field adjustment, uncertainty
  - INTERNAL_MODEL: immutable model-run artifact
  - INTERNAL_MODEL: out-of-sample calibration report
  - INTERNAL_MODEL: discrete margin PMF / p_cover / p_push / p_loss
  - INTERNAL_MARKET: stored market snapshot
  - OFFICIAL: league schedule / venue / neutral-site status
  - SPORTSBOOK: official house rules for the book used in model snapshot
  - HISTORICAL_DATA: nflverse / nflreadpy for margin distribution validation
secondary:
  - none
```

Nie potrzeba mediów. Ten punkt ma korzystac glownie z naszych danych i oficjalnego kontekstu meczu.

Najwazniejsza zasada:

```text
argument_against jest audytem modelu, nie zewnetrzna analiza meczu.
```

Nie traktujemy jako podstawy punktu 1:

```text
PFF grades, ESPN FPI, DVOA, power rankings, expert picks, beat reporters,
Twitter, kontuzje, pogoda, narrative articles.
```

Te rzeczy naleza do innych punktow.

Minimalny model-run artifact:

```yaml
model_run:
  run_id:
  generated_at_utc:
  model_name:
  model_version:
  code_commit_sha:
  feature_set_version:
  training_data_cutoff:
  training_dataset_hash:
  inference_input_hash:

prediction:
  selected_team:
  opponent:
  selection_spread:
  fair_margin:
  fair_line:
  fair_line_definition:
  edge_type:
  edge_value:
  edge_formula_version:

distribution:
  margin_pmf:
  p_cover:
  p_push:
  p_loss:
  prediction_interval_50:
  prediction_interval_80:
  prediction_interval_95:

context_features:
  neutral_site_flag:
  home_field_points:
  home_field_feature_value:
  venue:
  week:
  international_game_flag:

market_at_generation:
  spread:
  price:
  book:
  timestamp:
  quote_id:

validation:
  calibration_report_id:
  uncertainty_model_version:
```

Jesli nie ma kompletnego model-run artifactu:

```yaml
status: NOT_ASSESSABLE
triggered_rules:
  - MODEL_RUN_ARTIFACT_MISSING
```

Edge musi miec typ:

```yaml
edge:
  type: MARGIN_POINTS / PROBABILITY_EDGE / EXPECTED_VALUE
  value:
  formula_version:
```

Dla prostego point edge:

```text
edge_points = fair_margin + selection_spread
```

Przyklad:

```text
fair_margin = +4.99
selection_spread = -3.0
edge_points = 1.99
```

Ale to nadal:

```text
MARGIN_POINTS, nie EV
```

Pelny EV wymaga:

```yaml
ev_inputs:
  p_cover:
  p_push:
  p_loss:
  price_decimal:
```

Dla -110:

```text
decimal_odds = 1.90909
EV_per_unit = p_cover * 0.90909 - p_loss
```

House rules booka sa potrzebne do potwierdzenia:

```yaml
settlement_rules:
  book:
  jurisdiction:
  rules_version:
  captured_at:
  source_snapshot_hash:
  push_rule:
  overtime_included:
```

Hierarchia wyboru `strongest_argument`:

```yaml
priority_1_confirmed_error:
  - EDGE_RECALC_MISMATCH
  - HFA_APPLIED_AT_NEUTRAL_SITE
  - WRONG_TEAM_PERSPECTIVE
  - STALE_INPUT_SNAPSHOT
priority_2_ev_not_reproducible:
  - EDGE_IS_MARGIN_ONLY
  - INTEGER_SPREAD_PUSH_UNMODELED
  - PRICE_MISSING_FOR_EV
  - MARGIN_DISTRIBUTION_MISSING
priority_3_uncertainty_or_calibration:
  - EV_SIGN_UNSTABLE
  - PCOVER_NOT_CALIBRATED
  - CONTEXT_OUT_OF_DISTRIBUTION
  - NEUTRAL_SITE_SAMPLE_TOO_SMALL
priority_4_market_audit_gap:
  - MARKET_BOOK_MISSING
  - MARKET_TIMESTAMP_MISSING
  - MARKET_QUOTE_NOT_EXECUTABLE
```

Python wybiera kod `strongest_argument`. LLM moze tylko zbudowac zdanie.

### 2. market_move_notes

Zrodla:

```yaml
primary:
  - SPORTSBOOK: named book quote history
  - LICENSED_FEED: odds history provider
  - INTERNAL_MARKET: our model-generation quote snapshot
  - INTERNAL_MARKET: current executable quote
fallback:
  - DOCUMENTED_CONSENSUS: only if constituent books and timestamps are stored
not_enough:
  - MANUAL_CONSENSUS without book/timestamp
```

GPT moze znalezc zrodla odds, ale nie moze zgadywac openeru.

Ranking praktycznych zrodel dla punktu 2:

```yaml
best_api_automation:
  - OpticOdds
manual_odds_screen:
  - Betstamp PRO
  - SpotOdds
  - Unabated
budget_api:
  - The Odds API
historical_warehouse:
  - SportsDataIO
secondary_validation:
  - Don Best
sanity_check_only:
  - OddsPortal
  - Covers
```

Najwazniejsze:

```text
Zewnetrzna historia linii pomaga odtworzyc rynek,
ale nie zastepuje naszego wlasnego model-generation snapshot.
```

Warstwy danych:

```yaml
market_move_layers:
  reference_market_movement:
    purpose: "opener -> current for same book/consensus definition"
    source: "odds feed / odds screen"
  model_generation_quote:
    purpose: "quote seen by our model"
    source: "our append-only snapshot"
  current_executable_quote:
    purpose: "can this exact quote be used now?"
    source: "direct sportsbook/betslip confirmation"
```

Model-generation quote musi byc zapisany przez nas:

```yaml
model_generation_quote:
  model_run_id:
  event_id:
  market_id:
  selection:
  spread:
  price_american:
  price_decimal:
  book:
  provider:
  book_timestamp_utc:
  captured_at_utc:
  quote_age_seconds:
  market_status:
  is_main:
  max_limit:
  deep_link:
  eligible_books_policy_id:
  raw_payload_hash:
```

Rozszerzony `executable_status`:

```yaml
executable_status:
  - CONFIRMED_AT_BOOK
  - DISPLAYED_UNVERIFIED
  - STALE
  - SUSPENDED
  - UNAVAILABLE
  - LIMIT_TOO_LOW
  - ACCOUNT_RESTRICTED
  - MARKET_CLOSED
```

Quote z API/odds screena domyslnie:

```text
DISPLAYED_UNVERIFIED
```

Dopiero kontrola u booka/betslip:

```text
CONFIRMED_AT_BOOK
```

Nie porownujemy:

```text
opener jednego booka -> current quote innego booka
```

Chyba ze wyraznie oznaczymy, ze to nie jest ten sam rynek referencyjny.

Lepszy podzial:

```yaml
reference_market_movement:
  baseline: BOOK_OPENER / CONSENSUS_OPENER
execution_quote_movement:
  baseline: MODEL_GENERATION_QUOTE
```

Key-number events powinny byc lista zdarzen ze sciezki, nie tylko endpoint:

```yaml
key_number_events:
  - timestamp:
    from_spread:
    to_spread:
    key_number:
    status: MOVED_ONTO_KEY / MOVED_OFF_KEY / CROSSED_KEY
key_number_summary:
  status:
  key_numbers:
```

Dodajemy `UNCHANGED` do kierunku ruchu:

```yaml
direction:
  - FOR_PICK
  - AGAINST_PICK
  - MIXED
  - UNCHANGED
  - UNKNOWN
```

Przed uznaniem, ze stracilismy modelowa linie, trzeba sprawdzic alternate:

```yaml
current_quote:
  exact_model_line_available:
  exact_model_line_price:
  current_main_line:
  current_main_line_price:
```

No-chase zawsze liczy nasz rules engine. Provider dostarcza dane, nie decyzje.

### 3. injury_role_notes

Zrodla:

```yaml
primary:
  - OFFICIAL: NFL injury report
  - OFFICIAL: NFL inactives
  - OFFICIAL: Team A injury report
  - OFFICIAL: Team B injury report
  - OFFICIAL: team transactions / roster designations
role_context:
  - OFFICIAL: team press conferences / coach quotes
  - OFFICIAL: gamebooks / participation / snap counts
secondary:
  - MEDIA_CONTEXT: reputable beat reporters only for expected role/replacement context
prohibited_as_confirmed:
  - rumors
  - fantasy blurbs without primary source
  - social media without official confirmation
  - market movement
```

Uniwersalnie GPT ma znalezc:

```text
"[Team A official injury report]"
"[Team B official injury report]"
"NFL injuries"
"NFL inactives"
"[Team A official transactions]"
"[Team B official transactions]"
```

Rozszerzona hierarchia dla `injury_role_notes`:

```yaml
injury_sources:
  official_status_10_10:
    - NFL.com Injury Report
    - NFL.com Inactives
    - official team injury report
    - official team PR / communications account
    - official transactions / roster designations
  role_context_beat:
    - 32BeatWriters as aggregator
    - original local beat reporter post/article
    - official coach quote / press conference
  all_in_one_aggregator:
    - RotoWire
  medical_context:
    - Footballguys Gameday Injury Expectations
    - SICScore / Sports Injury Central
  utilization_context:
    - Fantasy Life Utilization Report
    - snap counts / routes / targets / carries
  projection_context:
    - Establish The Run
    - other projection sites with timestamped updates
  free_alert_context:
    - Rotoworld / NBC Player News
    - FantasyPros Injury News
```

Jak to traktowac:

```text
NFL.com / team official = confirmed status.
Team PR = official facts and official updates.
RotoWire = strong aggregator, not final authority over official status.
32BeatWriters = useful context, but open original reporter source.
Footballguys/SIC = medical/workload context, not official active/inactive status.
Fantasy Life = role/utilization context, not injury source of truth.
ETR = projection/workload context, not official status.
Rotoworld/FantasyPros = alert/context, verify primary source.
```

Minimalne pola dla dobrej notatki:

```yaml
injury_role_note_fields:
  official_status:
  practice_trend:
  injury_location:
  late_upgrade_or_downgrade:
  expected_active_probability:
  expected_role_if_active:
  expected_snap_or_route_range:
  primary_beneficiary:
  beneficiary_role:
  source_tier:
  last_updated:
  confidence:
```

Workflow ostatnich 24 godzin:

```yaml
T_minus_30_to_24h:
  - final Game Status Report
  - full practice trend
  - Friday downgrade/new injury
  - same-unit clusters
T_minus_24_to_12h:
  - official team PR
  - Saturday roster moves
  - practice squad elevations
  - original beat reporter notes
T_minus_12_to_2h:
  - RotoWire role note
  - Footballguys/SIC medical expectation
  - ETR or projection update
  - Fantasy Life utilization/replacement role
T_minus_90min:
  - official inactives
  - official/team warmup notes if available
```

Glowna zasada:

```text
Najwiekszy edge nie jest w "czy zawodnik zagra", tylko w "jaka role bedzie mial,
jesli zagra, i kto przejmie najwazniejsze elementy workloadu".
```

### 4. schedule_spot_notes

Zrodla:

```yaml
primary:
  - OFFICIAL: NFL schedule
  - OFFICIAL: NFL Football Operations / International Games
  - OFFICIAL: Team A schedule
  - OFFICIAL: Team B schedule
  - OFFICIAL: venue/event page
  - INTERNAL_DATA: nfl_data_py schedule
  - INTERNAL_DATA: nflreadpy / nflverse schedule
geo_time:
  - IANA_TZDB: timezone id and UTC offset at kickoff
  - AUDITED_DB: venue registry with coordinates and timezone
  - GEOGRAPHICLIB: WGS84 geodesic distance calculation
  - OFFICIAL: venue location
semi_manual:
  - OFFICIAL: team travel/practice/acclimation info
  - OFFICIAL: team PR / coach press conference / official transcript
  - MEDIA_CONTEXT: credentialed beat reporter, AP/Reuters as confirmation
```

Nie wolno:

```text
twierdzic, ze travel pomaga/szkodzi jednej stronie bez itinerary/arrival/practice data.
```

Warstwy danych:

```yaml
schedule_layers:
  official_fact:
    - week
    - matchup
    - venue
    - city/country
    - official kickoff time
    - neutral/international status
  derived_metric:
    - kickoff_utc
    - kickoff_local
    - rest_hours
    - travel distance
    - clock shift
    - consecutive road/away-from-home sequence
  reported_itinerary:
    - arrival date
    - practice location
    - acclimation plan
  model_assumption:
    - model neutral_site_flag
    - model international_game_flag
    - model home_field_points
    - schedule feature version
  unconfirmed_narrative:
    - anything not backed by official/reliable source
```

Kickoff source priority:

```yaml
kickoff_source_priority:
  1: NFL_FOOTBALL_OPERATIONS
  2: NFL_EVENT_PAGE
  3: OFFICIAL_TEAM_SCHEDULE
  4: OFFICIAL_VENUE
  5: OFFICIAL_TICKETING
```

Uwaga:

```text
Zwykla strona schedule moze personalizowac godzine pod lokalizacje uzytkownika.
Najbezpieczniej zapisac oficjalny czas ET i przeliczyc przez IANA TZDB.
```

Venue registry:

```yaml
venue_registry:
  venue_id:
  canonical_name:
  city:
  country:
  latitude:
  longitude:
  timezone_id:
  source_primary:
  source_coordinates:
  verified_at:
  manually_approved:
```

Distance policy:

```yaml
distance_method: WGS84_GEODESIC
distance_library: GeographicLib
distance_unit: km
```

Nie mylimy dystansow:

```yaml
distance_fields:
  scheduled_venue_to_venue_distance:
  team_base_to_current_venue_distance:
  confirmed_itinerary_distance:
```

Bez potwierdzonego itinerary nie znamy faktycznej trasy lotu.

Rest policy:

```yaml
if game_type == "REG" and week == 1:
  previous_regular_season_game: null
  rest_status: NOT_APPLICABLE
```

Nie uzywamy poprzedniego sezonu ani preseason jako zamiennika regular-season rest.

Rest powinien byc liczony z kickoff UTC:

```yaml
rest:
  team_a_rest_hours:
  team_b_rest_hours:
  team_a_calendar_gap_days:
  team_b_calendar_gap_days:
  rest_definition_version:
```

Rozdzielamy designation od fizycznej lokalizacji:

```yaml
sequence:
  designated_home_team:
  designated_away_team:
  away_from_standard_home_venue:
  neutral_site_game:
  consecutive_designated_road_games:
  consecutive_games_away_from_home_market:
```

Zamiast niejednoznacznego `time_zones_crossed` preferujemy:

```yaml
travel:
  origin_timezone:
  destination_timezone:
  origin_utc_offset:
  destination_utc_offset:
  clock_shift_hours:
  minimal_circadian_shift_hours:
  travel_direction:
```

Itinerary quality:

```yaml
itinerary_status:
  - CONFIRMED_OFFICIAL
  - CONFIRMED_CREDENTIALED_REPORTER
  - REPORTED_UNCONFIRMED
  - CONFLICTING_REPORTS
  - NOT_PUBLICLY_AVAILABLE
```

Aktualny poprawny kierunek dla SF-LA:

```yaml
schedule_spot_notes:
  status: PARTIALLY_CONFIRMED
  kickoff_utc: 2026-09-11T00:35:00Z
  kickoff_local: 2026-09-11T10:35:00+10:00
  timezone: Australia/Melbourne
  venue: Melbourne Cricket Ground
  location_type: NEUTRAL_INTERNATIONAL
  designated_home_team: LA
  rest_status: NOT_APPLICABLE
  reason: WEEK_1_NO_PRIOR_REGULAR_SEASON_GAME
  international_travel: true
  itinerary_status: NOT_PUBLICLY_CONFIRMED
  model_link:
    schedule_assumption_mismatch: AUDIT_REQUIRED
    effect_on_edge: NOT_QUANTIFIED
  note: "Week 1 neutral-site international game. Prior regular-season rest comparison is not applicable. No team-specific travel or acclimation advantage can be assigned without confirmed itinerary."
```

### 5. weather_notes

Zrodla:

```yaml
primary:
  - OFFICIAL_WEATHER: official meteorological service for venue jurisdiction
  - OFFICIAL_VENUE: roof/field/venue operating notices
  - LICENSED_WEATHER: provider with issue timestamp and valid game-window timestamp
  - INTERNAL_MODEL: model-run artifact for weather_features_in_model and weather_adjustment
```

Dla meczu w Australii oficjalnym startem jest Bureau of Meteorology:

```text
https://www.bom.gov.au/
```

Uniwersalnie GPT ma znalezc:

```text
"official weather service for [venue city/country]"
"game-window forecast for [venue name]"
```

Nie uzywamy:

```text
klimatu historycznego jako game-window forecast.
prognozy bez issue timestamp i valid timestamp.
```

Warstwy weather:

```yaml
weather_layers:
  official_forecast:
    - official weather service for venue jurisdiction
  observations_nowcast:
    - official observations
    - radar
    - warnings
  venue_operations:
    - venue roof/field notices
    - NFL/team PR operational notes
  model_link:
    - weather_features_in_model
    - weather_adjustment
    - rerun/sensitivity effect
```

Jurisdiction routing:

```yaml
if venue_country == "Australia":
  primary_weather_provider: BOM
elif venue_country == "United States":
  primary_weather_provider: NWS
else:
  primary_weather_provider: official_weather_service_for_country
```

Dla Australii:

```yaml
australia_weather_sources:
  official_forecast:
    - BOM MetEye
    - BOM Weather
  machine_readable:
    - BOM ADFD
  observations_nowcast:
    - BOM observations
    - BOM radar
    - BOM warnings
  secondary_model:
    - BOM ACCESS-C
    - BOM ACCESS-CE
  licensed_secondary:
    - Meteomatics
  budget_secondary:
    - Open-Meteo
```

Dla USA:

```yaml
usa_weather_sources:
  official_forecast:
    - NOAA / National Weather Service API
  observations_nowcast:
    - NWS observations
    - NWS radar
    - NWS alerts/warnings
```

Sportowe weather pages:

```text
RotoWire weather, Weather.com game pages, FantasyLabs weather i DFS weather pages
moga sluzyc jako discovery/sanity check, ale nie jako source of record, chyba ze
zawieraja pelna provenance: provider, issue/model time, valid time, coordinates
i forecast interval.
```

Forecast provenance:

```yaml
forecast_provenance:
  provider:
  product:
  source_type:
    - OFFICIAL_HUMAN_EDITED_FORECAST
    - OFFICIAL_RAW_NWP
    - LICENSED_BLEND
    - THIRD_PARTY_MODEL_DISTRIBUTION
    - OBSERVATION
    - RADAR_NOWCAST
    - VENUE_NOTICE
  underlying_model:
  model_run_time_utc:
  provider_issue_time_utc:
  source_last_modified_utc:
  captured_at_utc:
  valid_from_utc:
  valid_to_utc:
  raw_payload_hash:
  forecast_revision_id:
```

Uwaga dla BOM ADFD:

```text
ADFD moze miec valid_time i source_last_modified, ale nie pelny provider_issue_time.
captured_at_utc nie jest tym samym co official issue time.
```

Game window to przedzial, nie tylko kickoff:

```yaml
game_window:
  policy_id: NFL_WEATHER_WINDOW_V1
  start_offset_minutes: -60
  end_offset_minutes: 240
```

Przechowujemy summary i serie bazowa:

```yaml
game_window_summary:
  temperature_at_kickoff:
  temperature_min:
  temperature_max:
  sustained_wind_at_kickoff:
  sustained_wind_max:
  wind_gust_max:
  wind_direction_range:
  precipitation_probability_at_kickoff:
  precipitation_probability_max:
  precipitation_amount_total:
  humidity_min:
  humidity_max:
```

Nie usredniamy probability of precipitation jako glownej miary. Lepsze:

```yaml
precipitation_probability_max:
precipitation_probability_at_kickoff:
precipitation_amount_total_game_window:
```

Rozdzielamy wiatr:

```yaml
wind:
  sustained_speed:
  gust_speed:
  direction_degrees:
  direction_cardinal:
  measurement_height_m:
  valid_interval:
```

Forecast i actual observations sa osobne:

```yaml
forecast:
observed_conditions:
forecast_error:
  temperature_error:
  sustained_wind_error:
  gust_error:
  precipitation_amount_error:
```

Statusy weather:

```yaml
weather_status:
  - PENDING_NOT_DUE
  - PRELIMINARY
  - PRELIMINARY_GAME_WINDOW_AVAILABLE
  - ACTIONABLE
  - NOWCAST_CHECK_REQUIRED
  - NOWCAST_VALIDATED
  - STALE
  - CONFLICTING_SOURCES
  - NOT_ASSESSABLE
```

Dla BOM sensowny timing:

```yaml
more_than_7_days: PENDING_NOT_DUE
4_to_7_days: PRELIMINARY
72h_to_4_days: PRELIMINARY_GAME_WINDOW_AVAILABLE
6h_to_72h: ACTIONABLE
less_than_6h: NOWCAST_CHECK_REQUIRED
forecast_plus_observations_plus_radar_checked: NOWCAST_VALIDATED
```

Risk ma byc wynikiem naszej polityki, nie decyzja providera:

```yaml
risk:
  threshold_policy_id: NFL_WEATHER_RISK_V2
  wind_risk:
  rain_risk:
  surface_risk:
  offensive_environment_risk:
  triggered_rules:
```

Aktualny poprawny kierunek dla SF-LA:

```yaml
weather_notes:
  status: PENDING_NOT_DUE
  venue:
    name: Melbourne Cricket Ground
    country: Australia
    roof_type: OPEN_AIR_PLAYING_FIELD
    spectator_cover: PARTIAL
    surface: NATURAL_TURF
  forecast:
    official_source: AUSTRALIAN_BUREAU_OF_METEOROLOGY
    product: PENDING
    forecast_status: NOT_ACTIONABLE_YET
  observations:
    preferred_station: MELBOURNE_OLYMPIC_PARK
    observation_status: NOT_DUE
    radar_status: NOT_DUE
    warning_status: NOT_DUE
  model_link:
    weather_features_in_model: UNKNOWN
    weather_adjustment: UNKNOWN
    effect_on_edge: NOT_ASSESSABLE
  note: "Game-window weather is not yet actionable. Historical Melbourne climate must not be used as a game forecast."
```

### 6. key_number_check

Zrodla:

```yaml
primary:
  - INTERNAL_MARKET: own append-only quote event ledger
  - INTERNAL_MARKET: selected-team spread
  - INTERNAL_MARKET: model-generation quote path
  - INTERNAL_MODEL: margin PMF / affected probability mass
  - INTERNAL_RULES: key-number config
  - SPORTSBOOK: official house rules for settlement/push/overtime
  - ODDS_FEED: OpticOdds / SportsDataIO for external quote path control
  - HISTORICAL_DATA: nflverse / nflreadpy for key-number config validation
  - MANUAL_QA: Unabated
```

Nie potrzebuje internetu. Key numbers liczy nasz skrypt.

Najwazniejsza poprawka:

```text
Rozdzielamy dwa pytania:
1. Czy spread jest integer i moze dac push?
2. Jak wazna empirycznie/modelowo jest ta konkretna liczba?
```

Settlement engine musi dzialac dla kazdego integer spreadu:

```text
-1, -2, -3, -4, -6, -7, -10, ...
```

3 i 7 sa najwazniejsze, ale kazda liczba calkowita moze dac push.

Konfiguracja powinna miec dwie warstwy:

```yaml
integer_settlement_check:
  any_integer_supported: true

key_number_significance:
  config_version: NFL_KEY_NUMBERS_2026_V1
  empirical_weight:
  tier:
```

Lepszy config niz sama lista `3/7/10/14`:

```yaml
key_number_config:
  3:
    tier: PRIMARY
    historical_mass:
  7:
    tier: PRIMARY
    historical_mass:
  6:
    tier: SECONDARY
    historical_mass:
  10:
    tier: SECONDARY
    historical_mass:
  4:
    tier: SECONDARY_OR_WATCH
    historical_mass:
  14:
    tier: SECONDARY
    historical_mass:
```

Generic settlement formula:

```text
M = selected_team_score - opponent_score
S = spread_selected_team
adjusted_margin = M + S

adjusted_margin > 0 -> COVER
adjusted_margin = 0 -> PUSH
adjusted_margin < 0 -> LOSS
```

Settlement-state ranking:

```yaml
settlement_rank:
  LOSS: 0
  PUSH: 1
  COVER: 2
```

Kierunek ruchu:

```text
rank_after > rank_before -> FOR_PICK
rank_after < rank_before -> AGAINST_PICK
rank_after = rank_before -> NEUTRAL
```

Eventy:

```yaml
event_types:
  ARRIVED_AT_KEY: "from_spread != signed_key and to_spread == signed_key"
  MOVED_OFF_KEY: "from_spread == signed_key and to_spread != signed_key"
  CROSSED_KEY: "(from_spread - signed_key) * (to_spread - signed_key) < 0"
```

Event-level i path-level musza byc osobne:

```yaml
key_number_events:
  - timestamp_utc:
    sportsbook:
    from_spread:
    to_spread:
    key_number_abs:
    signed_key_line:
    selected_team_actual_margin:
    event_type:
    before_state:
    after_state:
    direction:
    market_was_suspended:

path_summary:
  crossed_key_during_path:
  crossed_keys:
  event_history_status:
```

Przy braku pelnej sciezki:

```text
event_history_status: NOT_ASSESSABLE
```

a nie:

```text
NO_KEY_NUMBER_EVENT
```

Risk level powinien korzystac z hierarchii:

```yaml
risk_source_priority:
  1_MODEL_PMF:
    affected_probability_mass:
  2_HISTORICAL_CONDITIONAL:
    condition: "spread range, favorite/underdog, total, era"
  3_STATIC_CONFIG_FALLBACK:
    tier:
```

Opcjonalny impact przy stalej cenie:

```text
q = probability mass on affected margin
d = decimal odds

COVER -> PUSH: EV delta = -q * (d - 1)
PUSH -> LOSS:  EV delta = -q
COVER -> LOSS: EV delta = -q * d
```

Punkt 6 moze policzyc settlement impact, ale no-chase decyzja zostaje w punkcie 7.

Poprawny wynik dla LA -3 bez quote path:

```yaml
key_number_check:
  status: PARTIALLY_ASSESSABLE
  selected_team: LA
  current_spread: -3.0
  integer_settlement_check:
    current_integer_spread: true
    current_push_possible: true
    signed_push_margin: 3
  key_number_status:
    current_on_key_number: true
    current_key_number: 3
    current_key_tier: PRIMARY
  key_number_events: []
  path_summary:
    crossed_key_during_path: UNKNOWN
    crossed_keys: UNKNOWN
    event_history_status: QUOTE_PATH_MISSING
  probability_impact:
    affected_margin_probability: UNKNOWN
    source: NOT_AVAILABLE
  risk_level:
    value: NOT_ASSESSABLE
    reason_codes:
      - QUOTE_PATH_MISSING
      - MARGIN_PMF_MISSING
```

### 7. no_chase_limit

Zrodla:

```yaml
primary:
  - INTERNAL_MARKET: model-generation quote
  - SPORTSBOOK/LICENSED_FEED: current executable quote
  - INTERNAL_RULES: max playable spread/price
  - INTERNAL_MODEL: p_cover/p_push/p_loss if available
  - INTERNAL_RULES: versioned no-chase policy registry
  - INTERNAL_MODEL: margin PMF / EV engine
  - SPORTSBOOK: direct betslip verification
  - SPORTSBOOK: official house rules for settlement semantics
  - ODDS_FEED: OpticOdds for main+alternate line discovery
  - ODDS_FEED: SportsDataIO for history/backfill/validation
  - MANUAL_QA: Betstamp PRO / Unabated
```

No-chase nie wynika z opinii GPT. To reguly.

Najwazniejsza zasada:

```text
Zrodlem prawdy dla no_chase_limit nie jest zewnetrzna strona.
Zrodlem prawdy sa:
1. immutable model-generation quote,
2. versioned no-chase policy,
3. model margin PMF / p_cover / p_push / p_loss dla rozwazanych linii.
```

Provider dostarcza aktualne line-price pairs, alternates, timestamps, market status i limity.
Provider nie decyduje, czy chase jest dopuszczalny.

Model-generation quote:

```yaml
model_generation_quote:
  run_id:
  event_id:
  market_id:
  market_scope: FULL_GAME
  overtime_included: true
  selected_team:
  spread:
  price_american:
  price_decimal:
  book:
  book_timestamp_utc:
  captured_at_utc:
  quote_age_seconds:
  quote_id:
  provider:
  is_main:
  executable_status_at_generation:
  model_version:
  margin_pmf_hash:
  policy_id:
```

Bez tego:

```yaml
status: NOT_ASSESSABLE
reason_codes:
  - MODEL_GENERATION_QUOTE_MISSING
```

Versioned no-chase policy:

```yaml
no_chase_policy:
  policy_id: NFL_SPREAD_NO_CHASE_V4
  policy_hash:
  effective_from:
  approved_at:
  approved_by:
  code_commit_sha:
  baseline_type: MODEL_GENERATION_QUOTE
  distribution_reference: MODEL_GENERATION_PMF
  book_universe_policy_id:
  comparison_mode: SAME_BOOK_ONLY / BEST_QUOTE_ACROSS_ELIGIBLE_BOOKS
  exact_line_checked_first: true
  minimum_target_stake:
  stale_quote_seconds:
  minimum_current_ev:
  maximum_ev_drop:
  minimum_edge_retention_ratio:
  primary_key_numbers: [3, 7]
  hard_blocks:
    - COVER_TO_LOSS_ON_PRIMARY_KEY
    - PUSH_TO_LOSS_ON_PRIMARY_KEY
    - CROSSED_PRIMARY_KEY_AGAINST_PICK
  review_rules:
    - COVER_TO_PUSH_ON_PRIMARY_KEY
    - MIXED_SPREAD_PRICE_MOVE_WITHOUT_PMF
```

Executable status:

```yaml
executable_status:
  - BETSLIP_CONFIRMED_AT_TARGET_STAKE
  - DISPLAYED_AT_BOOK
  - AGGREGATOR_ONLY
  - STALE
  - SUSPENDED
  - LIMIT_BELOW_REQUIRED_STAKE
  - ACCOUNT_OR_GEO_UNAVAILABLE
  - MARKET_UNAVAILABLE
  - UNKNOWN
```

Stake validation:

```yaml
stake_validation:
  target_stake:
  maximum_accepted_stake:
  verified_at_utc:
  odds_change_setting:
  price_change_prompt_received:
```

Najwieksza zmiana konstrukcyjna:

```text
Zamiast jednego max_playable_spread / max_acceptable_price,
zamrazamy acceptable_quote_frontier przy model run.
```

```yaml
acceptable_quote_frontier:
  generated_at_utc:
  model_run_id:
  margin_pmf_hash:
  policy_id:
  line_price_pairs:
    - spread: -2.5
      minimum_decimal_odds:
      minimum_american_odds:
      status: ALLOWED
    - spread: -3.0
      minimum_decimal_odds:
      minimum_american_odds:
      status: ALLOWED
    - spread: -3.5
      status: BLOCKED
      reason_codes:
        - MOVED_OFF_KEY_3_AGAINST_PICK
        - PUSH_TO_LOSS
```

Pytanie punktu 7:

```text
Czy jakakolwiek aktualna, potwierdzona oferta z kwalifikowanych bookow
nalezy do acceptable_quote_frontier?
```

EV dla spreadu i kursu:

```text
EV(spread, d) = p_cover(spread) * (d - 1) - p_loss(spread)
```

Minimalny kurs przy minimalnym EV tau:

```text
d_min(spread) = 1 + (p_loss(spread) + tau) / p_cover(spread)
```

Kolejnosc ewaluacji:

```yaml
evaluation_order:
  1: require model-generation quote
  2: require exact policy version
  3: verify market scope and settlement rules
  4: fetch all quotes from eligible books, including main and alternates
  5: filter stale/suspended/wrong jurisdiction/low limit/wrong market scope
  6: check exact model spread first
  7: evaluate other line-price pairs against acceptable_quote_frontier
  8: if at least one confirmed quote passes -> NOT_TRIGGERED
  9: if all confirmed quotes fail -> TRIGGERED
  10: if mixed and no PMF -> REVIEW_REQUIRED or NOT_ASSESSABLE
```

Stale/suspended nie zawsze znaczy TRIGGERED:

```text
STALE/SUSPENDED -> zwykle NOT_ASSESSABLE.
TRIGGERED dopiero gdy mamy potwierdzone, ze wszystkie kwalifikowane oferty sa poza polityka.
```

Reason codes:

```yaml
data_failures:
  - MODEL_GENERATION_QUOTE_MISSING
  - POLICY_VERSION_MISSING
  - MODEL_PMF_MISSING
  - CURRENT_QUOTE_MISSING
  - CURRENT_QUOTE_STALE
  - CURRENT_MARKET_SUSPENDED
  - CURRENT_QUOTE_NOT_DIRECTLY_VERIFIED
  - ELIGIBLE_BOOK_UNIVERSE_UNKNOWN
  - SETTLEMENT_RULES_NOT_VERIFIED
availability_failures:
  - EXACT_MODEL_LINE_UNAVAILABLE
  - LIMIT_BELOW_REQUIRED_STAKE
  - ACCOUNT_OR_GEO_UNAVAILABLE
  - NO_ELIGIBLE_EXECUTABLE_QUOTES
price_failures:
  - PRICE_WORSENED_SAME_SPREAD
  - MAX_ACCEPTABLE_PRICE_EXCEEDED
  - CURRENT_EV_BELOW_MINIMUM
  - EV_DROP_EXCEEDS_LIMIT
  - EDGE_RETENTION_BELOW_MINIMUM
spread_failures:
  - ARRIVED_AT_KEY_AGAINST_PICK
  - MOVED_OFF_KEY_AGAINST_PICK
  - CROSSED_KEY_AGAINST_PICK
  - COVER_TO_PUSH
  - PUSH_TO_LOSS
  - COVER_TO_LOSS
  - MAX_PLAYABLE_SPREAD_EXCEEDED
review_reasons:
  - MIXED_SPREAD_PRICE_MOVE
  - PMF_REQUIRED_FOR_LINE_PRICE_COMPARISON
  - CONFLICTING_PROVIDER_QUOTES
  - DIRECT_BOOK_VERIFICATION_REQUIRED
```

Poprawny wynik dla SF-LA teraz:

```yaml
no_chase_limit:
  selected_team: LA
  status: NOT_ASSESSABLE
  reason_codes:
    - MODEL_GENERATION_QUOTE_MISSING
    - CURRENT_QUOTE_NOT_DIRECTLY_VERIFIED
    - CURRENT_QUOTE_IS_CONSENSUS_NOT_EXECUTABLE
    - EXACT_MODEL_LINE_AVAILABILITY_UNKNOWN
    - PRICE_QUALITY_NOT_ASSESSABLE
  note: "No-chase cannot be evaluated because the original model-generation quote is missing and current LA -3 (-110) is manual consensus, not a directly verified sportsbook offer."
```

### 8. price_quality

Zrodla:

```yaml
primary:
  - INTERNAL_MODEL_RUN: model_run_id, model_version, margin_pmf_hash
  - INTERNAL_MODEL: p_cover, p_push, p_loss for the exact spread
  - INTERNAL_POLICY: frozen acceptable_quote_frontier generated at model run
  - DIRECT_SPORTSBOOK_BETSLIP: executable quote at target stake
  - OFFICIAL_BOOK_HOUSE_RULES: push, overtime, market scope, settlement
secondary:
  - OPTICODDS: current quotes, alternates, timestamps, market status
  - SPORTSDATAIO: second feed, history, backfill, provider validation
  - BETSTAMP_PRO: manual line shopping and limit context
  - UNABATED: manual line-price comparison / alternate line QA
  - THE_ODDS_API: budget current-price snapshots
validation:
  - NFLVERSE / NFLREADPY: final scores for realized cover/push/loss
  - CALIBRATION_REPORT: out-of-sample probability quality
```

Definicja:

```text
price_quality sprawdza, czy aktualny, konkretny spread+price dla wybranej strony
jest akceptowalny wedlug modelowego PMF albo zamrozonej frontiery.
```

Najwazniejsza hierarchia:

```text
MODEL PMF / FROZEN FRONTIER
            +
DIRECT SPORTSBOOK BETSLIP
            =
PRICE QUALITY DECISION
```

Rozdzielamy dwa pytania:

```yaml
quote_quality:
  status:
    - FRESH_EXECUTABLE
    - FRESH_UNVERIFIED
    - STALE
    - SUSPENDED
    - MISSING
    - CONFLICTING

price_valuation:
  status:
    - ACCEPTABLE
    - UNACCEPTABLE
    - REVIEW_REQUIRED
    - NOT_ASSESSABLE
```

Jesli quote jest stary, agregatorowy, consensus albo bez timestampu, wynik ceny nie jest automatycznie zly.
Wtedy:

```text
price_quality = NOT_ASSESSABLE
quote_quality = STALE / UNVERIFIED / MISSING
```

Jesli mamy poprawnie zamrozona frontiere, ale nie mamy zaladowanych p_cover/p_push/p_loss:

```yaml
price_status: ACCEPTABLE albo UNACCEPTABLE
valuation_method: FROZEN_ACCEPTABLE_QUOTE_FRONTIER
ev_per_unit: null
```

Jesli mamy tylko ogolna tabele limitow, np. "-3 max -120":

```yaml
valuation_method: GENERIC_POLICY_TABLE_FALLBACK
manual_review_required: true
```

Formula EV dla spreadu z mozliwym pushem:

```text
EV = p_cover * (decimal_odds - 1) - p_loss

minimum_decimal_odds = 1 + p_loss / p_cover
minimum_decimal_odds_with_min_ev = 1 + (p_loss + minimum_ev_required) / p_cover
```

Break-even trzeba zapisywac dwojako:

```yaml
conditional_cover_rate_given_no_push: 1 / decimal_odds
unconditional_cover_probability_required: (1 - p_push) / decimal_odds
```

Spread i cena musza byc atomowym quote'em:

```yaml
quote_integrity:
  fixture_id:
  market_id:
  quote_id:
  selected_team_id:
  market_scope: FULL_GAME
  overtime_included: true
  spread:
  price:
  source_timestamp_utc:
  captured_at_utc:
```

Standardowy cash bet, odds boost i bonus bet musza byc oceniane osobno:

```yaml
wager_type:
  type: STANDARD_CASH
  promotional_price: false
```

Reason codes:

```yaml
quote_failures:
  - CURRENT_QUOTE_MISSING
  - CURRENT_QUOTE_STALE
  - CURRENT_MARKET_SUSPENDED
  - CURRENT_QUOTE_NOT_EXECUTABLE
  - CURRENT_QUOTE_AGGREGATOR_ONLY
  - CURRENT_QUOTE_IS_CONSENSUS
  - TARGET_STAKE_NOT_ACCEPTED
  - QUOTE_TIMESTAMP_MISSING
  - SPREAD_PRICE_SNAPSHOT_MISMATCH
  - MARKET_SCOPE_MISMATCH
  - OVERTIME_RULE_UNKNOWN
model_failures:
  - MODEL_RUN_ID_MISSING
  - MARGIN_PMF_MISSING
  - P_COVER_MISSING
  - P_PUSH_MISSING
  - P_LOSS_MISSING
  - PROBABILITIES_DO_NOT_SUM_TO_ONE
  - CALIBRATION_REPORT_MISSING
  - PMF_FRONTIER_HASH_MISMATCH
policy_failures:
  - ACCEPTABLE_QUOTE_FRONTIER_MISSING
  - PRICE_POLICY_MISSING
  - MINIMUM_EV_THRESHOLD_MISSING
  - FRONTIER_VERSION_MISSING
valuation_failures:
  - CURRENT_EV_BELOW_MINIMUM
  - PRICE_BELOW_MINIMUM_DECIMAL_ODDS
  - PRICE_EXCEEDS_WORST_ACCEPTABLE_AMERICAN
  - QUOTE_OUTSIDE_ACCEPTABLE_FRONTIER
  - EXACT_SPREAD_NOT_EVALUATED
```

### 9. market_snapshot

Zrodla:

```yaml
primary:
  - ACCEPTED_TICKET_OR_RECEIPT: strongest execution proof
  - DIRECT_SPORTSBOOK_BETSLIP: target-stake verification before execution
  - OPTICODDS: named-book atomic quote, quote ID, market ID, timestamps
  - SPORTSDATAIO: second feed, history, backfill, market-scope validation
  - THE_ODDS_API: budget current snapshot / model-run capture
  - INTERNAL_MARKET_STORE: append-only raw payload, hash, timestamp
manual_qa:
  - BETSTAMP_PRO: manual odds screen, line shopping, provider limit context
  - UNABATED: manual scope, latency, visual QA
fallback:
  - MANUAL_CONSENSUS only as preview, never market-grade proof
```

Wymagane:

```text
book/source, spread, price, timestamp, executable status, selected side.
```

Najwazniejsze rozroznienie:

```text
QUOTE ISTNIAL W FEEDZIE
QUOTE BYL WYSWIETLONY W BOOKU
QUOTE BYL DOSTEPNY PRZY TARGET STAKE
WAGER ZOSTAL ZAAKCEPTOWANY
```

To sa cztery rozne poziomy dowodu.

Hierarchia dowodowa:

```yaml
evidence_grade:
  EXECUTED_GRADE      # zaakceptowany ticket/receipt
  DIRECT_BOOK_GRADE   # betslip sprawdzony przy target stake
  PROVIDER_GRADE      # named-book provider/feed quote
  PREVIEW_ONLY        # manual consensus, consensus provider line, article, no timestamp
  INVALID             # niespojny lub blednie zmapowany quote
```

Nie uzywamy jednego pola MARKET_GRADE do wszystkiego. Rozdzielamy trzy osie:

```yaml
market_snapshot:
  quote_integrity_status:
    - VALID
    - INVALID
    - INCOMPLETE
  evidence_grade:
    - EXECUTED_GRADE
    - DIRECT_BOOK_GRADE
    - PROVIDER_GRADE
    - PREVIEW_ONLY
    - INVALID
  market_state:
    - ACTIVE
    - SUSPENDED
    - REMOVED
    - UNKNOWN
  executable_status:
    - WAGER_ACCEPTED
    - BETSLIP_VERIFIED_AT_TARGET_STAKE
    - DISPLAYED_AT_BOOK_NOT_STAKE_TESTED
    - AGGREGATOR_DISPLAYED_UNVERIFIED
    - LIMIT_BELOW_TARGET_STAKE
    - ACCOUNT_OR_GEO_UNAVAILABLE
    - SUSPENDED
    - STALE
    - UNKNOWN
```

Zawieszony rynek moze byc poprawnym snapshotem stanu rynku:

```yaml
quote_integrity_status: VALID
evidence_grade: PROVIDER_GRADE
market_state: SUSPENDED
executable_status: SUSPENDED
```

To nie jest `INVALID`, tylko brak wykonywalnej oferty.

Quote musi byc atomowy:

```yaml
quote_identity:
  provider_quote_id:
  provider_event_id:
  provider_market_id:
  provider_selection_id:
  raw_payload_hash:

atomic_quote_validation:
  same_payload: true
  same_quote_id: true
  same_market_id: true
  same_selection_id: true
  same_source_timestamp: true
```

Timestampy:

```yaml
timestamps:
  book_or_source_timestamp_utc:
  provider_received_at_utc:
  captured_at_utc:
  timestamp_semantics:
    - BOOK_UPDATE_TIME
    - PROVIDER_UPDATE_TIME
    - BOOKMAKER_LAST_UPDATE
    - SNAPSHOT_QUERY_TIME
    - MANUAL_CAPTURE_TIME
    - UNKNOWN
  quote_age_ms:
```

Nie zastepujemy brakujacego source timestamp czasem pobrania. Brakujace pole zostaje `null`.

Stake check:

```yaml
stake_check_status:
  NOT_TESTED
  DISPLAYED_IN_BETSLIP
  ACCEPTED_IN_FULL
  PARTIALLY_ACCEPTED
  REJECTED
  PROVIDER_LIMIT_ONLY
```

`provider_reported_max_stake` i `account_specific_max_stake` to osobne pola.

Rodzaj ceny:

```yaml
price_context:
  price_type:
    - STANDARD
    - ODDS_BOOST
    - ACCOUNT_SPECIFIC_PROMO
    - BONUS_BET
    - UNKNOWN
```

Reason codes:

```yaml
integrity_failures:
  - EVENT_ID_MISSING
  - EVENT_MAPPING_AMBIGUOUS
  - SELECTED_SIDE_MISMATCH
  - SPREAD_MISSING
  - PRICE_MISSING
  - SPREAD_PRICE_NOT_ATOMIC
  - QUOTE_ID_MISSING
  - MARKET_SCOPE_UNKNOWN
  - OVERTIME_RULE_UNKNOWN
  - PARTIAL_GAME_MARKET_MISCLASSIFIED
source_limitations:
  - MANUAL_CONSENSUS_ONLY
  - CONSENSUS_NOT_EXECUTABLE
  - NAMED_BOOK_MISSING
  - SOURCE_TIMESTAMP_MISSING
  - PROVIDER_TIMESTAMP_ONLY
  - DIRECT_BOOK_NOT_CHECKED
  - AGGREGATOR_ONLY
execution_limitations:
  - TARGET_STAKE_NOT_TESTED
  - TARGET_STAKE_NOT_ACCEPTED
  - LIMIT_BELOW_TARGET_STAKE
  - ACCOUNT_SPECIFIC_LIMIT_UNKNOWN
  - ACCOUNT_OR_GEO_UNAVAILABLE
  - ODDS_CHANGE_PENDING
  - MARKET_SUSPENDED
  - QUOTE_STALE
evidence_limitations:
  - RAW_PAYLOAD_NOT_STORED
  - SCREENSHOT_ONLY
  - SYSTEM_CLOCK_NOT_VERIFIED
  - EVIDENCE_HASH_MISSING
```

Obecny test SF-LA:

```yaml
quote_integrity_status: INCOMPLETE
evidence_grade: PREVIEW_ONLY
market_state: UNKNOWN
executable_status: UNKNOWN
reason_codes:
  - MANUAL_CONSENSUS_ONLY
  - NAMED_BOOK_MISSING
  - SOURCE_TIMESTAMP_MISSING
  - QUOTE_ID_MISSING
  - DIRECT_BOOK_NOT_CHECKED
  - TARGET_STAKE_NOT_TESTED
  - EXECUTABLE_STATUS_UNKNOWN
```

### 10. public_bias / tickets_handle

Nie ma oficjalnego NFL zrodla. To zawsze `SECONDARY_MARKET_CONTEXT`.

Ranking zrodel:

```yaml
best_sources:
  - DRAFTKINGS_DIRECT: named single-book real wagers, % bets and % handle
  - VSIN_PRO: separate DraftKings and Circa samples
  - SPORTS_INSIGHTS: real wagers, multi-book contributing pool, ticket count if available
  - ACTION_NETWORK: broad multi-book sample, book pool undisclosed
  - OFFICIAL_BOOK_PUBLICATIONS: BetMGM/FanDuel/Caesars/etc. when market-specific
  - SCORES_AND_ODDS: secondary cross-check, pool composition undisclosed
community_only:
  - COVERS_CONSENSUS: community/contest sentiment, not sportsbook handle
```

Wymagane pola:

```text
provider, timestamp, market, side, tickets %, handle %, book/sample/methodology.
```

Zasada:

```text
Splits pokazuja rozklad betow/handle u danego providera.
Nie dowodza sharp money.
Nie dowodza przyczyny ruchu linii.
Nie zawsze odnosza sie wylacznie do aktualnego spreadu.
```

Jesli GPT nie znajdzie provider/timestamp/market:

```text
public_bias = NOT_ASSESSABLE
```

Najwazniejsza korekta:

```text
Covers Consensus nie zasila selected_team_tickets_pct ani selected_team_handle_pct.
To moze trafic tylko do community_sentiment.
```

Nie laczymy providerow w jeden procent:

```yaml
bad:
  provider: MULTIPLE
  selected_team_tickets_pct: 64

good:
  provider_observations:
    - provider: DRAFTKINGS_NETWORK
      underlying_book: DRAFTKINGS_SPORTSBOOK
      sample_scope: SINGLE_BOOK_MULTI_STATE
      sample_type: REAL_WAGERS
      independence_group: DRAFTKINGS
      selected_team_tickets_pct:
      selected_team_handle_pct:
    - provider: VSIN
      underlying_book: CIRCA
      sample_scope: SINGLE_BOOK
      sample_type: REAL_WAGERS
      independence_group: CIRCA
      selected_team_tickets_pct:
      selected_team_handle_pct:
```

Sample taxonomy:

```yaml
sample_scope:
  - SINGLE_BOOK
  - SINGLE_BOOK_MULTI_STATE
  - MULTI_BOOK_NAMED
  - MULTI_BOOK_UNDISCLOSED
  - COMMUNITY_CONTEST
  - MEDIA_REPORTED_BOOK_DATA
sample_type:
  - REAL_WAGERS
  - CONTEST_ENTRIES
  - USER_PICKS
  - UNKNOWN
```

Statusy:

```yaml
data_status:
  - AVAILABLE
  - PARTIAL
  - STALE
  - NO_DATA
  - INCOMPLETE
  - CONFLICTING_LINEAGE
bias_status:
  - PUBLIC_ON_SELECTED_TEAM
  - PUBLIC_AGAINST_SELECTED_TEAM
  - BALANCED
  - CROSS_PROVIDER_CONFLICT
  - NOT_ASSESSABLE
```

Public bias definiujemy glownie przez `tickets_pct`. Handle opisuje koncentracje pieniedzy.

Derived metrics:

```text
selected_ticket_handle_gap_pp = selected_handle_pct - selected_tickets_pct
average_ticket_ratio_selected_vs_opponent =
    (selected_handle_pct / selected_tickets_pct)
    /
    (opponent_handle_pct / opponent_tickets_pct)
```

Przyklad `68% tickets / 54% handle`:

```text
ticket_pattern: PUBLIC_MAJORITY_SELECTED
handle_pattern: MODEST_HANDLE_MAJORITY_SELECTED
ticket_handle_pattern: HIGHER_AVERAGE_TICKET_OPPONENT
sharp_identity: NOT_ESTABLISHED
```

Snapshot phases:

```yaml
split_snapshots:
  - phase: MODEL_GENERATION
  - phase: T_MINUS_24H
  - phase: T_MINUS_6H
  - phase: T_MINUS_90M
```

Source lineage:

```yaml
source_lineage:
  DRAFTKINGS_DIRECT:
    independence_group: DRAFTKINGS
  VSIN_DRAFTKINGS:
    independence_group: DRAFTKINGS
  VSIN_CIRCA:
    independence_group: CIRCA
  ACTION_NETWORK:
    independence_group: ACTION_SPORTS_INSIGHTS
  SPORTS_INSIGHTS:
    independence_group: ACTION_SPORTS_INSIGHTS
  COVERS_CONSENSUS:
    independence_group: COVERS_COMMUNITY
```

Reason codes:

```yaml
source_quality:
  - SINGLE_BOOK_REAL_WAGERS
  - MULTI_BOOK_POOL_DISCLOSED
  - MULTI_BOOK_POOL_UNDISCLOSED
  - COMMUNITY_CONTEST_ONLY
  - PROVIDER_LINEAGE_OVERLAP
  - TOTAL_TICKET_COUNT_AVAILABLE
  - TOTAL_TICKET_COUNT_MISSING
  - ABSOLUTE_HANDLE_MISSING
timing:
  - CAPTURE_TIMESTAMP_MISSING
  - SOURCE_UPDATE_TIME_MISSING
  - SNAPSHOT_STALE
  - MARKET_OPEN_TO_CAPTURE_ACCUMULATION
  - SPLITS_INCLUDE_MULTIPLE_LINE_VERSIONS
interpretation:
  - PUBLIC_TICKET_MAJORITY_SELECTED
  - PUBLIC_TICKET_MAJORITY_OPPONENT
  - TICKETS_BALANCED
  - HANDLE_MAJORITY_SELECTED
  - HANDLE_MAJORITY_OPPONENT
  - LOW_TICKET_HIGH_HANDLE_SELECTED
  - HIGH_TICKET_LOW_HANDLE_SELECTED
  - CROSS_PROVIDER_CONFLICT
  - INSUFFICIENT_SAMPLE
  - SHARP_IDENTITY_NOT_ESTABLISHED
```

Obecny test SF-LA:

```yaml
public_bias:
  data_status: NO_DATA
  bias_status: NOT_ASSESSABLE
  provider_observations: []
  independent_source_count: 0
  reason_codes:
    - NO_CURRENT_BETTING_SPLITS
    - PROVIDER_MISSING
    - CAPTURE_TIMESTAMP_MISSING
    - MARKET_SPECIFIC_SAMPLE_MISSING
```

### 11. power_rankings_check

To nie jest oficjalna prawda. To benchmark zewnetrzny.

Zrodla:

```yaml
primary_internal:
  - INTERNAL_MODEL: neutral-field PowerScore / team rating
  - INTERNAL_MODEL: internal_neutral_power_gap
  - INTERNAL_MODEL: game-specific adjustments separated from base power
external_benchmarks:
  direct_point_comparison:
    - ESPN FPI
    - PFF Point Spread Team Ratings
    - internal leave-one-game-out market-implied neutral rating
  direction_and_percentile_only:
    - FTN projected DVOA / DAVE
    - nfelo if not converted to spread points
    - SumerSports EPA / success rate component context
  narrative_only:
    - NFL.com power rankings
    - ESPN editorial power rankings
    - The Athletic / CBS / The Ringer power rankings
```

Zasada:

```text
Power rankings sa sanity checkiem, nie dowodem.
Nie porownujemy miejsc 1-32 jako glownej miary outliera.
Do pelnego porownania potrzebny jest internal_neutral_power_gap, nie sam final_model_margin.
```

GPT ma zwrocic:

```text
czy nasz model jest skrajnie rozny od kilku niezaleznych benchmarkow
i czy porownanie dotyczy kierunku, czy takze wielkosci neutral-field gap.
```

Jesli brak dostepu/paywall/metodologii:

```text
source_status = MEDIA_CONTEXT albo NOT_ASSESSABLE
```

Najwazniejsza regola porownywalnosci:

```text
model_margin_raw nie jest bezposrednio porownywalny z FPI/PFF, jesli zawiera:
venue, travel, rest, matchup adjustments, injuries, weather, QB adjustment.
```

Do punktu 11 powinno trafic:

```yaml
internal_power:
  selected_team_rating:
  opponent_rating:
  neutral_power_gap:
  rating_scale:
    - POINTS_ABOVE_AVERAGE
    - NEUTRAL_FIELD_POINTS
    - ELO
    - STANDARDIZED_SCORE
    - ORDINAL_ONLY
  game_adjustments:
    venue:
    travel:
    rest:
    matchup:
    injuries:
    weather:
    qb:
  final_model_margin:
```

Jesli mamy tylko final game margin:

```yaml
alignment_status: NOT_ASSESSABLE
reason_codes:
  - INTERNAL_NEUTRAL_POWER_GAP_MISSING
  - GAME_MARGIN_NOT_DIRECTLY_COMPARABLE_TO_POWER_RATING
```

Comparison modes:

```yaml
DIRECT_POINT_COMPARISON:
  description: porownywalna skala punktow vs srednia druzyna / neutral field
  examples:
    - INTERNAL_NEUTRAL_POWER_GAP
    - ESPN_FPI
    - PFF_POINT_SPREAD_TEAM_RATINGS
    - INTERNAL_MARKET_IMPLIED_RATING
DIRECTION_AND_PERCENTILE_ONLY:
  description: kierunek/tier, bez bezposredniej konwersji na punkty
  examples:
    - FTN_DVOA
    - NFELO_WITHOUT_SPREAD_TRANSLATION
    - SUMERSPORTS_EPA
NARRATIVE_ONLY:
  description: kontekst redakcyjny; nie moze sam uruchomic MODEL_MAJOR_OUTLIER
  examples:
    - NFL_COM
    - ESPN_EDITORIAL
    - THE_ATHLETIC
```

Independence groups:

```yaml
ESPN_FPI:
  independence_group: MARKET_INFORMED_PREDICTIVE
NFELO:
  independence_group: MARKET_INFORMED_PREDICTIVE
INTERNAL_MARKET_RATING:
  independence_group: MARKET_DERIVED
FTN_DVOA:
  independence_group: PLAY_BY_PLAY_EFFICIENCY
SUMERSPORTS_EPA:
  independence_group: PLAY_BY_PLAY_EFFICIENCY
PFF_POINT_SPREAD_RATING:
  independence_group: PFF_PROPRIETARY
NFL_COM:
  independence_group: MEDIA_EDITORIAL
```

Nie tworzymy falszywego konsensusu:

```text
ESPN FPI, nfelo i market-implied rating moga wszystkie miec wspolny sygnal rynkowy.
PFF Point Spread Rating i PFF editorial ranking to jedna rodzina PFF.
ESPN FPI i ESPN editorial ranking to jedna rodzina ESPN, ale rozne source_type.
```

Statusy:

```yaml
data_status:
  - AVAILABLE
  - PARTIAL
  - PRESEASON_ONLY
  - PRIOR_SEASON_ONLY
  - STALE
  - NO_DATA
alignment_status:
  - BROADLY_ALIGNED
  - MODEL_SLIGHT_OUTLIER
  - MODEL_MAJOR_OUTLIER
  - EXTERNAL_SOURCES_CONFLICT
  - NOT_ASSESSABLE
```

Przykladowa polityka:

```yaml
outlier_policy_id: NFL_POWER_ALIGNMENT_V2
slight_outlier_distance_points: 1.5
major_outlier_distance_points: 3.0
minimum_independent_quantitative_families: 2
media_rankings_can_trigger_major_outlier: false
```

Obecnie dla SF-LA:

```yaml
power_rankings_check:
  data_status: PARTIAL
  benchmark_period_status: PRESEASON_ONLY
  alignment_status: NOT_ASSESSABLE
  directional_context: RAMS_NOT_DIRECTIONALLY_ISOLATED
  reason_codes:
    - INTERNAL_NEUTRAL_POWER_GAP_MISSING
    - INTERNAL_TEAM_RANKS_MISSING
    - CURRENT_2026_PRESEASON_BENCHMARKS_AVAILABLE
    - NO_2026_REGULAR_SEASON_DATA_BY_DEFINITION
    - GAME_MARGIN_NOT_DIRECTLY_COMPARABLE_TO_POWER_RATING
```

Interpretacja:

```text
Dostepne benchmarki przedsezonowe moga pokazac, ze Rams nie sa kierunkowo samotnym typem.
Nie wystarcza to jednak do formalnego BROADLY_ALIGNED, dopoki nie mamy internal neutral power gap.
```

### 12. roster_change_check

Zrodla:

```yaml
primary:
  - INTERNAL_MODEL: frozen roster baseline
  - INTERNAL_MODEL: frozen role baseline
  - INTERNAL_MODEL: frozen staff/playcaller baseline
  - OFFICIAL: team roster snapshots
  - OFFICIAL: team transactions
  - OFFICIAL: NFL transaction hub
  - OFFICIAL: coaching announcements / staff pages
  - OFFICIAL: NFL Draft Tracker
  - OFFICIAL: gamebooks, starters, inactives
role_context:
  - NFLVERSE / NFLREADPY: rosters, status, snap counts, player IDs
  - PFR/NFLVERSE: prior season and recent snap shares
  - PFF: role quality, grades, snap-count context
  - OURLADS: projected depth chart manual QA
  - SPOTRAC / OVER_THE_CAP: contract/free-agency context
paid_automation:
  - SPORTRADAR: rosters, transactions, weekly depth charts, change log
  - SPORTSDATAIO: active/all depth charts, roster/injury status, timestamped role changes
secondary:
  - MEDIA_CONTEXT: beat reporters for expected roles, only labelled context
```

Trzy warstwy obowiazkowe:

```text
1. frozen model baseline: co model zakladal o skladzie/rolach/sztabie
2. current official roster/transactions: kto faktycznie jest w druzynie
3. prior/current role evidence: czy zmiana dotyczy startera, rotacji czy glebi
```

Bez baseline'u:

```text
roster_change_check = NOT_ASSESSABLE
```

Powod:

```text
Mozesz opisac offseason roster movement, ale nie mozesz odpowiedziec,
czy model opiera sie na nieaktualnym obrazie skladu.
```

Baseline modelu:

```yaml
model_baseline:
  model_run_id:
  model_version:
  generated_at_utc:
  roster_cutoff_utc:
  injury_cutoff_utc:
  baseline_roster_hash:
  baseline_role_hash:
  baseline_staff_hash:
  roster_source_snapshot_id:
  depth_chart_source_snapshot_id:
  snap_count_window:
```

Rozdzielamy cztery kategorie zmian:

```yaml
change_category:
  ROSTER_MEMBERSHIP_CHANGE:
    - free_agent_added
    - player_departed
    - trade
    - retirement
  ROSTER_STATUS_CHANGE:
    - active_to_ir
    - pup_to_active
    - practice_squad_to_active
  ROLE_CHANGE:
    - backup_to_starter
    - starter_to_rotation
    - outside_cb_to_nickel
    - returner_change
  STAFF_OR_SCHEME_CHANGE:
    - new_head_coach
    - new_coordinator
    - new_playcaller
    - new_ol_coach
```

Kazda zmiana musi miec `model_awareness`:

```yaml
model_awareness:
  status:
    - INCLUDED_IN_BASELINE
    - OCCURRED_AFTER_CUTOFF
    - MISSING_FROM_BASELINE
    - UNKNOWN
  baseline_cutoff_utc:
  transaction_effective_utc:
```

Materialnosc liczy rule engine, nie GPT:

```text
materiality =
    prior_role_weight
  * position_model_sensitivity
  * projected_role_change
  * evidence_confidence
```

Materiality inputs:

```yaml
materiality_inputs:
  prior_season_snap_share:
  recent_snap_share:
  games_started:
  special_teams_snap_share:
  internal_player_value:
  position_group_sensitivity:
  replacement_quality:
  source_confidence:
```

Statusy:

```yaml
risk_status:
  - NO_MATERIAL_CHANGE
  - MINOR_CHANGE
  - REVIEW_REQUIRED
  - MAJOR_ROSTER_DISCONTINUITY
  - NOT_ASSESSABLE
workflow_status:
  - PENDING_BASELINE
  - PENDING_FINAL_53
  - PENDING_ROLE_RESOLUTION
  - MODEL_RERUN_REQUIRED
  - COMPLETE
```

Week 1 rule:

```text
Przed finalnym cutdownem rosterow nie wolno traktowac offseason rosteru jako finalnego Week 1 skladu.
Depth chart przed Week 1 czesto ma status PRESEASON_UNRESOLVED.
```

Reason codes:

```yaml
baseline_failures:
  - INTERNAL_ROSTER_BASELINE_MISSING
  - INTERNAL_ROLE_BASELINE_MISSING
  - INTERNAL_STAFF_BASELINE_MISSING
  - ROSTER_CUTOFF_MISSING
  - BASELINE_HASH_MISSING
current_data_failures:
  - CURRENT_OFFICIAL_ROSTER_MISSING
  - CURRENT_ROSTER_SNAPSHOT_STALE
  - TRANSACTION_HISTORY_INCOMPLETE
  - PLAYER_ID_MAPPING_AMBIGUOUS
  - FINAL_53_NOT_AVAILABLE
  - DEPTH_CHART_PRESEASON_UNRESOLVED
material_changes:
  - STARTING_QB_CHANGED
  - PRIMARY_PLAYCALLER_CHANGED
  - OFFENSIVE_COORDINATOR_CHANGED
  - DEFENSIVE_COORDINATOR_CHANGED
  - MULTIPLE_OL_STARTERS_CHANGED
  - SECONDARY_STARTER_TURNOVER
  - PASS_RUSH_STARTER_TURNOVER
  - PRIMARY_SKILL_PLAYER_DEPARTED
  - KICKER_OR_PUNTER_CHANGED
  - MAJOR_ROOKIE_ROLE_EXPECTED
  - MAJOR_PLAYER_RETURNING_FROM_INJURY
model_link:
  - CHANGE_OCCURRED_AFTER_MODEL_CUTOFF
  - CHANGE_MISSING_FROM_MODEL_BASELINE
  - MODEL_AWARENESS_UNKNOWN
  - MODEL_RERUN_REQUIRED
  - EFFECT_ON_EDGE_NOT_QUANTIFIED
```

Obecnie dla SF-LA:

```yaml
roster_change_check:
  data_status: PARTIAL
  risk_status: NOT_ASSESSABLE
  workflow_status: PENDING_BASELINE_AND_FINAL_ROLE_RESEARCH
  current_snapshot:
    roster_phase: PRE_FINAL_CUTDOWN
    official_team_rosters_available: true
    official_transaction_history_available: true
    final_53_available: false
    role_resolution_status: PRESEASON_UNRESOLVED
  reason_codes:
    - INTERNAL_ROSTER_BASELINE_MISSING
    - INTERNAL_ROLE_BASELINE_MISSING
    - CURRENT_OFFICIAL_ROSTERS_AVAILABLE
    - OFFICIAL_TRANSACTION_HISTORY_AVAILABLE
    - FINAL_53_NOT_AVAILABLE
    - DEPTH_CHART_PRESEASON_UNRESOLVED
    - MATERIAL_ROSTER_DELTA_NOT_YET_COMPUTED
```

### 13. matchup_specific_risk

Zrodla:

```yaml
primary:
  - INTERNAL_MODEL: matchup dependency report
  - INTERNAL_MODEL: feature contribution / edge driver map
  - INTERNAL_MODEL: model sensitivity to matchup conflict
  - NFLVERSE / NFLREADPY: reproducible EPA, success, pace, xpass, splits
  - OFFICIAL: injuries, inactives, gamebooks, depth/roles from points 3 and 12
  - ESPN_ANALYTICS: PBWR, PRWR, RBWR, RSWR for trench matchups
  - NEXT_GEN_STATS / NFL_PRO / ALL_22: tracking, time to throw, separation, route/coverage context
  - PFF_PREMIUM: blocking, pressure, coverage, grades, matchup charts
  - FTN_DVOA: DVOA/DAVE, adjusted line yards, defense vs receivers, special teams
  - SUMERSPORTS: public EPA, success, personnel tendencies
professional:
  - SPORTS_INFO_SOLUTIONS: charting, participation, blown blocks, pressures, coverage
  - TRUMEDIA: enterprise filtered matchup queries and video
secondary:
  - MEDIA_CONTEXT: scheme notes only if source is clear
```

Zasada:

```text
Nie uzywamy generic rivalry/motivation.
Ryzyko musi byc powiazane z konkretnym matchupem i aktualnym personelem.
Najpierw driver modelu, potem matchup.
```

Prawidlowa kolejnosc:

```text
1. Co konkretnie napedza modelowy edge?
2. Jaka jednostka lub tendencja przeciwnika moze ten driver zneutralizowac?
3. Czy konflikt istnieje w porownywalnych danych?
4. Czy zawodnicy i role odpowiedzialni za konflikt nadal sa aktualni?
5. Jak bardzo model jest wrazliwy na ten konflikt?
```

Bez dependency map:

```yaml
risk_status: NOT_ASSESSABLE
reason_codes:
  - INTERNAL_MATCHUP_DEPENDENCY_MAP_MISSING
```

Model dependency:

```yaml
model_dependency:
  edge_driver:
  driver_category:
    - PASS_EFFICIENCY
    - RUSH_EFFICIENCY
    - PRESSURE_ADVANTAGE
    - EXPLOSIVE_PLAY_ADVANTAGE
    - COVERAGE_ADVANTAGE
    - PACE_ADVANTAGE
    - SPECIAL_TEAMS_ADVANTAGE
  feature_name:
  feature_value:
  baseline_value:
  contribution_to_margin_points:
  interaction_features:
  sensitivity:
```

Kazda hipoteza musi miec obie strony konfliktu:

```yaml
risk_hypothesis:
  risk_id:
  hypothesis_type:

  model_dependency:
    feature_name:
    contribution_to_margin:
    dependency_strength:

  selected_team_side:
    metric:
    value:
    rank_or_percentile:
    sample_size:
    period:
    personnel_snapshot:

  opponent_counter:
    metric:
    value:
    rank_or_percentile:
    sample_size:
    period:
    personnel_snapshot:

  comparability:
    same_season:
    same_game_state:
    same_down_context:
    opponent_adjusted:
    metric_definitions_compatible:

  current_personnel:
    confirmed:
    relevant_players:
    role_changes:
    injury_dependencies:

  evidence_quality:
    primary_source:
    corroborating_source:
    independent_source_families:
    source_cutoff:

  hypothesis_status:
    - SUPPORTED
    - PARTIALLY_SUPPORTED
    - PERSONNEL_CONFIRMATION_REQUIRED
    - DISCONFIRMED
    - NOT_ASSESSABLE

  falsification_condition:
  confirmation_required:
  severity:
  model_effect:
  note:
```

LLM nie wybiera severity:

```text
risk_score =
    model_dependency_strength
  * matchup_conflict_strength
  * sample_reliability
  * current_personnel_validity
  * source_confidence
```

Reguly antynarracyjne:

```text
1. Nie przeszukuj wszystkich statystyk po dowolny strach.
2. Nie wystarczy "SF ma dobry pass rush" - potrzeba tez LA pressure allowed, QB under pressure i aktualnego personnel.
3. Zapisuj sample size: plays/dropbacks/targets/routes/games.
4. Uzywaj porownywalnych filtrow i okresow.
5. Aktualny personnel jest bramka.
6. Same rankingi sa slabe bez metric_value, period, definition i sample.
7. Historyczny konflikt bez potwierdzenia Week 1 = hypothesis, nie confirmed risk.
```

Mapa konfliktow:

```yaml
PASS_RUSH_VS_PROTECTION:
  primary: ESPN Win Rates, SIS, PFF
  supporting: NGS time to throw, All-22
WR_TE_VS_COVERAGE:
  primary: PFF, SIS, NGS
  supporting: FTN Defense vs Receivers
RUN_OFFENSE_VS_RUN_DEFENSE:
  primary: FTN Adjusted Line Yards, ESPN RBWR/RSWR
  supporting: SumerSports, nflverse
EXPLOSIVE_PASS_VS_PREVENTION:
  primary: nflverse, NGS
  supporting: PFF/SIS
YAC_VS_TACKLING:
  primary: NGS xYAC, SIS
  supporting: PFF tackling
PACE_PASS_TENDENCY:
  primary: nflverse xpass/pass_oe
  supporting: SIS pace/expected pass rate
SPECIAL_TEAMS:
  primary: FTN Special Teams DVOA
  supporting: SIS/PFF/gamebooks
```

Obecna hipoteza SF-LA:

```yaml
matchup_specific_risk:
  data_status: PARTIAL
  risk_status: NOT_ASSESSABLE
  selected_team: Los Angeles Rams
  opponent: San Francisco 49ers
  model_dependency:
    edge_driver: UNKNOWN
    dependency_status: INTERNAL_MATCHUP_REPORT_MISSING
  risk_hypotheses:
    - risk_id: SF_21_PERSONNEL_PASSING_VS_LA_21_DEFENSE
      hypothesis_type: PERSONNEL_PACKAGE_STRESS
      affected_team: Los Angeles Rams
      data_period: 2025_REGULAR_SEASON
      hypothesis_status: PRESEASON_PERSONNEL_CONFIRMATION_REQUIRED
      severity: NOT_ASSESSABLE
      required_confirmation:
        - SF_2026_21_PERSONNEL_CORE_ACTIVE
        - LA_2026_LB_SAFETY_ROLES_CONFIRMED
        - COORDINATOR_AND_SCHEME_CONTINUITY_CHECKED
        - WEEK_1_INJURIES_AND_INACTIVES_CONFIRMED
        - INTERNAL_MODEL_DEPENDS_ON_LA_DEFENSIVE_EFFICIENCY
        - MODEL_SENSITIVITY_TO_THIS_MATCHUP_QUANTIFIED
      limitations:
        - PRIOR_SEASON_DATA
        - PERSONNEL_NOT_FINAL
        - MODEL_EDGE_DRIVER_UNKNOWN
        - NO_2026_REGULAR_SEASON_SAMPLE
```

### 14. game_script_risk

Zrodla:

```yaml
primary:
  - INTERNAL_MODEL: stateful play-by-play or possession-level simulator
  - INTERNAL_MODEL: margin PMF and p_cover/p_push/p_loss
  - INTERNAL_MODEL: scenario policy and frozen scenario definitions
  - NFLVERSE / NFLREADPY / NFLFASTR: play-by-play, EP/WP, xpass, score-state behavior
  - NEXT_GEN_STATS / NFL_PRO: tracking, time to throw, coverage, route, pressure context
  - SPORTS_INFO_SOLUTIONS: pace, expected pass rate, on/off, probability tools
  - TRUMEDIA: enterprise filtered game-state queries
  - SUMERSPORTS: public EPA, success, personnel and pass-rate priors
  - CURRENT_INPUTS: roster, injury, weather, market snapshot, price quality
```

Zasada:

```text
Game script risk nie jest pickiem.
To pytanie: czy edge zalezy od kruchego scenariusza?
Nie pytamy, ktory game script nastapi.
Pytamy, czy oferta nadal spelnia wymagania po wymuszeniu kilku zdefiniowanych scenariuszy.
```

Bez symulacji lub p_cover/p_push/p_loss:

```text
game_script_risk = NOT_ASSESSABLE
```

Wymagany artefakt symulacji:

```yaml
simulation_run:
  simulation_id:
  model_run_id:
  model_version:
  scenario_policy_id:
  generated_at_utc:
  random_seed_set:
  simulation_count:
  common_random_numbers: true
  baseline_quote:
    spread:
    price_decimal:
  baseline:
    margin_pmf:
    p_cover:
    p_push:
    p_loss:
    ev:
  monte_carlo_error:
    p_cover_se:
    ev_se:
```

Stanowy symulator musi obslugiwac co najmniej:

```yaml
game_state:
  quarter:
  game_seconds_remaining:
  score_differential:
  possession:
  field_position:
  down:
  distance:
  timeouts_remaining:
behavior:
  pass_probability:
  pace:
  fourth_down_aggressiveness:
  timeout_usage:
  run_rate:
  explosive_attempt_rate:
```

Symulacja `margin ~ Normal(mean, sd)` nie wystarcza dla punktu 14.
Przy spreadzie -3 wynik musi byc dyskretny:

```text
selected margin > 3 = COVER
selected margin = 3 = PUSH
selected margin < 3 = LOSS
```

Kazdy scenariusz zwraca:

```yaml
scenario_distribution:
  p_cover:
  p_push:
  p_loss:
  ev:
delta_vs_baseline:
  p_cover_delta:
  p_push_delta:
  p_loss_delta:
  ev_delta:
  edge_retention_ratio:
```

Rozdzielamy prawdopodobienstwo scenariusza od wplywu:

```yaml
scenario:
  plausibility:
    class:
      - CORE
      - STRESS
      - TAIL
      - UNKNOWN
    probability_estimate:
    probability_source:
  impact:
    p_cover_delta:
    ev_delta:
```

Scenariusz moze byc malo prawdopodobny, ale bardzo szkodliwy albo czesty, ale malo szkodliwy.

Wymagane scenariusze bazowe dla spreadu:

```yaml
score_state:
  - SELECTED_TRAILS_7_END_Q1
  - SELECTED_TRAILS_10_HALFTIME
  - CLOSE_GAME_HALFTIME
  - SELECTED_LEADS_10_HALFTIME
  - LATE_ONE_SCORE_LEAD
  - LATE_ONE_SCORE_DEFICIT
volume_pace:
  - LOW_POSSESSION_GAME
  - HIGH_POSSESSION_GAME
  - SELECTED_SLOW_LEAD_SCRIPT
  - OPPONENT_CLOCK_CONTROL
play_selection:
  - SELECTED_PASS_HEAVY
  - SELECTED_RUN_HEAVY
  - OPPONENT_COMEBACK_PASS_HEAVY
  - BOTH_TEAMS_RUN_HEAVY
efficiency_stress:
  - SELECTED_RED_ZONE_REGRESSION
  - SELECTED_EXPLOSIVES_SUPPRESSED
  - OPPONENT_EXPLOSIVE_SHOCK
  - SELECTED_THIRD_DOWN_REGRESSION
  - SELECTED_PRESSURE_STRESS
  - FIELD_POSITION_DISADVANTAGE
turnovers:
  - TURNOVER_DIFFERENTIAL_MINUS_1
  - TURNOVER_DIFFERENTIAL_MINUS_2
  - EARLY_TURNOVER_SELECTED
  - RED_ZONE_TURNOVER_SELECTED
late_game_key_number:
  - LATE_LEAD_3
  - LATE_LEAD_7
  - REGULATION_TIED
  - KNEELDOWN_VS_SCORE
```

Nie dublujemy efektow:

```text
Jesli deficyt 10 punktow endogenicznie zwieksza pass rate, nie dodajemy osobnego +20pp pass rate,
chyba ze scenariusz specjalnie testuje dodatkowy niezalezny szok.
```

Statusy:

```yaml
risk_status:
  - ROBUST_ACROSS_SCRIPTS
  - MODERATE_SCRIPT_SENSITIVITY
  - HIGH_SCRIPT_FRAGILITY
  - REVIEW_REQUIRED
  - NOT_ASSESSABLE
```

NOT_ASSESSABLE gdy:

```text
brak baseline PMF, brak p_cover/push/loss, brak stanowego symulatora,
brak scenario policy albo brak definicji scenariuszy.
```

Obecnie dla SF-LA:

```yaml
game_script_risk:
  data_status: NOT_ASSESSABLE
  risk_status: NOT_ASSESSABLE
  selected_team: Los Angeles Rams
  opponent: San Francisco 49ers
  market: FULL_GAME_SPREAD
  pick: Los Angeles Rams -3
  baseline_simulation:
    model_margin_raw: 4.99
    margin_pmf_available: false
    p_cover: null
    p_push: null
    p_loss: null
    ev: null
    simulator_type: UNKNOWN
  reason_codes:
    - MARGIN_PMF_MISSING
    - OUTCOME_PROBABILITIES_MISSING
    - SCENARIO_SIMULATION_MISSING
    - SCRIPT_RESPONSE_FUNCTIONS_MISSING
    - PERSONNEL_INPUTS_NOT_FINAL
    - GAME_SCRIPT_FRAGILITY_NOT_ESTABLISHED
```

### 15. closing_line

Zrodla:

```yaml
primary:
  - INTERNAL_MARKET: append-only quote ledger
  - DIRECT_SPORTSBOOK: direct book close capture near market close
  - OPTICODDS: full quote history with active/locked/removed events
  - SPORTSDATAIO: provider-declared close and line movement
  - THE_ODDS_API: interval snapshot fallback / budget backfill
manual_qa:
  - BETSTAMP_PRO: same-book and best-market CLV QA
  - UNABATED: line history and visual QA
fallback:
  - MANUAL_SCREENSHOT: fallback evidence
  - CONSENSUS_ONLY: reference benchmark only, not same-book close
```

Nie jest game-week pre-bet field. To post-close.

Najwazniejsza definicja:

```text
closing quote = ostatni aktywny pregame quote konkretnego booka, jurysdykcji,
eventu, rynku, market scope i selected side przed finalnym przejsciem rynku
do in-play albo finalnym zamknieciem pregame marketu.
```

Nie ustawiamy automatycznie:

```yaml
close_timestamp_utc: scheduled_kickoff_utc
```

Closing timestamp to timestamp closing quote'u albo finalnej granicy rynku, nie planowany kickoff.

Closing spread bez ceny jest niekompletny:

```yaml
closing_quote:
  spread:
  price_american:
  price_decimal:
  quote_id:
  source_timestamp_utc:
```

Rozdzielamy dwa close'y:

```yaml
closing_main_quote:
  spread:
  price_american:
  price_decimal:
  is_main: true

closing_exact_decision_line:
  decision_spread:
  available_at_close:
  closing_price_american:
  closing_price_decimal:
  is_main: false
```

Przyklad:

```text
Decision: LA -3 (-110)
Closing main: LA -3.5 (-110)
Closing exact decision line: LA -3 (-130)
```

To pozwala osobno ocenic ruch spreadu i cene dokladnie tej samej linii.

Same-book close i reference-market close to rozne pomiary:

```yaml
same_book_close:
  decision_book:
  close_book: same as decision_book
reference_market_close:
  provider_or_bookset:
  close_definition:
```

Nie wolno traktowac `decision_book: DraftKings` vs `close_book: Circa` jako same-book CLV.

Close policy:

```yaml
closing_policy:
  policy_id: NFL_PREGAME_CLOSE_V2
  close_definition: LAST_ACTIVE_PREGAME_QUOTE
  boundary_priority:
    - PROVIDER_PREGAME_TO_INPLAY_TRANSITION
    - FINAL_PREGAME_MARKET_LOCK
    - ACTUAL_GAME_START
    - SCHEDULED_KICKOFF_FALLBACK
```

Nie uzywamy pierwszego locka, jesli rynek pozniej znowu sie otworzyl przed kickoffem.
Nie mieszamy pierwszej linii live z closing line.

Timestampy:

```yaml
timestamps:
  source_timestamp_utc:
  captured_at_utc:
  close_boundary_utc:
  scheduled_kickoff_utc:
  actual_start_utc:
```

Statusy:

```yaml
status:
  - AVAILABLE
  - PENDING_NOT_CLOSED
  - MISSING
  - STALE
  - CONFLICTING
  - NOT_APPLICABLE
```

`NOT_APPLICABLE` rezerwujemy dla anulowania/no-action/braku porownywalnego rynku. Przed meczem uzywamy `PENDING_NOT_CLOSED`.

Evidence grade:

```yaml
evidence_grade:
  - DIRECT_BOOK_CLOSE_AT_TARGET_STAKE
  - FULL_EVENT_HISTORY_PROVIDER
  - PROVIDER_DECLARED_CLOSE
  - INTERVAL_SNAPSHOT
  - MANUAL_ODDS_SCREEN
  - MANUAL_SCREENSHOT
  - CONSENSUS_ONLY
  - UNKNOWN
```

Deterministyczny algorytm:

```text
1. Zidentyfikuj event.
2. Wez book i jurisdiction z decision quote.
3. Ustaw market=SPREAD, scope=FULL_GAME, selected side.
4. Pobierz wszystkie pregame quote events: main + alternates.
5. Odrzuc in-play, halves, quarters, props, zla strone i inne jurysdykcje.
6. Znajdz finalna granice pregame.
7. Wybierz ostatni ACTIVE main quote przed granica.
8. Osobno sprawdz ostatnia cene exact decision spread.
9. Zachowaj spread i price z jednego quote ID.
10. Zapisz raw payload i hash.
```

CLV inputs:

```yaml
clv_inputs:
  decision_spread:
  decision_price_decimal:
  closing_main_spread:
  closing_main_price_decimal:
  closing_exact_line_price_decimal:
```

Obecnie dla SF-LA:

```yaml
closing_line:
  status: PENDING_NOT_CLOSED
  event:
    season: 2026
    week: 1
    away: San Francisco 49ers
    home: Los Angeles Rams
    scheduled_kickoff_utc: "2026-09-11T00:35:00Z"
  selection:
    selected_team: Los Angeles Rams
  decision_reference:
    book: null
    jurisdiction: null
    spread: -3.0
    price_american: -110
    source_type: MANUAL_CONSENSUS
  closing_main_quote: null
  closing_exact_decision_line: null
  reason_codes:
    - EVENT_NOT_STARTED
    - PREGAME_MARKET_NOT_CLOSED
    - CLOSING_QUOTE_NOT_YET_AVAILABLE
    - DECISION_QUOTE_NOT_BOOK_SPECIFIC
```

### 16. closing_price

Zrodla:

```yaml
primary:
  - INTERNAL_MARKET: same close_snapshot_id as point 15
  - INTERNAL_MARKET: append-only quote ledger
  - DIRECT_SPORTSBOOK: direct book close capture / betslip near close
  - OPTICODDS: full quote history including alternates
  - SPORTSDATAIO: provider-declared close with spread and payout fields
  - THE_ODDS_API: interval snapshot fallback
manual_qa:
  - BETSTAMP: same-book and best-market close QA
  - UNABATED: line history and alternate-line QA
```

Spread i price musza byc z tego samego snapshotu.

Najwazniejsza zasada:

```text
closing_price nie jest osobna liczba dopisywana do closing_line.
Punkty 15 i 16 sa dwiema projekcjami tego samego closing_market_snapshot.
```

Wspolny obiekt:

```yaml
closing_market_snapshot:
  close_snapshot_id:
  book:
  jurisdiction:
  market: SPREAD
  market_scope: FULL_GAME
  selected_team:
  close_boundary_utc:
  closing_main_quote:
  closing_exact_decision_line_quote:
  raw_payload_hash:
```

Punkt 15 odczytuje spread z `close_snapshot_id`.
Punkt 16 odczytuje price z tego samego `close_snapshot_id`.

To blokuje bledy:

```text
closing spread z DraftKings + closing price z Circa
spread z 00:30 + price z 00:34
```

Wymagane zapisy ceny:

```yaml
closing_main_quote:
  status:
  book:
  jurisdiction:
  selected_team:
  spread:
  price_american:
  price_decimal:
  raw_implied_probability:
  is_main: true
  quote_id:
  opponent_quote:
    opponent:
    spread:
    price_american:
    price_decimal:
    quote_id:

closing_exact_decision_line:
  status:
    - AVAILABLE
    - NOT_OFFERED_AT_CLOSE
    - MISSING
    - UNKNOWN
  spread:
  available_at_close:
  price_american:
  price_decimal:
  raw_implied_probability:
  is_main:
  quote_id:
  opponent_quote:
    opponent:
    spread:
    price_american:
    price_decimal:
    quote_id:
```

Zapisuj obie strony rynku, gdy mozliwe:

```yaml
closing_exact_decision_line_market:
  selected:
    team: LA
    spread: -3.0
    price_american: -130
  opponent:
    team: SF
    spread: 3.0
    price_american: 110
```

Powod:

```text
Do no-vig closing probability i price-inclusive CLV w punkcie 17 potrzebna jest tez cena drugiej strony.
```

Najlepiej zapisac cala drabine:

```yaml
closing_spread_ladder:
  - selected_spread: -2.5
    selected_price:
    opponent_spread: 2.5
    opponent_price:
  - selected_spread: -3.0
    selected_price:
    opponent_spread: 3.0
    opponent_price:
  - selected_spread: -3.5
    selected_price:
    opponent_spread: 3.5
    opponent_price:
```

Exact decision line:

```yaml
NOT_OFFERED_AT_CLOSE:
  meaning: pelna drabina sprawdzona, sportsbook nie oferowal juz tej linii
MISSING:
  meaning: nie wiadomo, czy linia byla dostepna, bo brak alternates/pelnego snapshotu/timestampu
```

Nie interpolujemy ceny exact decision line w punkcie 16.

STALE:

```text
Quote nie jest stale tylko dlatego, ze ostatnia zmiana byla kilka minut przed close.
STALE oznacza: nie mozemy potwierdzic, ze last-seen quote pozostal aktywny do close boundary.
```

Price context:

```yaml
price_context:
  price_type:
    - STANDARD_PUBLIC
    - ACCOUNT_SPECIFIC
    - ODDS_BOOST
    - PROMOTIONAL
    - BONUS_BET
    - UNKNOWN
  promotion_id:
  maximum_stake:
```

Canonical closing price powinien byc `STANDARD_PUBLIC`.

Atomicity:

```yaml
atomic_quote_validation:
  same_provider_payload: true
  same_quote_id: true
  same_market_id: true
  same_selection_id: true
  same_spread: true
  same_source_timestamp: true
  same_market_snapshot_id: true
  same_provider_response_hash: true
```

Timestampy:

```yaml
timestamps:
  quote_source_timestamp_utc:
  provider_received_at_utc:
  captured_at_utc:
  close_boundary_utc:
  actual_game_start_utc:
  scheduled_kickoff_utc:
```

Nie podstawiamy `captured_at_utc` jako nieznanego `quote_source_timestamp_utc`.

Statusy:

```yaml
status:
  - AVAILABLE
  - PENDING_NOT_CLOSED
  - MISSING
  - STALE
  - CONFLICTING
  - NOT_APPLICABLE
```

Deterministyczny algorytm:

```text
1. Pobierz close_snapshot_id z punktu 15.
2. Potwierdz book, jurisdiction, event, selected team, full-game spread, overtime.
3. Ustal close boundary z punktu 15.
4. Pobierz wszystkie pregame outcomes: main + alternates.
5. Wybierz ostatni aktywny main quote dla selected team przed close boundary.
6. Zapisz jego spread i price z tego samego quote ID.
7. Znajdz przeciwna strone tego samego market snapshotu.
8. Wyszukaj exact decision spread wsrod wszystkich linii, nie tylko main.
9. Jesli exact line nie istnieje po pelnym sprawdzeniu: NOT_OFFERED_AT_CLOSE.
10. Jesli nie wiadomo, czy sprawdzono alternates: MISSING albo UNKNOWN.
11. Zapisz payload, hash i timestampy.
12. Nie licz CLV, EV ani kierunku.
```

Reason codes:

```yaml
availability:
  - CLOSING_MAIN_QUOTE_AVAILABLE
  - EXACT_DECISION_LINE_AVAILABLE
  - EXACT_DECISION_LINE_NOT_OFFERED_AT_CLOSE
  - EXACT_DECISION_LINE_AVAILABILITY_UNKNOWN
  - CLOSING_QUOTE_MISSING
integrity:
  - SPREAD_PRICE_ATOMIC
  - SPREAD_PRICE_NOT_ATOMIC
  - SAME_BOOK_CONFIRMED
  - SAME_JURISDICTION_CONFIRMED
  - MARKET_SCOPE_CONFIRMED
  - OVERTIME_RULE_CONFIRMED
  - OPPOSITE_SIDE_QUOTE_MISSING
timing:
  - FULL_CLOSE_PATH_AVAILABLE
  - PROVIDER_DECLARED_CLOSE_USED
  - INTERVAL_SNAPSHOT_USED
  - SOURCE_TIMESTAMP_MISSING
  - FINAL_MARKET_STATE_NOT_OBSERVED
  - QUOTE_STALE_AT_CLOSE
  - INPLAY_QUOTE_EXCLUDED
source:
  - DIRECT_BOOK_CAPTURE
  - FULL_EVENT_HISTORY_PROVIDER
  - PROVIDER_DECLARED_CLOSE
  - MANUAL_QA_ONLY
  - CONSENSUS_NOT_BOOK_SPECIFIC
price_context:
  - STANDARD_PUBLIC_PRICE
  - ACCOUNT_SPECIFIC_PRICE
  - PROMOTIONAL_PRICE
  - PRICE_TYPE_UNKNOWN
```

Obecnie dla SF-LA:

```yaml
closing_price:
  status: PENDING_NOT_CLOSED
  close_snapshot_id: null
  selected_team: Los Angeles Rams
  market: SPREAD
  market_scope: FULL_GAME
  overtime_included: true
  decision_reference:
    book: null
    jurisdiction: null
    spread: -3.0
    price_american: -110
    price_decimal: 1.9091
    price_type: UNKNOWN
    source_type: MANUAL_CONSENSUS
    quote_id: null
  closing_main_quote:
    status: PENDING
    spread: null
    price_american: null
    price_decimal: null
    quote_id: null
  closing_exact_decision_line:
    status: PENDING
    spread: -3.0
    available_at_close: UNKNOWN
    price_american: null
    price_decimal: null
    quote_id: null
  reason_codes:
    - EVENT_NOT_STARTED
    - PREGAME_MARKET_NOT_CLOSED
    - CLOSING_QUOTE_NOT_YET_AVAILABLE
    - DECISION_QUOTE_NOT_BOOK_SPECIFIC
    - DECISION_JURISDICTION_MISSING
    - DECISION_QUOTE_ID_MISSING
```

### 17. clv_points

Zrodla:

```yaml
primary:
  - POINT_9: atomic decision snapshot
  - POINT_15_16: shared atomic close snapshot
  - INTERNAL_MARKET: append-only quote ledger
  - CLOSING_LADDER: full close ladder and both sides when available
  - POINT_6: key-number context
  - INTERNAL_RULES: selected-team spread convention and CLV policy
manual_qa:
  - UNABATED: no-vig and CLV calculation QA
  - BETSTAMP: same-book versus best-market CLV QA
```

Liczy Python:

```text
clv_points = decision_spread_selected_team - closing_spread_selected_team
```

albo wedlug naszej docelowej konwencji z `variant_b_rules`.

Najwazniejsza zasada:

```text
Punkt 17 nie pobiera rynku i nie interpretuje go przez LLM.
Liczy deterministycznie z decision_snapshot_id oraz close_snapshot_id.
```

Trzy osobne wyniki:

```yaml
clv_outputs:
  spread_clv_points:
  raw_same_line_price_clv:
  price_inclusive_clv:
```

Nie dodajemy ich do siebie:

```text
0.5 punktu + 10 centow != jeden laczny CLV
```

Spread i cena sa roznymi reprezentacjami wartosci rynkowej. `price_inclusive_clv` musi wyceniac cala pare spread+price jedna metoda.

Poziom 1: spread CLV

```text
spread_clv_points =
    decision_spread_selected_team
    - closing_main_spread_selected_team
```

Interpretacja:

```yaml
positive: DECISION_SPREAD_BETTER
zero: SAME_SPREAD
negative: CLOSING_SPREAD_BETTER
```

Wymagana normalizacja:

```yaml
raw_provider_quote:
  selection: SF
  spread: 3.5
normalized_selected_team_quote:
  selection: LA
  spread: -3.5
```

Poziom 2: raw same-line price CLV

Tylko dla dokladnie tego samego spreadu:

```text
price_clv_decimal =
    decision_decimal - closing_exact_line_decimal

raw_implied_probability_delta_pp =
    100 * (1 / closing_exact_line_decimal - 1 / decision_decimal)
```

To nadal zawiera vig, wiec nazwa to:

```yaml
raw_same_line_price_clv:
  includes_vig: true
```

Poziom 3: price-inclusive CLV

Najlepsza metoda:

```yaml
price_inclusive_clv:
  method: CLOSING_FAIR_MARGIN_DISTRIBUTION
  closing_p_cover:
  closing_p_push:
  closing_p_loss:
  decision_price_decimal:
  closing_fair_ev_of_decision_quote:
```

Formula:

```text
closing_fair_ev_of_decision_quote =
    closing_p_cover * (decision_decimal - 1) - closing_p_loss
```

Fallback, gdy exact decision line ma obie strony:

```yaml
method: NO_VIG_EXACT_DECISION_LINE
valuation_scope: CONDITIONAL_ON_NO_PUSH
```

Przy integer spread potrzebny jest p_push do unconditional EV:

```yaml
unconditional_ev_status: NOT_ASSESSABLE
reason: P_PUSH_MISSING
```

Gdy exact decision line nie byla dostepna na close:

```yaml
price_inclusive_clv:
  status: NOT_ASSESSABLE
  reason_codes:
    - EXACT_DECISION_LINE_NOT_AVAILABLE
    - CLOSING_LADDER_MISSING
    - CLOSING_MARGIN_DISTRIBUTION_MISSING
```

Key number context z punktu 6:

```yaml
key_number_context:
  key_number:
  event_type:
  settlement_transition:
  affected_probability_mass:
```

Przyklad:

```text
LA -3 -> close LA -3.5 = PUSH_TO_LOSS through 3
LA -8.5 -> close LA -9 = COVER_TO_PUSH at 9
```

Te dwa ruchy maja ten sam `spread_clv_points: +0.5`, ale inna wartosc probabilistyczna.

Benchmarki:

```yaml
clv_benchmarks:
  same_book:
  reference_book:
  reference_no_vig_consensus:
  best_available:
```

Polityka musi byc zamrozona przed obliczeniem:

```yaml
close_benchmark_policy_id: NFL_CLV_BENCHMARK_V2
```

Nie wybieramy po fakcie booka, wobec ktorego CLV wyglada najlepiej.

Statusy:

```yaml
status:
  - AVAILABLE
  - PARTIAL
  - PENDING_NOT_CLOSED
  - MISSING_DECISION
  - MISSING_CLOSE
  - NOT_ASSESSABLE
  - CONFLICTING
```

Deterministyczna kolejnosc:

```text
1. Pobierz decision_snapshot_id.
2. Pobierz close_snapshot_id.
3. Potwierdz selected-team convention.
4. Potwierdz market scope, OT, book i jurysdykcje.
5. Policz spread_clv_points.
6. Wyszukaj exact decision spread na close: main + alternates.
7. Jesli exact line istnieje, policz raw same-line price CLV.
8. Jesli masz obie strony exact line, zastosuj zamrozony devig.
9. Jesli masz closing PMF, policz pelny price-inclusive EV.
10. Jesli exact line nie istnieje, uzyj closing ladder / pricing engine.
11. Jesli nie ma ladder ani PMF: spread CLV dostepny, price-inclusive NOT_ASSESSABLE.
12. Importuj key-number event z punktu 6.
13. Nie uzywaj wyniku meczu.
```

Reason codes:

```yaml
decision:
  - DECISION_SNAPSHOT_AVAILABLE
  - DECISION_SNAPSHOT_MISSING
  - DECISION_QUOTE_NOT_BOOK_SPECIFIC
  - DECISION_PRICE_MISSING
  - DECISION_QUOTE_PREVIEW_ONLY
  - DECISION_PRICE_PROMOTIONAL
close:
  - CLOSING_MAIN_QUOTE_AVAILABLE
  - CLOSING_MAIN_QUOTE_MISSING
  - EXACT_DECISION_LINE_AVAILABLE
  - EXACT_DECISION_LINE_NOT_OFFERED_AT_CLOSE
  - EXACT_DECISION_LINE_AVAILABILITY_UNKNOWN
  - CLOSING_LADDER_AVAILABLE
  - CLOSING_LADDER_MISSING
  - BOTH_SIDES_CLOSE_PRICES_AVAILABLE
  - OPPOSITE_SIDE_CLOSE_PRICE_MISSING
integrity:
  - DECISION_AND_CLOSE_SAME_BOOK
  - DECISION_AND_CLOSE_DIFFERENT_BOOK
  - SAME_JURISDICTION_CONFIRMED
  - MARKET_SCOPE_MATCH
  - SELECTED_TEAM_PERSPECTIVE_MATCH
  - CLOSING_SPREAD_PRICE_ATOMIC
  - ATOMICITY_VALIDATION_FAILED
  - INPLAY_QUOTE_EXCLUDED
calculation:
  - SPREAD_CLV_AVAILABLE
  - SAME_LINE_PRICE_CLV_AVAILABLE
  - RAW_PRICE_CLV_INCLUDES_VIG
  - DEVIG_POLICY_MISSING
  - CLOSING_PMF_AVAILABLE
  - CLOSING_PMF_MISSING
  - PRICE_INCLUSIVE_CLV_AVAILABLE
  - PRICE_INCLUSIVE_CLV_NOT_ASSESSABLE
  - KEY_NUMBER_TRANSITION_PRESENT
```

Obecnie dla SF-LA:

```yaml
clv_points:
  status: PENDING_NOT_CLOSED
  selected_team: Los Angeles Rams
  market: SPREAD
  market_scope: FULL_GAME
  overtime_included: true
  decision_quote:
    snapshot_id: null
    book: null
    jurisdiction: null
    spread: -3.0
    price_american: -110
    price_decimal: 1.9091
    evidence_grade: PREVIEW_ONLY
    source_type: MANUAL_CONSENSUS
  closing_reference:
    close_snapshot_id: null
    benchmark_type: UNKNOWN
  spread_clv:
    status: PENDING
    spread_clv_points: null
  raw_same_line_price_clv:
    status: PENDING
  price_inclusive_clv:
    status: PENDING
    method: NOT_AVAILABLE
  reason_codes:
    - EVENT_NOT_STARTED
    - PREGAME_MARKET_NOT_CLOSED
    - CLOSING_LINE_NOT_AVAILABLE
    - CLOSING_PRICE_NOT_AVAILABLE
    - DECISION_QUOTE_NOT_BOOK_SPECIFIC
    - SAME_BOOK_CLV_NOT_ASSESSABLE
```

### 18. process_quality

Zrodla:

```yaml
primary:
  - INTERNAL_AUDIT_BUNDLE: immutable outputs from points 1-17
  - INTERNAL_PROCESS_POLICY_REGISTRY: due phases, criticality, hard-block rules
  - INTERNAL_EVENT_CLOCK: audit phase, kickoff, close boundary, due windows
  - INTERNAL_EVIDENCE_MANIFEST: source tiers, timestamps, hashes, storage refs
  - INTERNAL_CALCULATION_MANIFEST: producer type, code version, input/output hashes
  - INTERNAL_MODEL_LINEAGE: model_run_id, PMF hash, calibration artifact
  - INTERNAL_MANUAL_OVERRIDE_LOG: approved overrides with before/after hashes
```

Nie potrzeba internetu. Punkt 18 nie szuka nowej informacji o meczu. Sprawdza, czy punkty 1-17 sa kompletne, spojne i wymagane w aktualnej fazie.

Kluczowe rozdzielenie:

```yaml
point_quality:
  run_status: VALID | INVALID | NOT_RUN
  domain_status: AVAILABLE | PARTIAL | NOT_ASSESSABLE | PENDING_NOT_CLOSED | PREVIEW_ONLY | STALE
  due_status: NOT_DUE | DUE | OVERDUE | POST_EVENT_ONLY
  criticality: HARD_REQUIRED | HARD_WHEN_DUE | SOFT_REQUIRED | CONTEXT_ONLY | POST_EVENT
  gate_effect: NONE | WARNING | HARD_BLOCK
  effective_status: OK | PARTIAL | NOT_ASSESSABLE | PENDING_NOT_DUE | BLOCKED
```

Punkt moze byc technicznie poprawny i jednoczesnie blokowac proces. Przyklad: `market_snapshot` zapisany jako `MANUAL_CONSENSUS` jest poprawnym rekordem, ale nie jest market-grade proof.

### 19. final_operator_decision

Zrodla:

```yaml
primary:
  - INTERNAL_PROCESS_QUALITY_SNAPSHOT: frozen point 18 output and output hash
  - INTERNAL_OPERATOR_DECISION_POLICY: action precedence and blocker routing
  - INTERNAL_AUDIT_PHASE_STATE: current phase and due window
  - INTERNAL_BLOCKER_CLASSIFICATION_REGISTRY: integrity/data/model/market/pending classes
  - INTERNAL_ACTION_ROUTING_REGISTRY: owner and required action per blocker class
  - INTERNAL_MANUAL_OVERRIDE_LOG: authorized operator overrides
  - INTERNAL_OPERATOR_DECISION_LEDGER: append-only decision history
```

To nie jest pick ani rekomendacja bettingowa. Punkt 19 nie czyta internetu, nie analizuje druzyn i nie przelicza EV/CLV/no-chase. Jest deterministycznym routerem dzialan na bazie punktu 18.

Rozdzielamy stan bramki od dzialania:

```yaml
gate_state:
  - OPEN
  - HOLD
  - INVALID

operator_action:
  - HOLD_PENDING_DATA
  - RETURN_FOR_DATA_CORRECTION
  - RETURN_FOR_MODEL_RERUN
  - READY_FOR_NEXT_AUDIT_STAGE
  - AUDIT_COMPLETE
  - INVALID_AUDIT
```

Priorytet decyzji:

```yaml
  - INVALID_AUDIT
  - RETURN_FOR_DATA_CORRECTION
  - RETURN_FOR_MODEL_RERUN
  - HOLD_PENDING_DATA
  - READY_FOR_NEXT_AUDIT_STAGE
  - AUDIT_COMPLETE
```

`HOLD_PENDING_DATA` musi miec `hold_type`, zeby odroznic pasywne czekanie od aktywnej naprawy modelu/danych.

## Zrodla, ktore GPT moze znalezc dynamicznie

Dla dowolnego meczu GPT powinien dynamicznie wyszukac:

```text
"[Team A] official injury report"
"[Team B] official injury report"
"[Team A] official transactions"
"[Team B] official transactions"
"[Team A] official depth chart"
"[Team B] official depth chart"
"[Team A] [Team B] official game page"
"[venue name] official event page"
"official weather service [venue city country]"
"NFL injuries"
"NFL inactives"
"NFL official schedule [season] [team]"
```

## Najwazniejsze ograniczenie

```text
Zrodlo moze wspierac tylko ten typ twierdzenia, do ktorego sie nadaje.
```

Przyklady:

```text
NFL injuries -> status kontuzji, nie market movement.
Public splits -> tickets/handle, nie sharp money.
Weather forecast -> pogoda, nie edge.
Venue page -> miejsce/godzina, nie football advantage.
Power rankings -> benchmark, nie dowod EV.
```
