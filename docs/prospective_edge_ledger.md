# Prospective Edge Ledger

This is the current operating instruction for turning model picks into forward edge evidence.

The goal is not to prove edge from a historical backtest. The goal is to freeze picks before games, with an auditable market snapshot, then settle only those frozen records.

## Current Status

Working pieces:

- proof-ready line validation;
- manual line/price timestamp stamping;
- matchup preview generation;
- variant pick generation;
- append-only prospective freeze;
- weekly settlement;
- YTD prospective report;
- active ledger compaction with archive.

Current 2026 Week 1 state:

- `config/lines/2026/week1_lines.yaml` is proof-ready;
- `data/picks_variant_m/2026/week_01.jsonl` exists;
- `data/prospective_ledger/2026/week_01_prospective.jsonl` has 16 active proof-qualified records;
- `data/prospective_ledger/2026/prospective_ytd_report.md` tracks 16 pending picks.

## Main Weekly Command

Use this after the weekly line YAML has been filled with proof fields:

```powershell
.\.venv\Scripts\python.exe scripts\prospective_week_flow.py `
  --season 2026 `
  --week 2 `
  --variant variant_m `
  --operator daniel
```

For Week 1 / preseason previews, use prior-season metrics explicitly:

```powershell
.\.venv\Scripts\python.exe scripts\prospective_week_flow.py `
  --season 2026 `
  --week 1 `
  --variant variant_m `
  --operator daniel `
  --metrics-season 2025 `
  --reference-week 18 `
  --preseason-seed-source data\rolling_core12\2025\through_18.parquet `
  --preseason-seed-destination data\rolling_core12\2026\through_1.parquet
```

The flow runs:

1. validate proof-ready lines;
2. optionally seed preseason rolling snapshot;
3. generate matchup previews;
4. generate picks;
5. freeze picks to prospective ledger;
6. refresh YTD report.

## Manual Market Snapshot Standard

Before running the weekly flow, every matchup in `config/lines/{season}/week{week}_lines.yaml` must include:

```yaml
- report: data/reports/comparisons/2026_w2/BAL_vs_CLE.md
  home: BAL
  away: CLE
  spread: -3.5
  total: 44.5
  market: spread
  line: -3.5
  book: MANUAL_MULTI_BOOK
  price: -110
  decision_ts_utc: "2026-09-10T15:00:00Z"
  odds_source: manual_snapshot
  odds_snapshot_type: decision
```

Use `MANUAL_MULTI_BOOK` when you manually checked several books and selected a representative line/price. Use `MANUAL_CONSENSUS` only for weaker consensus/manual config lines.

Optional stronger snapshot format:

```yaml
market_snapshot:
  reference_type: median_available
  captured_by: Daniel
  captured_at_utc: "2026-09-10T15:00:00Z"
  books:
    - book: DraftKings
      line: -3.5
      price: -110
    - book: FanDuel
      line: -3.5
      price: -108
    - book: BetMGM
      line: -4.0
      price: -105
  selected_line: -3.5
  selected_price: -110
  available_books: 3
  price_quality_tier: 3
```

The current freeze logic uses the top-level `line`, `price`, `book`, and `decision_ts_utc`. The nested `market_snapshot` is audit context.

## Process Discipline Layer

Every pick should start from our own fair line, then compare that fair line with the available market. The ledger now writes a `process_snapshot` into each frozen record, so postgame review can separate decision quality from result variance.

Recommended pick fields:

```json
{
  "model_margin": 2.0,
  "market_margin": -3.0,
  "edge_vs_line": 5.0,
  "argument_against": "Injury downgrade on OL could make pressure rate assumption too optimistic.",
  "market_move_notes": "Opened -2.5, current -3.0; no chase above key number without recheck.",
  "injury_role_notes": "Track starting LT and CB1; downgrade if either inactive.",
  "schedule_spot_notes": "Short rest for opponent, no travel penalty.",
  "weather_notes": "No material wind/rain issue expected.",
  "closing_line": null,
  "closing_price": null,
  "clv_points": null
}
```

Process quality labels in settlement:

- `complete_with_clv`: fair line, market line, price, timestamp, argument against, and closing line are present.
- `complete_pre_kick`: complete pregame decision record, but no closing line yet.
- `basic_price_proof`: fair line, market line, price, and timestamp are present.
- `result_only`: record can be settled, but process review is weak.
- `legacy_no_process_snapshot`: older ledger record frozen before this layer existed.

Rules:

- Write our fair/model line before treating market movement as useful information.
- Do not chase a move unless the remaining line still clears the fair-line edge.
- `PASS` is a valid output when price moved through the acceptable limit.
- Every real bet needs one argument against the pick before freeze.
- `TODO:` placeholders in line YAML are treated as empty and do not improve process quality.
- Postgame review should mark whether the process was good, bad, incomplete, or merely unlucky. The game result alone is not enough.
- CLV is optional for now because the book input is manual, but when closing data is available, write `closing_line`, `closing_price`, and/or explicit `clv_points`.

## Proof Qualification

A frozen record is `proof_qualified=true` when the pick has:

- `season`
- `week`
- `home`
- `away`
- `tag`
- `model_winner`
- `confidence`
- `handicap`
- `market`
- `line`
- `price`
- `book`
- `decision_ts_utc`
- `model_version`
- `commit_sha`

`code_is_dirty=true` is no longer a disqualification by itself. It is written as an `integrity_warnings` item, because this repo can have unrelated working-tree changes. For strongest reproducibility, run from a clean commit before freezing.

Records missing proof fields are still frozen, but `proof_qualified=false` and `disqualification_reasons` explains why.

## Useful Commands

Validate a line file:

```powershell
.\.venv\Scripts\python.exe scripts\validate_proof_ready_lines.py `
  --config config\lines\2026\week2_lines.yaml `
  --fail-on-not-ready
```

Stamp a line file with a manual snapshot when needed:

```powershell
.\.venv\Scripts\python.exe scripts\stamp_proof_ready_lines.py `
  --config config\lines\2026\week2_lines.yaml `
  --book MANUAL_MULTI_BOOK `
  --price -110 `
  --odds-source manual_snapshot
```

Freeze an already generated pick file:

```powershell
.\.venv\Scripts\python.exe scripts\freeze_prospective_picks.py `
  --source data\picks_variant_m\2026\week_02.jsonl `
  --operator daniel
```

Refresh settlement and YTD:

```powershell
.\.venv\Scripts\python.exe scripts\update_prospective_ytd_report.py --season 2026
```

Compact an active ledger after a bad demo/freeze attempt:

```powershell
.\.venv\Scripts\python.exe scripts\compact_prospective_ledger.py `
  --ledger data\prospective_ledger\2026\week_01_prospective.jsonl
```

Compaction archives the original ledger before rewriting the active ledger.

## Outputs

Per week:

```text
data/prospective_ledger/{season}/week_{week}_prospective.jsonl
data/prospective_ledger/{season}/week_{week}_manifest.json
data/prospective_ledger/{season}/week_{week}_prospective_settlement.md
```

Season YTD:

```text
data/prospective_ledger/{season}/prospective_ytd_report.md
```

Validation:

```text
data/proof_ready_checks/{season}/week_{week}_lines_check.md
```

## Interpretation Rules

- Historical backtests are research screens, not proof.
- Prospective records count only if `proof_qualified=true`.
- Pending records are expected before results are available.
- `MANUAL_CONSENSUS` is weaker than `MANUAL_MULTI_BOOK`.
- `basic_price_proof` is useful, but the target standard is at least `complete_pre_kick`.
- Positive YTD is not final until all pending picks settle.
- The strongest future version is an API-backed multi-book snapshot, but manual multi-book entry is acceptable if timestamped and not edited after freeze.
