# Point 19 Decision: final_operator_decision

## Finalna definicja

`final_operator_decision` jest deterministycznym routerem dzialan. Nie jest kolejnym punktem analitycznym, nie czyta internetu, nie przelicza EV/CLV/no-chase i nie interpretuje ponownie punktow 1-17.

Jego jedyna rola:

```text
Punkt 18 okresla jakosc i blockerow.
Punkt 19 stosuje zamrozona tabele priorytetow.
Punkt 19 ustawia gate_state, operator_action i kolejke naprawcza.
```

## Zrodla prawdy

```yaml
primary:
  - process_quality_snapshot
  - operator_decision_policy
  - audit_phase_state
  - blocker_classification_registry
  - action_routing_registry
  - manual_override_log
  - append_only_operator_decision_ledger
```

Punkt 19 musi odnosic sie do konkretnego snapshotu punktu 18:

```yaml
decision_basis:
  process_quality_snapshot_id:
  process_quality_output_hash:
  process_quality_policy_id:
  audit_id:
  audit_phase:
  as_of_utc:
```

Nie wolno czytac "najnowszego punktu 18" bez identyfikatora.

## Dwie osie decyzji

Rozdzielamy stan bramki od dzialania:

```yaml
gate_state: OPEN | HOLD | INVALID
operator_action:
  - HOLD_PENDING_DATA
  - RETURN_FOR_DATA_CORRECTION
  - RETURN_FOR_MODEL_RERUN
  - READY_FOR_NEXT_AUDIT_STAGE
  - AUDIT_COMPLETE
  - INVALID_AUDIT
```

`HOLD_PENDING_DATA` nie powinien ukrywac tego, ze czasem trzeba aktywnie naprawic model albo dane. Dlatego dodajemy:

```yaml
hold_type:
  - PASSIVE_WAIT_FOR_OFFICIAL_WINDOW
  - MANUAL_DATA_CAPTURE_REQUIRED
  - EXTERNAL_PROVIDER_DELAY
  - ACTIVE_REMEDIATION_REQUIRED
```

## Priorytet decyzji

```text
1. INVALID_AUDIT
2. RETURN_FOR_DATA_CORRECTION
3. RETURN_FOR_MODEL_RERUN
4. HOLD_PENDING_DATA
5. READY_FOR_NEXT_AUDIT_STAGE
6. AUDIT_COMPLETE
```

Nie wolno przykryc naruszenia integralnosci zwyklym `HOLD_PENDING_DATA`.

## Klasy blockerow

```yaml
blocker_class:
  INTEGRITY
  DATA_CORRECTION
  MODEL_RERUN
  MARKET_CAPTURE
  PENDING_EXTERNAL
```

Przyklady:

- `FUTURE_DATA_USED_IN_PREDECISION_AUDIT` => `INVALID_AUDIT`
- `SPREAD_PRICE_NOT_ATOMIC` => `RETURN_FOR_DATA_CORRECTION`
- `MARGIN_PMF_MISSING` => `RETURN_FOR_MODEL_RERUN`
- `MODEL_GENERATION_QUOTE_MISSING` => `RETURN_FOR_MODEL_RERUN` plus market capture during rerun
- `GAME_WINDOW_WEATHER_NOT_AVAILABLE` => `HOLD_PENDING_DATA`

## Decyzja dla SF-LA

Obecny najprecyzyjniejszy zapis:

```yaml
gate_state: HOLD
operator_action: RETURN_FOR_MODEL_RERUN
legacy_single_status: HOLD_PENDING_DATA
substatus: MODEL_RERUN_AND_MARKET_GRADE_SNAPSHOT_REQUIRED
hold_type: ACTIVE_REMEDIATION_REQUIRED
secondary_action: CAPTURE_MARKET_GRADE_SNAPSHOT
```

To nie jest pasywne czekanie. Brak PMF, `p_cover/p_push/p_loss`, acceptable frontier i model-generation quote wymaga nowego runu pipeline'u modelowego oraz atomowego market snapshotu.

## Zakazane przejscia

Przy hard blockerach punkt 19 musi blokowac:

```yaml
prohibited_transitions:
  - EXECUTION_AUDIT_APPROVAL
  - FINAL_PREKICK_APPROVAL
  - AUDIT_COMPLETE
```

## Zasada LLM

LLM moze napisac notatke. Nie moze tworzyc `gate_state`, `operator_action`, kolejki naprawczej, priorytetow ani override'ow bez wyniku rule engine.
