# Point 18 Decision: process_quality

## Finalna definicja

`process_quality` nie jest kolejnym researchem internetowym. To wewnetrzna bramka jakosci, ktora czyta zamrozony `audit_bundle` z wynikami punktow 1-17, ich dowodami, timestampami, hashami, zaleznosciami i wersja polityki.

Punkt 18 nie decyduje, czy pick jest dobry. Decyduje, czy proces audytu jest wystarczajaco kompletny dla aktualnej fazy.

## Zrodlo prawdy

Podstawowym zrodlem jest append-only audit package:

```yaml
audit_bundle:
  audit_id:
  event_id:
  selected_team:
  model_run_id:
  created_at_utc:
  as_of_utc:
  audit_phase:
  point_outputs:
    point_01_ref:
    point_02_ref:
    ...
    point_17_ref:
  bundle_hash:
```

Punkt 18 nie powinien czytac luznych opisow z czatu. Powinien czytac wersjonowane rekordy punktow.

## Osie oceny punktu

```yaml
point_quality:
  run_status: VALID | INVALID | NOT_RUN
  domain_status: AVAILABLE | PARTIAL | NOT_ASSESSABLE | PENDING_NOT_CLOSED | PREVIEW_ONLY | STALE
  due_status: NOT_DUE | DUE | OVERDUE | POST_EVENT_ONLY
  criticality: HARD_REQUIRED | HARD_WHEN_DUE | SOFT_REQUIRED | CONTEXT_ONLY | POST_EVENT
  gate_effect: NONE | WARNING | HARD_BLOCK
  effective_status: OK | PARTIAL | NOT_ASSESSABLE | PENDING_NOT_DUE | BLOCKED
```

To rozdziela dwie rzeczy, ktore latwo pomylic:

```text
PUNKT ZOSTAL POPRAWNIE WYKONANY
nie oznacza
DANE W TYM PUNKCIE SA WYSTARCZAJACE DO DECYZJI
```

## Due matrix

| Punkt | Kiedy due | Rola |
|---|---|---|
| 1 argument_against | model generation | HARD_REQUIRED |
| 2 market_move_notes | gdy jest model quote i current quote | HARD_REQUIRED |
| 3 injury_role_notes | etapowo; finalnie po inactives | HARD_WHEN_DUE |
| 4 schedule_spot_notes | od utworzenia audytu | HARD dla faktow, soft dla itinerary |
| 5 weather_notes | gdy forecast obejmuje game window | HARD_WHEN_DUE |
| 6 key_number_check | gdy istnieje spread | HARD_REQUIRED |
| 7 no_chase_limit | przy current executable quote | HARD_REQUIRED |
| 8 price_quality | przy decision/execution quote | HARD_REQUIRED |
| 9 market_snapshot | przy model run i decyzji | HARD_REQUIRED |
| 10 public_bias | blisko kickoffu, jesli dane istnieja | CONTEXT_ONLY |
| 11 power_rankings_check | preseason/current week | CONTEXT_ONLY |
| 12 roster_change_check | baseline przy model run; final przed meczem | HARD_REQUIRED |
| 13 matchup_specific_risk | po dependency map i personnel check | SOFT_REQUIRED albo HARD wedlug polityki |
| 14 game_script_risk | model generation | HARD jesli wymagany przez system |
| 15 closing_line | po finalnym close | POST_EVENT |
| 16 closing_price | po finalnym close | POST_EVENT |
| 17 clv_points | po 15 i 16 | POST_EVENT |

## Finalna zasada gate

1. Integrity failure => `BLOCKED`.
2. Due `HARD_REQUIRED` z `NOT_ASSESSABLE` albo `BLOCKED` => `PREKICK_NOT_READY`.
3. Hard-required OK, soft OK/PARTIAL => `PREKICK_READY`.
4. `NOT_DUE` nie obniza readiness.
5. Punkty 15-17 przed close => `post_close_readiness: PENDING_NOT_DUE`.
6. Po close punkty 15-17 automatycznie staja sie due.

## Decyzja dla frameworka

Punkt 18 zostaje przyjety jako deterministyczny internal rule gate. GPT moze napisac notatke na bazie reason codes, ale nie moze sam wyliczac `process_quality_status`, `gate_effect`, EV, CLV ani no-chase.
