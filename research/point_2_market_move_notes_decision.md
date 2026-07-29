# Punkt 2 - market_move_notes: decyzja po GPT Pro

## Status

```text
Punkt 2 zaakceptowany.
```

Odpowiedz GPT Pro jest zgodna z naszym kierunkiem:

```text
market_move_notes ma byc hybrydowe, ale obliczenia maja byc deterministyczne.
LLM moze napisac notatke, ale nie moze liczyc ruchu linii ani decydowac o no-chase.
```

## Co przyjmujemy

### 0. Trzy osobne punkty odniesienia

To jest najwazniejszy wniosek z drugiej czesci odpowiedzi GPT Pro.

Nie wolno mieszac:

```text
1. Opener - opisuje pelny ruch rynku.
2. Model snapshot - linia/cena w momencie wygenerowania picka.
3. Current executable quote - aktualna realna cena do audytu/decyzji.
```

No-chase powinien byc liczony przede wszystkim:

```text
model snapshot -> current executable quote
```

a nie:

```text
opener -> current
```

Powod: model mogl wygenerowac pick dopiero po openerze.

### 1. Obliczenia tylko deterministyczne

Przyjmujemy zasade:

```text
LLM nie liczy market movement.
LLM tylko opisuje wynik reguł.
```

To znaczy, ze skrypt ma liczyc:

- opener -> current movement;
- model snapshot -> current movement;
- price movement przy tej samej linii;
- przejscie przez key numbers;
- aktualny edge po zmianie linii;
- no-chase trigger;
- stale/executable quote status.

### 2. Normalizacja do strony picka

Kazda linia musi byc przeliczona do perspektywy naszego picka.

Przyklad:

```text
Pick: LA -3
current spread: LA -3
normalized_pick_line: -3
```

Dzieki temu ruch:

```text
-3 -> -3.5
```

jest zawsze ruchem przeciwko pickowi faworyta, bo cena staje sie gorsza.

Formalnie:

```text
spread_delta = current_selected_spread - reference_selected_spread

spread_delta > 0 -> ruch pomogl pickowi
spread_delta < 0 -> ruch zaszkodzil pickowi
spread_delta = 0 -> spread bez zmian, oceniamy cene
```

### 3. Etykiety ruchu

Przyjmujemy etykiety:

```yaml
movement_label:
  - FOR_PICK
  - AGAINST_PICK
  - MIXED
  - UNKNOWN
```

### 4. Key numbers

Skrypt ma wykrywac:

```text
onto key number
off key number
through key number
```

W pierwszej wersji:

```yaml
key_numbers:
  primary:
    - 3
    - 7
  secondary:
    - 10
    - 14
```

Skrypt ma odrozniac:

```text
ARRIVED_AT_KEY
MOVED_OFF_KEY
CROSSED_KEY
```

Dla faworyta LA:

```text
LA -2.5 -> LA -3.0 = ARRIVED_AT_KEY against pick
LA -3.0 -> LA -3.5 = MOVED_OFF_KEY against pick
LA -2.5 -> LA -3.5 = CROSSED_KEY against pick
LA -3.5 -> LA -3.0 = ARRIVED_AT_KEY for pick
LA -3.0 -> LA -2.5 = MOVED_OFF_KEY for pick
```

### 5. Price movement bez zmiany spreadu

Przyjmujemy jako osobna flage.

Przyklad:

```text
LA -3 (-110) -> LA -3 (-120)
```

To jest ruch przeciwko pickowi, mimo ze spread zostal taki sam.

American odds liczymy jako quoted break-even:

```text
negative odds: abs(price) / (abs(price) + 100)

-110 = 52.38%
-120 = 54.55%
roznica = +2.16 pp przeciwko pickowi
```

Jesli mamy tylko jedna strone rynku, nie nazywamy tego no-vig.
To jest tylko `QUOTED_BREAK_EVEN`.

### 5a. Mieszane ruchy spread/cena

Nie zawsze mozna dac proste `FOR_PICK` albo `AGAINST_PICK`.

Przyklad:

```text
LA -3 (-120) -> LA -3.5 (+100)
```

Cena jest lepsza, ale spread gorszy i traci key number 3.
To ma byc:

```text
MIXED_KEY_NUMBER_TRADEOFF
```

Bez rozkladu marginow nie zgadujemy, czy lepsza cena rekompensuje gorszy spread.

### 6. No-chase rules

No-chase nie moze byc wymyslany po fakcie.
Musi byc predeclared.

Dla naszego testu:

```yaml
pick: LA -3
no_chase_limit: LA -3.0
block_at: LA -3.5 or worse
```

Przyjmujemy statusy:

```text
NOT_TRIGGERED
TRIGGERED
REVIEW_REQUIRED
NOT_ASSESSABLE
```

Najwazniejsza zasada:

```text
Brak openeru nie oznacza no-chase.
Brak model snapshot oznacza, ze no-chase jest NOT_ASSESSABLE.
```

### 7. Czego nie wolno automatyzowac

Nie pozwalamy automatycznie wpisywac:

```text
sharp move
public move
steam
respected money
```

Chyba ze mamy zrodlo, tickets/handle albo inny potwierdzony dowod.

## Finalna odpowiedz na punkt 2 na bazie otrzymanej czesci

Dla `market_move_notes` system powinien generowac cos takiego:

```yaml
market_move_notes:
  opener_line:
  opener_price:
  opener_book:
  opener_ts_utc:
  decision_line:
  decision_price:
  decision_book:
  decision_ts_utc:
  current_line:
  current_price:
  current_book:
  current_ts_utc:
  movement_from_opener:
  movement_from_decision:
  movement_label:
  key_number_event:
  price_movement:
  stale_quote:
  executable_quote_confirmed:
  no_chase_triggered:
  note:
```

## Reguly MM do wdrozenia

Priorytetowo wdrazamy:

```yaml
market_move_rules:
  - MM-001_MARKET_IDENTITY_MISMATCH
  - MM-002_SELECTED_SIDE_NORMALIZATION_FAILURE
  - MM-003_MISSING_OPENER
  - MM-005_MISSING_MODEL_SNAPSHOT
  - MM-006_NON_ATOMIC_SPREAD_AND_PRICE
  - MM-007_STALE_CURRENT_SNAPSHOT
  - MM-008_NON_EXECUTABLE_QUOTE
  - MM-009_SPREAD_MOVE_AGAINST_PICK
  - MM-010_SPREAD_MOVE_FOR_PICK
  - MM-011_PRICE_MOVE_AGAINST_PICK
  - MM-012_PRICE_MOVE_FOR_PICK
  - MM-013_KEY_NUMBER_ARRIVAL_AGAINST_PICK
  - MM-014_KEY_NUMBER_DEPARTURE_AGAINST_PICK
  - MM-015_KEY_NUMBER_FULL_CROSS_AGAINST_PICK
  - MM-016_KEY_NUMBER_MOVE_FOR_PICK
  - MM-017_MIXED_SPREAD_PRICE_CHANGE
  - MM-018_CURRENT_RAW_EDGE_RECALCULATION
  - MM-019_PRICE_LIMIT_BREACH
  - MM-020_SPREAD_LIMIT_BREACH
  - MM-021_INSUFFICIENT_DATA_FOR_PLAYABILITY
  - MM-025_UNSUPPORTED_SHARP_LABEL
```

Pozniej:

```yaml
later_rules:
  - MM-004_OPENER_TYPE_UNDEFINED
  - MM-022_LINE_PATH_REVERSAL
  - MM-023_ISOLATED_BOOK_MOVE
  - MM-024_FEED_OUTLIER_OR_BAD_TICK
```

## Reguly no-chase do wdrozenia

```yaml
no_chase_rules:
  - NC-001_STALE_OR_NON_EXECUTABLE
  - NC-002_MISSING_SIGNAL_QUOTE
  - NC-003_CROSS_3_OR_7_AGAINST_PICK
  - NC-004_MOVE_OFF_3_OR_7_AGAINST_PICK
  - NC-005_MOVE_ONTO_KEY_AGAINST_PICK
  - NC-006_MAX_SPREAD_BREACH
  - NC-007_MAX_PRICE_BREACH
  - NC-008_MINIMUM_RAW_EDGE_BREACH
  - NC-009_MINIMUM_QUOTE_EV_BREACH
  - NC-010_MIXED_MOVE_WITHOUT_DISTRIBUTION
  - NC-011_NOTE_INVALIDATED_BY_NEW_QUOTE
  - NC-012_MISSING_OPENER_ONLY
```

## Test game - SF at LA

Na podstawie danych, ktore mamy teraz:

```yaml
market_move_notes:
  status: INCOMPLETE
  selected_side: LA
  opener_line: null
  opener_price: null
  opener_book: null
  opener_ts_utc: null
  model_snapshot_line: UNVERIFIED
  model_snapshot_price: UNVERIFIED
  model_snapshot_book: null
  model_snapshot_ts_utc: null
  current_line: LA -3.0
  current_price: -110
  current_book: MANUAL_CONSENSUS
  current_ts_utc: 2026-07-21T16:32:33Z
  movement_from_opener: UNKNOWN
  movement_from_model_snapshot: UNKNOWN
  movement_label: UNKNOWN
  key_number_event: ON_KEY_NUMBER_3
  price_movement: UNKNOWN
  stale_quote: true
  executable_quote_confirmed: false
  no_chase_status: NOT_ASSESSABLE
  no_chase_limit: LA -3.0
  block_at: LA -3.5 or worse
  note: "Opener data is unavailable. The stored current quote is LA -3.0 at -110 from MANUAL_CONSENSUS, which places the spread on key number 3, but the sportsbook, capture timestamp, and executable status are not market-grade. Opener-to-current movement, price movement, and whether the market touched or crossed 3 or 7 cannot be determined. The exact quote available at model generation is also not independently timestamped, so no-chase status is NOT_ASSESSABLE. Do not state that the market moved toward either side, do not call the move sharp, and do not treat -3/-110 as playable until a named executable quote and predeclared price limits are available."
```

## Finalna odpowiedz na punkt 2

```text
market_move_notes da sie zautomatyzowac w duzym stopniu.

Najlepszy sposob to deterministyczny state-machine nad timestampowanymi quote'ami.
LLM moze tylko opisac wynik.

Musimy trzymac osobno:
1. opener,
2. model snapshot,
3. current executable quote.

No-chase liczymy glownie model_snapshot -> current, nie opener -> current.

Jesli brakuje openeru, market movement jest UNKNOWN.
Jesli brakuje model snapshot, no-chase jest NOT_ASSESSABLE.
```
