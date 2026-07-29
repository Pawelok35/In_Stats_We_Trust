# Point 11 Decision: power_rankings_check

Status: accepted for Variant B.

## Core decision

`power_rankings_check` is a sanity check against external team-strength benchmarks.
It is not proof of edge and it must not turn media rankings into a betting signal.

The main methodological correction:

```text
Do not compare ordinal ranks 1-32 as the primary outlier test.
Do not compare final game-specific model margin directly with neutral-field power ratings.
```

For formal point-based alignment, the internal model must expose:

```yaml
internal_power:
  selected_team_rating:
  opponent_rating:
  internal_neutral_power_gap:
  final_model_margin:
  game_adjustments:
    venue:
    travel:
    rest:
    matchup:
    injuries:
    weather:
    qb:
```

If only `model_margin_raw` is available, formal alignment is not assessable.

## Comparison modes

```yaml
DIRECT_POINT_COMPARISON:
  examples:
    - INTERNAL_NEUTRAL_POWER_GAP
    - ESPN_FPI
    - PFF_POINT_SPREAD_TEAM_RATINGS
    - INTERNAL_MARKET_IMPLIED_RATING

DIRECTION_AND_PERCENTILE_ONLY:
  examples:
    - FTN_PROJECTED_DVOA
    - FTN_DAVE
    - NFELO_WITHOUT_SPREAD_TRANSLATION
    - SUMERSPORTS_EPA

NARRATIVE_ONLY:
  examples:
    - NFL_COM_POWER_RANKINGS
    - ESPN_EDITORIAL_POWER_RANKINGS
    - THE_ATHLETIC
    - CBS
    - THE_RINGER
```

Media/editorial rankings cannot independently trigger `MODEL_MAJOR_OUTLIER`.

## Source hierarchy

Production stack:

1. Internal neutral-field PowerScore.
2. ESPN FPI.
3. PFF Point Spread Team Ratings.
4. FTN projected DVOA / DAVE.
5. nfelo.
6. Leave-one-game-out market-implied neutral rating.
7. SumerSports EPA / success rate component context.
8. One editorial source such as NFL.com or The Athletic.

Minimal stack:

1. Internal neutral-field PowerScore.
2. ESPN FPI.
3. FTN projected DVOA / DAVE.
4. PFF Point Spread Rating or nfelo.
5. One editorial source.

## Independence groups

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

Do not treat ESPN FPI, nfelo, and market-implied ratings as fully independent market-free confirmations.
Do not treat PFF point ratings and PFF editorial rankings as independent source families.

## Statuses

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

These are separate. A Week 1 audit can have:

```yaml
data_status: PRESEASON_ONLY
alignment_status: NOT_ASSESSABLE
directional_context: SELECTED_TEAM_NOT_DIRECTIONALLY_ISOLATED
```

## Outlier policy

Initial policy:

```yaml
outlier_policy_id: NFL_POWER_ALIGNMENT_V2
slight_outlier_distance_points: 1.5
major_outlier_distance_points: 3.0
minimum_independent_quantitative_families: 2
media_rankings_can_trigger_major_outlier: false
```

The thresholds are a starting policy and should be calibrated historically.

## Current SF-LA decision

The first GPT answer was directionally useful but too optimistic if interpreted as formal alignment.

Accepted conclusion:

```yaml
power_rankings_check:
  data_status: PARTIAL
  benchmark_period_status: PRESEASON_ONLY
  alignment_status: NOT_ASSESSABLE
  directional_context: RAMS_NOT_DIRECTIONALLY_ISOLATED
  interpretation_status: PRESEASON_CONTEXT_ONLY
  reason_codes:
    - INTERNAL_NEUTRAL_POWER_GAP_MISSING
    - INTERNAL_TEAM_RANKS_MISSING
    - CURRENT_2026_PRESEASON_BENCHMARKS_AVAILABLE
    - NO_2026_REGULAR_SEASON_DATA_BY_DEFINITION
    - GAME_MARGIN_NOT_DIRECTLY_COMPARABLE_TO_POWER_RATING
```

Available preseason benchmarks generally rate the Rams above the 49ers, so the model is not directionally isolated.
However, formal `BROADLY_ALIGNED` is not allowed until the internal neutral-field gap is available and comparable with direct-point external ratings.

## Language rule

Allowed:

```text
Directional context is aligned with available preseason benchmarks.
Formal power-rating alignment is not assessable because internal neutral-field gap is missing.
```

Not allowed:

```text
Power rankings confirm the pick.
External rankings prove the edge.
Model is aligned because Rams rank above 49ers in media polls.
```
