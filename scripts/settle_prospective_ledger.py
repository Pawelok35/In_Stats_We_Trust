from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import polars as pl

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from utils.team_aliases import normalize_team_code

WIN_UNITS = 100 / 110
LOSS_UNITS = -1.0


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in {path}:{line_no}: {exc}") from exc
    return records


def load_results(data_root: Path, season: int) -> dict[tuple[int, str, str], dict[str, Any]]:
    candidates = [
        data_root / "schedules" / f"{season}.parquet",
        data_root / "schedule" / f"{season}.parquet",
    ]
    schedule_path = next((path for path in candidates if path.exists()), None)
    if schedule_path is None:
        raise FileNotFoundError(f"No local schedule parquet for {season}: {candidates}")

    df = pl.read_parquet(schedule_path)
    if "game_type" in df.columns:
        df = df.filter(pl.col("game_type") == "REG")

    results: dict[tuple[int, str, str], dict[str, Any]] = {}
    for row in df.to_dicts():
        home = normalize_team_code(row.get("home_team") or row.get("team_a") or row.get("TEAM"))
        away = normalize_team_code(row.get("away_team") or row.get("team_b") or row.get("OPP"))
        if not home or not away:
            continue
        results[(int(row["week"]), home, away)] = {
            "home_score": row.get("home_score"),
            "away_score": row.get("away_score"),
        }
    return results


def grade_record(
    record: dict[str, Any], results: dict[tuple[int, str, str], dict[str, Any]]
) -> dict[str, Any]:
    pick = record["pick"]
    process = record.get("process_snapshot", {})
    week = int(pick["week"])
    home = normalize_team_code(pick["home"])
    away = normalize_team_code(pick["away"])
    game = results.get((week, home, away))
    base = {
        "ledger_id": record["ledger_id"],
        "proof_qualified": bool(record.get("proof_qualified")),
        "season": int(pick["season"]),
        "week": week,
        "home": home,
        "away": away,
        "tag": str(pick.get("tag", "UNKNOWN")).upper(),
        "model_winner": normalize_team_code(pick.get("model_winner")),
        "line": pick.get("line"),
        "price": pick.get("price"),
        "fair_line": _process_or_pick_float(process, pick, "fair_line", "model_margin"),
        "edge_vs_line": _process_or_pick_float(process, pick, "edge_vs_line", "edge_vs_line"),
        "closing_line": _process_or_pick_float(process, pick, "closing_line", "closing_line"),
        "closing_price": _process_or_pick_float(process, pick, "closing_price", "closing_price"),
        "clv_points": _process_or_pick_float(process, pick, "clv_points", "clv_points"),
        "process_quality": process_quality(process),
        "outcome": "pending",
        "ats_margin": None,
        "profit_units": 0.0,
        "risk_units": 0.0,
    }
    if not record.get("proof_qualified"):
        base["outcome"] = "not_qualified"
        return base
    if not game or _is_null(game.get("home_score")) or _is_null(game.get("away_score")):
        return base

    home_score = int(game["home_score"])
    away_score = int(game["away_score"])
    model_winner = base["model_winner"]
    if model_winner == home:
        pick_margin = home_score - away_score
    elif model_winner == away:
        pick_margin = away_score - home_score
    else:
        base["outcome"] = "invalid_model_winner"
        return base

    handicap = float(pick.get("handicap", 0.0))
    ats_margin = pick_margin + handicap
    base["ats_margin"] = ats_margin
    base["risk_units"] = 1.0
    if ats_margin > 0:
        base["outcome"] = "win"
        base["profit_units"] = WIN_UNITS
    elif ats_margin < 0:
        base["outcome"] = "loss"
        base["profit_units"] = LOSS_UNITS
    else:
        base["outcome"] = "push"
    return base


def process_quality(process: dict[str, Any]) -> str:
    if not process:
        return "legacy_no_process_snapshot"
    has_fair = bool(process.get("has_fair_line"))
    has_market_line = bool(process.get("has_market_line"))
    has_price = bool(process.get("has_market_price"))
    has_ts = bool(process.get("has_decision_timestamp"))
    has_against = bool(process.get("has_argument_against"))
    has_close = bool(process.get("has_closing_line"))
    if has_fair and has_market_line and has_price and has_ts and has_against and has_close:
        return "complete_with_clv"
    if has_fair and has_market_line and has_price and has_ts and has_against:
        return "complete_pre_kick"
    if has_fair and has_market_line and has_price and has_ts:
        return "basic_price_proof"
    return "result_only"


def _process_or_pick_float(
    process: dict[str, Any],
    pick: dict[str, Any],
    process_key: str,
    pick_key: str,
) -> float | None:
    process_value = _safe_float(process.get(process_key))
    if process_value is not None:
        return process_value
    return _safe_float(pick.get(pick_key))


def _safe_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _is_null(value: Any) -> bool:
    return value is None or value != value


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    qualified = [row for row in rows if row["proof_qualified"]]
    settled = [row for row in qualified if row["outcome"] in {"win", "loss", "push"}]
    wins = sum(1 for row in settled if row["outcome"] == "win")
    losses = sum(1 for row in settled if row["outcome"] == "loss")
    pushes = sum(1 for row in settled if row["outcome"] == "push")
    decisions = wins + losses
    profit = sum(float(row["profit_units"]) for row in settled)
    risk = sum(float(row["risk_units"]) for row in settled)
    return {
        "records": len(rows),
        "proof_qualified": len(qualified),
        "not_qualified": len(rows) - len(qualified),
        "settled": len(settled),
        "pending": sum(1 for row in qualified if row["outcome"] == "pending"),
        "wins": wins,
        "losses": losses,
        "pushes": pushes,
        "win_rate": wins / decisions if decisions else 0.0,
        "profit_units": profit,
        "risk_units": risk,
        "roi": profit / risk if risk else 0.0,
        "process_quality_counts": _counts(row["process_quality"] for row in rows),
    }


def _counts(values: Any) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        key = str(value)
        counts[key] = counts.get(key, 0) + 1
    return counts


def write_report(
    path: Path, ledger_path: Path, rows: list[dict[str, Any]], summary: dict[str, Any]
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    process_counts = ", ".join(
        f"{name}: {count}" for name, count in sorted(summary["process_quality_counts"].items())
    )
    lines = [
        "# Prospective Ledger Settlement",
        "",
        f"Ledger: `{ledger_path}`",
        "",
        "## Summary",
        "",
        f"- Records: {summary['records']}",
        f"- Proof-qualified: {summary['proof_qualified']}",
        f"- Not qualified: {summary['not_qualified']}",
        f"- Settled qualified picks: {summary['settled']}",
        f"- W-L-P: {summary['wins']}-{summary['losses']}-{summary['pushes']}",
        f"- Win rate: {summary['win_rate']:.1%}",
        f"- Units: {summary['profit_units']:+.2f}u",
        f"- ROI: {summary['roi']:.1%}",
        f"- Process quality: {process_counts}",
        "",
        "## Records",
        "",
        "| Week | Game | Tag | Qualified | Outcome | Units | ATS Margin | Line | Fair | Edge | CLV | Process |",
        "|---:|---|---|---|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        ats = "" if row["ats_margin"] is None else f"{row['ats_margin']:.1f}"
        line = _format_number(row["line"])
        fair = _format_number(row["fair_line"])
        edge = _format_number(row["edge_vs_line"])
        clv = _format_number(row["clv_points"])
        lines.append(
            f"| {row['week']} | {row['away']} @ {row['home']} | {row['tag']} | "
            f"{row['proof_qualified']} | {row['outcome']} | {row['profit_units']:+.2f}u | {ats} | "
            f"{line} | {fair} | {edge} | {clv} | {row['process_quality']} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _format_number(value: Any) -> str:
    numeric = _safe_float(value)
    if numeric is None:
        return ""
    return f"{numeric:.1f}"


def settle(
    ledger_path: Path, data_root: Path, output_path: Path | None
) -> tuple[Path, dict[str, Any]]:
    records = load_jsonl(ledger_path)
    if not records:
        raise ValueError(f"No records in ledger: {ledger_path}")
    season = int(records[0]["pick"]["season"])
    results = load_results(data_root, season)
    rows = [grade_record(record, results) for record in records]
    summary = summarize(rows)
    report_path = output_path or ledger_path.with_name(ledger_path.stem + "_settlement.md")
    write_report(report_path, ledger_path, rows, summary)
    return report_path, summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Settle a prospective edge ledger.")
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--data-root", type=Path, default=Path("data"))
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report_path, summary = settle(args.ledger, args.data_root, args.output)
    print(f"report={report_path}")
    print(f"proof_qualified={summary['proof_qualified']}")
    print(f"settled={summary['settled']}")
    print(f"units={summary['profit_units']:+.2f}")


if __name__ == "__main__":
    main()
