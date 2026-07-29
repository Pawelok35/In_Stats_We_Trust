from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.variant_b_audit import clean_team


SCHEMA_VERSION = "variant_b_post_event_evaluation.v1"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def stable_hash(payload: dict[str, Any], prefix: str) -> str:
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return f"{prefix}_{hashlib.sha256(raw.encode('utf-8')).hexdigest()[:20]}"


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in {path}:{line_no}: {exc}") from exc
    return records


def append_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> int:
    rows = list(records)
    if not rows:
        return 0
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    return len(rows)


def safe_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(out):
        return None
    return out


def result_key(record: dict[str, Any]) -> tuple[int, int, str, str]:
    return (
        int(record.get("season") or 0),
        int(record.get("week") or 0),
        clean_team(record.get("home_team") or record.get("home")),
        clean_team(record.get("away_team") or record.get("away")),
    )


def load_results(path: Path, season: int, week: int) -> dict[tuple[int, int, str, str], dict[str, Any]]:
    results: dict[tuple[int, int, str, str], dict[str, Any]] = {}
    for record in load_jsonl(path):
        if int(record.get("season") or 0) != season or int(record.get("week") or 0) != week:
            continue
        results[result_key(record)] = record
    return results


def load_schedule_results(path: Path, season: int, week: int) -> dict[tuple[int, int, str, str], dict[str, Any]]:
    if not path.exists():
        return {}
    df = pd.read_parquet(path)
    if "game_type" in df.columns:
        df = df[df["game_type"] == "REG"]
    if "week" not in df.columns:
        return {}
    df = df[df["week"] == week]
    results: dict[tuple[int, int, str, str], dict[str, Any]] = {}
    for row in df.to_dict(orient="records"):
        home = clean_team(row.get("home_team"))
        away = clean_team(row.get("away_team"))
        home_score = row.get("home_score")
        away_score = row.get("away_score")
        if not home or not away:
            continue
        results[(season, week, home, away)] = {
            "season": season,
            "week": week,
            "home_team": home,
            "away_team": away,
            "home_score": home_score,
            "away_score": away_score,
            "source": str(path),
        }
    return results


def settlement(actual_margin: float, spread: float | None) -> str:
    if spread is None:
        return "NOT_ASSESSABLE"
    ats_margin = actual_margin + spread
    if ats_margin > 0:
        return "COVER"
    if ats_margin < 0:
        return "LOSS"
    return "PUSH"


def build_post_event_records(
    *,
    ledger_dir: Path,
    results_path: Path,
    schedule_results_path: Path,
    season: int,
    week: int,
    recorded_at: str,
) -> dict[str, list[dict[str, Any]]]:
    games = {row["game_id"]: row for row in load_jsonl(ledger_dir / "games.jsonl")}
    model_runs = {row["model_run_id"]: row for row in load_jsonl(ledger_dir / "model_runs.jsonl")}
    predictions = load_jsonl(ledger_dir / "model_predictions.jsonl")
    quotes_by_model_run: dict[str, dict[str, Any]] = {}
    quotes_by_id = {row["market_quote_id"]: row for row in load_jsonl(ledger_dir / "market_quotes.jsonl")}
    for run in model_runs.values():
        quote = quotes_by_id.get(run.get("market_quote_id"))
        if quote:
            quotes_by_model_run[run["model_run_id"]] = quote

    results = load_schedule_results(schedule_results_path, season, week)
    # Manual results are treated as fallback/override when present.
    results.update(load_results(results_path, season, week))
    outcomes: list[dict[str, Any]] = []
    evaluations: list[dict[str, Any]] = []

    for pred in predictions:
        run = model_runs.get(pred.get("model_run_id"))
        if not run:
            continue
        game = games.get(run.get("game_id"))
        if not game:
            continue
        key = (
            int(game["season"]),
            int(game["week"]),
            clean_team(game["home_team"]),
            clean_team(game["away_team"]),
        )
        result = results.get(key)
        selected = clean_team(pred.get("selected_team"))
        home = clean_team(game["home_team"])
        away = clean_team(game["away_team"])
        quote = quotes_by_model_run.get(pred["model_run_id"], {})

        base = {
            "schema_version": SCHEMA_VERSION,
            "ledger_recorded_at_utc": recorded_at,
            "season": season,
            "week": week,
            "game_id": game["game_id"],
            "model_run_id": pred["model_run_id"],
            "model_prediction_id": pred["model_prediction_id"],
            "selected_team": selected,
        }

        if not result:
            evaluations.append(
                {
                    **base,
                    "post_event_evaluation_id": stable_hash({**base, "status": "PENDING_RESULT"}, "postevaluation"),
                    "status": "PENDING_RESULT",
                }
            )
            continue

        home_score = safe_float(result.get("home_score"))
        away_score = safe_float(result.get("away_score"))
        if home_score is None or away_score is None:
            evaluations.append(
                {
                    **base,
                    "post_event_evaluation_id": stable_hash({**base, "status": "PENDING_SCORE"}, "postevaluation"),
                    "status": "PENDING_SCORE",
                }
            )
            continue

        if selected == home:
            actual_margin = home_score - away_score
        elif selected == away:
            actual_margin = away_score - home_score
        else:
            actual_margin = None

        outcome_payload = {
            **base,
            "home_team": home,
            "away_team": away,
            "home_score": home_score,
            "away_score": away_score,
            "actual_margin_selected_team": actual_margin,
            "result_finalized_at_utc": recorded_at,
        }
        outcome_payload["outcome_id"] = stable_hash(outcome_payload, "outcome")
        outcomes.append(outcome_payload)

        predicted_margin = safe_float(pred.get("predicted_margin_selected_team"))
        spread = safe_float(quote.get("selected_team_spread") or pred.get("market_spread_selected_team"))
        actual_settlement = settlement(actual_margin, spread) if actual_margin is not None else "NOT_ASSESSABLE"
        prediction_error = actual_margin - predicted_margin if actual_margin is not None and predicted_margin is not None else None
        evaluation_payload = {
            **base,
            "outcome_id": outcome_payload["outcome_id"],
            "status": "SETTLED",
            "actual_margin_selected_team": actual_margin,
            "predicted_margin_selected_team": predicted_margin,
            "prediction_error": prediction_error,
            "market_spread_selected_team": spread,
            "settlement": actual_settlement,
            "p_cover": pred.get("p_cover"),
            "p_push": pred.get("p_push"),
            "p_loss": pred.get("p_loss"),
            "clv_points": None,
            "process_review_status": "MVP_RESULT_ONLY",
        }
        evaluation_payload["post_event_evaluation_id"] = stable_hash(evaluation_payload, "postevaluation")
        evaluations.append(evaluation_payload)

    return {"outcomes": outcomes, "post_event_evaluations": evaluations}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Append post-event outcomes/evaluations to Variant B learning ledger.")
    parser.add_argument("--season", type=int, required=True)
    parser.add_argument("--week", type=int, required=True)
    parser.add_argument("--ledger-root", type=Path, default=Path("data/learning_ledger"))
    parser.add_argument("--results", type=Path, default=Path("data/results/manual_results.jsonl"))
    parser.add_argument("--schedule-results", type=Path, help="Defaults to data/schedules/{season}.parquet after sync-nfl-results.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ledger_root = args.ledger_root if args.ledger_root.is_absolute() else REPO_ROOT / args.ledger_root
    ledger_dir = ledger_root / str(args.season) / f"week_{args.week:02d}"
    if not ledger_dir.exists():
        raise SystemExit(f"Ledger week directory not found: {ledger_dir}")
    results_path = args.results if args.results.is_absolute() else REPO_ROOT / args.results
    schedule_results = args.schedule_results or Path("data") / "schedules" / f"{args.season}.parquet"
    schedule_results_path = schedule_results if schedule_results.is_absolute() else REPO_ROOT / schedule_results
    recorded_at = utc_now_iso()
    records = build_post_event_records(
        ledger_dir=ledger_dir,
        results_path=results_path,
        schedule_results_path=schedule_results_path,
        season=args.season,
        week=args.week,
        recorded_at=recorded_at,
    )
    counts = {
        "outcomes": append_jsonl(ledger_dir / "outcomes.jsonl", records["outcomes"]),
        "post_event_evaluations": append_jsonl(
            ledger_dir / "post_event_evaluations.jsonl",
            records["post_event_evaluations"],
        ),
    }
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "ledger_recorded_at_utc": recorded_at,
        "season": args.season,
        "week": args.week,
        "ledger_dir": str(ledger_dir.relative_to(REPO_ROOT) if ledger_dir.is_relative_to(REPO_ROOT) else ledger_dir),
        "results_path": str(results_path.relative_to(REPO_ROOT) if results_path.is_relative_to(REPO_ROOT) else results_path),
        "schedule_results_path": str(schedule_results_path.relative_to(REPO_ROOT) if schedule_results_path.is_relative_to(REPO_ROOT) else schedule_results_path),
        "appended_counts": counts,
    }
    manifest_path = ledger_dir / f"post_event_manifest_{recorded_at.replace(':', '').replace('-', '')}.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"[OK] post-event evaluation appended: {ledger_dir}")
    print(json.dumps(counts, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
