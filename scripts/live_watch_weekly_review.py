from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


PLAY_DECISIONS = {"PLAY_ML", "STRONG_PLAY_ML"}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise SystemExit(f"Settled live watch file not found: {path}")
    records = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise SystemExit(f"Invalid JSONL at {path}:{line_number}: {exc}") from exc
    return records


def model_source(record: dict[str, Any]) -> str:
    return str(record.get("decision", {}).get("model_source") or "unknown")


def summarize(records: list[dict[str, Any]], min_review_plays: int) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        groups.setdefault(model_source(record), []).append(record)

    rows = []
    for source, group in groups.items():
        plays = [r for r in group if r.get("settlement", {}).get("is_play")]
        settled_plays = [r for r in plays if r.get("settlement", {}).get("status") == "settled"]
        wins = sum(1 for r in settled_plays if r.get("settlement", {}).get("underdog_won_su"))
        losses = len(settled_plays) - wins
        profit = sum(float(r.get("settlement", {}).get("profit_units", 0.0)) for r in settled_plays)
        roi = profit / len(settled_plays) if settled_plays else 0.0
        avg_ev = _avg([r.get("decision", {}).get("offered_ev") for r in settled_plays])
        avg_cases = _avg([r.get("decision", {}).get("historical_cases") for r in group])
        rows.append(
            {
                "model_source": source,
                "records": len(group),
                "plays": len(plays),
                "settled_plays": len(settled_plays),
                "wins": wins,
                "losses": losses,
                "profit_units": profit,
                "roi": roi,
                "avg_offered_ev": avg_ev,
                "avg_historical_cases": avg_cases,
                "review_flag": review_flag(len(settled_plays), roi, avg_ev, min_review_plays),
            }
        )
    return sorted(rows, key=lambda row: (row["profit_units"], row["roi"], row["settled_plays"]), reverse=True)


def _avg(values: list[Any]) -> float | None:
    numeric = [float(v) for v in values if v is not None]
    if not numeric:
        return None
    return sum(numeric) / len(numeric)


def review_flag(settled_plays: int, roi: float, avg_ev: float | None, min_review_plays: int) -> str:
    if settled_plays == 0:
        return "NO_SETTLED_PLAYS"
    if settled_plays < min_review_plays:
        return "KEEP_OBSERVING_SMALL_SAMPLE"
    if roi < -0.10:
        return "TIGHTEN_OR_DISABLE"
    if roi < 0:
        return "TIGHTEN_BUFFER"
    if avg_ev is not None and avg_ev < 0.03:
        return "RAISE_PLAY_BUFFER"
    return "KEEP"


def write_report(path: Path, records: list[dict[str, Any]], rows: list[dict[str, Any]], min_review_plays: int) -> None:
    total_plays = sum(row["settled_plays"] for row in rows)
    total_profit = sum(row["profit_units"] for row in rows)
    total_roi = total_profit / total_plays if total_plays else 0.0
    lines = [
        "# Live Watch Weekly Review",
        "",
        f"Records: {len(records)}",
        f"Settled plays: {total_plays}",
        f"Profit units: {total_profit:+.2f}",
        f"ROI per 1u play: {total_roi:+.1%}",
        f"Minimum plays for model judgment: {min_review_plays}",
        "",
        "## Model Ranking",
        "",
        "| Model Source | Records | Plays | Settled | W-L | Profit | ROI | Avg EV | Avg Hist Cases | Review Flag |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            "| {model} | {records} | {plays} | {settled} | {wins}-{losses} | {profit:+.2f} | "
            "{roi:+.1%} | {avg_ev} | {avg_cases} | {flag} |".format(
                model=row["model_source"],
                records=row["records"],
                plays=row["plays"],
                settled=row["settled_plays"],
                wins=row["wins"],
                losses=row["losses"],
                profit=row["profit_units"],
                roi=row["roi"],
                avg_ev=_fmt_pct(row["avg_offered_ev"]),
                avg_cases=_fmt_float(row["avg_historical_cases"]),
                flag=row["review_flag"],
            )
        )

    lines.extend(
        [
            "",
            "## Parameter Notes",
            "",
            "- `KEEP_OBSERVING_SMALL_SAMPLE`: do not change rules yet.",
            "- `TIGHTEN_BUFFER`: consider raising `--play-buffer` or `--strong-buffer` for that model source.",
            "- `TIGHTEN_OR_DISABLE`: consider disabling that fallback until more evidence is collected.",
            "- `RAISE_PLAY_BUFFER`: model may be finding only thin edges; require a larger EV cushion.",
            "- `KEEP`: no adjustment suggested from this review window.",
            "",
            "## Suggested Next Actions",
            "",
        ]
    )
    suggestions = suggestions_from_rows(rows)
    if suggestions:
        lines.extend(f"- {suggestion}" for suggestion in suggestions)
    else:
        lines.append("- No rule changes suggested.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def suggestions_from_rows(rows: list[dict[str, Any]]) -> list[str]:
    suggestions = []
    for row in rows:
        flag = row["review_flag"]
        source = row["model_source"]
        if flag == "TIGHTEN_OR_DISABLE":
            suggestions.append(f"{source}: pause or require higher sample/EV buffer.")
        elif flag == "TIGHTEN_BUFFER":
            suggestions.append(f"{source}: raise EV buffer before next week.")
        elif flag == "RAISE_PLAY_BUFFER":
            suggestions.append(f"{source}: increase `--play-buffer` by 0.01 to 0.02.")
    return suggestions


def _fmt_pct(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:+.1%}"


def _fmt_float(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.1f}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Review settled live watch results by model source.")
    parser.add_argument("--season", type=int, required=True)
    parser.add_argument("--week", type=int, required=True)
    parser.add_argument("--data-root", type=Path, default=Path("data"))
    parser.add_argument("--settled", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--min-review-plays", type=int, default=10)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settled = args.settled or args.data_root / "live_watch" / str(args.season) / f"week_{args.week:02d}_settled.jsonl"
    output = args.output or settled.with_name(f"week_{args.week:02d}_weekly_review.md")
    records = read_jsonl(settled)
    rows = summarize(records, args.min_review_plays)
    write_report(output, records, rows, args.min_review_plays)
    print(f"review={output}")


if __name__ == "__main__":
    main()
