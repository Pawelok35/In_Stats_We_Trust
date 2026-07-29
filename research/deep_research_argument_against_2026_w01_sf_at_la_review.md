# Deep Research review - argument_against_auto

## Game

```yaml
season: 2026
week: 1
date_us: 2026-09-10
date_local_melbourne: 2026-09-11
away: San Francisco 49ers
home: Los Angeles Rams
venue: Melbourne Cricket Ground, Melbourne, Australia
market: spread
current_line: LA -3.0
price: -110
model_pick: LA -3.0
model_tag: VALUE PLAY
model_fair_margin_raw: LA -4.99
model_fair_margin_rounded: LA -5.0
edge_vs_line_raw: +1.99
edge_vs_line_rounded: +2.0
```

## Verdict on GPT Pro output

The output is useful, but it is too aggressive if copied directly into the
engine. It marks many unresolved checks as HIGH. That is good for audit
discipline, but not every missing external input should automatically block a
pick.

The highest-value parts for our system are:

- neutral-site / home-field leakage check;
- executable quote verification;
- key number 3 and no-chase rule;
- fair margin is not the same as cover probability / EV;
- Week 1 calibration penalty;
- injury and roster timestamp staleness;
- travel/acclimation check for Australia;
- weather/field setup check;
- manual checks list.

## Rules worth implementing first

### 1. neutral_site_home_field_leakage

```yaml
rule_id: neutral_site_home_field_leakage
factor: neutral_site
condition: neutral_site == true and home_field_adjustment_points > 0
risk_level: HIGH
auto_possible: semi
required_data:
  - neutral_site
  - model_home_field_adjustment_points
  - venue
argument_against: "Neutral-site game: verify the model did not give standard home-field value to the designated home team."
```

This is very important for LA vs SF because the Rams are listed as home team,
but the game is not at SoFi Stadium.

### 2. current_quote_verification

```yaml
rule_id: current_quote_verification
factor: market_quote
condition: book starts_with MANUAL or odds_snapshot_type != executable
risk_level: HIGH
auto_possible: semi
required_data:
  - book
  - line
  - price
  - odds_timestamp
  - executable_quote_status
argument_against: "Line is not confirmed as an executable sportsbook quote. Do not treat the edge as market-grade proof."
```

This fits our setup because Week 1 currently uses `MANUAL_CONSENSUS`.

### 3. key_number_three_exact

```yaml
rule_id: key_number_three_exact
factor: key_number
condition: favorite_spread == 3.0
risk_level: MEDIUM
auto_possible: true
required_data:
  - line
  - pick_side
argument_against: "Pick sits exactly on NFL key number 3. Keep push protection; do not chase worse numbers without recalculation."
```

This should be MEDIUM at -3.0, not automatically HIGH. It becomes HIGH only if
the market moves to -3.5.

### 4. no_chase_past_three

```yaml
rule_id: no_chase_past_three
factor: key_number
condition: model_input_spread == -3.0 and executable_spread <= -3.5
risk_level: HIGH
auto_possible: true
required_data:
  - model_input_spread
  - executable_spread
argument_against: "No-chase rule triggered: moving from -3.0 to -3.5 turns a three-point win from push into loss."
```

This is one of the best concrete rules from the GPT output.

### 5. fair_margin_not_ev

```yaml
rule_id: fair_margin_not_ev
factor: edge_quality
condition: model_fair_margin exists and cover_probability is missing
risk_level: MEDIUM
auto_possible: true
required_data:
  - model_fair_margin
  - cover_probability
  - push_probability
  - loss_probability
argument_against: "Fair margin alone is not full EV. Model should eventually estimate cover/push/loss probability at the exact line and price."
```

This is correct. Our current edge is point-margin based. It is useful, but not
yet a complete probability-based EV model.

### 6. edge_below_uncertainty_buffer

```yaml
rule_id: edge_below_uncertainty_buffer
factor: model_uncertainty
condition: edge_vs_line_rounded <= configured_uncertainty_buffer
risk_level: MEDIUM
auto_possible: true
required_data:
  - edge_vs_line
  - configured_uncertainty_buffer
argument_against: "Model edge may be smaller than the forecast uncertainty buffer."
```

For Week 1 we can set a stricter buffer, for example 2.0 points.

### 7. week_one_calibration

```yaml
rule_id: week_one_calibration
factor: early_season
condition: week <= 3
risk_level: MEDIUM
auto_possible: true
required_data:
  - week
argument_against: "Early-season sample risk: roles, scheme changes, and roster continuity are less certain."
```

This should be a standard Week 1-3 warning, not always an automatic block.

### 8. official_injury_report_missing

```yaml
rule_id: official_injury_report_missing
factor: injuries
condition: final_inactives_available == false
risk_level: HIGH
auto_possible: semi
required_data:
  - practice_reports
  - game_status
  - final_inactives
argument_against: "Game-week injury and inactive data are not final. Availability risk remains unresolved."
```

This should matter most close to kickoff. Months before the game, it is expected
to be missing and should be tracked as `pending`, not as a failed pick.

### 9. travel_acclimation_asymmetry

```yaml
rule_id: travel_acclimation_asymmetry
factor: travel
condition: international_game == true and arrival_plan_unknown == true
risk_level: MEDIUM
auto_possible: semi
required_data:
  - venue_country
  - team_arrival_dates
  - practice_schedule
argument_against: "International travel creates acclimation risk; compare arrival and practice plans before final approval."
```

Useful specifically because this game is in Australia.

### 10. weather_and_field_setup

```yaml
rule_id: weather_and_field_setup
factor: weather_field
condition: outdoor_or_non_dome == true and reliable_forecast_missing == true
risk_level: MEDIUM
auto_possible: semi
required_data:
  - venue
  - roof_type
  - wind
  - precipitation
  - field_condition
argument_against: "Weather and field setup are not final. Wind, rain, or surface issues could compress margin."
```

Keep this as a game-week check.

## Rules to keep manual for now

- Matthew Stafford health sensitivity;
- Rams backup QB dropoff;
- 49ers rehab/return variance;
- defensive staff and scheme changes;
- coaching familiarity;
- offensive line status;
- pass rush availability;
- secondary communication variance;
- public narrative / handle / tickets;
- roster version timestamp.

These are useful, but we should not pretend they are automatic until we have
reliable data sources.

## Important correction

GPT Pro's output treats many missing data points as HIGH risk. Operationally,
we should separate:

```text
missing because game is months away -> pending check
missing near kickoff -> real process failure / high risk
```

Otherwise every future Week 1 pick will be blocked too early.

## Recommended engine behavior

For this game today:

```yaml
argument_against_auto:
  risk_level: MEDIUM
  primary_reason: "Week 1 neutral-site international game at key number 3 with manual quote source."
  blocking_flags:
    - current_quote_verification
  warning_flags:
    - neutral_site_home_field_leakage
    - key_number_three_exact
    - fair_margin_not_ev
    - edge_below_uncertainty_buffer
    - week_one_calibration
    - travel_acclimation_asymmetry
  pending_game_week_checks:
    - official_injury_report_missing
    - weather_and_field_setup
    - roster_version_timestamp
    - offensive_line_status
    - qb_health
```

If the executable line becomes LA -3.5:

```yaml
argument_against_auto:
  risk_level: HIGH
  primary_reason: "No-chase rule triggered: LA -3.0 moved to LA -3.5 through key number 3."
  blocking_flags:
    - no_chase_past_three
```

## Sources checked

- NFL Melbourne Game page: https://www.nfl.com/international/games/melbourne/
- Rams official announcement: https://www.therams.com/news/rams-san-francisco-49ers-game-friday-september-11-melbourne-australia
- MCG event page: https://www.mcg.org.au/events/2026/september/los-angeles-rams-v-san-francisco-49ers

