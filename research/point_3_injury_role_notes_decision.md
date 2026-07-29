# Punkt 3 - injury_role_notes: decyzja po GPT Pro

## Status

```text
Punkt 3 zaakceptowany.
```

`injury_role_notes` nie ma byc lista kontuzjowanych zawodnikow. Ma laczyc:

```text
official status -> actual role -> replacement -> unit consequences -> model assumption -> raw-edge effect
```

## Finalna odpowiedz na punkt 3

```text
injury_role_notes da sie czesciowo zautomatyzowac, ale musi to byc proces hybrydowy.

Automatyzujemy zbieranie oficjalnych statusow, snap share, roli, roster status,
timestampow i porownanie z zalozeniami modelu.

Semi-automatyzujemy replacement quality, offensive-line reshuffle, secondary
alignment, pass-rush rotation i chain reaction.

Manualnie zostaje interpretacja nietypowych rol, konfliktow zrodel, ograniczen
workloadu i kazdej subiektywnej korekty punktowej.
```

## Co przyjmujemy

### 1. State machine raportow kontuzji

Przyjmujemy stany:

```yaml
injury_report_state:
  - PRE_REPORT_WINDOW
  - PRACTICE_REPORT_1
  - PRACTICE_REPORT_2
  - FINAL_PRACTICE_AND_GAME_STATUS
  - LATE_STATUS_UPDATE
  - FINAL_INACTIVES
  - POSTGAME_ROLE_VALIDATION
```

Najwazniejsza zasada:

```text
PRE_REPORT_WINDOW = PENDING, nie NO_INJURIES.
```

Czyli jesli oficjalne raporty jeszcze nie sa wymagane, nie wolno wpisywac:

```text
brak kontuzji
```

Wpisujemy:

```text
official injury reports pending / not assessable
```

### 2. Model snapshot comparison

Dla kazdego istotnego zawodnika musimy docelowo miec:

```yaml
model_assumption: ACTIVE_NORMAL / ACTIVE_LIMITED / INACTIVE / UNKNOWN
current_supported_state: ACTIVE_NORMAL / ACTIVE_LIMITED / INACTIVE / UNKNOWN
assumption_change: UPGRADE / DOWNGRADE / UNCHANGED / UNKNOWN
edge_direction: WEAKENS_PICK / SUPPORTS_PICK / NEUTRAL / UNKNOWN
fair_margin_delta:
revised_raw_edge:
```

Kontuzja, ktora byla juz uwzgledniona w modelu, nie moze byc policzona drugi raz.

### 3. Scenariusze zamiast jednej opinii

Dla materialnych zawodnikow nie wpisujemy jednej subiektywnej wartosci.

Robimy scenariusze:

```yaml
scenarios:
  - ACTIVE_NORMAL
  - ACTIVE_LIMITED
  - INACTIVE
```

Preferowane:

```text
rerun model under all three scenarios
```

### 4. QB jako osobny stan zespolu

QB1 nie jest zwykla pozycja z mnoznikiem.

Przy QB1 trzeba sprawdzac:

- kto faktycznie startuje;
- jaki jest backup;
- passing efficiency;
- sack exposure;
- turnover expectation;
- rushing/play-calling impact;
- tempo/personnel changes;
- uncertainty przy malym sample backupu.

### 5. Offensive line jako unit

OL oceniamy jako pieciu graczy razem, nie suma pojedynczych kontuzji.

Potrzebne:

- LT/LG/C/RG/RT;
- doswiadczenie na konkretnej pozycji;
- czy ktos musi zmienic pozycje;
- center-QB continuity;
- pass-block/run-block role;
- liczba starterow out/limited.

Przyklad chain reaction:

```text
starting_tackle_out -> starting_guard_moves_to_tackle -> backup_guard_enters
```

To jest jedna kontuzja z reakcja lancuchowa, nie trzy osobne kontuzje.

### 6. Secondary i pass rush jako role, nie tylko pozycje

Secondary dzielimy na:

- boundary corner;
- field corner;
- slot/nickel;
- deep safety;
- box safety;
- dime defender;
- communication role.

Pass rush dzielimy na:

- edge;
- interior pressure;
- third-down rusher;
- run-defense role;
- rotation depth.

### 7. Skill positions wedlug usage

WR/TE/RB/FB oceniamy przez:

- route participation;
- target/carry share;
- air yards;
- red zone;
- third down;
- motion/blocking/pass protection;
- package usage.

Nie przez fantasy value ani samo miejsce w depth chart.

## Reguly IRN do wdrozenia

Priorytetowo:

```yaml
injury_role_rules:
  - IRN-001_REPORT_WINDOW_NOT_OPEN
  - IRN-002_OFFICIAL_REPORT_OVERDUE
  - IRN-003_UNAPPROVED_OR_UNTIMESTAMPED_SOURCE
  - IRN-004_STALE_OR_SUPERSEDED_STATUS
  - IRN-005_FINAL_INACTIVE_OVERRIDE
  - IRN-006_LATE_DOWNGRADE
  - IRN-007_ADVERSE_PRACTICE_TREND
  - IRN-008_QB1_UNAVAILABLE
  - IRN-009_QB1_LIMITATION_UNMODELED
  - IRN-010_OFFENSIVE_LINE_CLUSTER
  - IRN-011_SINGLE_CORE_OFFENSIVE_LINEMAN
  - IRN-012_SECONDARY_CLUSTER
  - IRN-013_PASS_RUSH_CLUSTER
  - IRN-014_HIGH_USAGE_SKILL_ROLE
  - IRN-015_REPLACEMENT_UNKNOWN_OR_ROLE_MISMATCH
  - IRN-016_MATERIAL_CHAIN_REACTION
  - IRN-017_RETURNING_PLAYER_OR_SNAP_LIMIT
  - IRN-018_MODEL_AVAILABILITY_MISMATCH
  - IRN-019_RAW_EDGE_ERASED
  - IRN-020_MATERIAL_PARTIAL_EDGE_EROSION
  - IRN-021_LOW_ROLE_RESOLVED
  - IRN-022_DOUBLE_COUNTED_INJURY_IMPACT
  - IRN-023_RUMOR_PROMOTED_TO_FACT
  - IRN-024_UNSUPPORTED_MEDICAL_INFERENCE
```

## Zrodla

Przyjmujemy hierarchie:

```yaml
source_priority:
  1_official_availability:
    - NFL official injury report
    - official club injury report
    - official transactions
    - final inactives
  2_official_role_context:
    - team press conferences
    - official coach statements
    - official transcripts
  3_official_usage_data:
    - NFL Game Books
    - player participation
    - Next Gen Stats / official tracking where available
  4_licensed_data_feeds:
    - structured vendor feed, but with original source and timestamp retained
```

Nie wolno traktowac jako potwierdzone:

- rumor accounts;
- unsourced social media;
- fantasy blurbs bez primary source;
- praktyki z video bez oficjalnego potwierdzenia;
- ruchu rynku jako dowodu kontuzji;
- historii kontuzji bez aktualnego raportu.

## Finalne injury_role_notes dla test game

Dla:

```text
2026 Week 1
San Francisco 49ers at Los Angeles Rams
Melbourne, Australia
LA -3.0
as_of: 2026-07-23
```

wpisujemy:

```yaml
injury_role_notes:
  audit_status: PENDING_OFFICIAL_WEEK_1_REPORTS
  report_state: PRE_REPORT_WINDOW
  practice_participation:
    LA: PENDING
    SF: PENDING
  game_status:
    LA: PENDING
    SF: PENDING
  final_inactives: PENDING
  player_specific_entries: []
  role_impact:
    quarterback: NOT_ASSESSABLE
    offensive_line: NOT_ASSESSABLE
    defensive_secondary: NOT_ASSESSABLE
    pass_rush: NOT_ASSESSABLE
    skill_positions: NOT_ASSESSABLE
  replacement_quality: NOT_ASSESSABLE
  chain_reactions: NOT_ASSESSABLE
  model_assumption_comparison:
    availability_snapshot_at_model_generation: MISSING
    current_official_availability_snapshot: NOT_YET_AVAILABLE
    assumption_mismatches: NOT_ASSESSABLE
  effect_on_model_edge:
    original_raw_edge_points: +1.99
    injury_adjusted_fair_margin_change: UNKNOWN
    injury_adjusted_raw_edge: UNKNOWN
    direction: UNKNOWN
  note: "Official Week 1 injury reports are not yet available. This is PRE_REPORT_WINDOW, so injury status is PENDING, not cleared. No official DNP/LP/FP/OUT/DOUBTFUL/QUESTIONABLE entries are available for this matchup, so QB, OL, secondary, pass rush, skill-position role impact, replacement quality, chain reactions, and injury effect on the +1.99 raw edge are NOT_ASSESSABLE. Do not infer that either team is healthy."
```

## Czego nie wolno wpisywac teraz

```text
Nie piszemy, ze obie druzyny sa zdrowe.
Nie wymyslamy nazwisk z training campu.
Nie oceniamy replacement quality bez oficjalnych danych.
Nie przypisujemy korekty punktowej.
Nie twierdzimy, ze kontuzje wspieraja albo oslabiaja LA -3.
```

## Czy mozemy przejsc do punktu 4?

```text
Tak. Punkt 3 jest wystarczajaco dobrze zdefiniowany.
```

Przed wdrozeniem skryptowym potrzebujemy jeszcze zdecydowac, skad technicznie
bedziemy pobierac official injury reports albo czy w sezonie 2026 wpisujemy je
recznie do YAML.

