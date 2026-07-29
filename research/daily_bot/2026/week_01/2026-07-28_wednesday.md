# Variant B Daily Bot - 2026-07-28 wednesday

Season: `2026`
Week: `1`
Variant: `variant_m`
Mode: `EXECUTE`

Day plan: `Sroda - TNF delta refresh`

Objective:

```text
Sprawdzic zmiany pod TNF oraz zrobic pierwszy lekki monitoring Sunday/MNF.
```

## Tasks

| Status | Task | Type | Detail |
| --- | --- | --- | --- |
| SKIPPED | Aktualizuj quote dla TNF, jesli TNF jest kandydatem. | manual | `no_action_candidate_in_scope:tnf` |
| SKIPPED | Zlec GPT delta refresh dla TNF, jesli TNF jest kandydatem. | manual | `no_action_candidate_in_scope:tnf` |
| READY | Pierwszy lekki zrzut quote dla Sunday/MNF kandydatow. | manual | `data\book_snapshots\2026\week_01_screen_snapshot.yaml` |
| READY | Aktualizuj quote dla Sunday/MNF kandydatow, jesli linia sie zmienila. | manual | `data\market_quotes\2026\week_01.jsonl` |
| OPTIONAL | GPT delta dla Sunday/MNF tylko przy istotnej zmianie injury/line/weather/roster. | manual | `research/gpt_snapshots/2026/week_01/**/delta_*.md` |
| PASS | Odpal Variant B po srodowych zmianach. | command | `.\.venv\Scripts\python.exe scripts\variant_b_week_flow.py --season 2026 --week 1 --variant variant_m --with-model-proof --write-learning-ledger` |
| PASS | Sprawdz summary Variant B. | check_path | `research\variant_b_week_flow\2026\week_01\summary.md` |

## Next Manual Inputs

- Brak manualnych inputow oznaczonych jako missing.
