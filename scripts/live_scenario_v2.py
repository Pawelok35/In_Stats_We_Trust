from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from live_scenario.data_provider import processed_dataset_path
from live_scenario.dataset import dataset_status
from live_scenario.service import build_basic_after_q_report
from live_scenario.spread import build_pregame_spread_context
from live_scenario.state import (
    build_current_state_from_quarters,
    cumulative_state_from_margin,
    margin_bucket_v2,
    parse_path,
)


def parse_quarter_score(raw: str) -> tuple[int, int]:
    match = re.fullmatch(r"\s*(\d+)\s*[-:]\s*(\d+)\s*", raw)
    if not match:
        raise argparse.ArgumentTypeError("Quarter score must look like 7-3 or 7:3.")
    return int(match.group(1)), int(match.group(2))


def _add_v2_state_columns(rows: pd.DataFrame, completed_quarters: int) -> pd.DataFrame:
    rows = rows.copy()
    for quarter in range(1, completed_quarters + 1):
        margin_col = f"after_q{quarter}_margin"
        bucket_col = f"after_q{quarter}_margin_bucket_v2"
        state_col = f"after_q{quarter}_state_v2"
        if margin_col not in rows.columns:
            continue
        if bucket_col not in rows.columns:
            rows[bucket_col] = rows[margin_col].apply(lambda value: margin_bucket_v2(float(value)))
        if state_col not in rows.columns:
            rows[state_col] = rows[margin_col].apply(
                lambda value: cumulative_state_from_margin(float(value))
            )
    if (
        "team_a_closing_spread" not in rows.columns
        and "spread_line_away_perspective" in rows.columns
        and "side" in rows.columns
    ):
        rows["team_a_closing_spread"] = rows.apply(
            lambda row: (
                row["spread_line_away_perspective"]
                if str(row["side"]).lower() == "away"
                else -row["spread_line_away_perspective"]
            ),
            axis=1,
        )
    if "team_a_role" not in rows.columns and "role" in rows.columns:
        rows["team_a_role"] = rows["role"]
    return rows


def _filter_path_only(rows: pd.DataFrame, path: str) -> pd.DataFrame:
    data = rows.copy()
    for idx, result in enumerate(parse_path(path), start=1):
        data = data[data[f"q{idx}_result"] == result]
    return data


def _legacy_path_only_summary(rows: pd.DataFrame, path: str) -> dict:
    data = _filter_path_only(rows, path)
    counts = data["final_state"].value_counts().to_dict() if not data.empty else {}
    wins = int(counts.get("WIN", 0))
    losses = int(counts.get("LOSS", 0))
    ties = int(counts.get("TIE", 0))
    sample = int(len(data))
    return {
        "mode": "legacy_path_only",
        "filters_applied": ["path"],
        "filters_not_applied": ["margin_bucket"],
        "path": path,
        "sample_size": sample,
        "wins": wins,
        "losses": losses,
        "ties": ties,
        "raw_probability": round(wins / sample, 6) if sample else None,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a Live Scenario V2 report from quarter points."
    )
    parser.add_argument("--team-a", required=True, help="Team A code, e.g. BUF.")
    parser.add_argument("--opponent", required=True, help="Opponent code, e.g. HOU.")
    parser.add_argument("--q1", required=True, type=parse_quarter_score, help="Q1 score, e.g. 7-3.")
    parser.add_argument("--q2", type=parse_quarter_score, help="Q2 score, e.g. 10-7.")
    parser.add_argument("--q3", type=parse_quarter_score, help="Q3 score, e.g. 3-10.")
    parser.add_argument("--q4", type=parse_quarter_score, help="Q4 score, e.g. 7-7.")
    parser.add_argument(
        "--historical-rows",
        type=Path,
        help="Legacy/test CSV override. Production uses validated processed Parquet.",
    )
    parser.add_argument("--data-root", type=Path, default=REPO_ROOT / "data")
    parser.add_argument("--data-cutoff-utc", required=True)
    parser.add_argument("--generated-at-utc")
    parser.add_argument("--team-a-live-decimal", type=float)
    parser.add_argument("--opponent-live-decimal", type=float)
    parser.add_argument(
        "--team-a-closing-spread",
        type=float,
        help="Pregame closing spread from Team A perspective. Negative means favorite.",
    )
    parser.add_argument(
        "--team-a-role", help="Optional role validation: FAVORITE, UNDERDOG, PICKEM."
    )
    parser.add_argument("--spread-source")
    parser.add_argument("--spread-captured-at-utc")
    parser.add_argument("--spread-quality")
    parser.add_argument("--stability-threshold-pp", type=float, default=15.0)
    parser.add_argument(
        "--tie-policy",
        choices=["TIE_AS_PUSH", "TIE_AS_LOSS", "THREE_WAY_DISTRIBUTION"],
        default="TIE_AS_LOSS",
    )
    parser.add_argument(
        "--legacy-compatibility-mode",
        action="store_true",
        help="Add legacy path-only comparison block without changing V2 results.",
    )
    parser.add_argument("--output", type=Path, help="Optional JSON output path.")
    return parser.parse_args()


def _load_historical_rows(args: argparse.Namespace) -> pd.DataFrame:
    if args.historical_rows:
        return pd.read_csv(args.historical_rows)
    status = dataset_status(args.data_root, seasons=list(range(2015, 2026)))
    if status.status != "READY":
        raise SystemExit(
            "DATASET NOT READY. Run: "
            ".\\.venv\\Scripts\\python.exe scripts\\sync_live_scenario_data.py --bootstrap"
        )
    return pd.read_parquet(processed_dataset_path(args.data_root))


def _apply_data_cutoff(rows: pd.DataFrame, cutoff_utc: str) -> pd.DataFrame:
    if "gameday" not in rows.columns:
        return rows
    cutoff = pd.to_datetime(cutoff_utc, utc=True, errors="coerce")
    if pd.isna(cutoff):
        return rows
    dates = pd.to_datetime(rows["gameday"], utc=True, errors="coerce")
    return rows[dates <= cutoff].copy()


def build_report_from_args(args: argparse.Namespace) -> dict:
    quarter_scores = [args.q1]
    for value in [args.q2, args.q3, args.q4]:
        if value is not None:
            quarter_scores.append(value)
    current_state = build_current_state_from_quarters(
        team_a=args.team_a,
        opponent=args.opponent,
        quarter_scores=quarter_scores,
    )
    historical_rows = _load_historical_rows(args)
    historical_rows = _apply_data_cutoff(historical_rows, args.data_cutoff_utc)
    historical_rows = _add_v2_state_columns(
        historical_rows,
        completed_quarters=current_state.completed_quarters,
    )
    report = build_basic_after_q_report(
        current_state=current_state,
        historical_rows=historical_rows,
        data_cutoff_utc=args.data_cutoff_utc,
        generated_at_utc=args.generated_at_utc,
        team_a_live_decimal=args.team_a_live_decimal,
        opponent_live_decimal=args.opponent_live_decimal,
        tie_policy=args.tie_policy,
        pregame_spread_context=build_pregame_spread_context(
            team_a_closing_spread=args.team_a_closing_spread,
            team_a_role=args.team_a_role,
            spread_source=args.spread_source,
            spread_captured_at_utc=args.spread_captured_at_utc,
            spread_quality=args.spread_quality,
        ),
        stability_threshold_pp=args.stability_threshold_pp,
    )
    payload = report.to_dict()
    if args.legacy_compatibility_mode:
        legacy = _legacy_path_only_summary(historical_rows, current_state.team_a_path)
        v2 = payload["league_baseline"]
        payload["legacy_compatibility"] = {
            "mode": "legacy_compatibility",
            "purpose": "Compare legacy quarter path-only against V2 cumulative-state path+margin.",
            "identical_results_required": False,
            "note": (
                "Different sample sizes are expected when V2 applies cumulative_state_path "
                "plus margin_bucket and legacy uses quarter_result_path only."
            ),
            "legacy_path_only": legacy,
            "v2_path_margin": {
                "mode": "v2_path_margin",
                "filters_applied": list(v2["filters_applied"]),
                "quarter_result_path": current_state.team_a_quarter_result_path,
                "cumulative_state_path": current_state.team_a_cumulative_state_path,
                "margin_bucket": current_state.margin_bucket,
                "sample_size": v2["sample_size"],
                "wins": v2["wins"],
                "losses": v2["losses"],
                "ties": v2["ties"],
                "raw_probability": v2["raw_probability"],
            },
            "sample_size_delta": legacy["sample_size"] - v2["sample_size"],
        }
    return payload


def main() -> None:
    args = parse_args()
    payload = build_report_from_args(args)
    rendered = json.dumps(payload, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()
