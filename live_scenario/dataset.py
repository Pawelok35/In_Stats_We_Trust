"""Build, validate, and load the durable Live Scenario processed dataset."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from live_scenario.data_provider import (
    live_scenario_manifest_path,
    load_raw_pbp,
    load_raw_schedules,
    processed_dataset_path,
    raw_pbp_path,
    raw_schedules_path,
)
from live_scenario.spread import role_from_team_a_spread
from live_scenario.state import (
    cumulative_state_from_margin,
    margin_bucket_v2,
    path_key,
    result_from_margin,
    season_phase_v2,
    spread_bucket,
)

PROCESSED_MIN_TEAM_GAME_ROWS = 1000
NON_OT_RECONCILIATION_REPORT = "score_reconciliation_non_ot_mismatches.md"
REQUIRED_PBP_COLUMNS = {
    "game_id",
    "play_id",
    "qtr",
    "home_team",
    "away_team",
    "total_home_score",
    "total_away_score",
    "home_score",
    "away_score",
}


@dataclass(frozen=True)
class LiveScenarioDatasetStatus:
    status: str
    reason: str
    manifest: dict[str, Any] | None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def normalize_team(team: Any) -> str:
    if pd.isna(team):
        return ""
    value = str(team).strip().upper()
    return {"OAK": "LV", "SD": "LAC", "STL": "LA"}.get(value, value)


def normalize_pbp_columns(pbp: pd.DataFrame) -> pd.DataFrame:
    data = pbp.copy()
    rename = {}
    if "quarter" in data.columns and "qtr" not in data.columns:
        rename["quarter"] = "qtr"
    if "old_game_id" in data.columns and "game_id" not in data.columns:
        rename["old_game_id"] = "game_id"
    if rename:
        data = data.rename(columns=rename)
    missing = sorted(REQUIRED_PBP_COLUMNS - set(data.columns))
    if missing:
        raise ValueError(f"PBP missing required columns: {missing}")
    return data


def completed_regular_games(schedules: pd.DataFrame, seasons: list[int]) -> pd.DataFrame:
    if schedules.empty:
        return schedules
    data = schedules.copy()
    if "season" in data.columns:
        data = data[data["season"].astype(int).isin(seasons)]
    if "game_type" in data.columns:
        data = data[data["game_type"].astype(str).str.upper() == "REG"]
    if {"home_score", "away_score"}.issubset(data.columns):
        data = data.dropna(subset=["home_score", "away_score"])
    return data


def _last_row_for_quarter(game: pd.DataFrame, quarter: int) -> pd.Series | None:
    rows = game[game["qtr"].astype(int) == quarter].sort_values("play_id")
    if rows.empty:
        return None
    score_rows = rows.dropna(subset=["total_home_score", "total_away_score"])
    if score_rows.empty:
        return None
    return score_rows.iloc[-1]


def _schedule_lookup(schedules: pd.DataFrame) -> dict[str, dict[str, Any]]:
    if schedules.empty or "game_id" not in schedules.columns:
        return {}
    return {
        str(row["game_id"]): row.to_dict()
        for _, row in schedules.drop_duplicates("game_id").iterrows()
    }


def _source_spread(row: pd.Series, schedule_row: dict[str, Any] | None) -> float | None:
    for source in (row, schedule_row or {}):
        for col in ("spread_line", "spread"):
            if col in source and not pd.isna(source[col]):
                return float(source[col])
    return None


def _final_score(
    row: pd.Series, schedule_row: dict[str, Any] | None, side: str
) -> tuple[float, float]:
    if schedule_row and not pd.isna(schedule_row.get("home_score")):
        home_final = float(schedule_row["home_score"])
        away_final = float(schedule_row["away_score"])
    else:
        home_final = float(row["home_score"])
        away_final = float(row["away_score"])
    return (home_final, away_final) if side == "home" else (away_final, home_final)


def _schedule_overtime(schedule_row: dict[str, Any] | None, after_q4_margin: float) -> bool:
    if schedule_row:
        overtime = schedule_row.get("overtime")
        if not pd.isna(overtime):
            return bool(overtime)
    return after_q4_margin == 0


def _analyzed_team_spread(source_spread_line: float | None, side: str) -> float | None:
    if source_spread_line is None:
        return None
    # nflverse spread_line is from away-team perspective: negative = away favorite.
    return source_spread_line if side == "away" else -source_spread_line


def _last_scoring_play_payload(game: pd.DataFrame) -> dict[str, Any]:
    sorted_game = game.sort_values("play_id").copy()
    score_change = (
        sorted_game["total_home_score"].fillna(method="ffill").diff().fillna(0).ne(0)
        | sorted_game["total_away_score"].fillna(method="ffill").diff().fillna(0).ne(0)
    )
    sp = (
        pd.to_numeric(sorted_game["sp"], errors="coerce").fillna(0)
        if "sp" in sorted_game.columns
        else pd.Series(0, index=sorted_game.index)
    )
    scoring = sorted_game[
        score_change | (sp == 1)
    ].dropna(subset=["total_home_score", "total_away_score"])
    if scoring.empty:
        scoring = sorted_game.dropna(subset=["total_home_score", "total_away_score"])
    if scoring.empty:
        return {
            "play_id": None,
            "qtr": None,
            "time": None,
            "desc": None,
            "home_score": None,
            "away_score": None,
        }
    row = scoring.iloc[-1]
    return {
        "play_id": float(row["play_id"]) if not pd.isna(row.get("play_id")) else None,
        "qtr": int(row["qtr"]) if not pd.isna(row.get("qtr")) else None,
        "time": str(row.get("time")) if not pd.isna(row.get("time")) else None,
        "desc": str(row.get("desc")) if not pd.isna(row.get("desc")) else None,
        "home_score": float(row["total_home_score"]),
        "away_score": float(row["total_away_score"]),
    }


def _reconciliation_status(
    *,
    after_q4_home_score: float,
    after_q4_away_score: float,
    schedule_row: dict[str, Any] | None,
) -> tuple[str, dict[str, float | None], dict[str, float | None], bool, list[str]]:
    schedule_score = {
        "home": (
            float(schedule_row["home_score"])
            if schedule_row and not pd.isna(schedule_row.get("home_score"))
            else None
        ),
        "away": (
            float(schedule_row["away_score"])
            if schedule_row and not pd.isna(schedule_row.get("away_score"))
            else None
        ),
    }
    pbp_score = {"home": after_q4_home_score, "away": after_q4_away_score}
    if schedule_score["home"] is None or schedule_score["away"] is None:
        return "SCHEDULE_FINAL_MISSING", pbp_score, schedule_score, False, [
            "schedule_final_score_missing"
        ]

    schedule_margin = schedule_score["home"] - schedule_score["away"]
    pbp_margin = after_q4_home_score - after_q4_away_score
    is_ot = _schedule_overtime(schedule_row, pbp_margin)
    if round(schedule_margin, 6) == round(pbp_margin, 6):
        return "MATCH", pbp_score, schedule_score, True, []
    if is_ot:
        return "MISMATCH_OT_EXPECTED", pbp_score, schedule_score, True, [
            "final_score_includes_overtime"
        ]
    return "MISMATCH_NON_OT", pbp_score, schedule_score, False, [
        "pbp_after_q4_score_differs_from_schedule_final_without_overtime"
    ]


def build_team_game_scenario_rows(
    pbp: pd.DataFrame,
    schedules: pd.DataFrame,
    *,
    seasons: list[int],
    data_cutoff_utc: str | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    data = normalize_pbp_columns(pbp)
    completed = completed_regular_games(schedules, seasons)
    valid_game_ids = (
        set(completed["game_id"].dropna().astype(str)) if not completed.empty else set()
    )
    if valid_game_ids:
        data = data[data["game_id"].astype(str).isin(valid_game_ids)].copy()
    data = data.dropna(subset=["game_id", "qtr", "total_home_score", "total_away_score"])
    schedule_by_game = _schedule_lookup(completed)

    rows: list[dict[str, Any]] = []
    excluded: list[dict[str, str]] = []
    for game_id, game in data.groupby("game_id", sort=False):
        game_id = str(game_id)
        game = game.sort_values("play_id")
        q_rows = {q: _last_row_for_quarter(game, q) for q in (1, 2, 3, 4)}
        if any(row is None for row in q_rows.values()):
            excluded.append({"game_id": game_id, "reason": "missing_quarter_score"})
            continue

        first = game.iloc[0]
        schedule_row = schedule_by_game.get(game_id)
        home = normalize_team(first["home_team"])
        away = normalize_team(first["away_team"])
        season = (
            int(first["season"])
            if "season" in first and not pd.isna(first["season"])
            else int(game_id[:4])
        )
        week = int(first["week"]) if "week" in first and not pd.isna(first["week"]) else None
        gameday = schedule_row.get("gameday") if schedule_row else None
        source_spread = _source_spread(first, schedule_row)

        end_scores = {
            q: (float(q_rows[q]["total_home_score"]), float(q_rows[q]["total_away_score"]))
            for q in (1, 2, 3, 4)
        }
        after_q4_home_score, after_q4_away_score = end_scores[4]
        reconciliation_status, pbp_score, schedule_score, play_events_eligible, dq_warnings = (
            _reconciliation_status(
                after_q4_home_score=after_q4_home_score,
                after_q4_away_score=after_q4_away_score,
                schedule_row=schedule_row,
            )
        )
        last_scoring_play = _last_scoring_play_payload(game)
        home_q = {
            "q1": end_scores[1][0],
            "q2": end_scores[2][0] - end_scores[1][0],
            "q3": end_scores[3][0] - end_scores[2][0],
            "q4": end_scores[4][0] - end_scores[3][0],
        }
        away_q = {
            "q1": end_scores[1][1],
            "q2": end_scores[2][1] - end_scores[1][1],
            "q3": end_scores[3][1] - end_scores[2][1],
            "q4": end_scores[4][1] - end_scores[3][1],
        }

        for team, opponent, side in ((home, away, "home"), (away, home, "away")):
            team_q = home_q if side == "home" else away_q
            opp_q = away_q if side == "home" else home_q
            team_final, opp_final = _final_score(first, schedule_row, side)
            cumulative_team = 0.0
            cumulative_opp = 0.0
            cumulative: dict[str, float] = {}
            quarter_results = {}
            cumulative_states = {}
            margin_buckets = {}
            for q in ("q1", "q2", "q3", "q4"):
                quarter_results[q] = result_from_margin(team_q[q] - opp_q[q])
                cumulative_team += team_q[q]
                cumulative_opp += opp_q[q]
                margin = cumulative_team - cumulative_opp
                cumulative[f"after_{q}_team_score"] = cumulative_team
                cumulative[f"after_{q}_opponent_score"] = cumulative_opp
                cumulative[f"after_{q}_margin"] = margin
                cumulative_states[f"after_{q}_state_v2"] = cumulative_state_from_margin(margin)
                margin_buckets[f"after_{q}_margin_bucket_v2"] = margin_bucket_v2(margin)

            team_spread = _analyzed_team_spread(source_spread, side)
            exact_spread = abs(team_spread) if team_spread is not None else None
            team_role = role_from_team_a_spread(team_spread)
            spread_bucket_value = spread_bucket(exact_spread)
            prefix = {"FAVORITE": "FAV", "UNDERDOG": "DOG", "PICKEM": "PK"}.get(team_role)
            prefixed_bucket = f"{prefix}_{spread_bucket_value}" if prefix else "UNKNOWN"

            rows.append(
                {
                    "game_id": game_id,
                    "season": season,
                    "week": week,
                    "season_phase": season_phase_v2(week) if week and week <= 18 else "PLAYOFFS",
                    "gameday": (
                        str(gameday) if gameday is not None and not pd.isna(gameday) else None
                    ),
                    "team": team,
                    "opponent": opponent,
                    "side": side,
                    "home_team": home,
                    "away_team": away,
                    "source_spread_line": source_spread,
                    "spread_line_away_perspective": source_spread,
                    "team_a_closing_spread": team_spread,
                    "opponent_closing_spread": -team_spread if team_spread is not None else None,
                    "team_a_role": team_role,
                    "role": team_role,
                    "exact_spread": exact_spread,
                    "spread_bucket": spread_bucket_value,
                    "team_a_spread_bucket": prefixed_bucket,
                    "spread_source": "nflverse_schedules_or_pbp",
                    "spread_quality": "CLOSING_OR_SOURCE_LINE",
                    "score_reconciliation_status": reconciliation_status,
                    "pbp_after_q4_score": (
                        f"{pbp_score['away']:.0f}-{pbp_score['home']:.0f}"
                        if pbp_score["away"] is not None and pbp_score["home"] is not None
                        else None
                    ),
                    "schedule_final_score": (
                        f"{schedule_score['away']:.0f}-{schedule_score['home']:.0f}"
                        if schedule_score["away"] is not None
                        and schedule_score["home"] is not None
                        else None
                    ),
                    "play_level_events_eligible": play_events_eligible,
                    "data_quality_warnings": dq_warnings,
                    "last_scoring_play_id": last_scoring_play["play_id"],
                    "last_scoring_play_qtr": last_scoring_play["qtr"],
                    "last_scoring_play_time": last_scoring_play["time"],
                    "last_scoring_play_desc": last_scoring_play["desc"],
                    "last_scoring_play_score": (
                        f"{last_scoring_play['away_score']:.0f}-{last_scoring_play['home_score']:.0f}"
                        if last_scoring_play["away_score"] is not None
                        and last_scoring_play["home_score"] is not None
                        else None
                    ),
                    "q1_result": quarter_results["q1"],
                    "q2_result": quarter_results["q2"],
                    "q3_result": quarter_results["q3"],
                    "q4_result": quarter_results["q4"],
                    "quarter_result_path4": path_key(
                        tuple(quarter_results[q] for q in ("q1", "q2", "q3", "q4"))
                    ),
                    "q1_points_for": team_q["q1"],
                    "q1_points_against": opp_q["q1"],
                    "q2_points_for": team_q["q2"],
                    "q2_points_against": opp_q["q2"],
                    "q3_points_for": team_q["q3"],
                    "q3_points_against": opp_q["q3"],
                    "q4_points_for": team_q["q4"],
                    "q4_points_against": opp_q["q4"],
                    **cumulative,
                    **cumulative_states,
                    **margin_buckets,
                    "cumulative_state_path4": path_key(
                        tuple(
                            cumulative_states[f"after_{q}_state_v2"]
                            for q in ("q1", "q2", "q3", "q4")
                        )
                    ),
                    "final_margin": team_final - opp_final,
                    "final_state": result_from_margin(team_final - opp_final),
                    "went_to_overtime": _schedule_overtime(
                        schedule_row,
                        cumulative["after_q4_margin"],
                    ),
                }
            )

    processed = pd.DataFrame(rows)
    if data_cutoff_utc and "gameday" in processed.columns:
        cutoff = pd.to_datetime(data_cutoff_utc, utc=True, errors="coerce")
        dates = pd.to_datetime(processed["gameday"], utc=True, errors="coerce")
        processed = processed[dates <= cutoff].copy()

    return processed, {"excluded_games": excluded}


def score_reconciliation_report_path(data_root: Path) -> Path:
    return data_root / "live_scenario" / "reports" / NON_OT_RECONCILIATION_REPORT


def write_score_reconciliation_report(rows: pd.DataFrame, data_root: Path) -> Path:
    report_path = score_reconciliation_report_path(data_root)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Live Scenario Score Reconciliation - Non-OT Mismatches",
        "",
        "Policy: final_state/final_margin use schedules final score. "
        "Q2/Q3 state may remain from PBP when complete. "
        "MISMATCH_NON_OT rows are not automatically removed from all samples, "
        "but they are not eligible for play-level events that require a complete "
        "later PBP sequence.",
        "",
    ]
    if rows.empty or "score_reconciliation_status" not in rows.columns:
        lines.append("No reconciliation fields found.")
        report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return report_path

    mismatches = (
        rows[rows["score_reconciliation_status"] == "MISMATCH_NON_OT"]
        .sort_values(["season", "week", "game_id", "team"])
        .drop_duplicates("game_id")
    )
    lines.append(f"Total problem games: {len(mismatches)}")
    lines.append("")
    for _, row in mismatches.iterrows():
        diff = f"{row['pbp_after_q4_score']} -> {row['schedule_final_score']}"
        lines.extend(
            [
                f"## {row['game_id']}",
                "",
                f"- season: {int(row['season'])}",
                f"- week: {int(row['week']) if not pd.isna(row['week']) else 'UNKNOWN'}",
                f"- teams: {row['away_team']} at {row['home_team']}",
                f"- PBP score after Q4: {row['pbp_after_q4_score']}",
                f"- schedules final score: {row['schedule_final_score']}",
                f"- difference: {diff}",
                "- last valid scoring play in PBP:",
                f"  - play_id: {row.get('last_scoring_play_id')}",
                f"  - qtr/time: {row.get('last_scoring_play_qtr')} / "
                f"{row.get('last_scoring_play_time')}",
                f"  - score: {row.get('last_scoring_play_score')}",
                f"  - desc: {row.get('last_scoring_play_desc')}",
                "- probable cause: PBP cumulative Q4 score does not reconcile with schedules final "
                "score despite no overtime flag; likely late scoring/stat-correction or source "
                "score-field inconsistency. Do not use for complete later play-level "
                "sequence events "
                "without manual review.",
                "",
            ]
        )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path


def validate_processed_dataset(
    rows: pd.DataFrame,
    schedules: pd.DataFrame,
    *,
    seasons: list[int],
) -> dict[str, Any]:
    warnings = []
    errors = []
    seasons_present = (
        sorted(int(v) for v in rows["season"].dropna().unique()) if not rows.empty else []
    )
    missing_seasons = [season for season in seasons if season not in seasons_present]
    if missing_seasons:
        errors.append(f"missing_seasons={missing_seasons}")
    if 2015 in seasons and 2015 not in seasons_present:
        errors.append("season_2015_missing")
    if 2020 in seasons and 2020 not in seasons_present:
        errors.append("season_2020_missing")

    completed = completed_regular_games(schedules, seasons)
    completed_game_ids = (
        set(completed["game_id"].dropna().astype(str)) if not completed.empty else set()
    )
    processed_game_ids = set(rows["game_id"].dropna().astype(str)) if "game_id" in rows else set()
    missing_games = sorted(completed_game_ids - processed_game_ids)
    extra_games = sorted(processed_game_ids - completed_game_ids)
    if missing_games:
        warnings.append(f"processed_missing_completed_games={len(missing_games)}")
    if extra_games:
        errors.append(f"processed_has_extra_games={len(extra_games)}")

    if {"game_id", "team"}.issubset(rows.columns):
        counts = rows.groupby("game_id")["team"].nunique()
        bad_counts = counts[counts != 2]
        if not bad_counts.empty:
            errors.append(f"games_without_two_team_observations={len(bad_counts)}")
    if len(rows) < PROCESSED_MIN_TEAM_GAME_ROWS:
        errors.append(f"processed_dataset_too_small={len(rows)}")
    if rows.duplicated(["game_id", "team"]).any():
        errors.append("duplicate_game_team_rows")
    for q in (1, 2, 3, 4):
        required = {f"after_q{q}_team_score", f"after_q{q}_opponent_score"}
        if not required.issubset(rows.columns):
            errors.append(f"missing_cumulative_score_q{q}")

    if not rows.empty and {
        "q1_points_for",
        "q2_points_for",
        "q3_points_for",
        "q4_points_for",
        "after_q4_team_score",
    }.issubset(rows.columns):
        total = rows[["q1_points_for", "q2_points_for", "q3_points_for", "q4_points_for"]].sum(
            axis=1
        )
        mismatches = (total.round(6) != rows["after_q4_team_score"].round(6)).sum()
        if mismatches:
            errors.append(f"quarter_sum_mismatch={int(mismatches)}")

    if "score_reconciliation_status" in rows.columns:
        non_ot_mismatches = int((rows["score_reconciliation_status"] == "MISMATCH_NON_OT").sum())
        if non_ot_mismatches:
            warnings.append(f"score_reconciliation_mismatch_non_ot_observations={non_ot_mismatches}")

    return {
        "status": "READY" if not errors else "FAILED",
        "errors": errors,
        "warnings": warnings,
        "seasons_present": seasons_present,
        "missing_seasons": missing_seasons,
        "unique_completed_games": len(completed_game_ids),
        "unique_processed_games": len(processed_game_ids),
        "team_game_observations": int(len(rows)),
    }


def write_manifest(
    data_root: Path,
    *,
    provider_name: str,
    provider_version: str,
    seasons_requested: list[int],
    pbp_rows_per_season: dict[int, int],
    rows: pd.DataFrame,
    validation: dict[str, Any],
    data_cutoff_utc: str | None,
) -> dict[str, Any]:
    manifest = {
        "source_provider": provider_name,
        "source_version": provider_version,
        "seasons_requested": seasons_requested,
        "seasons_present": validation["seasons_present"],
        "missing_seasons": validation["missing_seasons"],
        "raw_pbp_rows_per_season": {str(k): int(v) for k, v in pbp_rows_per_season.items()},
        "unique_completed_games": validation["unique_completed_games"],
        "unique_processed_games": validation["unique_processed_games"],
        "team_game_observations": validation["team_game_observations"],
        "excluded_games": validation.get("warnings", []),
        "build_timestamp_utc": utc_now(),
        "data_cutoff_utc": data_cutoff_utc,
        "validation_status": validation["status"],
        "errors": validation["errors"],
        "warnings": validation["warnings"],
        "processed_dataset": str(processed_dataset_path(data_root)),
    }
    path = live_scenario_manifest_path(data_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def load_manifest(data_root: Path) -> dict[str, Any] | None:
    path = live_scenario_manifest_path(data_root)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def dataset_status(
    data_root: Path, *, seasons: list[int] | None = None
) -> LiveScenarioDatasetStatus:
    manifest = load_manifest(data_root)
    if manifest is None:
        return LiveScenarioDatasetStatus("FAILED", "manifest_missing", None)
    if manifest.get("validation_status") != "READY":
        return LiveScenarioDatasetStatus("FAILED", "manifest_status_failed", manifest)
    if seasons:
        missing = [
            season for season in seasons if season not in manifest.get("seasons_present", [])
        ]
        if missing:
            return LiveScenarioDatasetStatus("FAILED", f"missing_seasons={missing}", manifest)
    if int(manifest.get("team_game_observations", 0)) < PROCESSED_MIN_TEAM_GAME_ROWS:
        return LiveScenarioDatasetStatus("FAILED", "processed_dataset_too_small", manifest)
    if not processed_dataset_path(data_root).exists():
        return LiveScenarioDatasetStatus("FAILED", "processed_dataset_missing", manifest)
    return LiveScenarioDatasetStatus("READY", "ready", manifest)


def save_raw_pbp(data_root: Path, season: int, pbp: pd.DataFrame, *, force: bool = False) -> Path:
    path = raw_pbp_path(data_root, season)
    if path.exists() and not force:
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    pbp.to_parquet(path, index=False)
    return path


def save_raw_schedules(data_root: Path, schedules: pd.DataFrame, *, force: bool = False) -> Path:
    path = raw_schedules_path(data_root)
    if path.exists() and not force:
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    schedules.to_parquet(path, index=False)
    return path


def rebuild_processed_dataset(
    data_root: Path,
    *,
    seasons: list[int],
    provider_name: str,
    provider_version: str,
    data_cutoff_utc: str | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    pbp = load_raw_pbp(data_root, seasons)
    schedules = load_raw_schedules(data_root)
    rows, _audit = build_team_game_scenario_rows(
        pbp,
        schedules,
        seasons=seasons,
        data_cutoff_utc=data_cutoff_utc,
    )
    out = processed_dataset_path(data_root)
    out.parent.mkdir(parents=True, exist_ok=True)
    rows.to_parquet(out, index=False)
    reconciliation_report = write_score_reconciliation_report(rows, data_root)
    validation = validate_processed_dataset(rows, schedules, seasons=seasons)
    pbp_rows_per_season = (
        {int(k): int(v) for k, v in pbp.groupby("season").size().to_dict().items()}
        if "season" in pbp.columns and not pbp.empty
        else {}
    )
    manifest = write_manifest(
        data_root,
        provider_name=provider_name,
        provider_version=provider_version,
        seasons_requested=seasons,
        pbp_rows_per_season=pbp_rows_per_season,
        rows=rows,
        validation=validation,
        data_cutoff_utc=data_cutoff_utc,
    )
    manifest["score_reconciliation_report"] = str(reconciliation_report)
    live_scenario_manifest_path(data_root).write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return rows, manifest
