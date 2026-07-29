from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import nfl_data_py as nfl
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.analyze_in_game_underdogs import _lead_bucket, _spread_bucket, underdog_side


PBP_COLUMNS = [
    "game_id",
    "play_id",
    "week",
    "qtr",
    "home_team",
    "away_team",
    "total_home_score",
    "total_away_score",
    "spread_line",
    "home_wp",
    "away_wp",
]

SNAPSHOT_QUARTERS = {"Q1": 1, "H1": 2, "Q3": 3}


def american_to_decimal(price: float | None) -> float | None:
    if price is None or math.isnan(price) or price == 0:
        return None
    if price > 0:
        return 1 + (price / 100)
    return 1 + (100 / abs(price))


def decimal_to_american(decimal_price: float | None) -> float | None:
    if decimal_price is None or math.isnan(decimal_price) or decimal_price <= 1:
        return None
    if decimal_price >= 2:
        return (decimal_price - 1) * 100
    return -100 / (decimal_price - 1)


def american_odds_from_probability(probability: float | None) -> float | None:
    if probability is None or math.isnan(probability) or probability <= 0 or probability >= 1:
        return None
    return decimal_to_american(1 / probability)


def binary_state_from_margin(margin: float) -> str:
    return "WIN" if margin > 0 else "NOT_WIN"


def spread_micro_bucket(value: float) -> str:
    if value <= 1.5:
        return "0.5-1.5"
    if value <= 3:
        return "2-3"
    if value <= 4.5:
        return "3.5-4.5"
    if value <= 6:
        return "5-6"
    if value <= 7:
        return "6.5-7"
    if value <= 9.5:
        return "7.5-9.5"
    if value <= 13.5:
        return "10-13.5"
    return "14+"


def margin_bucket(value: float) -> str:
    if value == 0:
        return "TIE"
    prefix = "LEAD" if value > 0 else "TRAIL"
    abs_value = abs(value)
    if abs_value <= 3:
        return f"{prefix}_1_3"
    if abs_value <= 7:
        return f"{prefix}_4_7"
    if abs_value <= 13:
        return f"{prefix}_8_13"
    return f"{prefix}_14_PLUS"


def delta_bucket(value: float) -> str:
    if value == 0:
        return "FLAT"
    prefix = "IMPROVED" if value > 0 else "WORSE"
    abs_value = abs(value)
    if abs_value <= 3:
        return f"{prefix}_1_3"
    if abs_value <= 7:
        return f"{prefix}_4_7"
    return f"{prefix}_8_PLUS"


def parse_price(args: argparse.Namespace) -> tuple[float | None, float | None, str | None]:
    if args.live_decimal is not None and args.live_ml is not None:
        raise SystemExit("Use either --live-ml or --live-decimal, not both.")
    if args.live_decimal is not None:
        return args.live_decimal, decimal_to_american(args.live_decimal), "decimal"
    if args.live_ml is not None:
        return american_to_decimal(args.live_ml), float(args.live_ml), "american"
    return None, None, None


def load_game_snapshot(season: int, game_id: str, snapshot: str) -> pd.Series:
    quarter = SNAPSHOT_QUARTERS[snapshot]
    pbp = nfl.import_pbp_data(
        [season],
        columns=PBP_COLUMNS,
        include_participation=False,
        downcast=True,
        cache=False,
    )
    game = pbp[(pbp["game_id"] == game_id) & (pbp["qtr"] == quarter)].copy()
    game = game.dropna(subset=["spread_line", "total_home_score", "total_away_score"])
    if game.empty:
        raise SystemExit(f"No usable {snapshot} play-by-play snapshot found for {game_id}.")
    return game.sort_values("play_id").iloc[-1]


def load_game_pbp(season: int, game_id: str) -> pd.DataFrame:
    pbp = nfl.import_pbp_data(
        [season],
        columns=PBP_COLUMNS,
        include_participation=False,
        downcast=True,
        cache=False,
    )
    game = pbp[pbp["game_id"] == game_id].copy()
    game = game.dropna(subset=["spread_line", "total_home_score", "total_away_score"])
    if game.empty:
        raise SystemExit(f"No usable play-by-play found for {game_id}.")
    return game.sort_values("play_id")


def load_week_pbp(season: int, week: int) -> pd.DataFrame:
    pbp = nfl.import_pbp_data(
        [season],
        columns=PBP_COLUMNS,
        include_participation=False,
        downcast=True,
        cache=False,
    )
    week_pbp = pbp[pbp["week"] == week].copy()
    return week_pbp.dropna(subset=["spread_line", "total_home_score", "total_away_score"])


def load_week_snapshots(season: int, week: int, snapshot: str) -> pd.DataFrame:
    quarter = SNAPSHOT_QUARTERS[snapshot]
    pbp = nfl.import_pbp_data(
        [season],
        columns=PBP_COLUMNS,
        include_participation=False,
        downcast=True,
        cache=False,
    )
    week_pbp = pbp[(pbp["week"] == week) & (pbp["qtr"] == quarter)].copy()
    week_pbp = week_pbp.dropna(subset=["spread_line", "total_home_score", "total_away_score"])
    if week_pbp.empty:
        return pd.DataFrame()
    return week_pbp.sort_values(["game_id", "play_id"]).groupby("game_id", as_index=False).tail(1)


def build_current_state(row: pd.Series, snapshot: str) -> dict[str, Any]:
    spread = float(row["spread_line"])
    side = underdog_side(spread)
    if side is None:
        raise SystemExit("Pregame spread is pick'em; no pregame underdog bucket.")

    home_score = float(row["total_home_score"])
    away_score = float(row["total_away_score"])
    underdog_team = row["away_team"] if side == "away" else row["home_team"]
    favorite_team = row["home_team"] if side == "away" else row["away_team"]
    underdog_score = away_score if side == "away" else home_score
    favorite_score = home_score if side == "away" else away_score
    underdog_wp = row["away_wp"] if side == "away" else row["home_wp"]
    underdog_wp = None if pd.isna(underdog_wp) else float(underdog_wp)
    margin = underdog_score - favorite_score

    return {
        "game_id": row["game_id"],
        "snapshot": snapshot,
        "home_team": row["home_team"],
        "away_team": row["away_team"],
        "underdog_team": underdog_team,
        "favorite_team": favorite_team,
        "underdog_side": side,
        "location": "home dog" if side == "home" else "away dog",
        "spread_line_away_perspective": spread,
        "pregame_spread_abs": abs(spread),
        "spread_bucket": _spread_bucket(abs(spread)),
        "spread_micro_bucket": spread_micro_bucket(abs(spread)),
        "underdog_score_now": underdog_score,
        "favorite_score_now": favorite_score,
        "underdog_margin_now": margin,
        "lead_bucket": _lead_bucket(margin) if margin > 0 else None,
        "underdog_wp": underdog_wp,
        "fair_ml_bucket": "plus-money fair" if underdog_wp is not None and underdog_wp < 0.5 else "favorite fair",
    }


def snapshot_row(game: pd.DataFrame, quarter: int) -> pd.Series | None:
    quarter_rows = game[game["qtr"] == quarter].copy()
    if quarter_rows.empty:
        return None
    return quarter_rows.sort_values("play_id").iloc[-1]


def build_current_state_from_game(game: pd.DataFrame, snapshot: str) -> dict[str, Any]:
    quarter = SNAPSHOT_QUARTERS[snapshot]
    current = snapshot_row(game, quarter)
    q1 = snapshot_row(game, 1)
    q2 = snapshot_row(game, 2)
    q3 = snapshot_row(game, 3)
    if current is None or q1 is None or q2 is None or q3 is None:
        raise SystemExit("Missing Q1/Q2/Q3 snapshot rows for binary path.")
    state = build_current_state(current, snapshot)

    def margin_at(row: pd.Series) -> float:
        home_score = float(row["total_home_score"])
        away_score = float(row["total_away_score"])
        underdog_score = away_score if state["underdog_side"] == "away" else home_score
        favorite_score = home_score if state["underdog_side"] == "away" else away_score
        return underdog_score - favorite_score

    q1_margin = margin_at(q1)
    q2_margin = margin_at(q2)
    q3_margin = margin_at(q3)
    q1_binary = binary_state_from_margin(q1_margin)
    q2_binary = binary_state_from_margin(q2_margin)
    q3_binary = binary_state_from_margin(q3_margin)
    p1_binary = binary_state_from_margin(q1_margin)
    p2_binary = binary_state_from_margin(q2_margin - q1_margin)
    p3_binary = binary_state_from_margin(q3_margin - q2_margin)
    binary_path = f"Q1_{q1_binary}__Q2_{q2_binary}__Q3_{q3_binary}"
    flow_path = (
        f"P1_{p1_binary}_AFTER_Q1_{q1_binary}__"
        f"P2_{p2_binary}_AFTER_Q2_{q2_binary}__"
        f"P3_{p3_binary}_AFTER_Q3_{q3_binary}"
    )
    margin_trajectory = (
        f"Q1_{margin_bucket(q1_margin)}__Q2_{margin_bucket(q2_margin)}__Q3_{margin_bucket(q3_margin)}"
    )
    delta_trajectory = (
        f"Q1Q2_{delta_bucket(q2_margin - q1_margin)}__Q2Q3_{delta_bucket(q3_margin - q2_margin)}"
    )
    state.update(
        {
            "q1_margin": q1_margin,
            "q2_margin": q2_margin,
            "q3_margin": q3_margin,
            "q1_period_margin": q1_margin,
            "q2_period_margin": q2_margin - q1_margin,
            "q3_period_margin": q3_margin - q2_margin,
            "q1_binary_state": q1_binary,
            "q2_binary_state": q2_binary,
            "q3_binary_state": q3_binary,
            "p1_binary_state": p1_binary,
            "p2_binary_state": p2_binary,
            "p3_binary_state": p3_binary,
            "binary_path": binary_path,
            "flow_path": flow_path,
            "margin_trajectory": margin_trajectory,
            "delta_trajectory": delta_trajectory,
            "binary_path_with_q3_lead": f"{binary_path}__Q3_LEAD_{_lead_bucket(q3_margin)}"
            if q3_margin > 0
            else None,
            "flow_path_with_q3_lead": f"{flow_path}__Q3_LEAD_{_lead_bucket(q3_margin)}"
            if q3_margin > 0
            else None,
            "margin_trajectory_with_q3_lead": f"{margin_trajectory}__Q3_LEAD_{_lead_bucket(q3_margin)}"
            if q3_margin > 0
            else None,
            "delta_trajectory_with_q3_lead": f"{delta_trajectory}__Q3_LEAD_{_lead_bucket(q3_margin)}"
            if q3_margin > 0
            else None,
            "path_micro": (
                f"{binary_path}__Q3_LEAD_{_lead_bucket(q3_margin)}__SPREAD_{state['spread_micro_bucket']}"
                if q3_margin > 0
                else None
            ),
        }
    )
    return state


def load_bucket_summary(bucket_source: Path) -> pd.DataFrame:
    if not bucket_source.exists():
        raise SystemExit(f"Historical source not found: {bucket_source}")
    detail = pd.read_csv(bucket_source)
    q3 = detail[detail["snapshot"] == "Q3"].copy()
    q3["spread_bucket"] = q3["pregame_spread_abs"].apply(_spread_bucket)
    q3["lead_bucket"] = q3["underdog_margin_now"].apply(_lead_bucket)
    q3["location"] = q3["underdog_side"].map({"home": "home dog", "away": "away dog"})
    q3["fair_ml_bucket"] = q3["underdog_wp"].apply(
        lambda p: "plus-money fair" if p < 0.5 else "favorite fair"
    )
    rows = []
    for keys, group in q3.groupby(["spread_bucket", "lead_bucket", "location", "fair_ml_bucket"]):
        cases = len(group)
        su_wins = int(group["underdog_won_su"].sum())
        su_rate = su_wins / cases if cases else 0.0
        rows.append(
            {
                "spread_bucket": keys[0],
                "lead_bucket": keys[1],
                "location": keys[2],
                "fair_ml_bucket": keys[3],
                "cases": cases,
                "su_wins": su_wins,
                "su_win_rate": su_rate,
                "break_even_live_ml": american_odds_from_probability(su_rate),
                "fair_decimal": 1 / su_rate if su_rate > 0 else None,
            }
        )
    return pd.DataFrame(rows)


def match_bucket(summary: pd.DataFrame, state: dict[str, Any]) -> dict[str, Any] | None:
    matched = summary[
        (summary["spread_bucket"] == state["spread_bucket"])
        & (summary["lead_bucket"] == state["lead_bucket"])
        & (summary["location"] == state["location"])
        & (summary["fair_ml_bucket"] == state["fair_ml_bucket"])
    ]
    if matched.empty and state["fair_ml_bucket"] == "plus-money fair":
        matched = summary[
            (summary["spread_bucket"] == state["spread_bucket"])
            & (summary["lead_bucket"] == state["lead_bucket"])
            & (summary["location"] == state["location"])
            & (summary["fair_ml_bucket"] == "favorite fair")
        ]
    if matched.empty:
        return None
    return matched.iloc[0].to_dict()


def load_path_summary(path_source: Path) -> pd.DataFrame:
    if not path_source.exists():
        return pd.DataFrame()
    return pd.read_csv(path_source)


def match_path_bucket(summary: pd.DataFrame, state: dict[str, Any]) -> dict[str, Any] | None:
    if summary.empty or not state.get("binary_path_with_q3_lead"):
        return None
    matched = summary[summary["binary_path_with_q3_lead"] == state["binary_path_with_q3_lead"]]
    if matched.empty:
        return None
    row = matched.iloc[0].to_dict()
    row["model_source"] = "binary_path_q3_lead"
    return row


def match_micro_path_bucket(summary: pd.DataFrame, state: dict[str, Any]) -> dict[str, Any] | None:
    if summary.empty or not state.get("path_micro"):
        return None
    matched = summary[summary["path_micro"] == state["path_micro"]]
    if matched.empty:
        return None
    row = matched.iloc[0].to_dict()
    row["model_source"] = "binary_path_micro_spread"
    return row


def match_flow_path_bucket(summary: pd.DataFrame, state: dict[str, Any]) -> dict[str, Any] | None:
    if summary.empty or not state.get("flow_path_with_q3_lead"):
        return None
    matched = summary[summary["flow_path_with_q3_lead"] == state["flow_path_with_q3_lead"]]
    if matched.empty:
        return None
    row = matched.iloc[0].to_dict()
    row["model_source"] = "combined_flow_q3_lead"
    return row


def match_margin_trajectory_bucket(summary: pd.DataFrame, state: dict[str, Any]) -> dict[str, Any] | None:
    if summary.empty or not state.get("margin_trajectory_with_q3_lead"):
        return None
    matched = summary[summary["margin_trajectory_with_q3_lead"] == state["margin_trajectory_with_q3_lead"]]
    if matched.empty:
        return None
    row = matched.iloc[0].to_dict()
    row["model_source"] = "margin_trajectory_q3_lead"
    return row


def match_delta_trajectory_bucket(summary: pd.DataFrame, state: dict[str, Any]) -> dict[str, Any] | None:
    if summary.empty or not state.get("delta_trajectory_with_q3_lead"):
        return None
    matched = summary[summary["delta_trajectory_with_q3_lead"] == state["delta_trajectory_with_q3_lead"]]
    if matched.empty:
        return None
    row = matched.iloc[0].to_dict()
    row["model_source"] = "delta_trajectory_q3_lead"
    return row


def select_bucket(
    flow_bucket: dict[str, Any] | None,
    margin_bucket_row: dict[str, Any] | None,
    delta_bucket_row: dict[str, Any] | None,
    micro_bucket: dict[str, Any] | None,
    path_bucket: dict[str, Any] | None,
    broad_bucket: dict[str, Any] | None,
    min_cases: int,
) -> dict[str, Any] | None:
    if flow_bucket is not None and int(flow_bucket.get("cases", 0)) >= min_cases:
        return flow_bucket
    if margin_bucket_row is not None and int(margin_bucket_row.get("cases", 0)) >= min_cases:
        return margin_bucket_row
    if delta_bucket_row is not None and int(delta_bucket_row.get("cases", 0)) >= min_cases:
        return delta_bucket_row
    if micro_bucket is not None and int(micro_bucket.get("cases", 0)) >= min_cases:
        return micro_bucket
    if path_bucket is not None and int(path_bucket.get("cases", 0)) >= min_cases:
        return path_bucket
    if broad_bucket is not None:
        broad_bucket = {**broad_bucket, "model_source": "broad_q3_bucket"}
    return broad_bucket


def make_decision(
    state: dict[str, Any],
    bucket: dict[str, Any] | None,
    live_decimal: float | None,
    min_cases: int,
    min_win_rate: float,
    play_buffer: float,
    strong_buffer: float,
) -> dict[str, Any]:
    if state["underdog_margin_now"] <= 0:
        return {"decision": "NO_WATCH_NOT_LEADING", "reason": "Pregame underdog is not leading at snapshot."}
    if bucket is None:
        return {"decision": "NO_BET_NO_BUCKET", "reason": "No historical Q3 bucket matched this state."}

    probability = float(bucket["su_win_rate"])
    fair_decimal = 1 / probability if probability > 0 else None
    min_ev_decimal = (1 + play_buffer) / probability if probability > 0 else None
    strong_decimal = (1 + strong_buffer) / probability if probability > 0 else None
    ev = (probability * live_decimal - 1) if live_decimal is not None else None

    metrics = {
        "model_source": bucket.get("model_source", "unknown"),
        "historical_cases": int(bucket["cases"]),
        "historical_su_wins": int(bucket["su_wins"]),
        "historical_su_win_rate": probability,
        "fair_decimal": fair_decimal,
        "fair_american": decimal_to_american(fair_decimal),
        "min_ev_decimal": min_ev_decimal,
        "min_ev_american": decimal_to_american(min_ev_decimal),
        "strong_ev_decimal": strong_decimal,
        "strong_ev_american": decimal_to_american(strong_decimal),
        "offered_ev": ev,
    }

    if int(bucket["cases"]) < min_cases:
        return {
            **metrics,
            "decision": "NO_BET_SMALL_SAMPLE",
            "reason": f"Historical bucket has fewer than {min_cases} cases.",
        }
    if probability < min_win_rate:
        return {
            **metrics,
            "decision": "NO_ML_LOW_WIN_RATE",
            "reason": f"Historical SU win rate is below {min_win_rate:.0%}.",
        }
    if live_decimal is None:
        return {
            **metrics,
            "decision": "WATCH_PRICE_REQUIRED",
            "reason": "Enter live ML from book and play only if price clears the EV buffer.",
        }
    if strong_decimal is not None and live_decimal >= strong_decimal:
        return {
            **metrics,
            "decision": "STRONG_PLAY_ML",
            "reason": "Live price clears the strong EV buffer.",
        }
    if min_ev_decimal is not None and live_decimal >= min_ev_decimal:
        return {
            **metrics,
            "decision": "PLAY_ML",
            "reason": "Live price clears the minimum EV buffer.",
        }
    if fair_decimal is not None and live_decimal > fair_decimal:
        return {
            **metrics,
            "decision": "THIN_EDGE_NO_BET",
            "reason": "Live price is above fair but does not clear the EV buffer.",
        }
    return {
        **metrics,
        "decision": "PRICE_TOO_SHORT",
        "reason": "Live price is not better than historical fair price.",
    }


def write_ledger(record: dict[str, Any], data_root: Path, season: int, week: int) -> Path:
    ledger_dir = data_root / "live_watch" / str(season)
    ledger_dir.mkdir(parents=True, exist_ok=True)
    path = ledger_dir / f"week_{week:02d}.jsonl"
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True, default=str) + "\n")
    return path


def fmt_decimal(value: Any) -> str:
    if value is None or pd.isna(value):
        return "n/a"
    return f"{float(value):.3f}"


def fmt_american(value: Any) -> str:
    if value is None or pd.isna(value):
        return "n/a"
    return f"{float(value):+.0f}"


def print_card(record: dict[str, Any]) -> None:
    state = record["state"]
    decision = record["decision"]
    print("LIVE WATCH CARD")
    print(f"Game: {state['away_team']} at {state['home_team']} ({state['game_id']})")
    print(
        "Pregame underdog: "
        f"{state['underdog_team']} +{state['pregame_spread_abs']:.1f} ({state['location']})"
    )
    print(
        f"Snapshot: {state['snapshot']} | Score: underdog {state['underdog_score_now']:.0f}, "
        f"favorite {state['favorite_score_now']:.0f} | Lead: {state['underdog_margin_now']:+.0f}"
    )
    print(
        "Bucket: "
        f"{state['spread_bucket']} / {state['lead_bucket']} / {state['location']} / {state['fair_ml_bucket']}"
    )
    print(f"Binary path: {state.get('binary_path', 'n/a')}")
    print(f"Binary Q3 path: {state.get('binary_path_with_q3_lead', 'n/a')}")
    print(f"Flow path: {state.get('flow_path_with_q3_lead', 'n/a')}")
    print(f"Margin trajectory: {state.get('margin_trajectory_with_q3_lead', 'n/a')}")
    print(f"Delta trajectory: {state.get('delta_trajectory_with_q3_lead', 'n/a')}")
    print(f"Micro path: {state.get('path_micro', 'n/a')}")
    print("")
    print(f"Model source: {decision.get('model_source', 'n/a')}")
    print(f"Historical cases: {decision.get('historical_cases', 'n/a')}")
    if "historical_su_wins" in decision and "historical_cases" in decision:
        losses = decision["historical_cases"] - decision["historical_su_wins"]
        print(f"Historical SU: {decision['historical_su_wins']}-{losses}")
    if "historical_su_win_rate" in decision:
        print(f"Historical SU win rate: {decision['historical_su_win_rate']:.1%}")
    print(f"Fair price: {fmt_decimal(decision.get('fair_decimal'))} / {fmt_american(decision.get('fair_american'))}")
    print(
        "Minimum EV+ price: "
        f"{fmt_decimal(decision.get('min_ev_decimal'))} / {fmt_american(decision.get('min_ev_american'))}"
    )
    print(
        "Strong EV+ price: "
        f"{fmt_decimal(decision.get('strong_ev_decimal'))} / {fmt_american(decision.get('strong_ev_american'))}"
    )
    print(f"Book live price: {fmt_decimal(record.get('live_decimal'))} / {fmt_american(record.get('live_ml'))}")
    if decision.get("offered_ev") is not None:
        print(f"Offered EV: {decision['offered_ev']:.1%}")
    print("")
    print(f"Decision: {decision['decision']}")
    print(f"Reason: {decision['reason']}")
    if record.get("ledger_path"):
        print(f"Ledger: {record['ledger_path']}")


def print_candidates(records: list[dict[str, Any]]) -> None:
    if not records:
        print("No live watch candidates found for this week/snapshot.")
        return
    print("LIVE WATCH CANDIDATES")
    print(
        "| Game ID | Underdog | Lead | Flow/Micro Path | Model | Cases | SU Win% | Min EV+ Decimal | "
        "Strong Decimal | Decision |"
    )
    print("|---|---|---:|---|---|---:|---:|---:|---:|---|")
    for record in records:
        state = record["state"]
        decision = record["decision"]
        cases = decision.get("historical_cases", "n/a")
        win_rate = decision.get("historical_su_win_rate")
        win_rate_text = "n/a" if win_rate is None else f"{win_rate:.1%}"
        print(
            "| {game_id} | {dog} +{spread:.1f} | {lead:+.0f} | {path} | {model} | {cases} | "
            "{win_rate} | {min_price} | {strong_price} | {decision_name} |".format(
                game_id=state["game_id"],
                dog=state["underdog_team"],
                spread=state["pregame_spread_abs"],
                lead=state["underdog_margin_now"],
                path=state.get("flow_path_with_q3_lead")
                or state.get("path_micro")
                or state.get("binary_path_with_q3_lead")
                or "n/a",
                model=decision.get("model_source", "n/a"),
                cases=cases,
                win_rate=win_rate_text,
                min_price=fmt_decimal(decision.get("min_ev_decimal")),
                strong_price=fmt_decimal(decision.get("strong_ev_decimal")),
                decision_name=decision["decision"],
            )
        )


def list_candidates(args: argparse.Namespace) -> None:
    week_pbp = load_week_pbp(args.season, args.week)
    if week_pbp.empty:
        print("No usable play-by-play snapshots found for this week/snapshot.")
        return
    summary = load_bucket_summary(args.bucket_source)
    path_summary = load_path_summary(args.path_source)
    micro_summary = load_path_summary(args.micro_path_source)
    flow_summary = load_path_summary(args.flow_path_source)
    margin_summary = load_path_summary(args.margin_trajectory_source)
    delta_summary = load_path_summary(args.delta_trajectory_source)
    records = []
    for _, game in week_pbp.groupby("game_id", sort=False):
        try:
            state = build_current_state_from_game(game, args.snapshot)
        except SystemExit:
            continue
        if args.team and args.team.upper() not in {
            str(state["home_team"]).upper(),
            str(state["away_team"]).upper(),
            str(state["underdog_team"]).upper(),
        }:
            continue
        if state["underdog_margin_now"] <= 0:
            continue
        broad_bucket = match_bucket(summary, state)
        path_bucket = match_path_bucket(path_summary, state)
        micro_bucket = match_micro_path_bucket(micro_summary, state)
        flow_bucket = match_flow_path_bucket(flow_summary, state)
        margin_bucket_row = match_margin_trajectory_bucket(margin_summary, state)
        delta_bucket_row = match_delta_trajectory_bucket(delta_summary, state)
        bucket = select_bucket(
            flow_bucket,
            margin_bucket_row,
            delta_bucket_row,
            micro_bucket,
            path_bucket,
            broad_bucket,
            args.min_cases,
        )
        decision = make_decision(
            state,
            bucket,
            live_decimal=None,
            min_cases=args.min_cases,
            min_win_rate=args.min_win_rate,
            play_buffer=args.play_buffer,
            strong_buffer=args.strong_buffer,
        )
        records.append(
            {
                "state": state,
                "matched_bucket": bucket,
                "flow_bucket": flow_bucket,
                "margin_bucket": margin_bucket_row,
                "delta_bucket": delta_bucket_row,
                "micro_bucket": micro_bucket,
                "path_bucket": path_bucket,
                "broad_bucket": broad_bucket,
                "decision": decision,
            }
        )
    records.sort(
        key=lambda record: (
            record["decision"].get("historical_cases", 0),
            record["decision"].get("historical_su_win_rate", 0),
        ),
        reverse=True,
    )
    print_candidates(records)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a Q3 live moneyline watch card for a pregame underdog.")
    parser.add_argument("--season", type=int, required=True)
    parser.add_argument("--week", type=int, required=True)
    parser.add_argument("--game-id")
    parser.add_argument("--list-candidates", action="store_true")
    parser.add_argument("--team", help="Optional team filter for --list-candidates, e.g. DAL.")
    parser.add_argument("--snapshot", choices=SNAPSHOT_QUARTERS.keys(), default="Q3")
    parser.add_argument("--live-ml", type=float, help="American live moneyline, e.g. -120 or +145.")
    parser.add_argument("--live-decimal", type=float, help="Decimal live price, e.g. 1.85.")
    parser.add_argument("--book", default="MANUAL_MULTI_BOOK")
    parser.add_argument("--notes", default="")
    parser.add_argument("--bucket-source", type=Path, default=Path("research/in_game_underdog_study_2017_2025.csv"))
    parser.add_argument(
        "--path-source",
        type=Path,
        default=Path("research/quarter_path_underdog_study_2015_2025_binary_q3_leads.csv"),
    )
    parser.add_argument(
        "--micro-path-source",
        type=Path,
        default=Path("research/quarter_path_underdog_study_2015_2025_q3_micro.csv"),
    )
    parser.add_argument(
        "--flow-path-source",
        type=Path,
        default=Path("research/quarter_path_underdog_study_2015_2025_flow_q3_leads.csv"),
    )
    parser.add_argument(
        "--margin-trajectory-source",
        type=Path,
        default=Path("research/quarter_path_underdog_study_2015_2025_margin_q3_leads.csv"),
    )
    parser.add_argument(
        "--delta-trajectory-source",
        type=Path,
        default=Path("research/quarter_path_underdog_study_2015_2025_delta_q3_leads.csv"),
    )
    parser.add_argument("--data-root", type=Path, default=Path("data"))
    parser.add_argument("--min-cases", type=int, default=30)
    parser.add_argument("--min-win-rate", type=float, default=0.55)
    parser.add_argument("--play-buffer", type=float, default=0.03)
    parser.add_argument("--strong-buffer", type=float, default=0.07)
    parser.add_argument("--no-ledger", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.list_candidates:
        list_candidates(args)
        return
    if not args.game_id:
        raise SystemExit("Provide --game-id or use --list-candidates.")
    live_decimal, live_ml, price_format = parse_price(args)
    game = load_game_pbp(args.season, args.game_id)
    state = build_current_state_from_game(game, args.snapshot)
    summary = load_bucket_summary(args.bucket_source)
    path_summary = load_path_summary(args.path_source)
    micro_summary = load_path_summary(args.micro_path_source)
    flow_summary = load_path_summary(args.flow_path_source)
    margin_summary = load_path_summary(args.margin_trajectory_source)
    delta_summary = load_path_summary(args.delta_trajectory_source)
    broad_bucket = match_bucket(summary, state)
    path_bucket = match_path_bucket(path_summary, state)
    micro_bucket = match_micro_path_bucket(micro_summary, state)
    flow_bucket = match_flow_path_bucket(flow_summary, state)
    margin_bucket_row = match_margin_trajectory_bucket(margin_summary, state)
    delta_bucket_row = match_delta_trajectory_bucket(delta_summary, state)
    bucket = select_bucket(
        flow_bucket,
        margin_bucket_row,
        delta_bucket_row,
        micro_bucket,
        path_bucket,
        broad_bucket,
        args.min_cases,
    )
    decision = make_decision(
        state,
        bucket,
        live_decimal,
        min_cases=args.min_cases,
        min_win_rate=args.min_win_rate,
        play_buffer=args.play_buffer,
        strong_buffer=args.strong_buffer,
    )

    record = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "season": args.season,
        "week": args.week,
        "book": args.book,
        "price_format": price_format,
        "live_decimal": live_decimal,
        "live_ml": live_ml,
        "notes": args.notes,
        "state": state,
        "matched_bucket": bucket,
        "flow_bucket": flow_bucket,
        "margin_bucket": margin_bucket_row,
        "delta_bucket": delta_bucket_row,
        "micro_bucket": micro_bucket,
        "path_bucket": path_bucket,
        "broad_bucket": broad_bucket,
        "decision": decision,
    }
    if not args.no_ledger:
        record["ledger_path"] = str(write_ledger(record, args.data_root, args.season, args.week))
    print_card(record)


if __name__ == "__main__":
    main()
