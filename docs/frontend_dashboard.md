# Frontend Operational Dashboard

Point 7 turns the frontend into an operational dashboard backed by pipeline artifacts.

## Added Data Source

The frontend now exposes:

```text
GET /api/picks?season=<season>&week=<week>
```

It reads pick JSONL files from configured variant directories and enriches each row with:

- variant name,
- variant status,
- matchup,
- tag,
- model pick,
- confidence,
- edge vs line,
- decision label,
- version metadata when present.

## Added View

The dashboard now includes an operational pick queue:

- filters by variant lifecycle status,
- filters by decision (`bet`, `lean`, `avoid`, `no bet`),
- shows active variant count,
- shows bet/lean counts,
- displays model version and commit when present,
- opens the matchup report when a pick row is selected.

## Decision Labels

Current decision mapping:

- `GOY`, `GOM` -> `bet`
- `GOW`, `VALUE PLAY` -> `lean`
- high confidence and large edge -> `lean`
- `NEUTRAL` -> `avoid`
- fallback -> `no bet`

This is intentionally simple and should later be replaced with a shared rule/config from the model layer.

## Commands

From `frontend/`:

```powershell
npm run lint
npm run build
npm run dev -- --port 3000
```

Dashboard URL:

```text
http://localhost:3000/dashboard
```

