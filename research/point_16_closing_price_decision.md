# Point 16 Decision: closing_price

Status: accepted for Variant B.

## Core decision

`closing_price` must not be collected independently from `closing_line`.

Points 15 and 16 are two projections of the same immutable object:

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

Point 15 reads spread from `close_snapshot_id`.
Point 16 reads price from the same `close_snapshot_id`.

This prevents:

```text
closing spread from DraftKings + closing price from Circa
spread from 00:30 + price from 00:34
```

## Required quote structure

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

## Both sides and ladder

Point 16 should store both sides when available:

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

The full closing ladder is best:

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

This enables no-vig and price-inclusive CLV in Point 17.
Point 16 still does not calculate CLV.

## Exact decision line status

```yaml
NOT_OFFERED_AT_CLOSE:
  meaning: full ladder checked and sportsbook did not offer the decision spread

MISSING:
  meaning: unknown whether decision spread was offered because alternates, full snapshot, or timestamp are missing
```

Do not interpolate exact-decision-line price in Point 16.

## Stale definition

A quote is not stale merely because its last price change occurred several minutes before close.

`STALE` means:

```text
we only have an old last-seen quote and cannot confirm that it remained active until close boundary
```

## Price context

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

Canonical closing price should be `STANDARD_PUBLIC`.

## Deterministic algorithm

1. Read `close_snapshot_id` from Point 15.
2. Confirm book, jurisdiction, event, selected team, full-game spread, overtime.
3. Use close boundary from Point 15.
4. Retrieve all pregame outcomes: main and alternates.
5. Select last active main quote for selected team before close boundary.
6. Store its spread and price from the same quote ID.
7. Find the opposite side from the same market snapshot.
8. Search exact decision spread across all lines, not only main.
9. If exact line is absent after full ladder check, set `NOT_OFFERED_AT_CLOSE`.
10. If alternates were not checked, set `MISSING` or `UNKNOWN`.
11. Store payload, hash, and timestamps.
12. Do not calculate CLV, EV, or direction.

## Current SF-LA status

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

## Language rule

Allowed:

```text
Closing price is pending because the shared close snapshot does not exist yet.
```

Not allowed:

```text
Closing price was -110 without quote identity.
Closing price can be copied from another book.
Point 16 proves CLV.
```
