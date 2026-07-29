# NCAAF Research

Separate research area for testing whether the current NFL ATS champion idea can be
ported to college football.

This folder is intentionally isolated from the NFL pipeline. Do not write NCAAF
artifacts into the existing `data/`, `etl/`, or `metrics/` contracts until the data
source and schema are validated.

## Current NFL Benchmark

Champion reference:

- variant: `variant_d_balanced`
- tag: `GOM`
- confidence: `>= 85`
- edge_vs_line: `>= 4`
- week: `>= 3`
- abs(handicap): `<= 7`

NFL benchmark, seasons 2017-2025:

- Bets: 74
- W-L-P: 61-12-1
- Profit: +128.7u
- ROI: 58.0%
- Worst season: +2.1u
- Max drawdown: -6.3u

## NCAAF Caveat

This rule cannot be copied 1:1 into NCAAF without rebuilding the upstream model.
College football has larger team count, wider strength gaps, conference/FCS effects,
neutral sites, roster volatility, bowls, opt-outs, and less uniform market coverage.

The first goal is not to backtest the rule immediately. The first goal is to verify
whether we can reliably obtain:

- schedules and final scores,
- betting lines/spreads/totals,
- play-by-play or advanced stats available before each game,
- enough history for leakage-safe rolling features.

## Data Source

Primary candidate:

- CollegeFootballData API
- Python access via direct HTTP or the official `cfbd` client

Required environment variable:

```powershell
$env:CFBD_API_KEY = "your_api_key"
```

## First Probe

Run:

```powershell
.venv\Scripts\python.exe ncaaf_research\scripts\cfbd_probe.py --year 2025 --week 1
```

The probe checks:

- `/games`
- `/lines`
- `/plays`

It writes small JSON samples under `ncaaf_research/data/probe/` when the API key is
available.

## Research Plan

1. Verify CFBD access and field availability.
2. Save raw samples for one season/week.
3. Define NCAAF-specific L1 schema.
4. Map schedule, lines, results, teams, and plays.
5. Build leakage-safe weekly features.
6. Create NCAAF-specific pick model.
7. Only then compare a GOM-like rule against the NFL champion benchmark.
