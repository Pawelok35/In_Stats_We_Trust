# Variant B Daily Bot

Ten bot porzadkuje codzienny workflow NFL Variant B.

Domyslnie bot dziala jako `DRY_RUN`: pokazuje, co jest dzisiaj do zrobienia, sprawdza brakujace pliki i zapisuje raport. Komendy odpala dopiero po dodaniu `--execute`.

## Glowna Komenda

```powershell
.\.venv\Scripts\python.exe scripts\variant_b_daily_bot.py --season 2026 --week 1
```

Raport trafia tutaj:

```text
research/daily_bot/2026/week_01/YYYY-MM-DD_day.md
```

## Okno GUI

Mozesz tez odpalic bota w osobnym oknie:

```powershell
.\.venv\Scripts\pythonw.exe scripts\variant_b_daily_bot_gui.py
```

Albo przez wrapper:

```powershell
.\scripts\Start-VariantBDailyBotGui.ps1
```

W oknie wybierasz:

```text
season
week
day: auto / monday / tuesday / wednesday / thursday / friday / saturday / sunday
Dry run albo Execute
```

Panel `Plan for selected day` pokazuje od razu:

```text
cel dnia
liste zadan
ktore zadania sa manualne
ktore zadania sa komendami
jakie pliki beda sprawdzane
```

Panel `Model picks for selected week` pozwala wczytac kandydatow modelu:

```text
Load model picks = wczytuje data/picks_variant_m/{season}/week_XX.jsonl
Pick pokazuje tylko VALUE PLAY / GOW / GOM / GOY
Watchlist pokazuje NEUTRAL z abs(edge_vs_line) >= 2.0
po wyborze picka bot automatycznie ustawia Game ID w sekcji GPT Paste
po wyborze picka bot automatycznie uzupelnia prompt GPT danymi z modelu
```

Watchlist to nie sa typy do gry. To lista obserwacyjna: neutralne mecze blisko progu, ktore moga przejsc na VP/GOW/GOM/GOY po zmianie linii albo po aktualizacji danych.

`Reset week test data` usuwa tylko artefakty generowane. Zachowuje reczne wejscia:
book snapshot, market quotes, GPT snapshots oraz closing snapshot.

Ten panel ma sens po wykonaniu:

```powershell
.\.venv\Scripts\python.exe -m app.cli sync-nfl-schedule --season 2026
.\.venv\Scripts\python.exe -m app.cli export-lines-from-nfl --season 2026 --week 1
.\.venv\Scripts\python.exe scripts\prospective_week_flow.py --season 2026 --week 1 --variant variant_m --skip-freeze --allow-not-proof-ready
```

Panel `GPT Prompt for selected day` pokazuje gotowy prompt dla wybranego dnia.

Przyciski:

```text
Generate GPT prompt = odswieza prompt po zmianie dnia / game_id / typu snapshotu
Copy GPT prompt = kopiuje prompt do schowka
```

Po kliknieciu `Dry run` albo `Execute`, panel `Output` pokazuje checklist:

```text
[x] PASS / READY / DRY_RUN / SKIPPED
[ ] NEEDS_OPERATOR / MISSING / FAIL
```

Przyklad: wybierasz `wednesday` i klikasz `Dry run`, a bot tworzy raport tylko dla zadan srody.

## Tryb Wykonania

Po sprawdzeniu raportu mozesz odpalic komendy:

```powershell
.\.venv\Scripts\python.exe scripts\variant_b_daily_bot.py --season 2026 --week 1 --execute
```

## Test Konkretnego Dnia

```powershell
.\.venv\Scripts\python.exe scripts\variant_b_daily_bot.py --season 2026 --week 1 --day tuesday
.\.venv\Scripts\python.exe scripts\variant_b_daily_bot.py --season 2026 --week 1 --day thursday
.\.venv\Scripts\python.exe scripts\variant_b_daily_bot.py --season 2026 --week 1 --day sunday
```

Mozesz tez podac date:

```powershell
.\.venv\Scripts\python.exe scripts\variant_b_daily_bot.py --season 2026 --week 1 --date 2026-09-08
```

## Co Robi Bot

Bot czyta:

```text
config/variant_b_daily_bot.yaml
```

I wedlug dnia tygodnia:

```text
wtorek = zamkniecie poprzedniej kolejki + glowny skan nowej
sroda = TNF delta refresh
czwartek = final TNF + zrzuty Sunday/MNF
piatek = glowny refresh Sunday/MNF
sobota = pre-final Sunday/MNF
niedziela = final Sunday + zrzut MNF + live note
poniedzialek = final MNF
```

## Co Nadal Robisz Recznie

```text
linie / screeny z pregame.com albo booka
realny quote: book, spread, price, timestamp, executable_status
GPT pelne 19 punktow dla VP/GOW/GOM/GOY
GPT delta refresh
finalna decyzja operatora
```

Bot nie podejmuje decyzji bettingowej i nie rekonstruuje brakujacych quote.

## Gdzie Wklejac Raport GPT

Najprosciej: w oknie bota uzyj panelu `GPT Paste`.

Wpisujesz:

```text
Game ID: 2026_w01_SF_at_LA
Type: full_19_points albo delta_refresh
Source: GPT
```

Potem wklejasz odpowiedz GPT do pola tekstowego i klikasz:

```text
Save GPT snapshot
```

Bot sam zapisze plik w odpowiednim folderze.

Pelne 19 punktow dla meczu:

```text
research/gpt_snapshots/2026/week_01/2026_w01_SF_at_LA/full_19_points.md
```

Delta refresh:

```text
research/gpt_snapshots/2026/week_01/2026_w01_SF_at_LA/delta_2026-09-09_wednesday.md
```

Dokladna instrukcja:

```text
docs/gpt_snapshot_storage.md
```

## Prompty GPT W Bocie

Bot generuje prompt na podstawie wybranego dnia i wybranego meczu z listy model picks.

```text
Wtorek: full_19_points
- pelne 19 punktow Variant B tylko dla VP/GOW/GOM/GOY

Sroda: delta_tnf
- TNF delta refresh, czyli zmiany quote/injury/roster/weather/market od wtorku

Czwartek: final_tnf_plus_sunday_mnf_delta
- final check TNF oraz osobny zrzut zmian dla Sunday/MNF

Piatek: sunday_mnf_delta
- glowny refresh niedzielnych i poniedzialkowych kandydatow

Sobota: prefinal_sunday_mnf_delta
- pre-final check Sunday/MNF i lista brakow przed dniem meczu

Niedziela: final_sunday_plus_mnf_delta
- final check niedzielnych kandydatow oraz osobny delta refresh MNF

Poniedzialek: final_delta_mnf
- final check MNF
```

W praktyce: wybierasz dzien, klikasz `Load model picks`, wybierasz mecz z listy, potem `Generate GPT prompt` albo `Copy GPT prompt`.

Do wtorkowego przerobienia screenow z pregame.com na YAML uzyj w GUI:

```text
Copy book snapshot prompt
```

Ten przycisk kopiuje prompt z aktualnym `season` i `week`. Wklejasz go do GPT razem ze screenami linii, a odpowiedz YAML wklejasz potem do Codex.

Gdy GPT zwroci YAML, uzyj drugiego przycisku:

```text
Copy Codex save instruction
```

Ten przycisk kopiuje instrukcje dla Codex: gdzie zapisac YAML, co sprawdzic i czego nie zgadywac. Wklejasz do Codex instrukcje + YAML od GPT.

## Symulacja W Bocie

Do treningowego Week 1 uzywaj pliku:

```text
research/simulations/2026_week1_full_training_simulation.md
```

W GUI masz przyciski:

```text
Open simulation file
Save book snapshot from paste
Convert snapshot to lines
```

Workflow symulacyjny:

```text
1. Kliknij Open simulation file.
2. Skopiuj blok YAML z danego dnia.
3. Wklej go do pola GPT Paste.
4. Kliknij Save book snapshot from paste.
5. Kliknij Convert snapshot to lines.
6. Dopiero potem Dry run / Execute dla wybranego dnia.
```

`Save book snapshot from paste` przyjmuje sam YAML albo caly blok markdown z ```yaml.

## Najwazniejszy Workflow Po Pracy

```powershell
.\.venv\Scripts\python.exe scripts\variant_b_daily_bot.py --season 2026 --week 1
```

Potem:

```text
1. Otwierasz raport daily_bot.
2. Wklejasz brakujace linie/GPT/quote do Codex.
3. Gdy raport wyglada sensownie, odpalasz z --execute.
4. Sprawdzasz summary Variant B.
```

## Test Week 1 Od Zera W GUI

W GUI sa dwa przyciski pomocnicze:

```text
Reset week test data
Week dry run Tue-Mon
```

`Reset week test data` usuwa tylko artefakty dla wybranego sezonu i tygodnia:

```text
research/daily_bot/{season}/week_XX
research/variant_b_week_flow/{season}/week_XX
research/gpt_snapshots/{season}/week_XX
data/learning_ledger/{season}/week_XX
data/book_snapshots/{season}/week_XX_screen_snapshot.yaml
data/market_quotes/{season}/week_XX.jsonl
data/picks_variant_m/{season}/week_XX.jsonl
config/lines/{season}/weekX_lines.yaml
```

Nie usuwa danych historycznych ani calego cache `nfl_data_py`.

`Week dry run Tue-Mon` odpala raporty dzienne od wtorku do poniedzialku bez wykonywania komend. Dla Week 1 wtorkowe zamkniecie poprzedniej kolejki powinno byc oznaczone jako `SKIPPED`, bo `previous_week=0`.

Testowy przebieg:

```text
1. Season = 2026, Week = 1.
2. Kliknij Reset week test data.
3. Wklej screeny/linie z pregame.com do GPT i popros o format YAML.
4. Wklej YAML do Codex, zeby zapisac book snapshot / quote snapshot.
5. W bocie wybierz Tuesday i kliknij Execute albo Dry run.
6. Kliknij Load model picks.
7. Dla kazdego VP/GOW/GOM/GOY wygeneruj prompt GPT, wklej wynik do GPT Paste i zapisz snapshot.
8. Kolejne dni rob tak samo: Wednesday, Thursday, Friday, Saturday, Sunday, Monday.
9. Do szybkiego sprawdzenia samego harmonogramu uzyj Week dry run Tue-Mon.
```

## Live Scenario W Centrum Dowodzenia

GUI ma panel `Live Scenario`.

Sluzy do odpalenia:

```text
scripts/live_quarter_scenario_matrix.py
```

Najwazniejsze pola:

```text
Start / End
- historyczny zakres sezonow, domyslnie 2016-2025

Path
- przebieg kwart z perspektywy Team A
- WIN = Team A wygral Q1
- WIN-LOSS = Team A wygral Q1, przegral Q2
- WIN-LOSS-WIN = Team A wygral Q1, przegral Q2, wygral Q3

Event
- TEAM_A_WIN_FINAL = Team A wygra caly mecz
- TEAM_A_WIN_NEXT_QUARTER = Team A wygra nastepna kwarte
- TEAM_A_LEAD_AFTER_NEXT_QUARTER = Team A bedzie prowadzic po nastepnej kwarcie

Live decimal / Live ML
- recznie wpisany kurs live, zeby policzyc EV
- wpisz jedno z dwoch: decimal albo moneyline

Sample
- LEAGUE_WIDE = cala liga
- TEAM_A_HISTORY = historia Team A
- TEAM_B_HISTORY = historia przeciwnika
- HEAD_TO_HEAD = bezposrednie mecze Team A vs Opponent
```

Przyciski:

```text
Run live lookup
- odpala lookup dla wpisanego Path/Event i pokazuje probability, fair odds oraz EV w Output

Rebuild live matrix
- przebudowuje historyczna macierz live scenario dla wybranych filtrow

Open live folder
- otwiera folder z plikami live scenario
```

Jesli najpierw wybierzesz mecz w `Model picks for selected week`, bot sam uzupelni w live scenario:

```text
Team A
Opponent
Role
Side
Spread bucket
Season phase
```

Live scenario nie pobiera live kursow i nie daje automatycznego picka. To jest narzedzie kontekstowe do reakcji live.
