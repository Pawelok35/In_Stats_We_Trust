# In Stats We Trust

In Stats We Trust (ISTW) is a modular NFL analytics pipeline that ingests raw play data, normalizes it into layered parquet artifacts, computes core metrics, and publishes weekly summaries.

## Repository Layout

| Path | Description |
| --- | --- |
| `app/` | CLI, API, and reporting modules |
| `etl/` | Layered ETL stages (L1-L3) |
| `metrics/` | Post-ETL metric computations (Core12, PowerScore) |
| `utils/` | Shared utilities (config, paths, data helpers) |
| `data/` | Generated artifacts (parquet, manifests, reports) |
| `docs/validation/` | Validation logs per milestone |
| `scripts/` | Local CI helpers |
| `tests/` | Pytest-based coverage for key components |

```
                +--------------+
                |   Sources    |
                +------+-------+
                       |
                       v
                +--------------+
                |     L1       |
                | Raw ingest   |
                +------+-------+
                       |
                       v
                +--------------+
                |     L2       |
                | Clean + audit|
                +------+-------+
                       |
                       v
                +--------------+
                |     L3       |
                | Team-week    |
                +------+-------+
                       |
                       v
                +--------------+
                |     L4       |
                | Core12/PS    |
                +------+-------+
                       |
                       v
                +--------------+
                |   Reports    |
                +--------------+
```

## Quickstart

1. **Install dependencies**

   ```powershell
   python -m pip install -r requirements.txt
   ```

2. **Run the full weekly build**

   ```powershell
   python -m app.cli build-week --season 2025 --week 8
   ```

   This pipeline will:
   - Ingest raw files into `data/l1/...`
   - Normalize & audit `data/l2/...`
   - Aggregate `data/l3_team_week/...`
   - Generate `data/reports/{season}_w{week}_summary.md`

3. **Preview metrics**

   ```powershell
   python -c "import polars as pl; from metrics.core12 import compute; df=pl.read_parquet('data/l3_team_week/2025/8.parquet'); compute(df,2025,8)"
   python -c "import polars as pl; from metrics.power_score import compute; df=pl.read_parquet('data/l4_core12/2025/8.parquet'); compute(df,2025,8)"
   ```

4. **Serve the API (optional)**

   ```powershell
   uvicorn app.api:app --reload
   ```

   - `GET /health` ? `{ "status": "ok" }`
   - `GET /metrics/core12/preview?season=2025&week=8&n=10` ? Core12 snapshot

5. **Run local CI gate**

   ```powershell
   .\scripts\precommit_check.ps1
   # or (if make available)
   make check
   ```

## Data Sources

By default, ISTW uses the `nfl_data_py` provider defined in `config/settings.yaml` to fetch play-by-play data. To point the pipeline at local parquet/CSV sources instead, update the configuration:

```yaml
data_sources:
  provider: filesystem
  filesystem:
    l1_raw_dir: data/sources/nfl
```

Ensure the specified directory contains `{season}/{week}.parquet` files before running `build-week`.

## Configuration

- Settings live in `config/settings.yaml` (data root, source provider, weights).
- Paths resolved through `utils.paths.path_for(layer, season, week)`.
- CLI defaults read from config (`default_season`, `default_week`).

### Season-specific matchup line files

Matchup configs use `week*_lines.yaml`. To keep multiple seasons in one repo:

1. Place each season’s files under `config/lines/<season>/week<nr>_lines.yaml` (e.g., `config/lines/2025/week11_lines.yaml`).
2. `utils.paths.week_lines_path(season, week)` automatically picks the season-specific file and falls back to the legacy `config/week<nr>_lines.yaml` when the new location is missing, so old workflows keep working.
3. Runners such as `scripts/tag_variant_runner.py --season 2022 --regenerate ...` already rely on this helper—just copy the line files into the new folder structure for every season you import.

### Weekly pipeline helper

To trigger the full weekly workflow (schedule update → cumulative build → previews → matchup batch → pick regeneration) run:

```powershell
python scripts/run_week_pipeline.py `
  --season 2025 `
  --week 12 `
  --reference-week 4 `
  --run-convergence
```

Before running:

- `config/lines/<season>/week<week>_lines.yaml` — betting lines and report paths.
- `data/results/manual_results.jsonl` — up-to-date results (missing ones remain `PENDING`).
- Any pre-existing previews in `data/reports/comparisons/<season>_w<week>/...` can be replaced; the script regenerates them.
- Adjust `--picks-start-week` if you only want to refresh a partial season.

Adding `--run-convergence` executes `scripts/convergence_analyzer.py` on the freshly generated picks (`picks_variant_{j,c_psdiff,k}` on Weather Scale 2.0) and prints the recommendation table.

### Weather Scale summary

Once a week has been generated, you can print the forecast table directly from the pick files:

```powershell
python -X utf8 scripts\convergence_analyzer.py ^
  --variant-m data/picks_variant_m/2025/week_12.jsonl ^
  --variant-d data/picks_variant_d_balanced/2025/week_12.jsonl ^
  --variant-b data/picks_variant_b_edge_focus/2025/week_12.jsonl ^
  --week-label "Week 12" ^
  --weather-only
```

This produces the concise table:

```
**Weather Scale Picks:**
| Codename | Rating | Stake | Matchup | Models / direction |
|:-------- | ------:| -----:|:------- |:------------------ |
| Ultimate Supercell | - | - | BRAK | - |
| Supercell | 6.30 | 3.5u | BUF vs TB (→ BUF -5.5) | M:GOY->BUF | D:GOY->BUF | B:GOY->BUF |
| Supercell | 6.30 | 3.5u | TEN vs HOU (→ HOU -7.5) | M:GOY->HOU | D:GOY->HOU | B:GOY->HOU |
| Vortex    | 5.90 | 3.0u | LV vs DAL (→ DAL -3.5) | M:GOY->DAL | D:GOY->DAL | B:GOM->DAL |
| Gale      | 3.80 | 2.0u | PIT vs CIN (→ PIT -5.5) | M:GOM->PIT | D:GOM->PIT | B:GOW->PIT |
| Calm      | 1.70 | 1.0u | CLE vs BAL (→ BAL -8.5) | M:GOW->BAL | D:GOW->BAL | B:- |
```

Run the command with any season/week to inspect the recommendations or capture Ultimate Supercell signals.

## Running the weekly pipeline (upcoming week) with guardrails

python -X utf8 scripts/generate_weather_buckets.py `
  --season 2025 `
  --start-week 12 `
  --end-week 12 `
  --guardrails-mode v2_1 `
  --output data/results/weather_bucket_games.csv



### Running the weekly pipeline (upcoming week)

For an upcoming week that jeszcze się nie odbył (np. Week 12), bazujemy na metrykach do zakończonego tygodnia (Week 11), a linie/raporty bierzemy na tydzień nadchodzący (Week 12). Używaj referencji `week - 1`, żeby uniknąć future data leak:

np. Przed nami Week 12 (mecze sie jeszcze nie odbyły).
```powershell
python -X utf8 scripts\run_week_pipeline.py `
  --season 2025 `
  --week 12 `
  --reference-week 11 `
  --picks-start-week 12 `
  --run-convergence
```

Co to oznacza:
- `--week 12` – generujemy raporty/picki na tydzień 12.
- `--reference-week 11` – metryki rolling (Core12/PowerScore) liczymy na bazie danych do Week 11 (ostatni rozegrany tydzień).
- `--picks-start-week 12` – start generowania picków od tygodnia 12.
- `--run-convergence` – uruchamia analizę konwergencyjną wariantów picków.

Jeśli masz kompletne wyniki i metryki dla n+1 (czyli Week 12 po rozegraniu), wtedy referencja może równać się tygodniowi docelowemu. Dla tygodni nadchodzących trzymaj referencję na `week - 1`.

## Validation Artifacts

Completed validation reports are stored under `docs/validation/` (e.g., `ISTW_T21_PASS.md`, `T32_ci_local.md`).

## Contributing

1. Fork & clone repo
2. Create feature branch
3. Run `scripts/precommit_check.ps1`
4. Submit PR with updated tests and documentation



## Generowanie listy meczy na dany sezon i wybrane kolejki 
python -X utf8 scripts/generate_weather_buckets.py --season 2025 --start-week 2 --end-week 12 --output data/results/weather_bucket_games.csv

- Wybór innego sezonu
python -X utf8 scripts/generate_weather_buckets.py --season 2024 --start-week 2 --end-week 18 --output data/results/weather_bucket_games.csv


## Dla całego sezonu week 2 - week 18


2..18 | ForEach-Object {
  $w = $_
  python -X utf8 scripts/run_week_pipeline.py `
    --season 2022 `
    --week $w `
    --reference-week ($w-1) `
    --picks-start-week $w `
    --run-convergence
}



## INSTRUKCJA krok po kroku 
Przyklad gdy analizuje week13 

1) Aktualizuje 
  - terminarz w scripts/update_schedule.py ,
  - linie w config/lines/2025/week13_lines.yaml,
  - wyniki w data/results/manual_results.jsonl (tylko rozegrane mecze; reszta PENDING).

2) Pipeline na referencji poprzedniego tygodnia (12): 

python -X utf8 scripts/run_week_pipeline.py --season 2025 --week 13 --reference-week 12 --run-convergence

3) Buckety tylko dla week 13, dopisanie do istniejącego pliku (bez ruszania historii):

python -X utf8 scripts/generate_weather_buckets.py --season 2025 --start-week 13 --end-week 13 --guardrails-mode v2_1 --preserve-existing --output data/results/weather_bucket_games_season2025.csv



4) Podgląd w terminalu:

python scripts/show_weather_picks.py --season 2025 --week 13 --guardrails-mode v2_1



## KOMENDY LICZĄCE

1)  policzy średni rating wygranych/przegranych, profit per bucket i winrate per action na bazie Twojego pliku.

Profit per bucket:
Gale       21.20
Cyclone    13.25
Vortex      7.80
Calm        1.20
Breeze      0.90

Skutecznosc per rail_guard_action (% WIN):
DOWNGRADE TO BREEZE     100.0
DOWNGRADE TO CYCLONE    100.0
PROMOTE TO GALE         100.0
NO_CHANGE                78.3
DOWNGRADE TO GALE        50.0



python -X utf8 -c "import pandas as pd
from pathlib import Path
df = pd.read_csv('data/results/weather_bucket_games_season2025.csv')
df = df[df['result'].isin(['WIN','LOSS'])].copy()
df['pnl'] = df.apply(lambda r: 0.9*r['stake_u'] if r['result']=='WIN' else -1*r['stake_u'], axis=1)
print('Profit per bucket:')
print(df.groupby('bucket')['pnl'].sum().sort_values(ascending=False).round(2))
winrate = (df.assign(is_win=lambda d: d['result']=='WIN')
             .groupby('rail_guard_action')['is_win']
             .mean()
             .sort_values(ascending=False)
             .mul(100)
             .round(1))
print('\nSkutecznosc per rail_guard_action (% WIN):')
print(winrate)
"


2) Liczby (tylko WIN/LOSS):

PROMOTE TO GALE: 9 gier, 100.0% WIN
DOWNGRADE TO CYCLONE: 2 gier, 100.0% WIN
DOWNGRADE TO BREEZE: 1 gra, 100.0% WIN
NO_CHANGE: 23 gier, 78.3% WIN
DOWNGRADE TO GALE: 4 gier, 50.0% WIN


python -X utf8 -c "import pandas as pd
df = pd.read_csv('data/results/weather_bucket_games_season2025.csv')
df = df[df['result'].isin(['WIN','LOSS'])].copy()
df['is_win'] = df['result']=='WIN'
counts = df.groupby('rail_guard_action').agg(games=('is_win','size'), winrate=('is_win','mean'))
counts = counts.sort_values(by='winrate', ascending=False)
print(counts.assign(winrate=lambda d: (d['winrate']*100).round(1)))"

