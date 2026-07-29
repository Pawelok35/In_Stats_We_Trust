# CLI Workflow

`python -m app.cli` is the canonical entrypoint for project workflows.

Scripts under `scripts/` may still exist as implementation helpers or developer tools, but routine usage should go through the CLI commands below.

## Core Commands

Build one completed week through L1-L4 and the weekly report:

```powershell
python -m app.cli build-week --season 2025 --week 8
```

Run the full weekly workflow for an upcoming or active slate:

```powershell
python -m app.cli weekly-pipeline `
  --season 2025 `
  --week 12 `
  --reference-week 11 `
  --picks-start-week 12 `
  --run-convergence
```

Generate matchup preview reports for a target week:

```powershell
python -m app.cli generate-matchups `
  --season 2025 `
  --week 12 `
  --reference-week 11
```

Evaluate pick results:

```powershell
python -m app.cli evaluate-picks `
  --season 2025 `
  --from-week 2 `
  --to-week 12 `
  --manual-results data/results/manual_results.jsonl
```

Evaluate active champion/challenger variants:

```powershell
python -m app.cli evaluate-variants `
  --season 2025 `
  --start-week 2 `
  --end-week 12 `
  --manual-results data/results/manual_results.jsonl
```

## Script Status

The CLI delegates workflow commands to importable workflow modules:

- `weekly-pipeline` delegates to `app.workflows.run_week_pipeline`.
- `generate-matchups` delegates to `app.workflows.generate_matchup_previews`.
- `evaluate-variants` delegates to `app.workflows.tag_variant_runner`.

Compatibility wrappers remain in `scripts/` so older commands continue to work.
