# Point 15 Decision: closing_line

Status: accepted for Variant B.

## Core decision

`closing_line` is a post-close market evidence field.
It should be derived from quote history, not manually guessed from scheduled kickoff.

Best source stack:

```text
append-only quote ledger
        +
deterministic close definition
        +
last active pregame quote
        +
separate main close and exact-decision-line close
```

## Closing definition

```yaml
closing_policy:
  policy_id: NFL_PREGAME_CLOSE_V2
  close_definition: >
    Last active pregame quote for the exact sportsbook, jurisdiction,
    event, market scope, selection and market family before the
    final transition from pregame to in-play.
  boundary_priority:
    - PROVIDER_PREGAME_TO_INPLAY_TRANSITION
    - FINAL_PREGAME_MARKET_LOCK
    - ACTUAL_GAME_START
    - SCHEDULED_KICKOFF_FALLBACK
```

Do not use scheduled kickoff as the closing timestamp unless it is only a fallback and explicitly labeled.
Do not use the first lock if the market later reopens before kickoff.
Do not use the first live/in-play line as the closing line.

## Atomic quote rule

Closing spread without closing price is incomplete.

```yaml
closing_quote:
  spread:
  price_american:
  price_decimal:
  quote_id:
  source_timestamp_utc:
```

Spread and price must come from the same quote ID or provider-declared close record.

## Two close records

Store both when possible:

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

Example:

```text
Decision: LA -3 (-110)
Closing main: LA -3.5 (-110)
Closing exact decision line: LA -3 (-130)
```

This separates spread movement from price movement at the exact decision line.

## Same-book vs reference close

```yaml
same_book_close:
  decision_book:
  close_book: same as decision_book

reference_market_close:
  provider_or_bookset:
  close_definition:
```

DraftKings decision quote versus Circa close is not same-book CLV. It may be a reference-market benchmark, but must be labeled that way.

## Evidence grades

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

OpticOdds full quote history is best for full event path.
SportsDataIO provider-declared close is useful but should still be validated.
The Odds API interval snapshots are useful fallback, not exact close proof.

## Statuses

```yaml
status:
  - AVAILABLE
  - PENDING_NOT_CLOSED
  - MISSING
  - STALE
  - CONFLICTING
  - NOT_APPLICABLE
```

`NOT_APPLICABLE` is reserved for cancellation, no-action, or no comparable market.
Before the game, use `PENDING_NOT_CLOSED`.

## Deterministic algorithm

1. Identify event.
2. Select exact book and jurisdiction from decision quote.
3. Select market = SPREAD, scope = FULL_GAME, selected side.
4. Retrieve all pregame quote events: main and alternates.
5. Drop in-play, halves, quarters, props, wrong side, wrong jurisdiction.
6. Find final pregame boundary.
7. Select last ACTIVE main quote before boundary.
8. Separately check last price for exact decision spread.
9. Preserve spread and price from one quote ID.
10. Store raw payload and hash.

## CLV inputs

Point 15 does not interpret CLV, but it must provide:

```yaml
clv_inputs:
  decision_spread:
  decision_price_decimal:
  closing_main_spread:
  closing_main_price_decimal:
  closing_exact_line_price_decimal:
```

## Current SF-LA status

As of July 24, 2026, the event has not reached pregame close.

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

No closing spread or closing price should be recorded yet.

## Language rule

Allowed:

```text
Closing line is pending because the pregame market has not closed.
```

Not allowed:

```text
Closing line equals scheduled kickoff quote.
Consensus close can replace same-book close.
Spread-only close is enough for CLV.
```
