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

## Validation Artifacts

Completed validation reports are stored under `docs/validation/` (e.g., `ISTW_T21_PASS.md`, `T32_ci_local.md`).

## Contributing

1. Fork & clone repo
2. Create feature branch
3. Run `scripts/precommit_check.ps1`
4. Submit PR with updated tests and documentation
