# Variant Policy

Pick variants are managed through `config/tag_variants.yaml`.

## Statuses

- `champion`: the current production/default variant. Exactly one variant should have this status.
- `challenger`: active contender evaluated alongside the champion.
- `experimental`: research variant that is available, but not part of the default weekly run.
- `retired`: historical variant kept for reference only.

## Current Working Selection

- Champion: `variant_j`
- Challengers: `variant_b_edge_focus`, `variant_c_psdiff`, `variant_d_balanced`, `variant_k`, `variant_m`
- Retired: `variant_e_loose`
- Experimental: baseline plus remaining variants

This selection keeps the existing convergence workflow intact because it expects `variant_j`, `variant_c_psdiff`, and `variant_k`.

## Runner Defaults

The canonical command defaults to active variants only:

```powershell
python -m app.cli evaluate-variants --season 2025 --start-week 2 --end-week 12
```

To include research variants:

```powershell
python -m app.cli evaluate-variants `
  --season 2025 `
  --start-week 2 `
  --end-week 12 `
  --status experimental
```

To run a named variant:

```powershell
python -m app.cli evaluate-variants `
  --season 2025 `
  --start-week 2 `
  --end-week 12 `
  --variant variant_o
```

## Promotion Rule

A challenger should only replace the champion after a documented comparison over a meaningful sample. Minimum comparison fields:

- weeks evaluated,
- number of graded picks,
- units,
- ROI,
- win rate,
- confidence bucket behavior,
- notes on pending or missing results.
