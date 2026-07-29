# Point 8 Decision: price_quality

Status: accepted for Variant B.

## Core decision

`price_quality` is not a generic note about whether the line "looks good".
It is a deterministic check of the exact current line-price pair for the selected side.

Best hierarchy:

```text
MODEL PMF / FROZEN FRONTIER
            +
DIRECT SPORTSBOOK BETSLIP
            =
PRICE QUALITY DECISION
```

Odds feeds help discover and validate prices. They do not decide whether the price is acceptable according to our model.

## Required separation

We separate quote reliability from valuation:

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

A stale, aggregator-only, or manual-consensus quote is not automatically `UNACCEPTABLE`.
It is usually `NOT_ASSESSABLE`.

## Primary sources

1. Own model-run artifact and margin PMF.
2. Direct sportsbook / betslip confirmation at target stake.
3. Frozen `acceptable_quote_frontier`.
4. OpticOdds for current prices, alternates, timestamps, and market status.
5. Official sportsbook house rules.
6. SportsDataIO as second feed, history, and backfill.
7. Betstamp PRO for manual line shopping and limits.
8. Unabated for manual line-price comparison.
9. The Odds API as budget quote snapshot source.
10. nflverse / nflreadpy plus calibration reports for validation.

## EV formula

For a standard cash spread bet with push probability:

```text
EV = p_cover * (decimal_odds - 1) - p_loss
minimum_decimal_odds = 1 + p_loss / p_cover
minimum_decimal_odds_with_min_ev = 1 + (p_loss + minimum_ev_required) / p_cover
```

Break-even needs two fields:

```yaml
conditional_cover_rate_given_no_push: 1 / decimal_odds
unconditional_cover_probability_required: (1 - p_push) / decimal_odds
```

American odds are stored for display, but valuation should use decimal odds.

## Atomic quote rule

Spread and price must come from the same quote, snapshot, selected side, market ID, and market scope.
Do not combine a spread from one timestamp with a price from another timestamp.

## Promotions

Standard cash bets, odds boosts, bonus bets, and free bets must be evaluated separately.
The standard EV formula is valid only for ordinary cash wagers.

## Current SF-LA test result

For the current preview record:

```yaml
selected_team: LA
spread: -3.0
price_american: -110
book: MANUAL_CONSENSUS
p_cover: null
p_push: null
p_loss: null
acceptable_quote_frontier: null
```

Correct classification:

```yaml
quote_quality_status: UNVERIFIED
price_status: NOT_ASSESSABLE
valuation_method: NOT_AVAILABLE
reason_codes:
  - CURRENT_QUOTE_IS_CONSENSUS
  - CURRENT_QUOTE_NOT_EXECUTABLE
  - QUOTE_TIMESTAMP_MISSING
  - P_COVER_MISSING
  - P_PUSH_MISSING
  - P_LOSS_MISSING
  - ACCEPTABLE_QUOTE_FRONTIER_MISSING
```

This is not a rejection of the pick. It means the current data is not enough to reproduce EV for the exact spread and price.
