# ðŸˆ NFL System Start

To jest szybki panel startowy. Tu masz krotko, z czego mozemy korzystac i kiedy.

## 0. Diagram Week 1 Workflow

Dokladny diagram pracy od tygodnia przed pierwszym kickoffem:

```text
docs/week1_pregame_workflow_diagram.md
```

## 0A. Daily Bot

Codzienny bot checklisty i komend:

```powershell
.\.venv\Scripts\python.exe scripts\variant_b_daily_bot.py --season 2026 --week 1
```

Wersja w osobnym oknie:

```powershell
.\scripts\Start-VariantBDailyBotGui.ps1
```

Instrukcja:

```text
docs/variant_b_daily_bot.md
```

## 1. Basic Model

Cel:

```text
automatycznie przeskanowac kolejke i znalezc: VALUE PLAY / GOW / GOM / GOY
```

Uzywasz, gdy chcesz sprawdzic, czy w kolejce w ogole jest cos wartego dalszej analizy.

Kolejnosc:

```powershell
.\.venv\Scripts\python.exe -m app.cli sync-nfl-schedule --season 2026
.\.venv\Scripts\python.exe -m app.cli export-lines-from-nfl --season 2026 --week 1
.\.venv\Scripts\python.exe scripts\prospective_week_flow.py --season 2026 --week 1 --variant variant_m --skip-freeze
```

Wynik:

```text
data/picks_variant_m/2026/week_01.jsonl
```

Szukasz tylko:

```text
VALUE PLAY
GOW
GOM
GOY
```

Jesli wszystko jest `NEUTRAL`, nie robimy glebszego audytu.

## 2. Basic Model + Variant B / 19 Punktow GPT

Cel:

```text
sprawdzic, czy kandydat z modelu ma realny, udokumentowany edge
```

Uzywasz tylko dla meczow, ktore basic model oznaczyl jako:

```text
VALUE PLAY / GOW / GOM / GOY
```

Komenda:

```powershell
.\.venv\Scripts\python.exe scripts\variant_b_week_flow.py --season 2026 --week 1 --variant variant_m --with-model-proof
```

Wynik:

```text
research/variant_b_week_flow/2026/week_01/summary.md
```

Do GPT wysylasz:

```text
docs/variant_b_final_gpt_research_prompt.md
docs/variant_b_gpt_short_wrapper.md
```

Reczny quote z booka wpisujesz tutaj:

```text
data/market_quotes/2026/week_01.jsonl
```

Ten etap sprawdza m.in.:

```text
p_cover / p_push / p_loss
market move
injuries
schedule spot
weather
public bias
roster changes
matchup risk
game script risk
price quality
process quality
final operator decision
```

Werdykt roboczy:

```text
PASS / WATCH / HOLD / NO BET
```

Glowna instrukcja:

```text
docs/variant_b_orchestrator.md
```

## 3. Live Scenario

Cel:

```text
w trakcie meczu sprawdzic historyczne scenariusze po Q1 / H1 / Q3
```

Uzywasz, gdy chcesz wiedziec np.:

```text
Team A wygrala Q1 i przegrala Q2.
Jak czesto wygrywala mecz?
Jaki jest minimalny kurs live do EV+?
```

Glowna komenda:

```powershell
.\.venv\Scripts\python.exe scripts\live_quarter_scenario_matrix.py --start-season 2016 --end-season 2025
```

Lookup przykladowego scenariusza:

```powershell
.\.venv\Scripts\python.exe scripts\live_quarter_scenario_matrix.py --start-season 2016 --end-season 2025 --lookup-path WIN-LOSS --event TEAM_A_WIN_FINAL --live-decimal 1.90
```

Wynik:

```text
research/live_quarter_scenario_matrix/2016_2025_league_wide/
```

Najwazniejsze pliki:

```text
scenario_lookup.json
quarter_transition_matrix.csv
full_quarter_path_matrix.csv
margin_bucket_matrix.csv
segment_transition_matrix.csv
```

Instrukcja:

```text
docs/live_quarter_scenario_matrix.md
```

## 4. Model Uczacy Sie - Roadmap

Cel:

```text
docelowo zbudowac kontrolowany system, ktory uczy sie na kolejnych meczach
```

To nie jest model, ktory sam zmienia zasady.

To system:

```text
snapshot danych -> predykcja -> audyt -> wynik -> ewaluacja -> candidate model -> test -> promocja albo odrzucenie
```

Roadmap:

```text
docs/variant_b_learning_model_roadmap.md
```

Kontrakt danych:

```text
docs/model_learning_data_contract.md
```

Append-only ledger:

```powershell
.\.venv\Scripts\python.exe scripts\variant_b_learning_ledger.py --season 2026 --week 1
```

Albo razem z Variant B:

```powershell
.\.venv\Scripts\python.exe scripts\variant_b_week_flow.py --season 2026 --week 1 --variant variant_m --with-model-proof --write-learning-ledger
```

Post-event evaluation:

```powershell
.\.venv\Scripts\python.exe scripts\variant_b_post_event_evaluation.py --season 2026 --week 1
```

Learning report:

```powershell
.\.venv\Scripts\python.exe scripts\variant_b_learning_report.py
```

## Najprostszy Workflow Tygodnia

Wtorek:

```text
1. Pobierz schedule i linie z nfl_data_py.
2. Odpal basic model.
3. Sprawdz, czy sa VP/GOW/GOM/GOY.
4. Jesli sa, robimy Variant B + GPT 19 punktow.
```

Sroda / piatek / sobota:

```text
delta refresh: injuries, weather, line, quote, roster
```

Czwartek / niedziela / poniedzialek:

```text
final check kilka godzin przed kickoffem
```

W trakcie meczu:

```text
Live Scenario po Q1 / H1 / Q3
```

Po meczu:

```text
wynik, closing line, CLV, review procesu
```

## Co Jest Najwazniejsze

```text
Basic model znajduje kandydatow.
Variant B sprawdza, czy kandydat ma dowod.
GPT zbiera research, ale nie liczy EV.
Quote z booka wpisujemy recznie.
Live Scenario pomaga w trakcie meczu, ale sam nie daje finalnego betu.
Ledger i review sa podstawa modelu uczacego sie.
```
