# Reports Pipeline Reference

This guide explains how to run the reporting commands, understand the artefacts they generate, and troubleshoot common hiccups. All commands are intended to be executed from the repository root with the project virtual environment activated (`.venv\Scripts\Activate.ps1` on Windows).

---

## CLI Usage

| Command | Purpose |
| ------- | ------- |
| `python -m app.cli build-week --season 2025 --week 8` | Runs the full ETL, renders the weekly markdown report, and refreshes manifests. |
| `python -m app.cli team-report --season 2025 --week 8 --team BAL` | Produces a single team report (markdown + charts). |
| `python -m app.cli compare-report --season 2025 --week 8 --team-a BAL --team-b MIA` | Builds a specific matchup report. |
| `python -m app.cli build-weekly-reports --season 2025 --week 8` | Batch generates all available team reports and the weekly summary roll-up. |
| `python -m app.cli build-weekly-reports --season 2025 --week 8 --pairs-only` | Generates only matchup reports based on the schedule (skips teams). |

Each command logs progress and exits with a non-zero status on failure, so they can be chained inside scripts or CI jobs.

> Schedule validation: both `build-week` and `build-weekly-reports` now fail fast when the matchup
> schedule (`data/schedules/<season>.parquet`) is missing or references teams without computed
> metrics for the requested week. If you need to bypass the check for ad-hoc debugging, append
> `--no-require-complete-schedule`.

---

## Output Structure

After running `build-week` and `build-weekly-reports`, the key directories look like this (for `season=2025`, `week=8`):

```
data/
  l1/2025/8.parquet                 # raw ingest (manifest alongside)
  l2/2025/8.parquet                 # cleaned layer + audit JSONL
  l3_team_week/2025/8.parquet       # aggregate ETL output
  l4_core12/2025/8.parquet          # metrics preview
  l4_powerscore/2025/8.parquet      # PowerScore metrics
  reports/
    2025_w8_summary.md              # weekly markdown report (manifest in the same folder)
    2025_w8/                        # summary bundle, weekly_summary.md + assets/
    teams/2025_w8/                  # per-team markdown + PNG charts + manifest.json
    comparisons/2025_w8/            # matchup markdown + PNG charts + manifest.json (when schedule available)
```

Every parquet has a `*_manifest.json` with SHA-256, row/column counts, and timestamps. Report bundles also maintain manifests covering their markdown files and chart assets.

---

## Troubleshooting Checklist

1. **Missing data or schedule**: ensure `data/sources/nfl/<season>/<week>.parquet` (or the configured provider) exists, and add `data/schedules/<season>.parquet` before running matchup commands. The CLI reports the exact teams that are missing if the schedule is incomplete.
2. **Charts not rendering**: confirm `matplotlib` is installed in `.venv` and that PNGs appear under `data/reports/teams/<season>_w<week>/assets/<TEAM>/`.
3. **Empty summary or reports**: rerun `python -m app.cli build-week` followed by `python -m app.cli build-weekly-reports` to repopulate manifests and markdown.
4. **CI failures**: run `.\scripts\verify_repo.ps1` locally. The script now includes a `== Reports QA ==` section that validates manifests, counts team reports, and checks for charts.

---

## Example Workflows

1. **Standard build**  
   ```powershell
   python -m app.cli build-week --season 2025 --week 8
   python -m app.cli build-weekly-reports --season 2025 --week 8
   ```
   After completion you should see:
   - `data/reports/2025_w8_summary.md` with links to artefacts.
   - `data/reports/teams/2025_w8/BAL.md` (and other teams) with embedded charts.

2. **Matchup-focused batch (schedule required)**  
   ```powershell
   python -m app.cli build-week --season 2025 --week 9
   python -m app.cli build-weekly-reports --season 2025 --week 9 --pairs-only
   ```
   Expected outputs:
   - `data/reports/comparisons/2025_w9/<TEAM>_vs_<TEAM>.md` tables and edge summaries.
   - Updated manifests and `weekly_summary.md` linking to the generated comparisons.

> Tip: rerun `.\scripts\verify_repo.ps1` after making changes so the full QA script passes before CI.
---

## Automated Weekly Update

For routine Tuesday updates you can rely on the helper script:

```powershell
.\scripts\Update-FinishedWeek.ps1            # Detects season/week automatically
.\scripts\Update-FinishedWeek.ps1 -PairsOnly # Only matchup reports
.\scripts\Update-FinishedWeek.ps1 -Season 2025
```

The script finds the most recent completed week (prefers schedule data, falls back to existing L2 artefacts), runs `build-week`, and then executes `build-weekly-reports` with the optional `--pairs-only` flag. On success you should see refreshed L1->L4 parquet outputs, team/matchup reports, manifests, and `weekly_summary.md`.

---

Screenshots of generated charts typically live in the `assets` subdirectories. Attach them to documentation or dashboards by referencing their relative paths (e.g. `data/reports/teams/2025_w8/assets/BAL/bal_metrics.png`).

