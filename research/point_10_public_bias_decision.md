# Point 10 Decision: public_bias / tickets_handle

Status: accepted for Variant B.

## Core decision

`public_bias / tickets_handle` is documented public-positioning context.
It is not a sharp-money detector and it does not prove why a line moved.

Splits describe a specific sample from a specific provider/book, usually accumulated from market open.
They may include wagers placed at earlier line versions.

## Source ranking

1. DraftKings direct betting splits: named single-book real wagers.
2. VSiN Pro: separate DraftKings and Circa samples.
3. Sports Insights: real wagers, multi-book contributing pool, ticket count if available.
4. Action Network: broad multi-book sample, pool undisclosed.
5. Official book publications such as BetMGM, FanDuel, Caesars when market-specific.
6. ScoresAndOdds: secondary cross-check, pool composition undisclosed.
7. Covers Consensus: community sentiment only, not sportsbook handle.

## Covers rule

Covers Consensus must not populate:

```yaml
selected_team_tickets_pct:
selected_team_handle_pct:
```

It can only populate:

```yaml
community_sentiment:
  provider: COVERS_CONSENSUS
  sample_type: FREE_CONTEST_ENTRIES
  selected_team_pick_pct:
  participant_count:
```

If Covers reports direct book data from DraftKings, BetMGM, FanDuel, etc., record the underlying book and use Covers only as the reporting channel.

## Per-provider schema

Do not create one combined percentage across providers unless absolute denominators are available.

```yaml
public_bias:
  data_status:
  bias_status:
  selected_team:
  market: SPREAD
  market_scope: FULL_GAME

  provider_observations:
    - provider:
      underlying_book:
      source_family:
      independence_group:
      sample_scope:
      sample_type:
      captured_at_utc:
      source_updated_at_utc:
      current_spread_at_capture:
      current_price_at_capture:
      selected_team_tickets_pct:
      selected_team_handle_pct:
      opponent_tickets_pct:
      opponent_handle_pct:
      total_ticket_count:
      total_handle_amount:
      accumulation_window:
      splits_include_prior_line_versions:
      line_segmented_data_available:
      reason_codes:

  cross_provider_summary:
    independent_source_count:
    ticket_direction_agreement:
    handle_direction_agreement:
    provider_conflict:
```

## Sample taxonomy

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

## Interpretation rules

Public bias is primarily about ticket count.
Handle describes money concentration, not the number of people.

For `68% tickets / 54% handle` on the selected team:

```yaml
ticket_pattern: PUBLIC_MAJORITY_SELECTED
handle_pattern: MODEST_HANDLE_MAJORITY_SELECTED
ticket_handle_pattern: HIGHER_AVERAGE_TICKET_OPPONENT
sharp_identity: NOT_ESTABLISHED
```

The approximate average-ticket ratio:

```text
(selected_handle_pct / selected_tickets_pct)
/
(opponent_handle_pct / opponent_tickets_pct)
```

This is approximate because public percentages are often rounded and absolute denominators may be missing.

## Source lineage

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

Action Network and Sports Insights should not be treated as fully independent confirmations.
VSiN DraftKings and DraftKings direct should not be treated as independent confirmations either.

## Snapshot phases

Store repeated split snapshots when possible:

```yaml
split_snapshots:
  - phase: MODEL_GENERATION
  - phase: T_MINUS_24H
  - phase: T_MINUS_6H
  - phase: T_MINUS_90M
```

Changing percentages show how the provider sample changed over time. They do not prove causality for line movement.

## Current SF-LA test result

With no current provider-specific NFL spread splits:

```yaml
public_bias:
  data_status: NO_DATA
  bias_status: NOT_ASSESSABLE
  selected_team: LA
  market: SPREAD
  provider_observations: []
  independent_source_count: 0
  reason_codes:
    - NO_CURRENT_BETTING_SPLITS
    - PROVIDER_MISSING
    - CAPTURE_TIMESTAMP_MISSING
    - MARKET_SPECIFIC_SAMPLE_MISSING
```

Do not infer public bias from team popularity, media coverage, consensus picks, or the current market line.
