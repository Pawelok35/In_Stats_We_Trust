# Point 14 Decision: game_script_risk

Status: accepted for Variant B.

## Core decision

`game_script_risk` asks whether the pick's EV survives predefined game-state stress tests.
It does not ask which script will happen.

The decision source is an internal stateful simulator:

```text
stateful simulator
        +
baseline margin PMF / p_cover / p_push / p_loss
        +
frozen scenario policy
        =
game-script sensitivity result
```

External data estimates behavior parameters. It does not classify the risk by itself.

## Required simulation artifact

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

A normal final-score model such as `margin ~ Normal(mean, sd)` is not enough.
Point 14 needs the game path: time, score, possession, field position, pace, play selection, and drive/play outcomes.

For spread `-3`, the simulator must preserve discrete settlement:

```text
selected margin > 3 = COVER
selected margin = 3 = PUSH
selected margin < 3 = LOSS
```

## Scenario outputs

Each scenario must return:

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

Scenario plausibility and impact are separate:

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

## Required scenario groups

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

Do not double-count endogenous behavior.
If trailing by 10 already raises pass rate inside the simulator, do not add a separate +20pp pass-rate shock unless that is the specific independent stress being tested.

## Statuses

```yaml
risk_status:
  - ROBUST_ACROSS_SCRIPTS
  - MODERATE_SCRIPT_SENSITIVITY
  - HIGH_SCRIPT_FRAGILITY
  - REVIEW_REQUIRED
  - NOT_ASSESSABLE
```

`NOT_ASSESSABLE` applies when baseline PMF, p_cover/p_push/p_loss, simulator, scenario policy, or scenario definitions are missing.

## Source hierarchy

1. Internal stateful play-by-play or possession-level simulator.
2. Margin PMF and p_cover/p_push/p_loss.
3. nflverse / nflreadpy / nflfastR for play-by-play, EP/WP, xpass, and score-state behavior.
4. Sports Info Solutions or TruMedia for pace, expected pass rate, on/off, and probability tools.
5. NFL Next Gen Stats / NFL Pro for tracking and player-level response context.
6. SumerSports for public EPA, success, personnel, and pass-rate priors.
7. Current injury, roster, weather, market snapshot, and price-quality inputs.

## Current SF-LA status

With current pick data:

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

The listed scenarios are required stress tests, not forecasts.
Each scenario must produce a push-aware distribution and updated EV for Rams -3.

## Language rule

Allowed:

```text
Game-script sensitivity is not assessable from mean margin alone.
```

Not allowed:

```text
The Rams are fragile if they trail early.
This game will be low possession, so the pick is risky.
```
