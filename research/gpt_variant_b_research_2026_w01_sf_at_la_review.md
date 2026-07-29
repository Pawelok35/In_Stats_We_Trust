# GPT Variant B Research Review - 2026 Week 1 SF at LA

## Snapshot

Raw GPT output:

```text
research/gpt_variant_b_research_2026_w01_sf_at_la_raw.md
```

Game:

```yaml
season: 2026
week: 1
away: San Francisco 49ers
home_designated: Los Angeles Rams
venue: Melbourne Cricket Ground
neutral_site: true
international_game: true
selected_team: Los Angeles Rams
market: full-game spread
input_line: Rams -3.0
input_price: -110
input_source: MANUAL_CONSENSUS
model_version: variant_m
model_tag: VALUE PLAY
model_fair_margin_selected_team_raw: -4.99
edge_vs_line_points_raw: 1.99
```

## Ocena

Ocena jako research layer: 80/100.

Ocena jako pelny edge-proof: niegotowe.

GPT poprawnie wykonal role research/checklist engine:

- potwierdzil tozsamosc meczu, venue, kickoff i designated home;
- oznaczyl `MANUAL_CONSENSUS` jako `PREVIEW_ONLY`, nie jako executable quote;
- nie zamienil raw edge `+1.99` na pelne EV;
- poprawnie wskazal brak `p_cover`, `p_push`, `p_loss` i PMF;
- oznaczyl injury/weather jako `PENDING_NOT_DUE`;
- oznaczyl closing line, closing price i CLV jako `POST_EVENT_ONLY`;
- nie wygenerowal betting recommendation;
- wskazal konflikt secondary opener context: Rams -2.5 vs Rams -3.0.

## Co przyjmujemy do audytu

```yaml
accepted_research_facts:
  game_identity: CONFIRMED
  neutral_site_international: CONFIRMED
  designated_home_team: Los Angeles Rams
  selected_team_from_model_input: Los Angeles Rams
  current_input_line: -3.0
  current_input_price: -110
  current_input_evidence_grade: PREVIEW_ONLY
  raw_edge_status: FAIR_MARGIN_EDGE_ONLY
  full_ev_status: NOT_ASSESSABLE
  injury_status: PENDING_NOT_DUE
  weather_status: PENDING_NOT_DUE
  closing_clv_status: POST_EVENT_ONLY
```

## Czego nie przyjmujemy jako proof

```yaml
not_proof:
  manual_consensus_quote: true
  secondary_opener_articles: true
  public_market_context: true
  offseason_roster_designations_as_week1_availability: true
  raw_edge_as_ev: true
```

## Aktualne hard blockery

```yaml
hard_blockers:
  - MODEL_RUN_ID_MISSING
  - MODEL_GENERATED_AT_MISSING
  - MODEL_INPUT_OR_COMMIT_HASH_MISSING
  - MODEL_GENERATION_QUOTE_MISSING
  - P_COVER_MISSING
  - P_PUSH_MISSING
  - P_LOSS_MISSING
  - MARGIN_PMF_UNKNOWN
  - ACCEPTABLE_QUOTE_FRONTIER_UNKNOWN
  - CURRENT_EXECUTABLE_QUOTE_MISSING
  - NAMED_BOOK_MISSING
  - QUOTE_TIMESTAMP_MISSING
  - QUOTE_ID_MISSING
  - TARGET_STAKE_CHECK_MISSING
  - HOUSE_RULES_MISSING
  - FROZEN_ROSTER_ROLE_STAFF_BASELINE_MISSING
```

## Korekta punktu 19

GPT zwrocil konserwatywne:

```yaml
gate_state: HOLD
operator_action: HOLD_PENDING_DATA
```

Nasza polityka operacyjna powinna to zaostrzyc do:

```yaml
gate_state: HOLD
operator_action: RETURN_FOR_MODEL_RERUN
secondary_action: CAPTURE_MARKET_GRADE_SNAPSHOT
hold_type: ACTIVE_REMEDIATION_REQUIRED
```

Powod: PMF, `p_cover/p_push/p_loss`, acceptable frontier i model-generation quote nie pojawia sie same z czasem. To wymaga model pipeline / rerunu albo odzyskania prawidlowego model-run bundle.

## Następny krok

Najpierw trzeba uzupelnic dwie warstwy:

1. Model proof:

```yaml
required:
  - model_run_id
  - model_generated_at_utc
  - model_commit_hash_or_input_hash
  - margin_pmf
  - p_cover
  - p_push
  - p_loss
  - acceptable_quote_frontier
  - model_generation_quote
```

2. Market proof:

```yaml
required:
  - named_book
  - spread
  - price
  - quote_timestamp_utc
  - quote_id_if_available
  - executable_status
  - target_stake_check
  - house_rules
```

Po uzupelnieniu tych danych ponownie uruchomic:

```powershell
python scripts\variant_b_audit.py --picks-file data\picks_variant_m\2026\week_01.jsonl --home LA --away SF --output research\variant_b_audit_2026_w01_sf_at_la.json
```
