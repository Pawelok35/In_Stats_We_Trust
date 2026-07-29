# Live Scenario Refactor Audit Plan

## Cel

Live Scenario ma pozostac historycznym analizatorem stanu meczu NFL. Modul nie ma dawac automatycznej rekomendacji zakladu. Ma odpowiadac na pytanie:

```text
Jezeli mecz osiagnal okreslony stan po Q2 albo Q3, co historycznie dzialo sie dalej?
```

Stara implementacja zostaje zachowana do czasu, az nowy backend i kontrakt danych przejda testy porownawcze.

## 1. Co Mozemy Zachowac

Mozemy zachowac:

- Pobieranie danych play-by-play z `nfl_data_py` w `scripts/live_quarter_scenario_matrix.py`.
- Funkcje pomocnicze:
  - `result_from_margin`
  - `state_after_margin`
  - `parse_path`
  - `path_key`
  - `decimal_to_american`
  - `american_to_decimal`
  - `ev_no_push`
  - `ev_tie_push`
- Budowanie wierszy team-game, bo juz tworzy dwa wiersze na mecz: home-perspective i away-perspective.
- Obecne rozroznienie:
  - wynik samej kwarty,
  - stan skumulowany po kwarcie,
  - wynik finalny z dogrywka.
- Obecny output plikowy jako legacy:
  - `team_game_quarter_rows.csv`
  - `quarter_transition_matrix.csv`
  - `margin_bucket_matrix.csv`
  - `scenario_lookup.json`
- GUI jako host panelu Live Scenario w `scripts/variant_b_daily_bot_gui.py`.
- Obecny przycisk `RUN LIVE LOOKUP` jako legacy/manual lookup.

Nie powinnismy zachowywac bez zmian:

- Recznego wpisywania `Path` jako glownego sposobu pracy.
- Obecnych margin bucketow `LEAD_1_3`, `LEAD_4_7`, itd. jako finalnego kontraktu.
- Obecnej definicji `season_phase`, bo teraz jest `EARLY <= 5`, `MIDDLE <= 11`, a nowy wymog to `EARLY 1-4`, `MID 5-12`, `LATE 13-18`, `PLAYOFFS`.
- Nazewnictwa `fair odds` jako glownego pola wyniku.
- Traktowania team-history jako rownorzednego dowodu wobec league baseline.

## 2. Gdzie Jest Logika Live Scenario

Backend:

```text
scripts/live_quarter_scenario_matrix.py
```

Najwazniejsze funkcje:

- `load_pbp` - pobiera PBP z `nfl_data_py`.
- `build_team_game_rows` - przelicza mecz na wiersze z perspektywy kazdej druzyny.
- `apply_filters` - filtruje sample po team/opponent/role/side/spread/phase.
- `build_transition_matrix` - liczy przejscia po path.
- `build_margin_bucket_matrix` - liczy warianty path + margin bucket.
- `lookup_payload` - buduje `scenario_lookup.json`.
- `event_probability_from_lookup` - wybiera blok prawdopodobienstwa dla eventu.
- `main` - CLI, zapis plikow i lookup JSON.

GUI:

```text
scripts/variant_b_daily_bot_gui.py
```

Najwazniejsze miejsca:

- `_build_live_scenario_panel` - prawy panel Live Scenario.
- `_live_base_command` - sklada komende dla legacy backendu.
- `_run_live_scenario` - uruchamia `RUN LIVE LOOKUP`.
- `_run_team_history_compare` - obecny basic after Q2 dla Team A i Team B.
- `_update_live_result_panel` - formatuje wynik legacy lookup.
- `_format_team_history_compare` - formatuje obecny `RUN BASIC AFTER Q2`.

Dokumentacja:

```text
docs/live_quarter_scenario_matrix.md
```

## 3. Jak Obecnie Obliczane Sa Kwarty I Path

Obecnie `build_team_game_rows`:

1. Pobiera ostatni play z Q1-Q4.
2. Wylicza punkty kwartowe:

```text
Q1 = total score after Q1
Q2 = total score after Q2 - total score after Q1
Q3 = total score after Q3 - total score after Q2
Q4 = total score after Q4 - total score after Q3
```

3. Dla kazdej druzyny liczy:

```text
q1_result = WIN / LOSS / TIE
q2_result = WIN / LOSS / TIE
q3_result = WIN / LOSS / TIE
q4_result = WIN / LOSS / TIE
```

4. Buduje path:

```text
WIN-WIN
WIN-LOSS
LOSS-WIN
LOSS-LOSS
...
```

5. Liczy stan skumulowany po kazdej kwarcie:

```text
after_q1_margin
after_q2_margin
after_q3_margin
after_q4_margin
```

6. Liczy final:

```text
final_state = WIN / LOSS / TIE
final_margin = team_final - opponent_final
```

Dogrywka nie jest doliczana do Q4, ale jest uwzgledniona w `final_state`.

## 4. Zmiany Wymagajace Migracji Danych

Migracji albo nowej wersji kontraktu beda wymagaly:

1. Margin buckets

Obecnie:

```text
LEAD_1_3
LEAD_4_7
LEAD_8_14
LEAD_15_PLUS
TIE
TRAIL_1_3
TRAIL_4_7
TRAIL_8_14
TRAIL_15_PLUS
```

Docelowo:

```text
TRAILING_15_PLUS
TRAILING_8_TO_14
TRAILING_1_TO_7
TIED
LEADING_1_TO_7
LEADING_8_TO_14
LEADING_15_PLUS
```

2. Season phase

Obecnie:

```text
EARLY: week <= 5
MIDDLE: week <= 11
LATE: week 12+
```

Docelowo:

```text
EARLY: Week 1-4
MID: Week 5-12
LATE: Week 13-18
PLAYOFFS: osobna kategoria
```

3. Pregame spread perspective

Obecnie `spread_line` jest przechowywany z perspektywy away team, a role jest wyliczane przez `favorite_side`.

Docelowo trzeba miec jawne:

```text
team_a_closing_spread
team_a_role
```

gdzie:

```text
ujemny = Team A favorite
dodatni = Team A underdog
zero = pick'em
```

4. Nowe eventy

Obecnie sa tylko:

```text
TEAM_A_WIN_FINAL
TEAM_A_WIN_NEXT_QUARTER
TEAM_A_LEAD_AFTER_NEXT_QUARTER
```

Docelowo dochodza:

```text
TEAM_A_TIED_OR_LED_AFTER_NEXT_QUARTER
OPPONENT_TIED_GAME_LATER
OPPONENT_TOOK_LEAD_LATER
OPPONENT_CAME_WITHIN_8_POINTS
OPPONENT_WON_FINAL
TEAM_A_WON_SECOND_HALF
TEAM_A_FINAL_MARGIN
TEAM_A_REMAINING_GAME_MARGIN
```

Eventy play-level musza byc budowane z kazdego pozniejszego play-by-play, a nie tylko z wyniku na koniec kwarty:

```text
OPPONENT_TIED_GAME_LATER
OPPONENT_TOOK_LEAD_LATER
OPPONENT_CAME_WITHIN_8_POINTS
```

Docelowe agregaty/flag fields w wierszu team-game:

```text
opponent_tied_game_after_state
opponent_took_lead_after_state
opponent_came_within_8_after_state
min_team_a_margin_after_state
max_opponent_margin_after_state
first_play_id_opponent_tied_game
first_play_id_opponent_took_lead
first_play_id_opponent_within_8
```

Te pola musza byc liczone z play-by-play po analizowanym stanie, np. po Q2 albo po Q3, az do konca meczu lacznie z dogrywka, jezeli event dotyczy finalnej sciezki meczu.

5. Output contract

Obecny JSON lookup jest za prosty. Nowy kontrakt musi oddzielac:

```text
current_state
league_baseline
team_a_history
opponent_recovery_history
market_comparison
sample_and_reliability
warnings
```

Nowy kontrakt musi tez zawierac metadane anty-leakage i jakosci danych:

```text
schema_version
methodology_version
data_cutoff_utc
generated_at_utc
seasons_included
games_included
sample_unit
excluded_games_count
data_quality_warnings
```

`sample_unit` musi jasno mowic, ze standardowa jednostka proby to `team-game observations`, a nie zawsze unikalne mecze.

6. Future-data leakage

Historyczny lookup nie moze korzystac z meczow rozegranych po analizowanym spotkaniu. V2 musi przyjmowac:

```text
data_cutoff_utc
analysis_game_id optional
analysis_game_datetime_utc optional
```

I zwracac:

```text
generated_at_utc
data_cutoff_utc
seasons_included
games_included
excluded_games_count
```

7. Legacy compatibility mode

Porownanie starej i nowej wersji musi dzialac w specjalnym trybie:

```text
legacy_compatibility_mode = true
```

Nowy model `path + margin bucket` nie musi dawac tych samych wynikow co legacy `path-only`. Porownanie sluzy do wykrycia regresji w parsowaniu kwart i path, a nie do wymuszenia identycznych probek analitycznych.

8. Symetryczne stany i podwojne liczenie

League-wide standardowo uzywa `team-game observations`, bo kazdy mecz tworzy dwie perspektywy. Dla stanow symetrycznych, np. `TIE-TIE`, V2 musi jawnie zabezpieczyc sie przed sztucznym podwajaniem tej samej obserwacji, kiedy event jest symetryczny i obie perspektywy niosa ten sam sygnal.

## 5. Testy Do Dodania Przed Refaktoryzacja

Najpierw dopisac testy dla istniejacej logiki, zanim zmienimy backend.

Nowy plik:

```text
tests/test_live_scenario_core.py
```

Testy minimalne:

1. `result_from_margin`

- `+1 -> WIN`
- `0 -> TIE`
- `-1 -> LOSS`

2. `parse_path`

- `WIN-WIN -> ("WIN", "WIN")`
- `WIN>LOSS -> ("WIN", "LOSS")`
- invalid value rzuca blad.

3. `mirror path`

Funkcja jest obecnie w GUI, ale powinna trafic do backend util:

- `WIN-WIN -> LOSS-LOSS`
- `WIN-LOSS-TIE -> LOSS-WIN-TIE`

4. Quarter scoring

Na sztucznym PBP:

- Q1: A 7-3
- Q2: A 10-7
- system daje:
  - `q1_result = WIN`
  - `q2_result = WIN`
  - `after_q2_margin = +7`

Dodac rowniez test przyszlego wymogu V2:

- quarter-end score bierze ostatni poprawny, niepusty cumulative score w danej kwarcie,
- brakujacy score w ostatnim rekordzie kwarty nie moze psuc path,
- suma punktow kwartowych musi zgadzac sie z wynikiem po Q4.

Ten test moze byc najpierw oznaczony jako expected-fail, dopoki legacy backend nie zostanie zastapiony V2.

5. Margin bucket legacy

Zabezpieczy obecne zachowanie przed migracja:

- `+3 -> LEAD_1_3`
- `+7 -> LEAD_4_7`
- `0 -> TIE`
- `-10 -> TRAIL_8_14`

6. `sample_quality`

Obecnie:

- 0 -> `NO_DATA`
- 1-19 -> `VERY_LOW`
- 20-49 -> `LOW`
- 50-99 -> `MODERATE`
- 100+ -> `STRONG`

Nowy wymog bedzie inny, wiec najpierw testujemy legacy, potem migrujemy.

7. `event_probability_from_lookup`

- `TEAM_A_WIN_NEXT_QUARTER` bierze `next_quarter_distribution`.
- `TEAM_A_LEAD_AFTER_NEXT_QUARTER` bierze `cumulative_after_next_quarter`.
- `TEAM_A_WIN_FINAL` bierze `final_including_overtime`.
- `TIE_IS_LOSS` przenosi tie do loss.

## 6. Proponowany Nowy Model Danych

Nie zmieniac od razu starego CSV. Najpierw dodac nowy kontrakt obok starego.

Proponowane nowe pliki:

```text
live_scenario/
  __init__.py
  config.py
  state.py
  stats.py
  events.py
  service.py
```

### `live_scenario/config.py`

```python
MARGIN_BUCKETS = [
    ("TRAILING_15_PLUS", None, -15),
    ("TRAILING_8_TO_14", -14, -8),
    ("TRAILING_1_TO_7", -7, -1),
    ("TIED", 0, 0),
    ("LEADING_1_TO_7", 1, 7),
    ("LEADING_8_TO_14", 8, 14),
    ("LEADING_15_PLUS", 15, None),
]

SAMPLE_QUALITY_THRESHOLDS = {
    "NO_DATA": (0, 0),
    "VERY_LOW": (1, 9),
    "LOW": (10, 29),
    "MODERATE": (30, 74),
    "STRONG": (75, None),
}
```

### `live_scenario/state.py`

```python
LiveCurrentState:
  team_a
  opponent
  q1_team_a
  q1_opponent
  q2_team_a
  q2_opponent
  q3_team_a optional
  q3_opponent optional
  completed_quarters
  team_a_path
  opponent_path
  team_a_score
  opponent_score
  margin
  margin_bucket
```

### `live_scenario/stats.py`

```python
ProbabilityResult:
  sample_size
  wins
  losses
  ties
  raw_probability
  adjusted_probability
  confidence_interval_low
  confidence_interval_high
  sample_quality
```

### `live_scenario/service.py`

```python
LiveScenarioReport:
  current_state
  league_baseline
  team_a_history
  opponent_recovery_history
  market_comparison
  sample_and_reliability
  warnings
```

## 7. Proponowany Schemat Wyniku

Docelowy JSON dla `RUN BASIC AFTER Q2`:

```json
{
  "schema_version": "live_scenario.v2",
  "methodology_version": "live_scenario_methodology.v1",
  "generated_at_utc": "2026-09-10T02:30:00Z",
  "data_cutoff_utc": "2026-09-10T02:29:59Z",
  "seasons_included": [2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025],
  "games_included": 2560,
  "sample_unit": "team-game observations",
  "excluded_games_count": 0,
  "data_quality_warnings": [],
  "current_state": {
    "team_a": "BUF",
    "opponent": "HOU",
    "completed_quarters": 2,
    "team_a_path": "WIN-WIN",
    "opponent_path": "LOSS-LOSS",
    "team_a_score": 17,
    "opponent_score": 10,
    "margin": 7,
    "margin_bucket": "LEADING_1_TO_7"
  },
  "league_baseline": {
    "filters_applied": ["path", "margin_bucket"],
    "sample_size": 120,
    "event_results": {}
  },
  "team_a_history": {
    "team": "BUF",
    "filters_applied": ["team", "path", "margin_bucket"],
    "filters_relaxed": [],
    "sample_size": 12,
    "event_results": {}
  },
  "opponent_recovery_history": {
    "team": "HOU",
    "filters_applied": ["team", "opponent_path", "opponent_margin_bucket"],
    "filters_relaxed": [],
    "sample_size": 9,
    "event_results": {}
  },
  "market_comparison": {
    "team_a_live_decimal": null,
    "opponent_live_decimal": null,
    "market_available": false,
    "primary_probability_source": "league_baseline",
    "tie_policy": "TIE_AS_LOSS"
  },
  "sample_and_reliability": {
    "exact_filtered_match": {},
    "expanded_team_match": {},
    "contextual_league_match": {},
    "broad_league_baseline": {}
  },
  "warnings": [
    "Historical context only. No automatic betting recommendation.",
    "Historical live profitability cannot be validated without archived live market prices."
  ]
}
```

## 7A. Market Comparison Probability Source

W MVP glowne prawdopodobienstwo dla `market_comparison` pochodzi z:

```text
league_baseline.adjusted_probability
```

Team A history i opponent recovery history sa pokazywane jako osobne odchylenia wzgledem ligi:

```text
team_a_delta_vs_league_pp
opponent_recovery_delta_vs_league_pp
```

Nie laczymy ich naiwnie w jedno `combined probability`, bo nie sa niezaleznymi dowodami. Ewentualne laczenie moze powstac dopiero jako osobny model po walidacji.

## 7B. Tie Policy

Kazdy event i market comparison musi miec jawne:

```text
tie_policy
```

Dopuszczalne wartosci:

```text
TIE_AS_PUSH
TIE_AS_LOSS
THREE_WAY_DISTRIBUTION
```

Przyklad:

```text
TEAM_A_WIN_FINAL + TIE_AS_LOSS
TEAM_A_WIN_NEXT_QUARTER + TIE_AS_PUSH
TEAM_A_FINAL_MARGIN + THREE_WAY_DISTRIBUTION
```

## 8. Shrinkage Proposal

Pierwsza wersja: posterior Beta z priorem opartym na league baseline.

```text
k = 20
alpha_prior = league_p * k
beta_prior = (1 - league_p) * k
alpha_posterior = wins + alpha_prior
beta_posterior = losses + beta_prior
adjusted_p = alpha_posterior / (alpha_posterior + beta_posterior)
```

Adjusted probability i adjusted interval musza pochodzic z tego samego modelu posterior Beta.

Wilson interval moze zostac wylacznie jako:

```text
raw_probability_interval
```

Interpretacja:

- przy bardzo malej probce team wynik jest mocno sciagany do ligi,
- przy duzej probce team wynik ma coraz wieksza wage,
- metoda jest deterministyczna i latwa do testowania.

Przyklad:

```text
league_p = 0.62
team sample = 4
team wins = 4
raw team p = 1.00

adjusted_p = (4 + 20 * 0.62) / (4 + 20)
adjusted_p = 0.6833
```

Nie pokazujemy wiec `100%` jako wiarygodnego prawdopodobienstwa przy 4 przypadkach.

Confidence intervals:

```text
raw_interval = Wilson interval
adjusted_interval = Beta posterior credible interval
```

## 9. Plan Przebudowy Etapami

### Etap 1 - Testy legacy

Pliki:

- dodac `tests/test_live_scenario_core.py`

Cel:

- zamrozic obecne zachowanie path, quarter result, sample quality i event lookup.

Bez zmian GUI.

### Etap 2 - Wydzielenie core utils

Pliki:

- dodac `live_scenario/__init__.py`
- dodac `live_scenario/config.py`
- dodac `live_scenario/state.py`
- dodac `live_scenario/events.py`
- zostawic `scripts/live_quarter_scenario_matrix.py` jako wrapper legacy.

Cel:

- przeniesc czyste funkcje bez zmiany wynikow.

### Etap 3 - Current state z punktow kwartowych

Pliki:

- `live_scenario/state.py`
- testy w `tests/test_live_scenario_state.py`

Cel:

- uzytkownik podaje punkty Q1/Q2/Q3,
- system sam liczy:
  - path Team A,
  - path Opponent,
  - score,
  - margin,
  - margin bucket.

### Etap 4 - Nowe margin buckets i season phase

Pliki:

- `live_scenario/config.py`
- `live_scenario/state.py`
- testy bucketow.

Cel:

- wdrozyc nowe buckety:
  - `LEADING_1_TO_7`,
  - `TRAILING_8_TO_14`,
  - itd.
- wdrozyc phase:
  - `EARLY`, `MID`, `LATE`, `PLAYOFFS`.

### Etap 5 - Nowy report service

Pliki:

- `live_scenario/service.py`
- `live_scenario/stats.py`
- `live_scenario/events.py`

Cel:

- jedna funkcja buduje `LiveScenarioReport`:
  - current state,
  - league baseline,
  - team A history,
  - opponent recovery history,
  - market comparison,
  - reliability,
  - warnings.

### Etap 6 - Expanded sample levels

Pliki:

- `live_scenario/service.py`
- testy `tests/test_live_scenario_relaxation.py`

Cel:

- pokazac:
  1. exact filtered match,
  2. expanded team match,
  3. contextual league match,
  4. broad league baseline.

Nie luzowac filtrow po cichu.

### Etap 7 - Market comparison

Pliki:

- `live_scenario/market.py`
- testy `tests/test_live_scenario_market.py`

Cel:

- decimal odds Team A,
- decimal odds Opponent,
- implied probability,
- no-vig probability,
- roznica vs adjusted historical probability,
- orientacyjne EV.

Bez twierdzenia o historycznej rentownosci.

### Etap 8 - CLI v2 obok legacy

Pliki:

- dodac `scripts/live_scenario_v2.py`

Cel:

- nowa komenda przyjmuje punkty kwartowe zamiast recznego path.
- legacy script zostaje.

### Etap 9 - GUI v2

Pliki:

- `scripts/variant_b_daily_bot_gui.py`

Cel:

- dodac pola Q1/Q2/Q3 points,
- `RUN BASIC AFTER Q2` uzywa v2,
- `RUN LIVE LOOKUP` legacy zostaje jako fallback.

### Etap 10 - Porownanie i migracja

Cel:

- porownac legacy path-only z v2 current-state.
- dopiero po zgodnosci i testach mozna wygaszac stara sciezke.

### Etap 11 - Dwa niezalezne pathy

Pliki:

- `live_scenario/state.py`
- `live_scenario/service.py`
- `scripts/live_scenario_v2.py`
- testy `tests/test_live_scenario_current_state.py`

Cel:

- dodac jawne rozroznienie:
  - `quarter_result_path` - wynik kazdej kwarty osobno: `WIN`, `LOSS`, `TIE`,
  - `cumulative_state_path` - skumulowany stan meczu po kazdej kwarcie: `LEAD`, `TRAIL`, `TIE`.
- oba pathy maja byc generowane automatycznie z punktow kwartowych.
- lustrzany path przeciwnika ma byc generowany dla obu typow:
  - `WIN-LOSS` -> `LOSS-WIN`,
  - `LEAD-TIE` -> `TRAIL-TIE`.

Przyklad:

```text
Q1: BUF 7-3 HOU
Q2: BUF 3-7 HOU

quarter_result_path BUF: WIN-LOSS
cumulative_state_path BUF: LEAD-TIE
```

Decyzja:

- `quarter_result_path` opisuje przebieg kwart.
- `cumulative_state_path` opisuje rzeczywisty stan meczu po Q1/Q2/Q3.
- raport powinien pokazywac oba, ale glowny baseline live powinien domyslnie uzywac `cumulative_state_path`.

### Etap 12 - Pregame spread context V2

Pliki:

- `live_scenario/state.py`
- `live_scenario/service.py`
- potencjalnie `live_scenario/spread.py`
- testy `tests/test_live_scenario_spread.py`

Cel:

- dodac pola z perspektywy Team A:
  - `team_a_closing_spread`,
  - `opponent_closing_spread`,
  - `team_a_role`,
  - `exact_spread`,
  - `spread_bucket`,
  - `spread_source`,
  - `spread_captured_at_utc`,
  - `spread_quality`.
- nie pozwalac na role sprzeczna ze spreadem:
  - spread ujemny = Team A favorite,
  - spread dodatni = Team A underdog,
  - spread zero = pick'em.
- spread ma byc kontekstem i filtrem probki, nie automatycznym sygnalem zakladu.

### Etap 13 - Broad baseline vs spread-conditioned baseline

Pliki:

- `live_scenario/service.py`
- testy `tests/test_live_scenario_service.py`

Cel:

- rozdzielic wyniki league baseline na:
  - `broad_baseline_without_spread`,
  - `spread_conditioned_baseline`,
  - opcjonalnie `exact_spread_match`.
- exact spread nie moze byc jedynym domyslnym filtrem, bo czesto bedzie mial bardzo mala probe.
- rozluznianie filtrow musi byc jawne:
  1. `exact_spread_match`,
  2. `spread_bucket_match`,
  3. `role_only_match`,
  4. `no_spread_baseline`.

Kazdy poziom musi pokazywac:

```text
filters_applied
filters_relaxed
sample_size
sample_quality
historical_window
```

### Etap 14 - Historyczne okna i stabilnosc wyniku

Pliki:

- `live_scenario/config.py`
- `live_scenario/service.py`
- testy `tests/test_live_scenario_historical_windows.py`

Cel:

- dodac konfigurowalne okna:
  - `PRIMARY_WINDOW = 2015-2025`,
  - `RECENT_WINDOW = 2021-2025`,
  - `EXTENDED_WINDOW = 2012-2025`.
- w sezonie 2026 mozna dolaczac zakonczone mecze 2026, ale tylko z ochrona `data_cutoff_utc`.
- nie dolaczac automatycznie sezonow 1999-2000 do glownego baseline.
- dodac prosty status stabilnosci:
  - `historical_window_stability = STABLE`,
  - `historical_window_stability = UNSTABLE`.

Pierwsza wersja:

```text
STABLE, jezeli primary/recent/extended roznia sie maksymalnie o konfigurowalny prog pp.
UNSTABLE, jezeli roznica przekracza prog.
```

Nie tworzyc skomplikowanej stabilnosci bez testow.

### Etap 15 - Forum content summary

Pliki:

- `live_scenario/service.py`
- `scripts/live_scenario_v2.py`
- GUI pozniej, po stabilizacji backendu
- testy `tests/test_live_scenario_forum_summary.py`

Cel:

- dodac do kontraktu osobna sekcje:

```text
forum_content_summary
```

Sekcja ma zawierac dane do krotkiego wpisu na forum:

```text
matchup
current_score
quarter_scores
quarter_result_path
cumulative_state_path
pregame_spread
spread_bucket
broad_final_win_probability
broad_sample_size
spread_conditioned_final_win_probability
spread_conditioned_sample_size
difference_vs_broad_pp
team_specific_note
warning
```

Zakazane slowa/wnioski automatyczne:

```text
BET
VALUE BET
PLAY
PICK
```

To ma byc ciekawostka historyczna i kontekst live, nie automatyczna rekomendacja zakladu.

## 10. Decyzja Na Teraz

Nie implementowac calego modulu naraz.

Status:

```text
Etap 1 - testy legacy: wykonane.
Etap 2 - wydzielenie core utils bez zmiany wynikow: wykonane.
Etap 3 - current state z punktow Q1/Q2/Q3: wykonane.
Etap 4 - season phase V2 i kontrakt bucketow/metadanych: wykonane.
Etap 5 - pierwszy report service V2: wykonane.
Etap 6 - expanded sample levels z jawnymi filtrami: wykonane.
Etap 7 - market comparison V2: wykonane.
Etap 8 - CLI v2 obok legacy: wykonane.
Etap 9 - GUI v2 z polami Q1/Q2/Q3 i RUN BASIC AFTER Q2 przez V2: wykonane.
Etap 10 - legacy compatibility mode i porownanie V2 vs legacy path-only: wykonane.
Etap 11 - dwa niezalezne pathy quarter/cumulative: wykonane.
Etap 12 - pregame spread context V2: wykonane.
Etap 13 - broad baseline vs spread-conditioned baseline: wykonane.
Etap 14 - okna historyczne i stabilnosc wyniku: wykonane.
Etap 15 - forum content summary: wykonane.
```

Etap 2 dodal pakiet:

```text
live_scenario/
  __init__.py
  config.py
  state.py
  stats.py
  events.py
```

Oraz testy porownawcze:

```text
tests/test_live_scenario_core_compare.py
```

Legacy backend i GUI nie zostaly przepiete na nowe moduly.

Nastepny krok:

```text
Etapy 11-15 sa wykonane. Nastepny krok to test praktyczny w GUI na scenariuszu
live oraz decyzja, ktore pola V2 maja byc mocniej wyeksponowane w prawym panelu.
Nie wygaszac jeszcze legacy RUN LIVE LOOKUP.
```
