# Point 9 Decision: market_snapshot

Status: accepted for Variant B.

## Core decision

`market_snapshot` is evidence capture, not analysis.

The key distinction:

```text
QUOTE EXISTED IN A FEED
QUOTE WAS DISPLAYED IN THE BOOK
QUOTE WAS AVAILABLE AT TARGET STAKE
WAGER WAS ACCEPTED
```

These are four different evidence levels and must not be collapsed into one generic `MARKET_GRADE`.

## Evidence grades

```yaml
evidence_grade:
  EXECUTED_GRADE: accepted ticket or digital receipt
  DIRECT_BOOK_GRADE: betslip checked at target stake before execution
  PROVIDER_GRADE: named-book quote from licensed provider/feed
  PREVIEW_ONLY: manual consensus, provider consensus, article, no named book, no timestamp
  INVALID: inconsistent quote, wrong event, wrong side, wrong market scope, missing price/spread
```

## Three separate axes

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

A suspended market can be a valid snapshot of market state, but it is not an executable quote.

## Source hierarchy

1. Accepted ticket / digital receipt.
2. Direct sportsbook betslip checked at target stake.
3. OpticOdds named-book atomic quote.
4. SportsDataIO as second feed and historical backfill.
5. The Odds API as budget current snapshot.
6. Betstamp PRO for manual odds screen and limits context.
7. Unabated for latency, market scope, and visual QA.
8. Manual consensus only as `PREVIEW_ONLY`.

## Atomic quote rule

Spread and price must come from the same quote object:

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

## Timestamp policy

Use three distinct timestamps when available:

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
```

Do not fill a missing source timestamp with capture time. Leave the unknown field as null.

## Stake policy

Provider limit and account-specific stake are separate:

```yaml
stake_check_status:
  NOT_TESTED
  DISPLAYED_IN_BETSLIP
  ACCEPTED_IN_FULL
  PARTIALLY_ACCEPTED
  REJECTED
  PROVIDER_LIMIT_ONLY
```

Only an accepted ticket can populate `accepted_stake`.

## Current SF-LA test result

For current preview data:

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

This can be used as a working market reference only. It cannot be used as market-grade edge proof.
