# Live Quarter Scenario Matrix

## Cel

Ten modul jest narzedziem live-scenario dla NFL.

Nie pobiera live kursow i nie daje automatycznego picka. Buduje historyczna macierz scenariuszy kwartowych z `nfl_data_py`, a potem pokazuje:

- jak czesto dana sciezka kwartowa wystepowala;
- jak czesto druzyna A wygrywala nastepna kwarte;
- jak czesto prowadzila po nastepnej kwarcie;
- jak czesto wygrywala mecz;
- fair odds;
- minimalny kurs wejscia;
- EV dla kursu live wpisanego recznie.

## Najwazniejsze rozroznienie

Skrypt pokazuje dwie rozne rzeczy:

```text
Quarter Reset View = kto wygral sama kwarte
Cumulative Game View = kto prowadzi / wygrywa caly mecz po tej kwarcie
```

Przyklad:

```text
Q1: A wygrywa 10:3
Q2: A przegrywa 3:7
```

Wtedy:

```text
Q2 result only = A LOSS
after H1 cumulative = A LEAD 13:10
```

To nie jest to samo i skrypt celowo trzyma te rzeczy osobno.

## Glowna komenda

Pelny zakres 2016-2025:

```powershell
.\.venv\Scripts\python.exe scripts\live_quarter_scenario_matrix.py --start-season 2016 --end-season 2025
```

Wyniki beda tutaj:

```text
research/live_quarter_scenario_matrix/2016_2025_league_wide/
```

## Pliki wynikowe

```text
team_game_quarter_rows.csv
full_quarter_path_matrix.csv
quarter_transition_matrix.csv
margin_bucket_matrix.csv
segment_transition_matrix.csv
scenario_lookup.json
summary.md
```

### team_game_quarter_rows.csv

Surowy widok kazdego meczu z perspektywy kazdej druzyny.

Jeden mecz tworzy dwa wiersze:

```text
Team A = home
Team A = away
```

### full_quarter_path_matrix.csv

Pelne 81 sciezek:

```text
WIN-WIN-WIN-WIN
WIN-WIN-WIN-LOSS
WIN-LOSS-WIN-LOSS
LOSS-LOSS-WIN-WIN
...
```

Dla kazdej sciezki:

- sample size;
- sample quality;
- frequency;
- regulation win/tie/loss;
- final win/tie/loss including overtime;
- fair odds.

### quarter_transition_matrix.csv

Macierz przejsc po kazdym wezle:

```text
START -> Q1
WIN -> Q2
WIN-LOSS -> Q3
WIN-LOSS-WIN -> Q4
```

Dla kazdego wezla pokazuje:

- P(A wygra nastepna kwarte);
- P(A przegra nastepna kwarte);
- P(nastepna kwarta bedzie remisem);
- P(A bedzie prowadzic po nastepnej kwarcie);
- P(A wygra caly mecz).

### margin_bucket_matrix.csv

Rozszerzenie o wynik skumulowany po danej kwarcie.

Przyklady bucketow:

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

To jest wazne, bo:

```text
WIN-LOSS po H1 przy prowadzeniu 3 pkt
```

to inny scenariusz niz:

```text
WIN-LOSS po H1 przy przegrywaniu 10 pkt
```

### segment_transition_matrix.csv

Rozszerzenie o segmenty:

```text
favorite / underdog
home / away
spread bucket
season phase
```

To jest wersja bardziej szczegolowa. Przy malych probach trzeba mocno patrzec na `sample_quality`.

### scenario_lookup.json

Szybki lookup do uzycia podczas meczu.

Przyklad klucza:

```text
WIN-LOSS-WIN
```

## Lookup podczas meczu

Przyklad: druzyna A wygrala Q1 i przegrala Q2. Chcesz sprawdzic szanse na finalne zwyciestwo i EV przy kursie live 1.90:

```powershell
.\.venv\Scripts\python.exe scripts\live_quarter_scenario_matrix.py --start-season 2016 --end-season 2025 --lookup-path WIN-LOSS --event TEAM_A_WIN_FINAL --live-decimal 1.90
```

Mozesz tez podac kurs amerykanski:

```powershell
.\.venv\Scripts\python.exe scripts\live_quarter_scenario_matrix.py --start-season 2016 --end-season 2025 --lookup-path WIN-LOSS --event TEAM_A_WIN_FINAL --live-ml -110
```

## Dostepne eventy

```text
TEAM_A_WIN_NEXT_QUARTER
TEAM_A_LEAD_AFTER_NEXT_QUARTER
TEAM_A_WIN_FINAL
```

Znaczenie:

```text
TEAM_A_WIN_NEXT_QUARTER = A wygra sama nastepna kwarte
TEAM_A_LEAD_AFTER_NEXT_QUARTER = A bedzie prowadzic po nastepnej kwarcie
TEAM_A_WIN_FINAL = A wygra caly mecz lacznie z dogrywka
```

## Settlement

Domyslnie:

```text
TIE_IS_LOSS
```

Czyli remis traktowany jest jako przegrana eventu.

Dla rynkow, gdzie remis jest zwrotem:

```powershell
--settlement TIE_IS_PUSH
```

Wtedy fair odds i EV sa liczone inaczej:

```text
fair odds = 1 + P(loss) / P(win)
EV = P(win) * (odds - 1) - P(loss)
```

## Filtrowanie probki

League-wide:

```powershell
.\.venv\Scripts\python.exe scripts\live_quarter_scenario_matrix.py --start-season 2016 --end-season 2025 --sample-mode LEAGUE_WIDE
```

Historia konkretnej druzyny:

```powershell
.\.venv\Scripts\python.exe scripts\live_quarter_scenario_matrix.py --start-season 2016 --end-season 2025 --sample-mode TEAM_A_HISTORY --team LA
```

Historia przeciwnika:

```powershell
.\.venv\Scripts\python.exe scripts\live_quarter_scenario_matrix.py --start-season 2016 --end-season 2025 --sample-mode TEAM_B_HISTORY --opponent SF
```

Head-to-head:

```powershell
.\.venv\Scripts\python.exe scripts\live_quarter_scenario_matrix.py --start-season 2016 --end-season 2025 --sample-mode HEAD_TO_HEAD --team LA --opponent SF
```

Filtry segmentow:

```powershell
--role FAVORITE
--role UNDERDOG
--side home
--side away
--spread-bucket 2-3
--season-phase EARLY
```

## Sample quality

Kazdy procent musi byc czytany razem z liczebnoscia proby:

```text
NO_DATA: 0
VERY_LOW: 1-19
LOW: 20-49
MODERATE: 50-99
STRONG: 100+
```

Przy `VERY_LOW` i `LOW` wynik jest tylko ciekawostka / kontekst, nie twarda podstawa decyzji.

## Jak to wpinamy w nasz system

Ten modul jest czescia `live_watch_card`.

Przed meczem:

```text
Variant B znajduje kandydatow VP/GOW/GOM/GOY.
Live Quarter Scenario Matrix przygotowuje historyczne scenariusze.
```

W trakcie meczu:

```text
po Q1 wpisujemy sciezke, np. WIN
po H1 wpisujemy sciezke, np. WIN-LOSS
po Q3 wpisujemy sciezke, np. WIN-LOSS-WIN
```

Skrypt pokazuje:

```text
historyczna szansa
fair odds
minimalny kurs
EV dla recznie wpisanego kursu live
sample quality
```

Finalna decyzja nadal wymaga:

- aktualnego kursu z booka;
- kontekstu meczu;
- kontuzji / inactives;
- line movement;
- zdrowego sample size;
- operator decision.

