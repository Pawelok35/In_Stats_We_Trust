# Repository Structure

This is the intended structure for In Stats We Trust.

## Runtime Code

- `app/` - CLI, API, report generation, dashboard helpers.
- `app/workflows/` - importable workflow entrypoints used by CLI.
- `etl/` - L1-L3 data pipeline.
- `metrics/` - Core12, PowerScore, backtesting, variants, similarity.
- `utils/` - shared configuration, paths, contracts, guards, manifests, metadata.
- `templates/` - report templates.
- `frontend/` - Next.js dashboard.

## Configuration

- `config/settings.yaml` - runtime settings.
- `config/contracts.yaml` - schema contracts.
- `config/tag_variants.yaml` - variant registry.
- `config/tag_rules/` - variant rule files.
- `config/lines/<season>/` - season/week line inputs.

## Operations

- `python -m app.cli` is the canonical operational entrypoint.
- `scripts/` contains compatibility wrappers, maintenance scripts, and developer helpers.
- Root-level `verify_metrics_v3.ps1` is a compatibility wrapper for `scripts/verify_metrics_v3.ps1`.

## Documentation

- `docs/decision_guide.md` is the starting point.
- `docs/README.md` is the documentation index.
- `docs/script_inventory.md` classifies scripts by role.

## Generated Artifacts

- `data/` is generated output and local runtime data.
- New generated artifacts under `data/` are ignored by git.
- Small committed fixtures should live under `data/fixtures/` or `data/samples/`.

## Cleanup Rule

Do not move runtime files unless either:

- all callers are updated and tested, or
- the old path remains as a compatibility wrapper.
