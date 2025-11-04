"""Utilities for finding historical opponent analogs based on team profiles."""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import polars as pl
from polars import exceptions as pl_exceptions

from utils.config import load_settings
from utils.paths import path_for, rolling_core12_through_path

# Default weights applied when analog_profile_weights are not provided.
DEFAULT_ANALOG_WEIGHTS: Dict[str, float] = {
    "core_epa_off": 0.2,
    "core_epa_def": 0.2,
    "core_sr_off": 0.15,
    "core_sr_def": 0.15,
    "core_explosive_play_rate_off": 0.1,
    "core_third_down_conv": 0.1,
    "core_points_per_drive_diff": 0.05,
    "core_redzone_td_rate": 0.05,
    "core_pressure_rate_def": 0.05,
    "tempo": 0.05,
}


@dataclass
class AnalogMatchup:
    """Represents a prior opponent that profiles similarly to the upcoming foe."""

    opponent: str
    week: int
    similarity: float
    location: str
    epa_off: Optional[float]
    success_rate: Optional[float]
    points_per_drive_diff: Optional[float]
    points_for: Optional[float]
    points_against: Optional[float]
    winner: Optional[str]


def compute_team_analogs(
    season: int,
    current_week: int,
    team: str,
    target_opponent: str,
    *,
    top_n: int = 3,
) -> List[AnalogMatchup]:
    """
    Return up to `top_n` prior opponents whose profile resembles `target_opponent`.
    """

    if current_week <= 1:
        return []

    team = team.upper().strip()
    target_opponent = target_opponent.upper().strip()

    schedule = _load_schedule_df(season)
    history = _team_history(schedule, season, team, current_week)
    if not history:
        return []

    rolling_df, _ = _load_rolling_snapshot(season, current_week - 1)
    if rolling_df is None or rolling_df.is_empty():
        return []

    base_row = _row_for_team(rolling_df, target_opponent)
    if base_row is None:
        return []

    weights = _effective_weights(rolling_df)
    if not weights:
        return []

    stats = _feature_stats(rolling_df, weights.keys())
    base_vector = _vectorize(base_row, weights, stats)

    results: list[AnalogMatchup] = []
    for game in history:
        opponent_row = _row_for_team(rolling_df, game["opponent"])
        if opponent_row is None:
            continue

        candidate_vector = _vectorize(opponent_row, weights, stats)
        similarity = _cosine_similarity(base_vector, candidate_vector)
        if similarity <= 0.0:
            continue

        performance = _team_game_metrics(season, game["week"], team)
        points_for = performance.get("points_for")
        points_against = performance.get("points_against")
        winner: Optional[str] = None
        if points_for is not None and points_against is not None:
            # treat small differences as tie to avoid floating noise
            if abs(points_for - points_against) < 0.5:
                winner = "TIE"
            elif points_for > points_against:
                winner = team
            else:
                winner = game["opponent"]

        results.append(
            AnalogMatchup(
                opponent=game["opponent"],
                week=game["week"],
                similarity=similarity,
                location=game["location"],
                epa_off=performance.get("epa_off_mean"),
                success_rate=performance.get("success_rate_off"),
                points_per_drive_diff=performance.get("points_per_drive_diff"),
                points_for=points_for,
                points_against=points_against,
                winner=winner,
            )
        )

    results.sort(key=lambda entry: entry.similarity, reverse=True)
    return results[:top_n]


def _effective_weights(df: pl.DataFrame) -> Dict[str, float]:
    settings = load_settings()
    configured = settings.analog_profile_weights or DEFAULT_ANALOG_WEIGHTS
    usable = {key: weight for key, weight in configured.items() if key in df.columns and weight > 0}
    return usable


def _load_rolling_snapshot(
    season: int,
    through_week: int,
) -> tuple[Optional[pl.DataFrame], Optional[int]]:
    """
    Load the latest available rolling Core12 snapshot up to `through_week`.
    """
    if through_week < 1:
        return None, None

    for candidate in range(through_week, 0, -1):
        path = Path(rolling_core12_through_path(season, candidate))
        if not path.exists():
            continue
        df = pl.read_parquet(path)
        if df.is_empty():
            continue
        df = df.with_columns(pl.col("TEAM").cast(pl.Utf8).str.to_uppercase().str.strip_chars())
        return df, candidate
    return None, None


def _load_schedule_df(season: int) -> Optional[pl.DataFrame]:
    settings = load_settings()
    candidates = [
        settings.data_root / "schedules" / f"{season}.parquet",
        settings.data_root / "schedule" / f"{season}.parquet",
    ]
    for path in candidates:
        if path.exists():
            df = pl.read_parquet(path)
            if df.is_empty():
                return None
            return _normalize_schedule(df)
    return None


def _normalize_schedule(df: pl.DataFrame) -> pl.DataFrame:
    columns = set(df.columns)
    if {"home_team", "away_team"}.issubset(columns):
        base = df.select("week", "home_team", "away_team")
    elif {"team_a", "team_b"}.issubset(columns):
        base = df.select("week", "team_a", "team_b").rename({"team_a": "home_team", "team_b": "away_team"})
    elif {"TEAM", "OPP"}.issubset(columns):
        base = df.select("week", "TEAM", "OPP").rename({"TEAM": "home_team", "OPP": "away_team"})
    else:
        raise ValueError("Schedule dataset must include home/away team columns.")
    return base.with_columns(
        [
            pl.col("week").cast(pl.Int64),
            pl.col("home_team").cast(pl.Utf8).str.to_uppercase().str.strip_chars(),
            pl.col("away_team").cast(pl.Utf8).str.to_uppercase().str.strip_chars(),
        ]
    )


def _team_history(
    schedule: Optional[pl.DataFrame],
    season: int,
    team: str,
    current_week: int,
) -> list[dict[str, object]]:
    seen_pairs: set[tuple[int, str]] = set()
    records: list[dict[str, object]] = []

    if schedule is not None:
        for row in schedule.iter_rows(named=True):
            week = int(row["week"])
            if week >= current_week:
                continue
            home = row["home_team"]
            away = row["away_team"]
            if home == team:
                records.append({"week": week, "opponent": away, "location": "home"})
                seen_pairs.add((week, away))
            elif away == team:
                records.append({"week": week, "opponent": home, "location": "away"})
                seen_pairs.add((week, home))

    fallback = _team_history_from_l2(season, team, current_week, seen_pairs)
    records.extend(fallback)

    records.sort(key=lambda entry: entry["week"])
    return records


def _team_history_from_l2(
    season: int,
    team: str,
    current_week: int,
    seen_pairs: set[tuple[int, str]],
) -> list[dict[str, object]]:
    history: list[dict[str, object]] = []
    team = team.upper()

    for week in range(1, current_week):
        if any(pair[0] == week for pair in seen_pairs):
            # Week already covered by schedule data.
            continue
        try:
            path = path_for("l2", season, week)
        except ValueError:
            continue
        if not Path(path).exists():
            continue
        try:
            df = pl.read_parquet(path, columns=["posteam", "defteam"])
        except pl_exceptions.ColumnNotFoundError:
            try:
                df = pl.read_parquet(path, columns=["TEAM", "OPP"]).rename(
                    {"TEAM": "posteam", "OPP": "defteam"}
                )
            except pl_exceptions.ColumnNotFoundError:
                df = pl.read_parquet(path)
        if not {"posteam", "defteam"}.issubset(df.columns):
            continue
        if df.is_empty():
            continue

        opponents: set[str] = set()
        if "posteam" in df.columns and "defteam" in df.columns:
            offensives = (
                df.filter(pl.col("posteam") == team)
                .select("defteam")
                .drop_nulls()
                .unique()
                .to_series()
                .to_list()
            )
            opponents.update(str(value).upper() for value in offensives if value)

            defensives = (
                df.filter(pl.col("defteam") == team)
                .select("posteam")
                .drop_nulls()
                .unique()
                .to_series()
                .to_list()
            )
            opponents.update(str(value).upper() for value in defensives if value)

        for opponent in sorted(opponents):
            if (week, opponent) in seen_pairs:
                continue
            seen_pairs.add((week, opponent))
            history.append(
                {
                    "week": week,
                    "opponent": opponent,
                    "location": "neutral",
                }
            )

    return history


def _row_for_team(df: pl.DataFrame, team: str) -> Optional[dict[str, float]]:
    result = df.filter(pl.col("TEAM") == team)
    if result.is_empty():
        return None
    return result.to_dicts()[0]


def _feature_stats(df: pl.DataFrame, features: Iterable[str]) -> Dict[str, tuple[float, float]]:
    stats: Dict[str, tuple[float, float]] = {}
    for feature in features:
        series = df.get_column(feature).drop_nulls()
        if series.is_empty():
            stats[feature] = (0.0, 0.0)
            continue
        mean = float(series.mean() or 0.0)
        std = float(series.std() or 0.0)
        stats[feature] = (mean, std if math.isfinite(std) else 0.0)
    return stats


def _vectorize(
    row: dict[str, Optional[float]],
    weights: Dict[str, float],
    stats: Dict[str, tuple[float, float]],
) -> list[Optional[float]]:
    vector: list[Optional[float]] = []
    for feature, weight in weights.items():
        value = row.get(feature)
        if value is None or not math.isfinite(float(value)):
            vector.append(None)
            continue
        mean, std = stats.get(feature, (0.0, 0.0))
        if std == 0.0:
            z = 0.0
        else:
            z = (float(value) - mean) / std
        vector.append(z * weight)
    return vector


def _cosine_similarity(vec_a: list[Optional[float]], vec_b: list[Optional[float]]) -> float:
    dot = 0.0
    norm_a = 0.0
    norm_b = 0.0
    overlap = 0
    for a, b in zip(vec_a, vec_b):
        if a is None or b is None:
            continue
        dot += a * b
        norm_a += a * a
        norm_b += b * b
        overlap += 1

    if overlap == 0 or norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    cos = dot / math.sqrt(norm_a * norm_b)
    cos = max(-1.0, min(1.0, cos))
    return (cos + 1.0) / 2.0


def _team_game_metrics(season: int, week: int, team: str) -> Dict[str, Optional[float]]:
    path = path_for("l3_team_week", season, week)
    if not path.exists():
        return {}

    df = pl.read_parquet(path)
    df = df.filter(pl.col("TEAM") == team)
    if df.is_empty():
        return {}

    row = df.to_dicts()[0]
    drives = _safe_float(row.get("drives"))
    ppd_off = _safe_float(row.get("points_per_drive_off"))
    ppd_def = _safe_float(row.get("points_per_drive_def"))
    points_for = None
    points_against = None
    if drives is not None and ppd_off is not None:
        points_for = drives * ppd_off
    if drives is not None and ppd_def is not None:
        points_against = drives * ppd_def

    return {
        "epa_off_mean": _safe_float(row.get("epa_off_mean")),
        "success_rate_off": _safe_float(row.get("success_rate_off")),
        "points_per_drive_diff": _safe_float(row.get("points_per_drive_diff")),
        "points_for": points_for,
        "points_against": points_against,
    }


def _safe_float(value: Optional[float]) -> Optional[float]:
    if value is None:
        return None
    try:
        candidate = float(value)
    except (TypeError, ValueError):
        return None
    return candidate if math.isfinite(candidate) else None


__all__ = ["AnalogMatchup", "compute_team_analogs"]
