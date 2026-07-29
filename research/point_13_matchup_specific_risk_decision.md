# Point 13 Decision: matchup_specific_risk

Status: accepted for Variant B.

## Core decision

`matchup_specific_risk` must start from the internal model dependency, not from searching opponent stats for anything scary.

Correct order:

```text
1. What specifically drives the model edge?
2. What opponent unit/tendency can neutralize that driver?
3. Does the conflict exist in comparable data?
4. Are the relevant players and roles current?
5. How sensitive is the model to that conflict?
```

Without a model dependency map, a matchup note can only be a candidate hypothesis.

```yaml
risk_status: NOT_ASSESSABLE
reason_codes:
  - INTERNAL_MATCHUP_DEPENDENCY_MAP_MISSING
```

## Required model dependency

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

## Risk hypothesis schema

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

## Anti-narrative rules

1. Do not search all stats to find a scary angle.
2. Do not write "team has good pass rush" without the other side of the conflict.
3. Store sample size: plays, dropbacks, targets, routes, games.
4. Use comparable filters, periods, and metric definitions.
5. Current personnel is a gate.
6. Rankings alone are weak without metric value, period, definition, and sample.
7. Historical conflict without Week 1 personnel confirmation is a hypothesis, not a confirmed risk.

## Severity

LLM does not assign severity.

```text
risk_score =
    model_dependency_strength
  * matchup_conflict_strength
  * sample_reliability
  * current_personnel_validity
  * source_confidence
```

Python/rule engine owns severity. LLM can summarize the hypothesis.

## Source hierarchy

1. Internal matchup dependency report.
2. nflverse / nflreadpy for reproducible play-by-play splits.
3. NFL Pro / Next Gen Stats / All-22 for tracking and film context.
4. Sports Info Solutions and TruMedia for professional charting and filtered queries.
5. ESPN win rates for trench matchups.
6. PFF Premium Stats for player-level blocking, pressure, coverage, and roles.
7. FTN DVOA/DAVE for opponent-adjusted unit comparisons.
8. SumerSports for public EPA, success, and personnel tendencies.
9. Official injury, inactive, roster, and gamebook sources for current personnel.

## Current SF-LA hypothesis

The SF 21 personnel vs LA defense angle can be stored as a preseason hypothesis, not as a confirmed risk.

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

## Language rule

Allowed:

```text
This is a preseason risk hypothesis requiring personnel and model-dependency confirmation.
```

Not allowed:

```text
This matchup breaks the Rams pick.
The 49ers 21 personnel edge proves the model is wrong.
```
