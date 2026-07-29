from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path
from typing import Any

import nfl_data_py as nfl
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.analyze_in_game_underdogs import load_regular_game_ids, underdog_side


PBP_COLUMNS = [
    "game_id",
    "play_id",
    "qtr",
    "home_team",
    "away_team",
    "total_home_score",
    "total_away_score",
    "home_score",
    "away_score",
    "spread_line",
    "home_wp",
    "away_wp",
]


def american_odds_from_probability(probability: float | None) -> float | None:
    if probability is None or math.isnan(probability) or probability <= 0 or probability >= 1:
        return None
    if probability >= 0.5:
        return -100 * probability / (1 - probability)
    return 100 * (1 - probability) / probability


def snapshot_rows(pbp: pd.DataFrame, quarter: int, label: str) -> pd.DataFrame:
    q = pbp[pbp["qtr"] == quarter].copy()
    q = q.sort_values(["game_id", "play_id"])
    return q.groupby("game_id", as_index=False).tail(1).assign(snapshot=label)


def state_from_margin(margin: float) -> str:
    if margin > 0:
        return "WIN"
    if margin < 0:
        return "LOST"
    return "TIE"


def binary_state_from_margin(margin: float) -> str:
    return "WIN" if margin > 0 else "NOT_WIN"


def period_state_from_margin(margin: float) -> str:
    if margin > 0:
        return "WIN"
    if margin < 0:
        return "LOST"
    return "TIE"


def period_binary_state_from_margin(margin: float) -> str:
    return "WIN" if margin > 0 else "NOT_WIN"


def lead_bucket(value: float) -> str:
    if value <= 0:
        return "not_leading"
    if value <= 3:
        return "1-3"
    if value <= 7:
        return "4-7"
    return "8+"


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


def spread_bucket(value: float) -> str:
    if value <= 3:
        return "<=3"
    if value <= 7:
        return "3.5-7"
    return "7.5+"


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


def enrich_game(game: pd.DataFrame, season: int) -> dict[str, Any] | None:
    game = game.sort_values("play_id")
    first = game.iloc[0]
    spread = first.get("spread_line")
    if pd.isna(spread):
        return None
    spread = float(spread)
    side = underdog_side(spread)
    if side is None:
        return None

    snapshots = {
        "q1": snapshot_rows(game, 1, "Q1"),
        "q2": snapshot_rows(game, 2, "Q2"),
        "q3": snapshot_rows(game, 3, "Q3"),
    }
    if any(frame.empty for frame in snapshots.values()):
        return None

    rows = {label: frame.iloc[0] for label, frame in snapshots.items()}
    last = game.dropna(subset=["home_score", "away_score"]).iloc[-1]

    underdog_team = first["away_team"] if side == "away" else first["home_team"]
    favorite_team = first["home_team"] if side == "away" else first["away_team"]

    def margin_at(row: pd.Series) -> float:
        home_score = float(row["total_home_score"])
        away_score = float(row["total_away_score"])
        underdog_score = away_score if side == "away" else home_score
        favorite_score = home_score if side == "away" else away_score
        return underdog_score - favorite_score

    q1_margin = margin_at(rows["q1"])
    q2_margin = margin_at(rows["q2"])
    q3_margin = margin_at(rows["q3"])
    home_final = int(last["home_score"])
    away_final = int(last["away_score"])
    underdog_final = away_final if side == "away" else home_final
    favorite_final = home_final if side == "away" else away_final
    final_margin = underdog_final - favorite_final
    q1_period_margin = q1_margin
    q2_period_margin = q2_margin - q1_margin
    q3_period_margin = q3_margin - q2_margin
    q4_period_margin = final_margin - q3_margin
    q1_to_q2_delta = q2_margin - q1_margin
    q2_to_q3_delta = q3_margin - q2_margin
    if side == "away":
        ats_margin = away_final + spread - home_final
    else:
        ats_margin = home_final - spread - away_final

    q1_state = state_from_margin(q1_margin)
    q2_state = state_from_margin(q2_margin)
    q3_state = state_from_margin(q3_margin)
    path = f"Q1_{q1_state}__Q2_{q2_state}__Q3_{q3_state}"
    q1_binary = binary_state_from_margin(q1_margin)
    q2_binary = binary_state_from_margin(q2_margin)
    q3_binary = binary_state_from_margin(q3_margin)
    p1_state = period_state_from_margin(q1_period_margin)
    p2_state = period_state_from_margin(q2_period_margin)
    p3_state = period_state_from_margin(q3_period_margin)
    p4_state = period_state_from_margin(q4_period_margin)
    p1_binary = period_binary_state_from_margin(q1_period_margin)
    p2_binary = period_binary_state_from_margin(q2_period_margin)
    p3_binary = period_binary_state_from_margin(q3_period_margin)
    p4_binary = period_binary_state_from_margin(q4_period_margin)
    binary_path = f"Q1_{q1_binary}__Q2_{q2_binary}__Q3_{q3_binary}"
    period_path = f"P1_{p1_state}__P2_{p2_state}__P3_{p3_state}"
    period_binary_path = f"P1_{p1_binary}__P2_{p2_binary}__P3_{p3_binary}"
    flow_path = (
        f"P1_{p1_binary}_AFTER_Q1_{q1_binary}__"
        f"P2_{p2_binary}_AFTER_Q2_{q2_binary}__"
        f"P3_{p3_binary}_AFTER_Q3_{q3_binary}"
    )
    margin_trajectory = (
        f"Q1_{margin_bucket(q1_margin)}__Q2_{margin_bucket(q2_margin)}__Q3_{margin_bucket(q3_margin)}"
    )
    delta_trajectory = f"Q1Q2_{delta_bucket(q1_to_q2_delta)}__Q2Q3_{delta_bucket(q2_to_q3_delta)}"
    flow_margin_trajectory = f"{flow_path}__{margin_trajectory}"
    q3_wp = rows["q3"].get("away_wp" if side == "away" else "home_wp")
    q3_wp = None if pd.isna(q3_wp) else float(q3_wp)

    return {
        "season": season,
        "game_id": first["game_id"],
        "home_team": first["home_team"],
        "away_team": first["away_team"],
        "underdog_team": underdog_team,
        "favorite_team": favorite_team,
        "underdog_side": side,
        "location": "home dog" if side == "home" else "away dog",
        "spread_line_away_perspective": spread,
        "pregame_spread_abs": abs(spread),
        "spread_bucket": spread_bucket(abs(spread)),
        "spread_micro_bucket": spread_micro_bucket(abs(spread)),
        "q1_margin": q1_margin,
        "q2_margin": q2_margin,
        "q3_margin": q3_margin,
        "q1_period_margin": q1_period_margin,
        "q2_period_margin": q2_period_margin,
        "q3_period_margin": q3_period_margin,
        "q4_period_margin": q4_period_margin,
        "q1_to_q2_delta": q1_to_q2_delta,
        "q2_to_q3_delta": q2_to_q3_delta,
        "q1_margin_bucket": margin_bucket(q1_margin),
        "q2_margin_bucket": margin_bucket(q2_margin),
        "q3_margin_bucket": margin_bucket(q3_margin),
        "q1_to_q2_delta_bucket": delta_bucket(q1_to_q2_delta),
        "q2_to_q3_delta_bucket": delta_bucket(q2_to_q3_delta),
        "final_margin": final_margin,
        "q1_state": q1_state,
        "q2_state": q2_state,
        "q3_state": q3_state,
        "q1_binary_state": q1_binary,
        "q2_binary_state": q2_binary,
        "q3_binary_state": q3_binary,
        "p1_state": p1_state,
        "p2_state": p2_state,
        "p3_state": p3_state,
        "p4_state": p4_state,
        "p1_binary_state": p1_binary,
        "p2_binary_state": p2_binary,
        "p3_binary_state": p3_binary,
        "p4_binary_state": p4_binary,
        "final_state": "WIN" if final_margin > 0 else "LOST",
        "q1_lead_bucket": lead_bucket(q1_margin),
        "q2_lead_bucket": lead_bucket(q2_margin),
        "q3_lead_bucket": lead_bucket(q3_margin),
        "path": path,
        "binary_path": binary_path,
        "period_path": period_path,
        "period_binary_path": period_binary_path,
        "flow_path": flow_path,
        "margin_trajectory": margin_trajectory,
        "delta_trajectory": delta_trajectory,
        "flow_margin_trajectory": flow_margin_trajectory,
        "path_with_q3_lead": f"{path}__Q3_LEAD_{lead_bucket(q3_margin)}",
        "binary_path_with_q3_lead": f"{binary_path}__Q3_LEAD_{lead_bucket(q3_margin)}",
        "period_binary_path_with_q3_lead": f"{period_binary_path}__Q3_LEAD_{lead_bucket(q3_margin)}",
        "flow_path_with_q3_lead": f"{flow_path}__Q3_LEAD_{lead_bucket(q3_margin)}",
        "margin_trajectory_with_q3_lead": f"{margin_trajectory}__Q3_LEAD_{lead_bucket(q3_margin)}",
        "delta_trajectory_with_q3_lead": f"{delta_trajectory}__Q3_LEAD_{lead_bucket(q3_margin)}",
        "flow_margin_trajectory_with_q3_lead": f"{flow_margin_trajectory}__Q3_LEAD_{lead_bucket(q3_margin)}",
        "underdog_won_su": final_margin > 0,
        "underdog_covered_pregame_spread": ats_margin > 0,
        "ats_margin": ats_margin,
        "q3_wp": q3_wp,
        "q3_fair_ml": american_odds_from_probability(q3_wp),
    }


def analyze(seasons: list[int], data_root: Path) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for season in seasons:
        pbp = nfl.import_pbp_data(
            [season],
            columns=PBP_COLUMNS,
            include_participation=False,
            downcast=True,
            cache=False,
        )
        game_ids = load_regular_game_ids(season, data_root)
        if game_ids:
            pbp = pbp[pbp["game_id"].isin(game_ids)].copy()
        pbp = pbp.dropna(subset=["spread_line", "home_score", "away_score"])
        for _, game in pbp.groupby("game_id", sort=False):
            row = enrich_game(game, season)
            if row:
                rows.append(row)
    return pd.DataFrame(rows)


def summarize_group(detail: pd.DataFrame, group_cols: list[str], min_cases: int) -> pd.DataFrame:
    rows = []
    grouper: str | list[str] = group_cols[0] if len(group_cols) == 1 else group_cols
    for keys, group in detail.groupby(grouper, dropna=False):
        if not isinstance(keys, tuple):
            keys = (keys,)
        cases = len(group)
        su_wins = int(group["underdog_won_su"].sum())
        covers = int(group["underdog_covered_pregame_spread"].sum())
        su_rate = su_wins / cases if cases else 0.0
        row = {col: value for col, value in zip(group_cols, keys)}
        row.update(
            {
                "cases": cases,
                "su_wins": su_wins,
                "su_win_rate": su_rate,
                "break_even_ml": american_odds_from_probability(su_rate),
                "covers": covers,
                "cover_rate_pregame_spread": covers / cases if cases else 0.0,
                "avg_final_margin": group["final_margin"].mean(),
                "median_q3_wp": group["q3_wp"].median(),
                "sample_flag": "OK" if cases >= min_cases else "SAMPLE_TOO_SMALL",
            }
        )
        rows.append(row)
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values(["cases", "su_win_rate"], ascending=[False, False])


def write_report(
    detail: pd.DataFrame,
    path_summary: pd.DataFrame,
    binary_path_summary: pd.DataFrame,
    period_path_summary: pd.DataFrame,
    period_binary_path_summary: pd.DataFrame,
    flow_path_summary: pd.DataFrame,
    margin_trajectory_summary: pd.DataFrame,
    delta_trajectory_summary: pd.DataFrame,
    q3_lead_summary: pd.DataFrame,
    binary_q3_lead_summary: pd.DataFrame,
    period_binary_q3_lead_summary: pd.DataFrame,
    flow_q3_lead_summary: pd.DataFrame,
    margin_q3_lead_summary: pd.DataFrame,
    delta_q3_lead_summary: pd.DataFrame,
    flow_margin_q3_lead_summary: pd.DataFrame,
    micro_q3_summary: pd.DataFrame,
    output: Path,
    min_cases: int,
    season_label: str,
) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# Quarter Path Pregame Underdog Study - {season_label}",
        "",
        "Scope: NFL regular season games, pregame underdogs only.",
        "",
        "A path describes whether the pregame underdog was leading, tied, or losing after Q1, Q2/H1, and Q3.",
        "",
        "## Overall",
        "",
        f"Games analyzed: {len(detail)}",
        f"Minimum cases flag: {min_cases}",
        "",
        "## Top Quarter Paths",
        "",
        "| Path | Cases | SU W-L | SU Win% | Break-even ML | Pregame ATS Cover% | Avg Final Margin | Sample |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in path_summary.head(30).to_dict("records"):
        lines.append(_summary_row(row, "path"))

    lines.extend(
        [
            "",
            "## Binary Quarter Path Matrix",
            "",
            "`NOT_WIN` means tied or losing at that snapshot.",
            "",
            "| Binary Path | Cases | SU W-L | SU Win% | Break-even ML | Pregame ATS Cover% | Avg Final Margin | Sample |",
            "|---|---:|---:|---:|---:|---:|---:|---|",
        ]
    )
    for row in binary_path_summary.to_dict("records"):
        lines.append(_summary_row(row, "binary_path"))

    lines.extend(
        [
            "",
            "## Period Quarter Path",
            "",
            "Period path means whether the pregame underdog won/lost/tied each individual quarter, not the cumulative game state.",
            "",
            "| Period Path | Cases | SU W-L | SU Win% | Break-even ML | Pregame ATS Cover% | Avg Final Margin | Sample |",
            "|---|---:|---:|---:|---:|---:|---:|---|",
        ]
    )
    for row in period_path_summary.head(30).to_dict("records"):
        lines.append(_summary_row(row, "period_path"))

    lines.extend(
        [
            "",
            "## Binary Period Quarter Path",
            "",
            "`NOT_WIN` means tied or lost that individual quarter.",
            "",
            "| Period Binary Path | Cases | SU W-L | SU Win% | Break-even ML | Pregame ATS Cover% | Avg Final Margin | Sample |",
            "|---|---:|---:|---:|---:|---:|---:|---|",
        ]
    )
    for row in period_binary_path_summary.to_dict("records"):
        lines.append(_summary_row(row, "period_binary_path"))

    lines.extend(
        [
            "",
            "## Combined Flow Path",
            "",
            "Flow path combines the individual quarter result with the cumulative state after that quarter.",
            "",
            "| Flow Path | Cases | SU W-L | SU Win% | Break-even ML | Pregame ATS Cover% | Avg Final Margin | Sample |",
            "|---|---:|---:|---:|---:|---:|---:|---|",
        ]
    )
    for row in flow_path_summary.head(40).to_dict("records"):
        lines.append(_summary_row(row, "flow_path"))

    lines.extend(
        [
            "",
            "## Margin Trajectory",
            "",
            "Margin trajectory buckets the cumulative underdog margin after Q1, Q2/H1, and Q3.",
            "",
            "| Margin Trajectory | Cases | SU W-L | SU Win% | Break-even ML | Pregame ATS Cover% | Avg Final Margin | Sample |",
            "|---|---:|---:|---:|---:|---:|---:|---|",
        ]
    )
    for row in margin_trajectory_summary.head(40).to_dict("records"):
        lines.append(_summary_row(row, "margin_trajectory"))

    lines.extend(
        [
            "",
            "## Delta Trajectory",
            "",
            "Delta trajectory buckets how the underdog margin changed from Q1 to Q2 and from Q2 to Q3.",
            "",
            "| Delta Trajectory | Cases | SU W-L | SU Win% | Break-even ML | Pregame ATS Cover% | Avg Final Margin | Sample |",
            "|---|---:|---:|---:|---:|---:|---:|---|",
        ]
    )
    for row in delta_trajectory_summary.head(30).to_dict("records"):
        lines.append(_summary_row(row, "delta_trajectory"))

    lines.extend(
        [
            "",
            "## Q3 Leading Paths With Lead Bucket",
            "",
            "| Path | Cases | SU W-L | SU Win% | Break-even ML | Pregame ATS Cover% | Avg Final Margin | Sample |",
            "|---|---:|---:|---:|---:|---:|---:|---|",
        ]
    )
    for row in q3_lead_summary.head(40).to_dict("records"):
        lines.append(_summary_row(row, "path_with_q3_lead"))

    lines.extend(
        [
            "",
            "## Binary Q3 Leading Paths",
            "",
            "| Binary Path | Cases | SU W-L | SU Win% | Break-even ML | Pregame ATS Cover% | Avg Final Margin | Sample |",
            "|---|---:|---:|---:|---:|---:|---:|---|",
        ]
    )
    for row in binary_q3_lead_summary.to_dict("records"):
        lines.append(_summary_row(row, "binary_path_with_q3_lead"))

    lines.extend(
        [
            "",
            "## Period Binary Q3 Leading Paths",
            "",
            "| Period Binary Path | Cases | SU W-L | SU Win% | Break-even ML | Pregame ATS Cover% | Avg Final Margin | Sample |",
            "|---|---:|---:|---:|---:|---:|---:|---|",
        ]
    )
    for row in period_binary_q3_lead_summary.to_dict("records"):
        lines.append(_summary_row(row, "period_binary_path_with_q3_lead"))

    lines.extend(
        [
            "",
            "## Combined Flow Q3 Leading Paths",
            "",
            "| Flow Path | Cases | SU W-L | SU Win% | Break-even ML | Pregame ATS Cover% | Avg Final Margin | Sample |",
            "|---|---:|---:|---:|---:|---:|---:|---|",
        ]
    )
    for row in flow_q3_lead_summary.head(50).to_dict("records"):
        lines.append(_summary_row(row, "flow_path_with_q3_lead"))

    lines.extend(
        [
            "",
            "## Margin Trajectory Q3 Leading Paths",
            "",
            "| Margin Trajectory | Cases | SU W-L | SU Win% | Break-even ML | Pregame ATS Cover% | Avg Final Margin | Sample |",
            "|---|---:|---:|---:|---:|---:|---:|---|",
        ]
    )
    for row in margin_q3_lead_summary.head(50).to_dict("records"):
        lines.append(_summary_row(row, "margin_trajectory_with_q3_lead"))

    lines.extend(
        [
            "",
            "## Delta Trajectory Q3 Leading Paths",
            "",
            "| Delta Trajectory | Cases | SU W-L | SU Win% | Break-even ML | Pregame ATS Cover% | Avg Final Margin | Sample |",
            "|---|---:|---:|---:|---:|---:|---:|---|",
        ]
    )
    for row in delta_q3_lead_summary.head(40).to_dict("records"):
        lines.append(_summary_row(row, "delta_trajectory_with_q3_lead"))

    lines.extend(
        [
            "",
            "## Combined Flow + Margin Q3 Leading Paths",
            "",
            "| Flow + Margin Trajectory | Cases | SU W-L | SU Win% | Break-even ML | Pregame ATS Cover% | Avg Final Margin | Sample |",
            "|---|---:|---:|---:|---:|---:|---:|---|",
        ]
    )
    for row in flow_margin_q3_lead_summary.head(50).to_dict("records"):
        lines.append(_summary_row(row, "flow_margin_trajectory_with_q3_lead"))

    lines.extend(
        [
            "",
            "## Q3 Leading Paths By Spread Micro Bucket",
            "",
            "| Path + Micro Spread | Cases | SU W-L | SU Win% | Break-even ML | Pregame ATS Cover% | Avg Final Margin | Sample |",
            "|---|---:|---:|---:|---:|---:|---:|---|",
        ]
    )
    for row in micro_q3_summary.head(50).to_dict("records"):
        lines.append(_summary_row(row, "path_micro"))

    ok_q3 = q3_lead_summary[
        (q3_lead_summary["sample_flag"] == "OK") & (q3_lead_summary["su_win_rate"] >= 0.60)
    ].copy()
    lines.extend(
        [
            "",
            "## Candidate Paths For Live Watch",
            "",
            "| Path | Cases | SU Win% | Break-even ML | Note |",
            "|---|---:|---:|---:|---|",
        ]
    )
    if ok_q3.empty:
        lines.append("| - | 0 | 0.0% | n/a | no paths met filter |")
    else:
        for row in ok_q3.sort_values(["su_win_rate", "cases"], ascending=[False, False]).head(20).to_dict(
            "records"
        ):
            lines.append(
                "| {path} | {cases} | {su:.1%} | {ml} | candidate for live_watch_card path filter |".format(
                    path=row["path_with_q3_lead"],
                    cases=int(row["cases"]),
                    su=row["su_win_rate"],
                    ml=_fmt_ml(row["break_even_ml"]),
                )
            )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- `Q2` is the halftime snapshot.",
            "- `SU Win%` is straight-up final win rate by the pregame underdog.",
            "- `Pregame ATS Cover%` uses the original pregame spread, not a live spread.",
            "- `Break-even ML` is derived from historical SU win rate, not from archived live book prices.",
            "- Paths below the minimum sample threshold should not be used as a standalone live signal.",
            "",
            "## Detail Export",
            "",
            f"CSV detail: `{output.with_suffix('.csv')}`",
            f"Path summary: `{output.with_name(output.stem + '_paths.csv')}`",
            f"Binary path summary: `{output.with_name(output.stem + '_binary_paths.csv')}`",
            f"Period path summary: `{output.with_name(output.stem + '_period_paths.csv')}`",
            f"Binary period path summary: `{output.with_name(output.stem + '_period_binary_paths.csv')}`",
            f"Combined flow path summary: `{output.with_name(output.stem + '_flow_paths.csv')}`",
            f"Margin trajectory summary: `{output.with_name(output.stem + '_margin_trajectories.csv')}`",
            f"Delta trajectory summary: `{output.with_name(output.stem + '_delta_trajectories.csv')}`",
            f"Q3 lead summary: `{output.with_name(output.stem + '_q3_leads.csv')}`",
            f"Binary Q3 lead summary: `{output.with_name(output.stem + '_binary_q3_leads.csv')}`",
            f"Period binary Q3 lead summary: `{output.with_name(output.stem + '_period_binary_q3_leads.csv')}`",
            f"Combined flow Q3 lead summary: `{output.with_name(output.stem + '_flow_q3_leads.csv')}`",
            f"Margin trajectory Q3 lead summary: `{output.with_name(output.stem + '_margin_q3_leads.csv')}`",
            f"Delta trajectory Q3 lead summary: `{output.with_name(output.stem + '_delta_q3_leads.csv')}`",
            f"Combined flow + margin Q3 lead summary: `{output.with_name(output.stem + '_flow_margin_q3_leads.csv')}`",
            f"Q3 micro spread summary: `{output.with_name(output.stem + '_q3_micro.csv')}`",
        ]
    )
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    detail.to_csv(output.with_suffix(".csv"), index=False)
    path_summary.to_csv(output.with_name(output.stem + "_paths.csv"), index=False)
    binary_path_summary.to_csv(output.with_name(output.stem + "_binary_paths.csv"), index=False)
    period_path_summary.to_csv(output.with_name(output.stem + "_period_paths.csv"), index=False)
    period_binary_path_summary.to_csv(output.with_name(output.stem + "_period_binary_paths.csv"), index=False)
    flow_path_summary.to_csv(output.with_name(output.stem + "_flow_paths.csv"), index=False)
    margin_trajectory_summary.to_csv(output.with_name(output.stem + "_margin_trajectories.csv"), index=False)
    delta_trajectory_summary.to_csv(output.with_name(output.stem + "_delta_trajectories.csv"), index=False)
    q3_lead_summary.to_csv(output.with_name(output.stem + "_q3_leads.csv"), index=False)
    binary_q3_lead_summary.to_csv(output.with_name(output.stem + "_binary_q3_leads.csv"), index=False)
    period_binary_q3_lead_summary.to_csv(
        output.with_name(output.stem + "_period_binary_q3_leads.csv"), index=False
    )
    flow_q3_lead_summary.to_csv(output.with_name(output.stem + "_flow_q3_leads.csv"), index=False)
    margin_q3_lead_summary.to_csv(output.with_name(output.stem + "_margin_q3_leads.csv"), index=False)
    delta_q3_lead_summary.to_csv(output.with_name(output.stem + "_delta_q3_leads.csv"), index=False)
    flow_margin_q3_lead_summary.to_csv(
        output.with_name(output.stem + "_flow_margin_q3_leads.csv"), index=False
    )
    micro_q3_summary.to_csv(output.with_name(output.stem + "_q3_micro.csv"), index=False)


def _summary_row(row: dict[str, Any], label_col: str) -> str:
    cases = int(row["cases"])
    wins = int(row["su_wins"])
    return (
        "| {label} | {cases} | {wins}-{losses} | {su:.1%} | {ml} | {cover:.1%} | "
        "{margin:+.1f} | {sample} |"
    ).format(
        label=row[label_col],
        cases=cases,
        wins=wins,
        losses=cases - wins,
        su=row["su_win_rate"],
        ml=_fmt_ml(row["break_even_ml"]),
        cover=row["cover_rate_pregame_spread"],
        margin=row["avg_final_margin"],
        sample=row["sample_flag"],
    )


def _fmt_ml(value: Any) -> str:
    if value is None or pd.isna(value):
        return "n/a"
    return f"{float(value):+.0f}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze quarter-by-quarter paths for NFL pregame underdogs.")
    parser.add_argument("--seasons", nargs="+", type=int, default=list(range(2015, 2026)))
    parser.add_argument("--data-root", type=Path, default=Path("data"))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--min-cases", type=int, default=30)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    detail = analyze(args.seasons, args.data_root)
    if detail.empty:
        raise SystemExit("No quarter path rows generated.")
    path_summary = summarize_group(detail, ["path"], args.min_cases)
    binary_path_summary = summarize_group(detail, ["binary_path"], args.min_cases)
    period_path_summary = summarize_group(detail, ["period_path"], args.min_cases)
    period_binary_path_summary = summarize_group(detail, ["period_binary_path"], args.min_cases)
    flow_path_summary = summarize_group(detail, ["flow_path"], args.min_cases)
    margin_trajectory_summary = summarize_group(detail, ["margin_trajectory"], args.min_cases)
    delta_trajectory_summary = summarize_group(detail, ["delta_trajectory"], args.min_cases)
    q3_lead_detail = detail[detail["q3_state"] == "WIN"].copy()
    q3_lead_summary = summarize_group(q3_lead_detail, ["path_with_q3_lead"], args.min_cases)
    binary_q3_lead_summary = summarize_group(q3_lead_detail, ["binary_path_with_q3_lead"], args.min_cases)
    period_binary_q3_lead_summary = summarize_group(
        q3_lead_detail, ["period_binary_path_with_q3_lead"], args.min_cases
    )
    flow_q3_lead_summary = summarize_group(q3_lead_detail, ["flow_path_with_q3_lead"], args.min_cases)
    margin_q3_lead_summary = summarize_group(q3_lead_detail, ["margin_trajectory_with_q3_lead"], args.min_cases)
    delta_q3_lead_summary = summarize_group(q3_lead_detail, ["delta_trajectory_with_q3_lead"], args.min_cases)
    flow_margin_q3_lead_summary = summarize_group(
        q3_lead_detail, ["flow_margin_trajectory_with_q3_lead"], args.min_cases
    )
    q3_lead_detail["path_micro"] = (
        q3_lead_detail["path_with_q3_lead"] + "__SPREAD_" + q3_lead_detail["spread_micro_bucket"]
    )
    micro_q3_summary = summarize_group(q3_lead_detail, ["path_micro"], args.min_cases)
    season_label = str(args.seasons[0]) if len(args.seasons) == 1 else f"{args.seasons[0]}_{args.seasons[-1]}"
    output = args.output or Path("research") / f"quarter_path_underdog_study_{season_label}.md"
    write_report(
        detail,
        path_summary,
        binary_path_summary,
        period_path_summary,
        period_binary_path_summary,
        flow_path_summary,
        margin_trajectory_summary,
        delta_trajectory_summary,
        q3_lead_summary,
        binary_q3_lead_summary,
        period_binary_q3_lead_summary,
        flow_q3_lead_summary,
        margin_q3_lead_summary,
        delta_q3_lead_summary,
        flow_margin_q3_lead_summary,
        micro_q3_summary,
        output,
        args.min_cases,
        season_label,
    )
    print(f"report={output}")
    print(f"detail={output.with_suffix('.csv')}")
    print(path_summary.head(15).to_string(index=False))
    print(q3_lead_summary.head(15).to_string(index=False))


if __name__ == "__main__":
    main()
