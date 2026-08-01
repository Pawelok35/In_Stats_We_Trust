# NFL 2026 Pregame Decision System - Plan Prac

Status dokumentu: plan architektury i kolejnosc prac.  
Data: 2026-08-01.  
Zakres: pregame decision system na sezon NFL 2026.  
Poza zakresem: Live Scenario, halftime prediction, live betting model, forum formatter.

## 1. Cel

Zbudowac kompletny system pregame NFL, ktory prowadzi operatora od pierwszego snapshotu rynku do decyzji przed kickoffem, a po meczu zapisuje closing line, CLV, wynik i ocene procesu.

Docelowy przeplyw:

```text
schedule
-> initial market snapshot
-> frozen statistical model
-> weekly candidate registry
-> research updates
-> injuries / roster / weather / schedule spot
-> public betting context
-> line movement
-> GPT Variant B
-> final quote gate
-> operator verdict
-> closing quote
-> CLV
-> settlement
-> learning ledger
```

System nie ma automatycznie zatwierdzac zakladow. Model znajduje kandydatow, research sprawdza ryzyka, a finalna decyzja nalezy do operatora.

## 2. Zasady Architektury

### 2.1. Zamrozony model pozostaje bez zmian

Produkcyjny baseline:

```text
commit: 5216a330d8c23d11fd7acc67ee11cfb2ab390c88
tag: production-pipeline-baseline-2026-07-29
```

Zakres zamrozonego baseline:

```text
L2
-> L3
-> rolling/Core12
-> report/analyzer
-> preflight
-> matchup_batch
-> pick output
```

Nowy system jest warstwa operatorska dookola modelu. Nie przebudowuje Champion CORE, progow tagow ani logiki backtestu bez osobnej decyzji.

### 2.2. Trzy poziomy decyzji

System musi rozrozniac:

```text
MODEL_CANDIDATE
RESEARCH_APPROVED
FINAL_OPERATOR_PICK
```

Znaczenie:

- `MODEL_CANDIDATE`: model znalazl potencjalna przewage.
- `RESEARCH_APPROVED`: research i Variant B nie wykryly blokujacego ryzyka.
- `FINAL_OPERATOR_PICK`: operator zatwierdzil decyzje przy aktualnym final quote.

Model candidate nie oznacza automatycznie finalnego picku.

### 2.3. Historia jako append-only event log

Nie nadpisujemy historii. Kazda nowa informacja jest osobnym zdarzeniem.

Docelowy model:

```text
append-only PregameEvent log
+
aktualny widok PregameGameRecord
```

Przyklady zdarzen:

```text
GAME_CREATED
INITIAL_MARKET_SNAPSHOT
MARKET_QUOTE_UPDATED
MODEL_SCAN_COMPLETED
MODEL_CANDIDATE_CREATED
GPT_RESEARCH_COMPLETED
INJURY_UPDATED
ROSTER_UPDATED
WEATHER_UPDATED
PUBLIC_BETTING_UPDATED
FINAL_QUOTE_CAPTURED
RESEARCH_APPROVED
OPERATOR_PICK_APPROVED
OPERATOR_PICK_REJECTED
CLOSING_QUOTE_CAPTURED
GAME_SETTLED
```

Srodowy snapshot nie moze nadpisac wtorkowego.

### 2.4. Kazda informacja zewnetrzna ma zrodlo

Kazdy rekord dotyczacy linii, ceny, injury, rosteru, pogody, public betting albo statusu treningowego musi miec:

- source,
- captured_at_utc albo reported_at_utc,
- quality_status,
- zakres informacji.

Brak zrodla lub timestampu musi obnizac jakosc danych albo blokowac finalna decyzje.

## 3. Mapa Do Istniejacego Repo

| Obszar | Obecny kod / dane | Status |
| --- | --- | --- |
| L1/L2/L3 ETL | `etl/l1_ingest.py`, `etl/l2_clean.py`, `etl/l3_aggregate.py`, `etl/mappers.py` | wykorzystac, nie przebudowywac |
| Core12 / PowerScore | `metrics/core12.py`, `metrics/power_score.py` | wykorzystac |
| Data cutoff / preflight | `utils/data_cutoff.py`, `utils/preflight.py` | wykorzystac jako gate produkcyjny |
| Model metrics policy | `utils/model_metrics.py` | wykorzystac |
| Matchup analyzer | `scripts/matchup_analyzer.py` | wykorzystac |
| Batch pick output | `scripts/matchup_batch.py` | wykorzystac |
| Weekly scan | `scripts/prospective_week_flow.py` | wykorzystac |
| Market snapshot conversion | `scripts/book_snapshot_to_week_lines.py` | rozszerzyc adapterem append-only |
| Daily bot | `scripts/variant_b_daily_bot.py`, `config/variant_b_daily_bot.yaml` | pozniej podlaczyc do nowych rekordow |
| GUI | `scripts/variant_b_daily_bot_gui.py` | pozniej, po kontraktach |
| Variant B audit | `scripts/variant_b_audit.py`, `scripts/variant_b_week_flow.py` | wykorzystac, nie tworzyc od zera |
| GPT prompts | `docs/variant_b_final_gpt_research_prompt.md`, `docs/variant_b_sources_by_point.md` | wykorzystac |
| Learning ledger | `scripts/variant_b_learning_ledger.py`, `scripts/variant_b_post_event_evaluation.py` | rozszerzyc po event logu |
| Data sources registry | `config/data_sources.yaml` | aktualizowac przy nowych warstwach |
| Contracts | `config/contracts.yaml`, `utils/contracts.py` | rozszerzyc albo dodac osobny kontrakt pregame |
| Live Scenario | `live_scenario/*` | poza zakresem tego planu |

## 4. Nowe Kontrakty Danych

Docelowe kontrakty:

```text
PregameEvent
PregameGameRecord
MarketSnapshot
CandidateRecord
ResearchRecord
InjuryRecord
RosterRecord
WeatherRecord
ScheduleSpotRecord
PublicBettingRecord
FinalQuote
OperatorDecision
ClosingQuote
SettlementRecord
```

### 4.1. PregameEvent

Podstawowy append-only rekord:

```text
event_id
game_id
season
week
event_type
created_at_utc
source
schema_version
payload
```

Wymagania:

- `event_id` musi byc stabilny i unikalny.
- `game_id` musi laczyc wszystkie zdarzenia jednego meczu.
- `payload` ma byc walidowany wedlug typu zdarzenia.
- Event log nie moze usuwac ani nadpisywac starych zdarzen.

### 4.2. PregameGameRecord

Aktualny widok meczu zbudowany z event logu.

Minimalne pola:

```text
season
week
game_id
away_team
home_team
kickoff_utc
venue
neutral_site

model_variant
model_tag
selected_team
model_margin
market_margin_at_scan
edge_vs_line
confidence
production_eligible
preflight_status
model_generated_at_utc

research_status
variant_b_status
injury_status
roster_status
weather_status
market_status
final_quote_status

decision_level
operator_verdict
stake
reason_codes
```

### 4.3. MarketSnapshot

Snapshot rynku:

```text
snapshot_id
game_id
snapshot_type
captured_at_utc
book
source
market_type
team_or_side
spread
spread_price
total
total_price
moneyline
quality_status
executable_status
```

Snapshot types:

```text
INITIAL
CURRENT
FINAL
CLOSING
```

Quality statuses:

```text
MARKET_GRADE
EXECUTABLE_CONFIRMED
DISPLAYED_UNVERIFIED
STALE
INCONSISTENT_DISPLAY
MISSING_TIMESTAMP
MISSING_PRICE
```

## 5. Etapy Prac

### Etap 0 - Dokument architektury

Cel: zapisac ten plan jako repozytoryjny dokument i zmapowac go na istniejacy kod.

Plik:

```text
docs/season_2026_pregame_system_plan.md
```

Kryterium zakonczenia:

- wiadomo, ktore moduly wykorzystujemy,
- wiadomo, czego nie ruszamy,
- wiadomo, jakie kontrakty dodajemy,
- brak zmian w logice modelu.

Status: wykonane przez utworzenie tego dokumentu.

### Etap 1 - Champion CORE regression test

Cel: automatycznie chronic zamrozony baseline.

Test ma potwierdzac:

```text
74 bets
61-12-1
+128.70u
ROI 58.0%
Max Drawdown -6.30u
```

Zakres testu:

- filtry Champion CORE,
- liczba zakladow,
- W-L-P,
- profit,
- risk,
- ROI,
- max drawdown.

Kryterium zakonczenia:

- test przechodzi na obecnych danych,
- przyszla zmiana pokazuje regresje, jesli naruszy CORE.

### Etap 2 - Kontrakty danych

Cel: zdefiniowac wspolny format dla calego pregame systemu.

Do dodania:

- `PregameEvent`,
- `PregameGameRecord`,
- `MarketSnapshot`,
- `CandidateRecord`,
- `OperatorDecision`,
- testy kontraktow.

Preferowane miejsce:

```text
pregame/
tests/test_pregame_contracts.py
```

Alternatywa, jesli chcemy trzymac wszystko w obecnym stylu:

```text
utils/pregame_contracts.py
tests/test_pregame_contracts.py
```

Kryterium zakonczenia:

- kontrakty mozna walidowac bez GUI,
- brak zmian w Champion CORE.

### Etap 3 - Append-only event log

Cel: zapisywac pelna historie procesu decyzyjnego.

Do dodania:

- writer eventow,
- reader eventow,
- rebuild aktualnego `PregameGameRecord`,
- test kolejnosci i braku nadpisywania.

Proponowane pliki:

```text
pregame/event_store.py
pregame/record_builder.py
tests/test_pregame_event_store.py
```

Kryterium zakonczenia:

- pelna historie jednego meczu mozna odtworzic od pierwszego snapshotu do settlementu.

### Etap 4 - MarketSnapshot history

Cel: ujednolicic linie i ceny przez caly tydzien.

Wykorzystac:

```text
scripts/book_snapshot_to_week_lines.py
data/book_snapshots/
config/lines/
data/market_quotes/
```

Dodac:

- snapshot history,
- validator,
- statusy jakosci,
- konwersje do eventow,
- brak nadpisywania starych snapshotow.

Kryterium zakonczenia:

- dla kazdego meczu istnieje historia linii,
- mozna policzyc ruch spreadu/ceny,
- mozna wykryc brak timestampu albo brak ceny.

### Etap 5 - Weekly Candidate Registry

Cel: zbudowac jeden rejestr statusow modelu dla calego tygodnia.

Wykorzystac:

```text
scripts/prospective_week_flow.py
scripts/matchup_batch.py
utils/preflight.py
data/picks_variant_*/
```

Statusy:

```text
MODEL_CANDIDATE
WATCHLIST
BLOCKED
NO_PLAY
MISSING_DATA
```

Kryterium zakonczenia:

- jedna komenda tworzy strukturalna liste wszystkich meczow i ich statusow modelowych,
- registry nie jest finalnym pick file.

### Etap 6 - Final Quote Gate

Cel: zablokowac zatwierdzenie decyzji na starej albo zlej linii.

Kontrole:

- timestamp quote,
- source/book,
- price present,
- executable status,
- acceptable quote frontier,
- no-chase,
- key number,
- model production eligibility,
- research status.

Statusy:

```text
FINAL_QUOTE_VALID
FINAL_QUOTE_STALE
FINAL_QUOTE_OUTSIDE_FRONTIER
FINAL_PRICE_REJECTED
KEY_NUMBER_REJECTED
QUOTE_MISSING
WAIT_FOR_MARKET
WAIT_FOR_INJURY_NEWS
```

Kryterium zakonczenia:

- bez poprawnego final quote nie mozna stworzyc `FINAL_OPERATOR_PICK`.

### Etap 7 - Operator Verdict

Cel: zapisac finalna, audytowalna decyzje operatora.

Dozwolone decyzje:

```text
APPROVED
APPROVED_REDUCED_STAKE
WAIT
PASS
REJECTED_MODEL_DATA
REJECTED_INJURY
REJECTED_PRICE
REJECTED_LINE_MOVE
REJECTED_MARKET_QUALITY
REJECTED_RESEARCH_RISK
REJECTED_OPERATOR
```

Kazda decyzja musi miec:

- operator,
- timestamp,
- final quote,
- stake,
- reason code,
- komentarz,
- model version,
- Variant B framework version.

Kryterium zakonczenia:

- kazdy candidate konczy proces jako approved, waiting, passed albo rejected.

### Etap 8 - Integracja Variant B i GPT

Cel: podlaczyc istniejacy workflow GPT/Variant B do event logu.

Wykorzystac:

```text
docs/variant_b_final_gpt_research_prompt.md
docs/variant_b_19_point_master_prompt.md
docs/variant_b_sources_by_point.md
scripts/variant_b_audit.py
scripts/variant_b_week_flow.py
research/gpt_snapshots/
research/variant_b_week_flow/
```

Typy aktualizacji:

```text
FULL_RESEARCH
DELTA_UPDATE
FINAL_REFRESH
```

Zasady:

- GPT dostarcza research,
- deterministic audit sprawdza gate'y,
- GPT nie moze ustawic `FINAL_OPERATOR_PICK`,
- brak informacji oznacza `UNKNOWN` albo `PENDING`.

Kryterium zakonczenia:

- kazdy GPT research jest osobnym eventem i mozna porownac kolejne wersje.

### Etap 9 - Injury i roster structured input

Cel: dodac strukturalny input kadrowy bez zaczynania od automatycznego scrapingu.

Minimalne pola:

```text
player
team
position
role
starter_status
practice_status
game_status
injury_type
source
reported_at_utc
impact
blocking
operator_note
```

Practice statuses:

```text
FULL
LIMITED
DNP
UNKNOWN
```

Game statuses:

```text
QUESTIONABLE
DOUBTFUL
OUT
IR
PUP
ACTIVE
INACTIVE
UNKNOWN
```

Impact:

```text
LOW
MEDIUM
HIGH
BLOCKING
```

Kryterium zakonczenia:

- kazdy kandydat ma injury/roster status z timestampem i zrodlem.

### Etap 10 - Weather i schedule spot

Cel: zapisac warunki meczu i kontekst terminarza.

Weather:

```text
temperature
wind
wind_gusts
precipitation
snow
surface
roof_status
forecast_horizon
source
captured_at_utc
```

Schedule spot:

```text
short_week
bye_week
rest_days
rest_difference
international_travel
time_zone_change
consecutive_road_games
Monday_to_Sunday
Thursday_game
```

Risk status:

```text
NO_MATERIAL_RISK
LOW_RISK
MEDIUM_RISK
HIGH_RISK
BLOCKING_RISK
```

Kryterium zakonczenia:

- weather i schedule spot sa widoczne w Variant B i operator record.

### Etap 11 - Public betting

Cel: dodac bet percentage i money percentage jako kontekst, nie jako samodzielny sygnal.

Priorytet: nizszy niz model, quote, injury, Variant B i final verdict.

Pola:

```text
market_type
side
bet_percentage
money_percentage
source
captured_at_utc
source_scope
book_count
reliability_status
```

Statusy:

```text
PUBLIC_HEAVY
MONEY_DIVERGENCE
POSSIBLE_REVERSE_LINE_MOVE
BALANCED_MARKET
LOW_RELIABILITY
```

Zakaz:

```text
SHARP_MONEY_CONFIRMED
```

bez twardych podstaw.

Kryterium zakonczenia:

- public betting jest informacja pomocnicza i nie steruje samodzielnie decyzja.

### Etap 12 - Line Movement Engine

Cel: automatycznie oceniac ruch rynku.

Funkcje:

- initial vs current,
- current vs final,
- final vs closing,
- ruch spreadu,
- ruch ceny,
- przejscie przez key numbers,
- ruch zgodny lub przeciwny do public betting,
- poprawa albo utrata wartosci,
- no-chase enforcement.

Key numbers:

```text
3
6
7
10
14
```

Statusy:

```text
VALUE_IMPROVED
VALUE_STABLE
VALUE_REDUCED
KEY_NUMBER_LOST
PRICE_TOO_HIGH
REVERSE_MOVE_POSSIBLE
NO_CHASE_BLOCK
QUOTE_REQUIRED
```

Kryterium zakonczenia:

- system pokazuje, czy aktualny quote nadal spelnia warunki wejscia.

### Etap 13 - Decision log, closing line i CLV

Cel: ocenic po sezonie nie tylko wynik, ale tez jakosc decyzji.

Dane:

```text
model_line
initial_line
bet_line
bet_price
bet_timestamp
closing_line
closing_price
spread_clv
price_clv
result
units
operator_verdict
reason_codes
```

Raporty:

- wynik wedlug model tag,
- wynik wedlug quote quality,
- wynik wedlug dnia zagrania,
- wynik wedlug injury risk,
- wynik wedlug public split,
- wynik wedlug line movement,
- CLV wedlug typu picku,
- approved vs rejected candidates.

Kryterium zakonczenia:

- po meczu mozliwe jest settlement i ocena procesu decyzyjnego.

### Etap 14 - Pelna symulacja Week 1

Cel: przejsc kompletny tydzien przed sezonem.

Symulowany przeplyw:

```text
schedule
-> initial snapshot
-> model scan
-> candidate registry
-> GPT full research
-> injury update
-> weather update
-> public betting update
-> market update
-> GPT delta update
-> final quote
-> final refresh
-> operator decision
-> closing quote
-> settlement
-> CLV
```

Testy:

- wspolny game_id,
- poprawne timestampy,
- brak nadpisywania,
- poprawna kolejnosc zdarzen,
- blokada stale quote,
- blokada missing required,
- poprawne reason codes,
- odtworzenie decyzji,
- brak wplywu na Champion CORE.

Kryterium zakonczenia:

- pelny tydzien mozna przeprowadzic bez niekontrolowanych recznych obejsc.

### Etap 15 - GUI Operator Center

Cel: podlaczyc stabilny backend do jednego centrum pracy.

Zasada:

GUI nie powstaje przed kontraktami danych. GUI jest nakladka na system, nie zrodlem logiki.

Docelowy uklad:

- lista meczow i statusow,
- panel modelu,
- panel researchu,
- panel final quote / decision,
- panel closing / CLV / settlement,
- Live Scenario pozostaje osobnym modulem.

Kryterium zakonczenia:

- operator moze przeprowadzic caly tydzien bez recznego szukania wielu niezaleznych plikow.

### Etap 16 - Gotowosc produkcyjna

System jest gotowy, kiedy:

- Champion CORE regression test przechodzi,
- wszystkie mecze maja wspolny game_id,
- event log jest append-only,
- snapshoty nie sa nadpisywane,
- candidate registry dziala,
- Variant B jest zapisany strukturalnie,
- injury/roster workflow dziala,
- final quote gate dziala,
- operator verdict jest wymagany,
- closing line i CLV sa zapisywane,
- Week 1 simulation przechodzi end-to-end,
- GUI korzysta ze stabilnych kontraktow,
- istnieje manualny workflow awaryjny.

## 6. Priorytety

### Krytyczne przed sezonem

1. Dokument architektury.
2. Champion CORE regression test.
3. Kontrakty danych.
4. Append-only event log.
5. MarketSnapshot history.
6. Weekly Candidate Registry.
7. Final Quote Gate.
8. Operator Verdict.
9. Variant B integration.
10. Injury/roster structured input.
11. Decision Log i CLV.
12. Week 1 simulation.

### Wazne, ale nieblokujace pierwszej wersji

1. Pogoda w pelni automatyczna.
2. Public betting.
3. Automatyczny injury ingestion.
4. Automatyczny odds feed.
5. Alerty o zmianach rynku.
6. Rozbudowany dashboard CLV.

### Poza zakresem

1. Live Scenario.
2. Halftime prediction.
3. Live betting model.
4. Forum formatter.
5. Automatyczne zatwierdzanie pickow bez operatora.

## 7. Rekomendowana Kolejnosc Commitow

1. `docs/season_2026_pregame_system_plan.md`.
2. Champion CORE regression test.
3. Kontrakty: `PregameEvent`, `PregameGameRecord`, `MarketSnapshot`, `CandidateRecord`, `OperatorDecision`.
4. Append-only event store i aktualny widok meczu.
5. Market snapshot history i validator.
6. Weekly Candidate Registry.
7. Final Quote Gate.
8. Operator Verdict.
9. Variant B integration.
10. Injury/roster structured input.
11. Weather i schedule spot.
12. Public Betting Record.
13. Line Movement Engine.
14. Decision Log, closing line i CLV.
15. Week 1 end-to-end simulation.
16. GUI Operator Center.
17. Production readiness report i finalny tag.

## 8. Pierwszy Etap Implementacyjny Po Zatwierdzeniu

Po zatwierdzeniu tego dokumentu pierwszy maly etap implementacyjny powinien obejmowac tylko:

```text
Champion CORE regression test
+
kontrakty danych
+
append-only event model
+
testy
```

Zakazy dla pierwszego etapu:

- nie zmieniac logiki modelu,
- nie zmieniac progow Champion CORE,
- nie zmieniac backtestu,
- nie przebudowywac GUI,
- nie mieszac Live Scenario z pregame systemem.
