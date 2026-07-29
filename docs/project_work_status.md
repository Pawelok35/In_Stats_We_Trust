# In Stats We Trust - status pracy

Ten dokument jest robocza mapa projektu NFL/NCAAF betting research. Ma pokazywac, nad czym pracujemy, co juz dziala, czego nie wolno nadinterpretowac i jaka jest kolejka nastepnych krokow.

## Glowny cel

Budujemy proces, ktory ma przejsc z luznej analizy NFL do mierzalnego, audytowalnego workflow:

1. model i dane generuja kandydatow;
2. rynek jest sprawdzany recznie albo automatycznie, ale zawsze z timestampem;
3. decyzje sa mrozone przed meczem w prospective ledgerze;
4. wyniki sa rozliczane dopiero po fakcie;
5. oceniamy osobno wynik i jakosc procesu decyzyjnego.

Najwazniejsza zasada: historyczne badania sluza do filtrow i watchlist, ale prawdziwy dowod edge powstaje dopiero przez forward proof ledger.

## Co juz mamy zrobione

### 1. Prospective edge ledger

Status: dziala.

Pliki:

- `scripts/freeze_prospective_picks.py`
- `scripts/settle_prospective_ledger.py`
- `scripts/update_prospective_ytd_report.py`
- `scripts/validate_proof_ready_lines.py`
- `scripts/stamp_proof_ready_lines.py`
- `scripts/prospective_week_flow.py`
- `docs/prospective_edge_ledger.md`
- `docs/source_takeaways_mapping.md`

Co robi:

- mrozi picki przed meczem do append-only JSONL;
- zapisuje line, price, book, timestamp, model_version i commit_sha;
- rozdziela rekordy `proof_qualified=true/false`;
- settlement liczy W-L-P, units, ROI;
- YTD raport laczy tygodnie;
- `code_is_dirty=true` jest warningiem, nie dyskwalifikacja.

Nowa warstwa procesu:

- kazdy frozen pick dostaje `process_snapshot`;
- zapisujemy fair/model line, market line, edge, price, timestamp;
- opcjonalnie: `argument_against`, `market_move_notes`, `injury_role_notes`, `schedule_spot_notes`, `weather_notes`, `closing_line`, `closing_price`, `clv_points`;
- settlement pokazuje `process_quality`.

Process quality:

- `complete_with_clv` - idealny standard, z closing line/CLV;
- `complete_pre_kick` - kompletny rekord przedmeczowy, bez closing line;
- `basic_price_proof` - fair line, market line, cena i timestamp;
- `result_only` - mozna rozliczyc wynik, ale proces jest slabo udokumentowany;
- `legacy_no_process_snapshot` - starszy rekord sprzed tej warstwy.

### 2. Manual market snapshot

Status: dziala, ale wymaga recznego wpisywania ceny.

Aktualnie nie mamy stabilnego API z kursami sportsbookow. Dlatego dla market-grade proof wpisujemy recznie:

- `book`
- `price`
- `decision_ts_utc`
- `odds_source`
- `odds_snapshot_type`
- `line`

Uzywamy:

- `MANUAL_MULTI_BOOK` - gdy sprawdziles kilka bookow i wpisujesz reprezentatywna linie/cene;
- `MANUAL_CONSENSUS` - slabszy standard, bardziej konfiguracyjny niz dowod rynkowy.

Ograniczenie: bez API odds nie mamy automatycznego, niezaleznego dowodu ceny. Manualny wpis jest akceptowalny tylko wtedy, gdy jest timestamped i nieedytowany po freeze.

### 3. Week 1 2026 config

Status: istnieje.

Plik:

- `config/lines/2026/week1_lines.yaml`

Co jest:

- 16 meczow;
- proof-ready line fields przechodza walidacje;
- dodane pola robocze procesu:
  - `argument_against`
  - `market_move_notes`
  - `injury_role_notes`
  - `schedule_spot_notes`
  - `weather_notes`

Wazne: pola sa teraz jako `TODO: ...`. Kod ignoruje placeholdery `TODO`, wiec nie podnosza sztucznie process quality. Dopiero realna tresc wpisana recznie bedzie liczona jako czesc procesu.

### 4. Live watch card

Status: dziala jako narzedzie research/live decision support.

Pliki:

- `scripts/live_watch_card.py`
- `scripts/settle_live_watch.py`
- `scripts/live_watch_weekly_review.py`
- `scripts/live_watch_week_flow.py`
- `docs/live_watch_card.md`
- `config/live_watch_games.yaml`

Co robi:

- sprawdza sytuacje underdoga live, glownie po Q3;
- porownuje aktualny stan meczu z historycznymi bucketami;
- liczy fair decimal, fair American, minimalna cene EV+ i oferowany EV;
- zapisuje decyzje do live ledgeru, jesli podasz cene live;
- settlement i weekly review rozliczaja decyzje live.

Decyzje:

- `STRONG_PLAY_ML`
- `PLAY_ML`
- `THIN_EDGE_NO_BET`
- `PRICE_TOO_SHORT`
- `WATCH_PRICE_REQUIRED`
- `NO_ML_LOW_WIN_RATE`
- `NO_BET_SMALL_SAMPLE`
- `NO_WATCH_NOT_LEADING`
- `NO_BET_NO_BUCKET`

Ograniczenie: `nfl_data_py` nie daje historycznych executable live odds. Skrypt potrafi policzyc minimalna cene EV+, ale realna cene live musisz wpisac z booka recznie.

### 5. Badania underdogow i przebiegu meczu

Status: wykonane jako research 2015-2025 / 2017-2025.

Pliki:

- `scripts/analyze_in_game_underdogs.py`
- `scripts/analyze_quarter_paths.py`
- `research/in_game_underdog_study_2017_2025.md`
- `research/quarter_path_underdog_study_2015_2025.md`
- dodatkowe CSV w `research/`

Najwazniejsze wnioski:

- Pregame underdog prowadzacy po Q3 wygrywal SU historycznie okolo 72.8% w badaniu 2017-2025.
- Q3 lead jest znacznie mocniejszy niz Q1 lead.
- Sam fakt prowadzenia nie wystarczy; wazny jest przebieg: czy underdog wygral/przegral poszczegolne kwarty, czy momentum sie poprawia, i ile punktow prowadzi.
- Najbardziej wartosciowe bucketowanie to polaczenie:
  - pregame spread bucket;
  - Q1/Q2/Q3 binary path;
  - period path, czyli kto wygral dana kwarte;
  - margin trajectory;
  - delta trajectory.

Ograniczenie: to jest research screen, nie dowod z kursami live.

### 6. Raporty i rutyna przedmeczowa

Status: mamy instrukcje i czesc automatyzacji.

Pliki:

- `docs/gom_research_process.md`
- `docs/decision_guide.md`
- `docs/nfl_edge_watch_2026_plan.md`
- `docs/prospective_edge_ledger.md`

Z forum i rutyny zostawilismy wartosciowe elementy:

- zaczynac od wlasnej fair line;
- nie robic picka z samego newsa/medialnego hype;
- injuries analizowac przez role, snap share, replacement i chain reaction;
- line movement traktowac ostroznie, nie kazdy ruch to sharp money;
- key numbers 3 i 7 maja znaczenie;
- PASS jest dobra decyzja;
- po meczu oceniac proces, nie tylko wynik.

## Jak obecnie pracujemy tygodniowo

### Krok 1 - przygotowanie linii

Uzupelniasz:

```yaml
book: MANUAL_MULTI_BOOK
price: -110
decision_ts_utc: "2026-09-10T15:00:00Z"
odds_source: manual_snapshot
odds_snapshot_type: decision
market: spread
line: -3.5
```

Dla potencjalnych betow uzupelniasz minimum:

```yaml
argument_against: "Najwieksze ryzyko: model moze sie mylic, bo ..."
```

Opcjonalnie:

```yaml
market_move_notes: "Nie gonic powyzej/pomizej kluczowego numeru ..."
injury_role_notes: "Sprawdzic status ..., downgrade jesli ..."
schedule_spot_notes: "Rest/travel/short week ..."
weather_notes: "Wiatr/deszcz/surface ..."
```

### Krok 2 - walidacja proof-ready

```powershell
.\.venv\Scripts\python.exe scripts\validate_proof_ready_lines.py `
  --config config\lines\2026\week1_lines.yaml `
  --fail-on-not-ready
```

### Krok 3 - weekly flow

Week 1 / preseason prior:

```powershell
.\.venv\Scripts\python.exe scripts\prospective_week_flow.py `
  --season 2026 `
  --week 1 `
  --variant variant_m `
  --operator daniel `
  --metrics-season 2025 `
  --reference-week 18 `
  --preseason-seed-source data\rolling_core12\2025\through_18.parquet `
  --preseason-seed-destination data\rolling_core12\2026\through_1.parquet
```

Normalny tydzien:

```powershell
.\.venv\Scripts\python.exe scripts\prospective_week_flow.py `
  --season 2026 `
  --week 2 `
  --variant variant_m `
  --operator daniel
```

### Krok 4 - settlement/YTD

```powershell
.\.venv\Scripts\python.exe scripts\settle_prospective_ledger.py `
  --ledger data\prospective_ledger\2026\week_01_prospective.jsonl

.\.venv\Scripts\python.exe scripts\update_prospective_ytd_report.py --season 2026
```

### Krok 5 - live watch podczas meczu

Lista kandydatow:

```powershell
.\.venv\Scripts\python.exe scripts\live_watch_card.py `
  --season 2026 `
  --week 1 `
  --list-candidates
```

Karta live dla meczu:

```powershell
.\.venv\Scripts\python.exe scripts\live_watch_card.py `
  --season 2026 `
  --week 1 `
  --game-id 2026_01_NYG_DAL `
  --live-decimal 1.90 `
  --book MANUAL_MULTI_BOOK
```

Settlement live week:

```powershell
.\.venv\Scripts\python.exe scripts\live_watch_week_flow.py `
  --season 2026 `
  --week 1
```

## Czego jeszcze nie mamy

### 1. Automatyczne odds API

Nie mamy jeszcze stabilnego zrodla realnych kursow sportsbookow.

Skutek:

- pregame line/price wpisujesz recznie;
- live ML wpisujesz recznie;
- CLV jest opcjonalne i reczne;
- market-grade proof jest slabszy niz przy API-backed snapshot.

### 2. Pelny CLV tracking

Mamy pola:

- `closing_line`
- `closing_price`
- `clv_points`

Ale nie mamy jeszcze automatycznego pobierania closing lines. Na razie mozna wpisywac recznie.

### 3. Automatyczny argument przeciw

Nie chcemy generowac fikcyjnych kontrtez. Docelowo mozemy zrobic helper, ktory zaproponuje argument przeciw na podstawie raportu, ale finalnie operator powinien go zaakceptowac albo poprawic.

### 4. NCAAF

Projekt jest przygotowywany pod NFL/NCAAF, ale obecny workflow i research sa najmocniej dopiete pod NFL i `nfl_data_py`.

### 5. Week 1 reliability

Week 1 2026 jest prior-heavy, bo model opiera sie glownie na danych poprzedniego sezonu. Wiarygodnosc rosnie po Week 3, kiedy mamy aktualne dane sezonowe.

## Plan kolejnych prac

## Wybrany staking phase-aware

Aktualnie wybrany plan do forward tracking zapisany jest w:

- `config/staking_phase_selected.yaml`

Plan:

```text
Week 2-5:
VALUE PLAY 0.25u
GOW        0.5u
GOM        0.75u
GOY        1u

Week 6-11:
VALUE PLAY 0.5u
GOW        1u
GOM        1.25u
GOY        1.5u

Week 12-17:
VALUE PLAY 1u
GOW        2u
GOM        3u
GOY        4u
```

Backtest 2015-2025 dla tego planu:

```text
529-260-15
Risk: 1425.75u
Units: +444.18u
ROI: 31.2%
Max DD: -35.86u
Max loss streak: 7
```

Zasada operacyjna: ten staking jest na razie planem forward tracking, nie pelnym dowodem edge. Realne uzycie wymaga `proof_qualified=true`, realnej ceny, `argument_against` i limitu ekspozycji tygodniowej.

### Najblizsze kroki

1. Wypelnic realne `argument_against` tylko dla kandydatow, ktore model wybierze jako potencjalne bety.
2. Zmienic `book` z `MANUAL_CONSENSUS` na `MANUAL_MULTI_BOOK`, gdy sprawdzisz kilka bookow.
3. Uruchomic weekly flow dla Week 1 i zobaczyc, ktore picki sa realnymi kandydatami.
4. Dla kandydatow dopisac market/injury/weather/schedule notes.
5. Freeze dopiero po uzupelnieniu notatek i ceny.

### Potem

1. Dodac reczne pola `closing_line` / `closing_price` po zamknieciu rynku.
2. Rozszerzyc settlement o osobny raport "process review":
   - dobry proces / zly wynik;
   - zly proces / dobry wynik;
   - brak danych;
   - price chased;
   - injury miss;
   - market overreaction.
3. Zbudowac helper do wypelniania process notes na podstawie matchup reportu.
4. Dodac osobny plik `week_review.md` po kazdym tygodniu.
5. Po Week 3 porownac skutecznosc prior-heavy Week 1-2 vs in-season Week 3+.

### Docelowy standard 90/100 proof

Minimalny cel dla kazdego realnego betu:

- frozen before kickoff;
- decision timestamp;
- line and price;
- book/source;
- model version;
- commit sha;
- fair/model line;
- edge vs line;
- argument against;
- market movement note;
- injury role note;
- postgame settlement;
- process quality review.

Mocniejszy cel:

- multi-book manual snapshot albo odds API;
- closing line;
- CLV;
- archived report;
- no post-freeze edits;
- YTD proof by market, tag, confidence, edge bucket and process quality.

## Najwazniejsze ograniczenia interpretacyjne

- Nie traktujemy backtestu jako dowodu edge.
- Nie traktujemy Week 1 jako pelnej wiarygodnosci modelu.
- Nie traktujemy `MANUAL_CONSENSUS` jako rownego z realnym multi-book snapshot.
- Nie wpisujemy fikcyjnych argumentow przeciw tylko po to, zeby ledger wygladal lepiej.
- Live watch pokazuje minimalna cene EV+, ale nie zna historycznej ceny live z booka.

## Aktualny nastepny krok operacyjny

Uruchomic weekly flow dla 2026 Week 1 i po wygenerowaniu pickow wrocic do `config/lines/2026/week1_lines.yaml`, uzupelniajac realne `argument_against` tylko przy kandydatach, ktore sa warte dalszej uwagi.
