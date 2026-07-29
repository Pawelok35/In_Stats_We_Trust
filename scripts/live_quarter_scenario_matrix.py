from __future__ import annotations

import argparse
import itertools
import json
import math
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import nfl_data_py as nfl
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.analyze_in_game_underdogs import load_regular_game_ids

PBP_COLUMNS = [
    "game_id",
    "play_id",
    "season",
    "week",
    "qtr",
    "home_team",
    "away_team",
    "total_home_score",
    "total_away_score",
    "home_score",
    "away_score",
    "spread_line",
]

RESULTS = ("WIN", "LOSS", "TIE")
STATE_RESULTS = ("WIN", "LOSS", "TIE")
QUARTERS = ("q1", "q2", "q3", "q4")


@dataclass(frozen=True)
class ProbabilitySet:
    wins: int
    losses: int
    ties: int
    sample_size: int

    @property
    def win_probability(self) -> float | None:
        return self.wins / self.sample_size if self.sample_size else None

    @property
    def loss_probability(self) -> float | None:
        return self.losses / self.sample_size if self.sample_size else None

    @property
    def tie_probability(self) -> float | None:
        return self.ties / self.sample_size if self.sample_size else None


def result_from_margin(margin: float) -> str:
    if margin > 0:
        return "WIN"
    if margin < 0:
        return "LOSS"
    return "TIE"


def state_after_margin(margin: float) -> str:
    return result_from_margin(margin)


def margin_bucket(margin: float) -> str:
    if margin == 0:
        return "TIE"
    prefix = "LEAD" if margin > 0 else "TRAIL"
    value = abs(margin)
    if value <= 3:
        return f"{prefix}_1_3"
    if value <= 7:
        return f"{prefix}_4_7"
    if value <= 14:
        return f"{prefix}_8_14"
    return f"{prefix}_15_PLUS"


def spread_bucket(abs_spread: float | None) -> str:
    if abs_spread is None or math.isnan(abs_spread):
        return "UNKNOWN"
    if abs_spread <= 1.5:
        return "0.5-1.5"
    if abs_spread <= 3:
        return "2-3"
    if abs_spread <= 4.5:
        return "3.5-4.5"
    if abs_spread <= 6:
        return "5-6"
    if abs_spread <= 7:
        return "6.5-7"
    if abs_spread <= 9.5:
        return "7.5-9.5"
    if abs_spread <= 13.5:
        return "10-13.5"
    return "14+"


def season_phase(week: int) -> str:
    if week <= 5:
        return "EARLY"
    if week <= 11:
        return "MIDDLE"
    return "LATE"


def sample_quality(sample_size: int) -> str:
    if sample_size <= 0:
        return "NO_DATA"
    if sample_size < 20:
        return "VERY_LOW"
    if sample_size < 50:
        return "LOW"
    if sample_size < 100:
        return "MODERATE"
    return "STRONG"


def decimal_to_american(decimal_price: float | None) -> float | None:
    if decimal_price is None or math.isnan(decimal_price) or decimal_price <= 1:
        return None
    if decimal_price >= 2:
        return round((decimal_price - 1) * 100, 2)
    return round(-100 / (decimal_price - 1), 2)


def american_to_decimal(price: float | None) -> float | None:
    if price is None or math.isnan(price) or price == 0:
        return None
    if price > 0:
        return 1 + price / 100
    return 1 + 100 / abs(price)


def fair_decimal_no_push(win_probability: float | None) -> float | None:
    if win_probability is None or win_probability <= 0:
        return None
    return 1 / win_probability


def fair_decimal_tie_push(win_probability: float | None, loss_probability: float | None) -> float | None:
    if win_probability is None or loss_probability is None or win_probability <= 0:
        return None
    return 1 + loss_probability / win_probability


def ev_no_push(win_probability: float | None, decimal_odds: float | None) -> float | None:
    if win_probability is None or decimal_odds is None:
        return None
    return win_probability * decimal_odds - 1


def ev_tie_push(
    win_probability: float | None,
    loss_probability: float | None,
    decimal_odds: float | None,
) -> float | None:
    if win_probability is None or loss_probability is None or decimal_odds is None:
        return None
    return win_probability * (decimal_odds - 1) - loss_probability


def pct(value: float | None) -> float | None:
    return round(value * 100, 4) if value is not None else None


def round_or_none(value: float | None, digits: int = 4) -> float | None:
    return round(value, digits) if value is not None else None


def normalize_team(value: str | None) -> str | None:
    return str(value).upper() if value else None


def path_key(path: tuple[str, ...]) -> str:
    return "START" if not path else "-".join(path)


def all_paths(length: int) -> list[tuple[str, ...]]:
    return list(itertools.product(RESULTS, repeat=length))


def parse_path(raw: str | None) -> tuple[str, ...]:
    if not raw or raw.upper() == "START":
        return ()
    parts = tuple(part.strip().upper() for part in raw.replace(">", "-").split("-") if part.strip())
    invalid = [part for part in parts if part not in RESULTS]
    if invalid:
        raise SystemExit(f"Invalid path result(s): {invalid}. Use WIN/LOSS/TIE, e.g. WIN-LOSS-WIN.")
    if len(parts) > 4:
        raise SystemExit("Path can contain at most four quarter results.")
    return parts


def load_pbp(seasons: list[int], data_root: Path) -> pd.DataFrame:
    frames = []
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
            pbp = pbp[pbp["game_id"].astype(str).isin(game_ids)].copy()
        frames.append(pbp)
    data = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    return data.dropna(subset=["game_id", "qtr", "total_home_score", "total_away_score"])


def last_row_for_quarter(game: pd.DataFrame, quarter: int) -> pd.Series | None:
    rows = game[game["qtr"] == quarter].sort_values("play_id")
    rows = rows.dropna(subset=["total_home_score", "total_away_score"])
    if rows.empty:
        return None
    return rows.iloc[-1]


def favorite_side(spread_line: float | None) -> str:
    if spread_line is None or math.isnan(spread_line) or spread_line == 0:
        return "PICKEM_OR_UNKNOWN"
    # nflverse spread_line is from the away team's perspective.
    return "away" if spread_line < 0 else "home"


def team_role(side: str, spread_line: float | None) -> str:
    fav = favorite_side(spread_line)
    if fav == "PICKEM_OR_UNKNOWN":
        return "PICKEM_OR_UNKNOWN"
    return "FAVORITE" if side == fav else "UNDERDOG"


def build_team_game_rows(pbp: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for game_id, game in pbp.groupby("game_id", sort=False):
        game = game.sort_values("play_id")
        q_rows = {q: last_row_for_quarter(game, q) for q in (1, 2, 3, 4)}
        if any(row is None for row in q_rows.values()):
            continue

        first = game.iloc[0]
        last = game.dropna(subset=["home_score", "away_score"]).tail(1)
        if last.empty:
            continue
        final = last.iloc[0]

        spread_raw = first.get("spread_line")
        spread = None if pd.isna(spread_raw) else float(spread_raw)
        home = normalize_team(first["home_team"])
        away = normalize_team(first["away_team"])
        season = int(first["season"]) if not pd.isna(first.get("season")) else int(str(game_id)[:4])
        week = int(first["week"]) if not pd.isna(first.get("week")) else None

        end_scores = {
            quarter: (
                float(q_rows[quarter]["total_home_score"]),
                float(q_rows[quarter]["total_away_score"]),
            )
            for quarter in (1, 2, 3, 4)
        }
        home_final = float(final["home_score"])
        away_final = float(final["away_score"])

        home_quarter_points = {
            "q1": end_scores[1][0],
            "q2": end_scores[2][0] - end_scores[1][0],
            "q3": end_scores[3][0] - end_scores[2][0],
            "q4": end_scores[4][0] - end_scores[3][0],
        }
        away_quarter_points = {
            "q1": end_scores[1][1],
            "q2": end_scores[2][1] - end_scores[1][1],
            "q3": end_scores[3][1] - end_scores[2][1],
            "q4": end_scores[4][1] - end_scores[3][1],
        }
        home_ot_points = home_final - end_scores[4][0]
        away_ot_points = away_final - end_scores[4][1]

        for team, opponent, side in ((home, away, "home"), (away, home, "away")):
            team_q = home_quarter_points if side == "home" else away_quarter_points
            opp_q = away_quarter_points if side == "home" else home_quarter_points
            quarter_results = {
                q: result_from_margin(team_q[q] - opp_q[q])
                for q in QUARTERS
            }

            cumulative_margins = {}
            running_team = 0.0
            running_opp = 0.0
            for q in QUARTERS:
                running_team += team_q[q]
                running_opp += opp_q[q]
                cumulative_margins[f"after_{q}"] = running_team - running_opp

            team_final = home_final if side == "home" else away_final
            opp_final = away_final if side == "home" else home_final
            team_ot = home_ot_points if side == "home" else away_ot_points
            opp_ot = away_ot_points if side == "home" else home_ot_points
            role = team_role(side, spread)
            abs_spread = abs(spread) if spread is not None else None

            row = {
                "game_id": game_id,
                "season": season,
                "week": week,
                "season_phase": season_phase(week or 0),
                "team": team,
                "opponent": opponent,
                "side": side,
                "home_team": home,
                "away_team": away,
                "role": role,
                "spread_line_away_perspective": spread,
                "spread_abs": abs_spread,
                "spread_bucket": spread_bucket(abs_spread),
                "q1_result": quarter_results["q1"],
                "q2_result": quarter_results["q2"],
                "q3_result": quarter_results["q3"],
                "q4_result": quarter_results["q4"],
                "path4": path_key(tuple(quarter_results[q] for q in QUARTERS)),
                "q1_points_for": team_q["q1"],
                "q1_points_against": opp_q["q1"],
                "q2_points_for": team_q["q2"],
                "q2_points_against": opp_q["q2"],
                "q3_points_for": team_q["q3"],
                "q3_points_against": opp_q["q3"],
                "q4_points_for": team_q["q4"],
                "q4_points_against": opp_q["q4"],
                "ot_points_for": team_ot,
                "ot_points_against": opp_ot,
                "after_q1_margin": cumulative_margins["after_q1"],
                "after_q2_margin": cumulative_margins["after_q2"],
                "after_q3_margin": cumulative_margins["after_q3"],
                "after_q4_margin": cumulative_margins["after_q4"],
                "after_q1_state": state_after_margin(cumulative_margins["after_q1"]),
                "after_q2_state": state_after_margin(cumulative_margins["after_q2"]),
                "after_q3_state": state_after_margin(cumulative_margins["after_q3"]),
                "after_q4_regulation_state": state_after_margin(cumulative_margins["after_q4"]),
                "after_q1_margin_bucket": margin_bucket(cumulative_margins["after_q1"]),
                "after_q2_margin_bucket": margin_bucket(cumulative_margins["after_q2"]),
                "after_q3_margin_bucket": margin_bucket(cumulative_margins["after_q3"]),
                "after_q4_margin_bucket": margin_bucket(cumulative_margins["after_q4"]),
                "final_margin": team_final - opp_final,
                "final_state": state_after_margin(team_final - opp_final),
                "went_to_overtime": cumulative_margins["after_q4"] == 0,
            }
            rows.append(row)

    return pd.DataFrame(rows)


def apply_filters(
    rows: pd.DataFrame,
    *,
    team: str | None = None,
    opponent: str | None = None,
    sample_mode: str = "LEAGUE_WIDE",
    role: str | None = None,
    side: str | None = None,
    spread_bucket_filter: str | None = None,
    season_phase_filter: str | None = None,
) -> pd.DataFrame:
    data = rows.copy()
    team = normalize_team(team)
    opponent = normalize_team(opponent)

    if sample_mode == "TEAM_A_HISTORY":
        if not team:
            raise SystemExit("--team is required for TEAM_A_HISTORY.")
        data = data[data["team"] == team]
    elif sample_mode == "TEAM_B_HISTORY":
        if not opponent:
            raise SystemExit("--opponent is required for TEAM_B_HISTORY.")
        data = data[data["team"] == opponent]
    elif sample_mode == "HEAD_TO_HEAD":
        if not team or not opponent:
            raise SystemExit("--team and --opponent are required for HEAD_TO_HEAD.")
        data = data[
            ((data["team"] == team) & (data["opponent"] == opponent))
            | ((data["team"] == opponent) & (data["opponent"] == team))
        ]
    elif sample_mode != "LEAGUE_WIDE":
        raise SystemExit(f"Unsupported sample mode: {sample_mode}")

    if role:
        data = data[data["role"] == role.upper()]
    if side:
        data = data[data["side"] == side.lower()]
    if spread_bucket_filter:
        data = data[data["spread_bucket"] == spread_bucket_filter]
    if season_phase_filter:
        data = data[data["season_phase"] == season_phase_filter.upper()]
    return data


def probability_set(group: pd.DataFrame, column: str) -> ProbabilitySet:
    counts = group[column].value_counts().to_dict() if not group.empty else {}
    return ProbabilitySet(
        wins=int(counts.get("WIN", 0)),
        losses=int(counts.get("LOSS", 0)),
        ties=int(counts.get("TIE", 0)),
        sample_size=len(group),
    )


def add_probability_fields(prefix: str, probs: ProbabilitySet) -> dict[str, Any]:
    fair_no_push = fair_decimal_no_push(probs.win_probability)
    fair_push = fair_decimal_tie_push(probs.win_probability, probs.loss_probability)
    return {
        f"{prefix}_win_count": probs.wins,
        f"{prefix}_loss_count": probs.losses,
        f"{prefix}_tie_count": probs.ties,
        f"{prefix}_win_probability": round_or_none(probs.win_probability),
        f"{prefix}_loss_probability": round_or_none(probs.loss_probability),
        f"{prefix}_tie_probability": round_or_none(probs.tie_probability),
        f"{prefix}_win_pct": pct(probs.win_probability),
        f"{prefix}_loss_pct": pct(probs.loss_probability),
        f"{prefix}_tie_pct": pct(probs.tie_probability),
        f"{prefix}_fair_decimal_tie_is_loss": round_or_none(fair_no_push),
        f"{prefix}_fair_american_tie_is_loss": decimal_to_american(fair_no_push),
        f"{prefix}_fair_decimal_tie_is_push": round_or_none(fair_push),
        f"{prefix}_fair_american_tie_is_push": decimal_to_american(fair_push),
    }


def build_full_path_matrix(data: pd.DataFrame) -> pd.DataFrame:
    total = len(data)
    rows = []
    for path in all_paths(4):
        path_filter = data
        for idx, result in enumerate(path, start=1):
            path_filter = path_filter[path_filter[f"q{idx}_result"] == result]
        sample = len(path_filter)
        regulation = probability_set(path_filter, "after_q4_regulation_state")
        final = probability_set(path_filter, "final_state")
        rows.append(
            {
                "q1_result": path[0],
                "q2_result": path[1],
                "q3_result": path[2],
                "q4_result": path[3],
                "completed_path": path_key(path),
                "sample_size": sample,
                "sample_quality": sample_quality(sample),
                "data_status": "AVAILABLE" if sample else "NOT_OBSERVED",
                "path_frequency": round_or_none(sample / total if total else None),
                "path_frequency_pct": pct(sample / total if total else None),
                **add_probability_fields("regulation", regulation),
                **add_probability_fields("final", final),
            }
        )
    return pd.DataFrame(rows)


def build_transition_matrix(data: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for completed_len in range(0, 4):
        next_quarter_idx = completed_len + 1
        next_quarter = f"Q{next_quarter_idx}"
        candidate_paths = [()] if completed_len == 0 else all_paths(completed_len)
        for path in candidate_paths:
            group = data
            for idx, result in enumerate(path, start=1):
                group = group[group[f"q{idx}_result"] == result]
            probs = probability_set(group, f"q{next_quarter_idx}_result")
            after_col = (
                "after_q4_regulation_state"
                if next_quarter_idx == 4
                else f"after_q{next_quarter_idx}_state"
            )
            cumulative = probability_set(group, after_col)
            final = probability_set(group, "final_state")
            for result in RESULTS:
                count = int((group[f"q{next_quarter_idx}_result"] == result).sum()) if not group.empty else 0
                rows.append(
                    {
                        "completed_quarters": completed_len,
                        "completed_path": path_key(path),
                        "next_quarter": next_quarter,
                        "next_result": result,
                        "count": count,
                        "sample_size": len(group),
                        "sample_quality": sample_quality(len(group)),
                        "data_status": "AVAILABLE" if len(group) else "NOT_OBSERVED",
                        "probability": round_or_none(count / len(group) if len(group) else None),
                        "probability_pct": pct(count / len(group) if len(group) else None),
                        **add_probability_fields("next_quarter", probs),
                        **add_probability_fields(f"after_{next_quarter.lower()}", cumulative),
                        **add_probability_fields("final", final),
                    }
                )
    return pd.DataFrame(rows)


def build_margin_bucket_matrix(data: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for completed_len in (1, 2, 3):
        candidate_paths = all_paths(completed_len)
        margin_col = f"after_q{completed_len}_margin_bucket"
        for path in candidate_paths:
            group = data
            for idx, result in enumerate(path, start=1):
                group = group[group[f"q{idx}_result"] == result]
            for bucket, bucket_group in group.groupby(margin_col, dropna=False):
                final = probability_set(bucket_group, "final_state")
                rows.append(
                    {
                        "completed_quarters": completed_len,
                        "completed_path": path_key(path),
                        "margin_bucket": bucket,
                        "sample_size": len(bucket_group),
                        "sample_quality": sample_quality(len(bucket_group)),
                        **add_probability_fields("final", final),
                    }
                )
    return pd.DataFrame(rows)


def build_segment_matrix(data: pd.DataFrame) -> pd.DataFrame:
    group_cols = ["role", "side", "spread_bucket", "season_phase"]
    rows = []
    for keys, group in data.groupby(group_cols, dropna=False):
        for completed_len in (1, 2, 3):
            for path in all_paths(completed_len):
                subgroup = group
                for idx, result in enumerate(path, start=1):
                    subgroup = subgroup[subgroup[f"q{idx}_result"] == result]
                if subgroup.empty:
                    continue
                next_idx = completed_len + 1
                next_probs = probability_set(subgroup, f"q{next_idx}_result")
                final = probability_set(subgroup, "final_state")
                rows.append(
                    {
                        "role": keys[0],
                        "side": keys[1],
                        "spread_bucket": keys[2],
                        "season_phase": keys[3],
                        "completed_quarters": completed_len,
                        "completed_path": path_key(path),
                        "next_quarter": f"Q{next_idx}",
                        "sample_size": len(subgroup),
                        "sample_quality": sample_quality(len(subgroup)),
                        **add_probability_fields("next_quarter", next_probs),
                        **add_probability_fields("final", final),
                    }
                )
    return pd.DataFrame(rows)


def lookup_payload(transition: pd.DataFrame, margin_matrix: pd.DataFrame) -> dict[str, Any]:
    lookup: dict[str, Any] = {}
    grouped = transition.groupby(["completed_path", "next_quarter"], dropna=False)
    for (completed_path, next_quarter), group in grouped:
        first = group.iloc[0]
        lookup[str(completed_path)] = {
            "completed_path": completed_path,
            "completed_quarters": int(first["completed_quarters"]),
            "next_quarter": next_quarter,
            "sample_size": int(first["sample_size"]),
            "sample_quality": first["sample_quality"],
            "next_quarter_distribution": {
                "win_probability": first["next_quarter_win_probability"],
                "loss_probability": first["next_quarter_loss_probability"],
                "tie_probability": first["next_quarter_tie_probability"],
                "win_pct": first["next_quarter_win_pct"],
                "loss_pct": first["next_quarter_loss_pct"],
                "tie_pct": first["next_quarter_tie_pct"],
                "fair_decimal_tie_is_loss": first["next_quarter_fair_decimal_tie_is_loss"],
                "fair_decimal_tie_is_push": first["next_quarter_fair_decimal_tie_is_push"],
            },
            "cumulative_after_next_quarter": {
                "win_probability": first[f"after_{str(next_quarter).lower()}_win_probability"],
                "loss_probability": first[f"after_{str(next_quarter).lower()}_loss_probability"],
                "tie_probability": first[f"after_{str(next_quarter).lower()}_tie_probability"],
                "win_pct": first[f"after_{str(next_quarter).lower()}_win_pct"],
                "loss_pct": first[f"after_{str(next_quarter).lower()}_loss_pct"],
                "tie_pct": first[f"after_{str(next_quarter).lower()}_tie_pct"],
            },
            "final_including_overtime": {
                "win_probability": first["final_win_probability"],
                "loss_probability": first["final_loss_probability"],
                "tie_probability": first["final_tie_probability"],
                "win_pct": first["final_win_pct"],
                "loss_pct": first["final_loss_pct"],
                "tie_pct": first["final_tie_pct"],
                "fair_decimal_tie_is_loss": first["final_fair_decimal_tie_is_loss"],
                "fair_decimal_tie_is_push": first["final_fair_decimal_tie_is_push"],
            },
        }

    margin_lookup: dict[str, list[dict[str, Any]]] = {}
    for _, row in margin_matrix.iterrows():
        margin_lookup.setdefault(str(row["completed_path"]), []).append(
            {
                "margin_bucket": row["margin_bucket"],
                "sample_size": int(row["sample_size"]),
                "sample_quality": row["sample_quality"],
                "final_win_probability": row["final_win_probability"],
                "final_win_pct": row["final_win_pct"],
                "final_fair_decimal_tie_is_loss": row["final_fair_decimal_tie_is_loss"],
            }
        )
    for key, value in margin_lookup.items():
        lookup.setdefault(key, {})["margin_bucket_overrides"] = value
    return lookup


def event_probability_from_lookup(
    node: dict[str, Any],
    event: str,
    settlement: str,
) -> tuple[float | None, float | None, float | None]:
    event = event.upper()
    if event == "TEAM_A_WIN_NEXT_QUARTER":
        block = node["next_quarter_distribution"]
    elif event == "TEAM_A_LEAD_AFTER_NEXT_QUARTER":
        block = node["cumulative_after_next_quarter"]
    elif event == "TEAM_A_WIN_FINAL":
        block = node["final_including_overtime"]
    else:
        raise SystemExit(
            "Unsupported --event. Use TEAM_A_WIN_NEXT_QUARTER, "
            "TEAM_A_LEAD_AFTER_NEXT_QUARTER, or TEAM_A_WIN_FINAL."
        )
    win_p = block.get("win_probability")
    loss_p = block.get("loss_probability")
    tie_p = block.get("tie_probability")
    if settlement == "TIE_IS_LOSS" and tie_p is not None and loss_p is not None:
        loss_p = loss_p + tie_p
        tie_p = 0.0
    return win_p, loss_p, tie_p


def write_summary(
    path: Path,
    *,
    seasons: list[int],
    sample_mode: str,
    rows: pd.DataFrame,
    output_dir: Path,
) -> None:
    lines = [
        "# NFL Quarter Scenario Matrix",
        "",
        f"Generated at UTC: `{datetime.now(timezone.utc).isoformat()}`",
        f"Seasons: `{min(seasons)}-{max(seasons)}`",
        f"Sample mode: `{sample_mode}`",
        f"Team-game rows: `{len(rows)}`",
        "",
        "## Files",
        "",
        f"- `{output_dir / 'team_game_quarter_rows.csv'}`",
        f"- `{output_dir / 'full_quarter_path_matrix.csv'}`",
        f"- `{output_dir / 'quarter_transition_matrix.csv'}`",
        f"- `{output_dir / 'margin_bucket_matrix.csv'}`",
        f"- `{output_dir / 'segment_transition_matrix.csv'}`",
        f"- `{output_dir / 'scenario_lookup.json'}`",
        "",
        "## Notes",
        "",
        "- Quarter Reset View liczy wynik pojedynczej kwarty od 0:0.",
        "- Cumulative Game View liczy skumulowany wynik meczu po danej kwarcie.",
        "- Dogrywka nie jest doliczana do Q4; final_including_overtime jest osobnym polem.",
        "- Skrypt nie pobiera live kursow. Kurs live wpisujesz recznie przez parametry lookup.",
        "- Male sample size oznacza wyzsza niepewnosc, nie automatyczny blad.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build NFL live quarter scenario matrix.")
    parser.add_argument("--start-season", type=int, default=2016)
    parser.add_argument("--end-season", type=int, default=2025)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument(
        "--sample-mode",
        choices=["LEAGUE_WIDE", "TEAM_A_HISTORY", "TEAM_B_HISTORY", "HEAD_TO_HEAD"],
        default="LEAGUE_WIDE",
    )
    parser.add_argument("--team", help="Team A code for filtered samples and lookup context.")
    parser.add_argument("--opponent", help="Team B/opponent code for filtered samples.")
    parser.add_argument("--role", choices=["FAVORITE", "UNDERDOG", "PICKEM_OR_UNKNOWN"])
    parser.add_argument("--side", choices=["home", "away"])
    parser.add_argument("--spread-bucket", help="Optional exact spread bucket filter, e.g. 2-3.")
    parser.add_argument("--season-phase", choices=["EARLY", "MIDDLE", "LATE"])
    parser.add_argument("--lookup-path", help="Completed path, e.g. WIN or WIN-LOSS-WIN.")
    parser.add_argument(
        "--event",
        choices=["TEAM_A_WIN_NEXT_QUARTER", "TEAM_A_LEAD_AFTER_NEXT_QUARTER", "TEAM_A_WIN_FINAL"],
        default="TEAM_A_WIN_FINAL",
    )
    parser.add_argument(
        "--settlement",
        choices=["TIE_IS_LOSS", "TIE_IS_PUSH"],
        default="TIE_IS_LOSS",
    )
    parser.add_argument("--live-decimal", type=float)
    parser.add_argument("--live-ml", type=float)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    seasons = list(range(args.start_season, args.end_season + 1))
    output_dir = args.output_dir or Path("research") / "live_quarter_scenario_matrix" / (
        f"{args.start_season}_{args.end_season}_{args.sample_mode.lower()}"
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    pbp = load_pbp(seasons, Path("data"))
    rows = build_team_game_rows(pbp)
    filtered = apply_filters(
        rows,
        team=args.team,
        opponent=args.opponent,
        sample_mode=args.sample_mode,
        role=args.role,
        side=args.side,
        spread_bucket_filter=args.spread_bucket,
        season_phase_filter=args.season_phase,
    )
    if filtered.empty:
        raise SystemExit("No historical rows after filters.")

    full_matrix = build_full_path_matrix(filtered)
    transition = build_transition_matrix(filtered)
    margin_matrix = build_margin_bucket_matrix(filtered)
    segment_matrix = build_segment_matrix(filtered)
    lookup = lookup_payload(transition, margin_matrix)

    filtered.to_csv(output_dir / "team_game_quarter_rows.csv", index=False)
    full_matrix.to_csv(output_dir / "full_quarter_path_matrix.csv", index=False)
    transition.to_csv(output_dir / "quarter_transition_matrix.csv", index=False)
    margin_matrix.to_csv(output_dir / "margin_bucket_matrix.csv", index=False)
    segment_matrix.to_csv(output_dir / "segment_transition_matrix.csv", index=False)
    (output_dir / "scenario_lookup.json").write_text(
        json.dumps(lookup, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    write_summary(
        output_dir / "summary.md",
        seasons=seasons,
        sample_mode=args.sample_mode,
        rows=filtered,
        output_dir=output_dir,
    )

    print(f"[OK] rows={len(filtered)} output={output_dir}")

    if args.lookup_path:
        path = path_key(parse_path(args.lookup_path))
        node = lookup.get(path)
        if not node:
            raise SystemExit(f"No lookup node for path={path}.")
        decimal = args.live_decimal if args.live_decimal is not None else american_to_decimal(args.live_ml)
        win_p, loss_p, tie_p = event_probability_from_lookup(node, args.event, args.settlement)
        if args.settlement == "TIE_IS_PUSH":
            fair_decimal = fair_decimal_tie_push(win_p, loss_p)
            ev = ev_tie_push(win_p, loss_p, decimal)
        else:
            fair_decimal = fair_decimal_no_push(win_p)
            ev = ev_no_push(win_p, decimal)
        payload = {
            "path": path,
            "event": args.event,
            "settlement": args.settlement,
            "sample_size": node["sample_size"],
            "sample_quality": node["sample_quality"],
            "win_probability": round_or_none(win_p),
            "loss_probability": round_or_none(loss_p),
            "tie_probability": round_or_none(tie_p),
            "fair_decimal": round_or_none(fair_decimal),
            "fair_american": decimal_to_american(fair_decimal),
            "live_decimal": round_or_none(decimal),
            "live_american": decimal_to_american(decimal),
            "ev": round_or_none(ev),
            "ev_pct": pct(ev),
        }
        print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
