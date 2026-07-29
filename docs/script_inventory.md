# Script Inventory

Scripts are classified by operational role. Routine usage should prefer `python -m app.cli`.

## Importable Workflow Entrypoints

These modules are the canonical homes for workflow logic:

- `app/workflows/run_week_pipeline.py`
- `app/workflows/generate_matchup_previews.py`
- `app/workflows/tag_variant_runner.py`

## Compatibility Wrappers

These script paths are kept so old commands continue to work:

- `scripts/run_week_pipeline.py`
- `scripts/generate_matchup_previews.py`
- `scripts/tag_variant_runner.py`

## Canonical CLI Delegates

These are still called by workflow modules and should not be moved without wrappers:

- `scripts/matchup_batch.py`
- `scripts/update_schedule.py`
- `scripts/convergence_analyzer.py`

## Analysis And Reporting Helpers

- `scripts/matchup_analyzer.py`
- `scripts/generate_weather_buckets.py`
- `scripts/show_weather_picks.py`
- `scripts/build_match_card.py`
- `scripts/bucket_summary.py`
- `scripts/bucket_split_summary.py`
- `scripts/pick_variant_split_summary.py`
- `scripts/export_weather_scale.py`
- `scripts/export_pick_outcomes.py`
- `scripts/export_model_matrix.py`

## Maintenance And Backfill

- `scripts/backfill_metrics.py`
- `scripts/recompute_l4_from_l3.py`
- `scripts/patch_week8_aliases.py`
- `scripts/seed_schedule_w9.py`
- `scripts/Update-FinishedWeek.ps1`

## QA

- `scripts/precommit_check.ps1`
- `scripts/verify_repo.ps1`
- `scripts/verify_metrics_v3.ps1`

## Legacy Compatibility

- `verify_metrics_v3.ps1` at repo root delegates to `scripts/verify_metrics_v3.ps1`.

## Candidate Future Moves

After the CLI surface is stable, more script internals can be moved into importable modules and the old script files can remain as thin wrappers.
