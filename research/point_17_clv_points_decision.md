# Point 17 Decision: clv_points

Status: accepted for Variant B.

## Core decision

`clv_points` is a deterministic calculation layer.
It must not fetch market data again and must not rely on LLM interpretation.

Inputs:

```yaml
decision_snapshot_id:  # Point 9
close_snapshot_id:     # shared Point 15/16 closing snapshot
```

Python/rule engine calculates CLV from those immutable inputs.

## Three separate outputs

Store three different outputs:

```yaml
spread_clv_points:
raw_same_line_price_clv:
price_inclusive_clv:
```

Do not add them together. A half point of spread and a price move are different units.

## Spread CLV

Formula, after normalizing both spreads to selected-team perspective:

```text
spread_clv_points =
    decision_spread_selected_team
    - closing_main_spread_selected_team
```

Interpretation:

```yaml
positive: DECISION_SPREAD_BETTER
zero: SAME_SPREAD
negative: CLOSING_SPREAD_BETTER
```

Examples:

```text
LA -3.0 -> LA -3.5 = +0.5
SF +3.5 -> SF +3.0 = +0.5
LA -3.5 -> LA -3.0 = -0.5
```

## Raw same-line price CLV

Only applies when the exact decision spread is available at close.

```text
price_clv_decimal =
    decision_decimal - closing_exact_line_decimal

raw_implied_probability_delta_pp =
    100 * (1 / closing_exact_line_decimal - 1 / decision_decimal)
```

This includes sportsbook vig, so the field must be named raw:

```yaml
raw_same_line_price_clv:
  includes_vig: true
```

## Price-inclusive CLV

This is the best long-term comparable CLV metric because it prices the whole decision quote.

Preferred method:

```yaml
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

Fallback method:

```yaml
method: NO_VIG_EXACT_DECISION_LINE
valuation_scope: CONDITIONAL_ON_NO_PUSH
```

For integer spreads, unconditional EV requires `p_push`.

If exact decision line is unavailable and there is no closing ladder or closing PMF:

```yaml
price_inclusive_clv:
  status: NOT_ASSESSABLE
  reason_codes:
    - EXACT_DECISION_LINE_NOT_AVAILABLE
    - CLOSING_LADDER_MISSING
    - CLOSING_MARGIN_DISTRIBUTION_MISSING
```

## Key numbers

`spread_clv_points: +0.5` is not always equally valuable.

Examples:

```text
LA -3 -> close LA -3.5: PUSH_TO_LOSS through 3
LA -8.5 -> close LA -9: COVER_TO_PUSH at 9
```

Point 17 must import:

```yaml
key_number_context:
  key_number:
  event_type:
  settlement_transition:
  affected_probability_mass:
```

## Benchmarks

Keep separate:

```yaml
clv_benchmarks:
  same_book:
  reference_book:
  reference_no_vig_consensus:
  best_available:
```

The benchmark policy must be frozen before calculation:

```yaml
close_benchmark_policy_id: NFL_CLV_BENCHMARK_V2
```

Do not choose the benchmark after the fact.

## Statuses

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

`PARTIAL` is important because spread CLV may be available when price-inclusive CLV is not.

## Calculation order

1. Load decision snapshot.
2. Load close snapshot.
3. Confirm selected-team convention.
4. Confirm market scope, overtime, book, and jurisdiction.
5. Calculate spread CLV.
6. Search exact decision spread at close: main and alternates.
7. If exact line exists, calculate raw same-line price CLV.
8. If both sides exist, apply frozen devig method.
9. If closing PMF exists, calculate full price-inclusive EV.
10. If exact line does not exist, use full closing ladder or pricing engine.
11. If ladder and PMF are missing, mark price-inclusive CLV not assessable.
12. Import key-number context from Point 6.
13. Do not use game result.

## Current SF-LA status

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

## Language rule

Allowed:

```text
CLV is pending because the pregame market has not closed.
```

Not allowed:

```text
CLV proves the bet was good.
CLV uses final score.
Spread CLV and price CLV can be summed directly.
```
