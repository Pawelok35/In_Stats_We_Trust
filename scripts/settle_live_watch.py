from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import nfl_data_py as nfl
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


PLAY_DECISIONS = {"PLAY_ML", "STRONG_PLAY_ML"}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise SystemExit(f"Live watch ledger not found: {path}")
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


def load_final_scores(season: int, week: int) -> dict[str, dict[str, Any]]:
    schedules = nfl.import_schedules([season])
    games = schedules[(schedules["week"] == week)].copy()
    if "game_type" in games.columns:
        games = games[games["game_type"] == "REG"].copy()
    scores = {}
    for _, row in games.iterrows():
        game_id = row.get("game_id")
        if pd.isna(game_id):
            continue
        away_score = row.get("away_score")
        home_score = row.get("home_score")
        if pd.isna(away_score) or pd.isna(home_score):
            scores[str(game_id)] = {
                "status": "pending",
                "away_team": row.get("away_team"),
                "home_team": row.get("home_team"),
                "away_score": None,
                "home_score": None,
            }
            continue
        scores[str(game_id)] = {
            "status": "final",
            "away_team": row.get("away_team"),
            "home_team": row.get("home_team"),
            "away_score": int(away_score),
            "home_score": int(home_score),
        }
    return scores


def settle_record(record: dict[str, Any], final_scores: dict[str, dict[str, Any]]) -> dict[str, Any]:
    state = record.get("state", {})
    decision = record.get("decision", {})
    game_id = str(state.get("game_id") or record.get("game_id") or "")
    final = final_scores.get(game_id)
    settled = {
        **record,
        "settlement": {
            "status": "missing_final_score",
            "is_play": decision.get("decision") in PLAY_DECISIONS,
            "profit_units": 0.0,
        },
    }
    if final is None:
        return settled
    if final["status"] != "final":
        settled["settlement"] = {
            "status": "pending",
            "is_play": decision.get("decision") in PLAY_DECISIONS,
            "profit_units": 0.0,
            "final": final,
        }
        return settled

    underdog_side = state.get("underdog_side")
    if underdog_side == "away":
        underdog_score = final["away_score"]
        favorite_score = final["home_score"]
    elif underdog_side == "home":
        underdog_score = final["home_score"]
        favorite_score = final["away_score"]
    else:
        underdog_score = None
        favorite_score = None

    won = (
        underdog_score is not None
        and favorite_score is not None
        and int(underdog_score) > int(favorite_score)
    )
    is_play = decision.get("decision") in PLAY_DECISIONS
    live_decimal = record.get("live_decimal")
    if is_play and live_decimal:
        profit = float(live_decimal) - 1 if won else -1.0
    else:
        profit = 0.0

    settled["settlement"] = {
        "status": "settled",
        "is_play": is_play,
        "underdog_won_su": won,
        "underdog_final_score": underdog_score,
        "favorite_final_score": favorite_score,
        "profit_units": profit,
        "final": final,
    }
    return settled


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True, default=str) + "\n")


def model_source(record: dict[str, Any]) -> str:
    return str(record.get("decision", {}).get("model_source") or "unknown")


def summarize_model_sources(settled: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for source, records in sorted(
        _group_by_model_source(settled).items(),
        key=lambda item: item[0],
    ):
        plays = [r for r in records if r["settlement"].get("is_play")]
        settled_plays = [r for r in plays if r["settlement"]["status"] == "settled"]
        wins = sum(1 for r in settled_plays if r["settlement"].get("underdog_won_su"))
        losses = len(settled_plays) - wins
        profit = sum(float(r["settlement"].get("profit_units", 0.0)) for r in settled_plays)
        roi = profit / len(settled_plays) if settled_plays else 0.0
        rows.append(
            {
                "model_source": source,
                "records": len(records),
                "play_decisions": len(plays),
                "settled_plays": len(settled_plays),
                "wins": wins,
                "losses": losses,
                "profit_units": profit,
                "roi": roi,
            }
        )
    return rows


def _group_by_model_source(settled: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for record in settled:
        groups.setdefault(model_source(record), []).append(record)
    return groups


def write_report(path: Path, settled: list[dict[str, Any]]) -> None:
    plays = [r for r in settled if r["settlement"].get("is_play")]
    settled_plays = [r for r in plays if r["settlement"]["status"] == "settled"]
    wins = sum(1 for r in settled_plays if r["settlement"].get("underdog_won_su"))
    losses = len(settled_plays) - wins
    profit = sum(float(r["settlement"].get("profit_units", 0.0)) for r in settled_plays)
    roi = profit / len(settled_plays) if settled_plays else 0.0
    pending = sum(1 for r in settled if r["settlement"]["status"] == "pending")

    lines = [
        "# Live Watch Settlement",
        "",
        f"Records: {len(settled)}",
        f"Play decisions: {len(plays)}",
        f"Settled plays: {len(settled_plays)}",
        f"Pending records: {pending}",
        f"ML W-L: {wins}-{losses}",
        f"Profit units: {profit:+.2f}",
        f"ROI per 1u play: {roi:+.1%}",
        "",
        "## By Model Source",
        "",
        "| Model Source | Records | Plays | Settled Plays | W-L | Profit | ROI |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summarize_model_sources(settled):
        lines.append(
            "| {model} | {records} | {plays} | {settled} | {wins}-{losses} | {profit:+.2f} | {roi:+.1%} |".format(
                model=row["model_source"],
                records=row["records"],
                plays=row["play_decisions"],
                settled=row["settled_plays"],
                wins=row["wins"],
                losses=row["losses"],
                profit=row["profit_units"],
                roi=row["roi"],
            )
        )

    lines.extend(
        [
            "",
            "## Detail",
            "",
            "| Game ID | Underdog | Model Source | Decision | Price | Result | Profit |",
            "|---|---|---|---|---:|---|---:|",
        ]
    )
    for record in settled:
        state = record.get("state", {})
        decision = record.get("decision", {})
        settlement = record.get("settlement", {})
        result = settlement["status"]
        if settlement["status"] == "settled":
            result = "WIN" if settlement.get("underdog_won_su") else "LOSS"
            if not settlement.get("is_play"):
                result = f"NO BET ({result})"
        lines.append(
            "| {game_id} | {dog} | {model} | {decision} | {price} | {result} | {profit:+.2f} |".format(
                game_id=state.get("game_id", ""),
                dog=state.get("underdog_team", ""),
                model=model_source(record),
                decision=decision.get("decision", ""),
                price=record.get("live_decimal") or "",
                result=result,
                profit=float(settlement.get("profit_units", 0.0)),
            )
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Settle live watch card ledger for one NFL week.")
    parser.add_argument("--season", type=int, required=True)
    parser.add_argument("--week", type=int, required=True)
    parser.add_argument("--data-root", type=Path, default=Path("data"))
    parser.add_argument("--ledger", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--report", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ledger = args.ledger or args.data_root / "live_watch" / str(args.season) / f"week_{args.week:02d}.jsonl"
    output = args.output or ledger.with_name(f"week_{args.week:02d}_settled.jsonl")
    report = args.report or ledger.with_name(f"week_{args.week:02d}_settlement.md")

    records = read_jsonl(ledger)
    final_scores = load_final_scores(args.season, args.week)
    settled = [settle_record(record, final_scores) for record in records]
    write_jsonl(output, settled)
    write_report(report, settled)

    print(f"settled={output}")
    print(f"report={report}")


if __name__ == "__main__":
    main()
