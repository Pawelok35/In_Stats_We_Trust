# Artifact Policy

This project separates source-controlled inputs from generated pipeline outputs.

## Keep In Git

- Application, ETL, metrics, and utility code.
- Tests and small deterministic fixtures.
- Configuration that defines behavior, for example `config/settings.yaml`, contracts, rules, and line/config snapshots that are intentionally reviewed.
- Documentation and templates.
- `data/.gitkeep` so the local data directory exists after checkout.

## Keep Out Of Git

- Layer outputs: `data/l1`, `data/l2`, `data/l3_team_week`, `data/l4_core12`, `data/l4_powerscore`, and rolling snapshots.
- Generated reports: `data/reports`, including matchup reports and rendered assets.
- Pick outputs and variants: `data/picks`, `data/picks_variant_*`.
- Audits and internal run logs: `data/l2_audit`, `data/internal_checks`.
- Temporary downloads and unpacked source files: `data/tmp_*`, raw zip/xlsx/xml extracts.
- Result exports such as generated CSV/JSON/JSONL files under `data/results`.

## Exceptions

Small files needed by tests may be committed under one of these explicit fixture roots:

- `data/fixtures/`
- `data/samples/`

If a new fixture is added, it should be minimal, deterministic, and documented by the test that uses it.

## Current Repository Note

The `.gitignore` rules stop new generated artifacts from being added by accident. They do not hide files that are already tracked by git.

For a later cleanup pass, use a deliberate index-only removal such as:

```bash
git rm -r --cached data/reports data/picks data/picks_variant_* data/l2_audit data/internal_checks data/results
```

Run that only after deciding which historical artifacts should remain available elsewhere.

