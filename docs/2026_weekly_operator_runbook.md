# NFL 2026 Weekly Operator Runbook

## Scope

This is the central pregame ledger workflow. It uses the append-only JSONL
event store and the existing domain services. It does not place wagers, fetch
executable sportsbook quotes, invent injuries, or create production results.

The financial contract for new executions is:

```text
AMERICAN_ODDS_RISK_BASED_V1
stake_units = amount risked
```

CLV is an operator-designated same-book closing benchmark, not a global market
close or a consensus line.

## Requirements

From the repository root:

```powershell
.\.venv\Scripts\Activate.ps1
.\.venv\Scripts\python.exe -m pytest -q
```

The event store defaults to:

```text
data/pregame/events/<season>/week_<WW>.jsonl
```

Reports default to:

```text
data/pregame/reports/<season>/week_<WW>.json
data/pregame/reports/<season>/week_<WW>.md
```

The equivalent PowerShell launcher is:

```powershell
.\scripts\Start-Pregame2026.ps1 -Season 2026 -Week 1 -Command status
```

## Weekly sequence

### 1. Initialize

```powershell
python -m pregame.weekly_cli --season 2026 --week 1 init-week
```

This only creates the event-store directory and reports the current state.

### 2. Register schedule games

Prepare a JSON array and import it:

```json
[
  {
    "game_id": "2026_w01_BUF_at_HOU",
    "season": 2026,
    "week": 1,
    "away_team": "BUF",
    "home_team": "HOU",
    "kickoff_utc": "2026-09-10T18:00:00Z",
    "neutral_site": false,
    "source": "NFL_SCHEDULE"
  }
]
```

```powershell
python -m pregame.weekly_cli --season 2026 --week 1 --input games.json import-games
```

### 3. Import candidates and market snapshots

Use the exact serialized `CandidateRecord` objects from the model output and
`MarketSnapshot` objects from the manually captured quote. The CLI validates
them through the existing registry services:

```powershell
python -m pregame.weekly_cli --season 2026 --week 1 --input candidates.json import-candidates
python -m pregame.weekly_cli --season 2026 --week 1 --input market_snapshots.json import-market-snapshots
```

Do not put a closing quote into the execution input. Closing is linked later by
its explicit `closing_snapshot_id`.

### 4. Structured research and audit

The `build-audits` input points to an existing structured GPT evidence sidecar,
rules file, and already registered evidence-lineage manifest. No missing source
or price is reconstructed:

```json
[
  {
    "candidate_id": "candidate-id",
    "model_generation_snapshot_id": "gpt-snapshot-id",
    "evidence_path": "research/evidence/game.json",
    "manifest_id": "variant-b-evidence-lineage-id",
    "rules_path": "config/variant_b_rules.yaml",
    "build_timestamp_utc": "2026-09-09T18:00:00Z",
    "output_path": "research/audits/game.json",
    "recorded_at_utc": "2026-09-09T18:01:00Z"
  }
]
```

Register a manifest first when needed:

```powershell
python -m pregame.weekly_cli --season 2026 --week 1 --input lineage.json register-lineage
python -m pregame.weekly_cli --season 2026 --week 1 --input audits.json build-audits
```

### 5. Operator decision and execution

Decision input must reference the existing gate evaluation. The operator, not
the CLI, supplies verdict and stake:

```powershell
python -m pregame.weekly_cli --season 2026 --week 1 --input decisions.json register-decisions
python -m pregame.weekly_cli --season 2026 --week 1 --input executions.json record-executions
```

New executions receive the fixed V1 financial terms from the service. The
caller cannot override that version. Existing unversioned historical events
remain replayable but are not centrally settled.

### 6. Closing, result and settlement

Link the exact same-book closing snapshot:

```powershell
python -m pregame.weekly_cli --season 2026 --week 1 --input closing_links.json link-closing
```

After the authoritative source finalizes the game, import a result with source
and provenance. Never use `GAME_SETTLED` or a local score as a substitute:

```powershell
python -m pregame.weekly_cli --season 2026 --week 1 --input results.json import-results
python -m pregame.weekly_cli --season 2026 --week 1 settle-ready
python -m pregame.weekly_cli --season 2026 --week 1 calculate-clv-ready
```

Settlement uses only `AUTHORITATIVE_GAME_RESULT_RECORDED`. CLV does not require
a result or settlement, but does require the immutable execution and explicit
same-book closing link.

### 7. Status, resume and report

```powershell
python -m pregame.weekly_cli --season 2026 --week 1 status
python -m pregame.weekly_cli --season 2026 --week 1 run-ready
python -m pregame.weekly_cli --season 2026 --week 1 report
```

`run-ready` is safe to repeat. It processes only records with all required
authorities and leaves pending records with a next action. A blocked record
does not stop valid records from being processed. Exit code `0` means no
blocked/conflicting record was returned; `1` means partial/blocked work; `2`
means a system or input error.

## GUI

Start the existing operator GUI with:

```powershell
.\scripts\Start-VariantBDailyBotGui.ps1
```

The **Centralny ledger pregame** panel reads `status` and opens the Markdown
report through the same central CLI. Existing GPT, quote, model-pick and Live
Scenario controls remain separate. The GUI does not duplicate settlement or CLV
logic.

## Simulation versus production

The Week 1 end-to-end fixture uses `SIMULATION_FIXTURE_ONLY` and lives only in
tests. It must never be copied into production event data. Production results
must come from an authoritative gamebook or another explicitly approved source.

## Conflicts and backups

An identical retry returns `ALREADY_EXISTS` and does not append a duplicate.
A different payload with the same deterministic event ID returns `CONFLICT`.
Do not overwrite JSONL lines. Before maintenance, copy the event store and
verify the copy can be replayed with `status` and `report`.

## Product limitations

This release does not provide paid odds feeds, automated injury/public betting
feeds, automated market discovery, live execution, moneyline/totals/props
settlement, cross-book CLV, consensus closing lines, corrections/reversals,
bankroll or real-money account integration.
