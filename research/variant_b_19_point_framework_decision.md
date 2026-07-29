# Variant B - decyzja po frameworku 19 punktow

## Status

```text
Framework 19 punktow zaakceptowany jako Variant B audit v1.
```

GPT Pro dobrze zdefiniowal kierunek: Variant B nie ma byc drugim modelem
typujacym. To ma byc warstwa audytu procesu, ktora sprawdza czy modelowy pick
ma komplet danych, realna cene, kontrolowany market snapshot i brak krytycznych
defektow przed decyzja.

## Najwazniejsza zasada

```text
Python/rule engine liczy.
LLM moze tylko streszczac wynik.
```

LLM nie moze:

- liczyc edge;
- liczyc market movement;
- decydowac o no-chase;
- nazywac ruchu sharp/public bez dowodu;
- uznawac brak raportu za brak kontuzji;
- zamieniac missing/pending w confirmed.

## 19 punktow

| Punkt | Nazwa | Priorytet | Status wdrozenia |
|---:|---|---|---|
| 1 | argument_against | HIGH | Hybrid, czesciowo zdefiniowany |
| 2 | market_move_notes | HIGH | Fully rule-driven po quote feed/manual input |
| 3 | injury_role_notes | HIGH | Hybrid, pending do official reports |
| 4 | schedule_spot_notes | HIGH | Hybrid, czesc auto, travel manual |
| 5 | weather_notes | MEDIUM | Semi, pending do game-window forecast |
| 6 | key_number_check | HIGH | Fully automatable |
| 7 | no_chase_limit | HIGH | Fully automatable po model snapshot/current quote |
| 8 | price_quality | HIGH | Fully automatable po price limits lub p_cover/p_push/p_loss |
| 9 | market_snapshot | HIGH | Fully automatable, fundament calego procesu |
| 10 | public_bias / tickets_handle | MEDIUM | Semi/manual, tylko z providerem |
| 11 | power_rankings_check | MEDIUM | Semi, benchmark niezalezny |
| 12 | roster_change_check | HIGH | Hybrid, game-week dependent |
| 13 | matchup_specific_risk | MEDIUM | Manual-heavy |
| 14 | game_script_risk | MEDIUM | Manual/semi, wymaga symulacji |
| 15 | closing_line | HIGH | Fully automatable po close |
| 16 | closing_price | HIGH | Fully automatable po close |
| 17 | clv_points | HIGH | Fully automatable po close |
| 18 | process_quality | HIGH | Rule-driven |
| 19 | final_operator_decision | HIGH | Hybrid, finalny workflow sign-off |

## Top 10 reguly do wdrozenia jako pierwsze

```yaml
top_10_rules:
  - MS-01   # market snapshot validation
  - AG-01   # pick math integrity
  - AG-02   # fair margin != full EV without p_cover/p_push/p_loss
  - KN-02   # push-aware key number handling
  - MM-04   # model-generation quote required for no-chase
  - NC-03   # unfavorable move off/through 3 or 7
  - PXQ-01  # sportsbook/timestamp/executable status for price quality
  - IR-01   # pre-report injury status = pending, not healthy
  - SS-05   # no travel/acclimation claim without itinerary evidence
  - PROC-02 # blocking rules outrank numeric quality score
```

## Co mozemy automatyzowac jako pierwsze

Te pola sa najlepsze do pierwszego skryptowego wdrozenia:

```yaml
fully_automatable_first:
  - market_snapshot
  - key_number_check
  - no_chase_limit
  - price_quality
  - market_move_notes
  - process_quality
```

Po zakonczeniu meczu:

```yaml
post_close_automatable:
  - closing_line
  - closing_price
  - clv_points
```

## Co wymaga manualnego lub semi-manualnego inputu

```yaml
manual_or_hybrid:
  - argument_against
  - injury_role_notes
  - schedule_spot_notes
  - weather_notes
  - public_bias / tickets_handle
  - power_rankings_check
  - roster_change_check
  - matchup_specific_risk
  - game_script_risk
  - final_operator_decision
```

To nie znaczy, ze te pola piszemy calkowicie recznie. Znaczy, ze wymagaja
zatwierdzenia lub zrodla, ktorego jeszcze nie mamy w projekcie.

## Co powinno zostac pending do game week

```yaml
pending_until_game_week:
  - injury_role_notes
  - schedule_spot_notes
  - weather_notes
  - public_bias / tickets_handle
  - roster_change_check
  - matchup_specific_risk
  - game_script_risk
```

Final pre-kick refresh:

```yaml
final_prekick_refresh:
  - market_move_notes
  - injury_role_notes
  - weather_notes
  - no_chase_limit
  - price_quality
  - market_snapshot
  - roster_change_check
```

Po close:

```yaml
post_close:
  - closing_line
  - closing_price
  - clv_points
```

## Minimalny schema kierunkowy

Przyjmujemy z frameworku te glowne obiekty:

```yaml
schema_version: variant_b_audit_schema_v1
calculation_owner: PYTHON_RULE_ENGINE
narrative_owner: TEMPLATE_OR_LANGUAGE_MODEL_WITH_NO_NUMERIC_AUTHORITY

audit:
  audit_id:
  audit_stage: EARLY_PREVIEW / GAME_WEEK / FINAL_PREKICK / POST_CLOSE
  as_of_timestamp_utc:
  framework_version:
  rule_policy_version:
  source_policy_version:

event:
  season:
  week:
  event_id:
  usa_game_date:
  venue_local_game_date:
  kickoff_timestamp_utc:
  venue_name:
  venue_country:
  location_type:
  away_team:
  home_designation_team:
  selected_team:

model_snapshot:
  model_run_id:
  model_version:
  model_run_timestamp_utc:
  model_fair_margin_selected_team_raw:
  model_fair_margin_selected_team_rounded:
  edge_points_raw:
  edge_points_rounded:
  confidence_tier:
  p_cover:
  p_push:
  p_loss:
  margin_distribution_id:
  uncertainty_id:
  home_field_adjustment:

market_snapshot:
  snapshot_id:
  source_type:
  sportsbook:
  selected_team_spread:
  selected_team_american_price:
  capture_timestamp_utc:
  executable_status:
  pregame_or_live:
  raw_payload_hash:

audit_point_output:
  point_number:
  point_name:
  status:
  due_status:
  confirmed_facts:
  missing_data:
  pending_data:
  conditional_risks:
  triggered_rules:
  calculations:
  source_records:
  manual_review:
  narrative:

process_quality:
  status:
  quality_score:
  due_blocking_rules:
  due_nonblocking_rules:
  pending_not_due:
  missing_due:
  model_freshness:
  outcome_used: false

operator_decision:
  decision:
    - HOLD_PENDING_DATA
    - RETURN_FOR_DATA_CORRECTION
    - RETURN_FOR_MODEL_RERUN
    - READY_FOR_NEXT_AUDIT_STAGE
    - AUDIT_COMPLETE
    - INVALID_AUDIT
```

## Decyzja dla test game: SF at LA

Dla obecnego etapu:

```yaml
audit_stage: EARLY_PREVIEW
process_quality_status: INCOMPLETE
operator_decision: HOLD_PENDING_DATA
substatus: RETURN_FOR_MARKET_SNAPSHOT_AND_MODEL_INPUT_COMPLETION
```

Glowne blokery teraz:

```yaml
open_blockers:
  - sportsbook, timestamp, executable quote status
  - model-generation market snapshot
  - p_cover, p_push, p_loss
  - model roster version and as-of timestamp
```

Pending, ale jeszcze nie blad:

```yaml
pending_not_due:
  - injury report
  - weather
  - game-week roster verification
  - public splits
  - closing line and price
  - CLV points
```

## Co wdrazamy teraz

Nastepny techniczny krok:

```text
Zbudowac Variant B rule skeleton:
1. YAML z definicjami reguł;
2. skrypt, ktory tworzy audit_point_output dla punktow 1,2,6,7,8,9,18,19;
3. zapis do research/ albo data/audits/variant_b/.
```

Pierwszy MVP powinien obslugiwac:

```yaml
mvp_points:
  - 1_argument_against
  - 2_market_move_notes
  - 6_key_number_check
  - 7_no_chase_limit
  - 8_price_quality
  - 9_market_snapshot
  - 18_process_quality
  - 19_final_operator_decision
```

Punkty 3,4,5,10,12,13,14 trzymamy jako `PENDING_NOT_DUE` do game week.
Punkty 15,16,17 trzymamy jako `PENDING_NOT_DUE` do market close.

