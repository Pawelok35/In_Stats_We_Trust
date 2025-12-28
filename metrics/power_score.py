"""Computation of PowerScore derived from Core12 metrics and configuration weights."""

from __future__ import annotations

from typing import Mapping

import polars as pl

from utils.config import load_settings
from utils.contracts import validate_df
from utils.guards import check_no_inf, check_no_nan_in_keys
from utils.logging import get_logger
from utils.manifest import write_manifest
from utils.paths import path_for

logger = get_logger(__name__)

TEAM_ALIASES: Mapping[str, str] = {
    "Arizona Cardinals": "ARI",
    "Atlanta Falcons": "ATL",
    "Baltimore Ravens": "BAL",
    "Buffalo Bills": "BUF",
    "Carolina Panthers": "CAR",
    "Chicago Bears": "CHI",
    "Cincinnati Bengals": "CIN",
    "Cleveland Browns": "CLE",
    "Dallas Cowboys": "DAL",
    "Denver Broncos": "DEN",
    "Detroit Lions": "DET",
    "Green Bay Packers": "GB",
    "Houston Texans": "HOU",
    "Indianapolis Colts": "IND",
    "Jacksonville Jaguars": "JAX",
    "Kansas City Chiefs": "KC",
    "Las Vegas Raiders": "LV",
    "Los Angeles Chargers": "LAC",
    "Los Angeles Rams": "LAR",
    "Miami Dolphins": "MIA",
    "Minnesota Vikings": "MIN",
    "New England Patriots": "NE",
    "New Orleans Saints": "NO",
    "New York Giants": "NYG",
    "New York Jets": "NYJ",
    "Philadelphia Eagles": "PHI",
    "Pittsburgh Steelers": "PIT",
    "San Francisco 49ers": "SF",
    "Seattle Seahawks": "SEA",
    "Tampa Bay Buccaneers": "TB",
    "Tennessee Titans": "TEN",
    "Washington Commanders": "WAS",
    "AAA": "BAL",
    "BBB": "MIA",
}


def _weight_mapping() -> Mapping[str, float]:
    settings = load_settings()
    weights = settings.weights
    return {
        "offense_epa": float(weights.get("offense_epa", 0.3)),
        "offense_success_rate": float(weights.get("offense_success_rate", 0.25)),
        "defense_epa": float(weights.get("defense_epa", 0.2)),
        "tempo": float(weights.get("tempo", 0.25)),
    }


def _normalize_team_alias(team: str | None) -> str | None:
    if team is None:
        return None
    normalized = TEAM_ALIASES.get(team, team)
    if isinstance(normalized, str):
        normalized = normalized.strip()
    if not normalized:
        return None
    return normalized.upper()


def compute(df_core12: pl.DataFrame, season: int, week: int) -> pl.DataFrame:
    """Compute the PowerScore aggregate from Core12 metrics."""

    if not isinstance(df_core12, pl.DataFrame):
        raise TypeError("compute expects a polars.DataFrame")

    validate_df(df_core12, "L4_CORE12")

    weights = _weight_mapping()
    logger.debug("Using PowerScore weights: %s", weights)

    if df_core12.is_empty():
        logger.warning(
            "PowerScore compute received empty dataframe for season=%s week=%s", season, week
        )
        df = pl.DataFrame(
            {
                "season": pl.Series([], dtype=pl.Int64),
                "week": pl.Series([], dtype=pl.Int64),
                "team": pl.Series([], dtype=pl.Utf8),
                "power_score": pl.Series([], dtype=pl.Float64),
            }
        )
    else:
        tempo_expr = (
            pl.col("tempo").cast(pl.Float64).fill_null(0.0)
            if "tempo" in df_core12.columns
            else pl.lit(0.0).cast(pl.Float64)
        )

        working = df_core12.with_columns(
            [
                pl.lit(season).cast(pl.Int64).alias("season"),
                pl.lit(week).cast(pl.Int64).alias("week"),
                pl.col("TEAM").cast(pl.Utf8),
                pl.col("core_epa_off").cast(pl.Float64),
                pl.col("core_epa_def").cast(pl.Float64),
                pl.col("core_sr_off").cast(pl.Float64),
                pl.col("core_sr_def").cast(pl.Float64),
                pl.col("core_ed_sr_off").cast(pl.Float64),
                pl.col("core_third_down_conv").cast(pl.Float64),
                tempo_expr.alias("tempo"),
            ]
        )

        power_score = (
            pl.col("core_epa_off") * weights["offense_epa"]
            + pl.col("core_sr_off") * weights["offense_success_rate"]
            + pl.col("core_epa_def") * weights["defense_epa"]
            + pl.col("tempo") * weights["tempo"]
        )

        df = working.with_columns(power_score.alias("PowerScore")).select(
            ["season", "week", "TEAM", "PowerScore"]
        )

    rename_map: dict[str, str] = {}
    if "TEAM" in df.columns:
        rename_map["TEAM"] = "team"
    if "PowerScore" in df.columns:
        rename_map["PowerScore"] = "power_score"
    if rename_map:
        df = df.rename(rename_map)

    if "team" in df.columns:
        df = df.with_columns(
            pl.col("team").map_elements(
                _normalize_team_alias,
                return_dtype=pl.Utf8,
                skip_nulls=False,
            )
        )

    check_no_nan_in_keys(df, ["season", "week", "team"])
    check_no_inf(df)

    out_path = path_for("l4_powerscore", season, week)
    df.write_parquet(out_path)

    write_manifest(
        layer="l4_powerscore",
        path=out_path,
        rows=df.height,
        cols=df.width,
        season=season,
        week=week,
        files=[out_path],  
    )

    logger.info("PowerScore metrics written to %s (rows=%s cols=%s)", out_path, df.height, df.width)
    return df
