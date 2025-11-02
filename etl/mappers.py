"""Mapping utilities converting raw data into canonical ETL layer schemas."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import polars as pl

from utils.logging import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class ColumnDefinition:
    name: str
    dtype: pl.DataType
    optional: bool = False


L1_SCHEMA: tuple[ColumnDefinition, ...] = (
    ColumnDefinition("season", pl.Int64),
    ColumnDefinition("week", pl.Int64),
    ColumnDefinition("game_id", pl.Utf8),
    ColumnDefinition("play_id", pl.Int64),
    ColumnDefinition("posteam", pl.Utf8),
    ColumnDefinition("defteam", pl.Utf8),
    ColumnDefinition("drive", pl.Int64),
    ColumnDefinition("play_type", pl.Utf8, optional=True),
    ColumnDefinition("epa", pl.Float64),
    ColumnDefinition("success", pl.Float64),
    ColumnDefinition("yardline_100", pl.Float64, optional=True),
    ColumnDefinition("down", pl.Int64, optional=True),
    ColumnDefinition("distance", pl.Int64, optional=True),
    ColumnDefinition("yards_gained", pl.Float64, optional=True),
    ColumnDefinition("interception", pl.Int64, optional=True),
    ColumnDefinition("fumble_lost", pl.Int64, optional=True),
    ColumnDefinition("touchdown", pl.Int64, optional=True),
    ColumnDefinition("play_description", pl.Utf8, optional=True),
)

_DISTANCE_ALIASES = ("distance", "ydstogo")
_TEAM_ALIAS_MAP = {
    "WAS": "WSH",
    "SD": "LAC",
    "OAK": "LV",
    "STL": "LA",
    "JAC": "JAX",
    "AAA": "BAL",
    "BBB": "MIA",
}


def _resolve_column(df: pl.DataFrame, candidates: Iterable[str]) -> str | None:
    for candidate in candidates:
        if candidate in df.columns:
            return candidate
    return None


def canonicalize_l1(df: pl.DataFrame, season: int, week: int) -> pl.DataFrame:
    """
    Remap raw play-level data into the canonical L1 schema.

    Rules:
    - We keep all key play-by-play info needed downstream (yards, turnovers, TD, text).
    - We try multiple alias names from the source and map them into our canonical columns.
    - We ALWAYS emit all columns from L1_SCHEMA, even if we have to fill defaults.
    """

    if not isinstance(df, pl.DataFrame):
        raise TypeError("canonicalize_l1 expects a polars.DataFrame input")

    # Handle empty case gracefully
    if df.is_empty():
        # Build an empty frame with the correct schema
        schema = {col.name: col.dtype for col in L1_SCHEMA}
        return pl.DataFrame(schema=schema)

    working = df.clone()

    # --- alias helpers -------------------------------------------------

    def _pick_alias(source_df: pl.DataFrame, aliases: list[str]) -> str | None:
        """
        Return the first column name from `aliases` that exists in `source_df`.
        If none exist, returns None.
        """
        for cand in aliases:
            if cand in source_df.columns:
                return cand
        return None

    # Map each logical field we care about to the first matching source column.
    # We'll then .with_columns() to create our canonical names.

    alias_plan = {
        # yards gained on this play
        "yards_gained": [
            "yards_gained", "yards_gained_play", "yds_gained", "yards_gained_raw", "gain", "yards",
        ],

        # was the pass intercepted / did offense throw an INT
        "interception": [
            "interception", "interception_thrown", "intercepted", "pass_intercepted", "int_thrown",
        ],

        # offense lost a fumble on this play
        "fumble_lost": [
            "fumble_lost", "lost_fumble", "fumble_lost_offense", "fumble_forced_lost", "fumble_lost_play",
        ],

        # did offense score TD on this play
        "touchdown": [
            "touchdown", "td", "td_offense", "offense_td", "rush_touchdown", "pass_touchdown",
            "td_team", "touchdown_scored",
        ],

        # human-readable play text / description
        "play_description": [
            "play_description", "desc", "play_desc", "pbp_desc", "playtext",
        ],

        # we already had "distance", so keep old behavior:
        "distance": [
            "distance", "ydstogo", "yards_to_go", "yds_to_go",
        ],
    }

    # We'll collect expressions to add/override.
    new_cols = {}

    # distance special-case: we already had code that renamed one alias to 'distance'.
    # We keep that behavior.
    distance_src = _pick_alias(working, alias_plan["distance"])
    if distance_src and distance_src != "distance":
        new_cols["distance"] = pl.col(distance_src).cast(pl.Int64)

    # yards_gained
    yg_src = _pick_alias(working, alias_plan["yards_gained"])
    if yg_src:
        new_cols["yards_gained"] = pl.col(yg_src).cast(pl.Float64)
    else:
        new_cols["yards_gained"] = pl.lit(0.0).cast(pl.Float64)

    # interception
    int_src = _pick_alias(working, alias_plan["interception"])
    if int_src:
        new_cols["interception"] = (
            pl.col(int_src)
            .cast(pl.Int64)
            .fill_null(0)
        )
    else:
        new_cols["interception"] = pl.lit(0).cast(pl.Int64)

    # fumble_lost
    fum_src = _pick_alias(working, alias_plan["fumble_lost"])
    if fum_src:
        new_cols["fumble_lost"] = (
            pl.col(fum_src)
            .cast(pl.Int64)
            .fill_null(0)
        )
    else:
        new_cols["fumble_lost"] = pl.lit(0).cast(pl.Int64)

    # touchdown
    td_src = _pick_alias(working, alias_plan["touchdown"])
    if td_src:
        new_cols["touchdown"] = (
            pl.col(td_src)
            .cast(pl.Int64)
            .fill_null(0)
        )
    else:
        new_cols["touchdown"] = pl.lit(0).cast(pl.Int64)

    # play_description
    desc_src = _pick_alias(working, alias_plan["play_description"])
    if desc_src:
        new_cols["play_description"] = pl.col(desc_src).cast(pl.Utf8)
    else:
        new_cols["play_description"] = pl.lit("").cast(pl.Utf8)

    # Add season/week literals if not already present
    # (this matches what your old code was doing)
    new_cols["season"] = pl.lit(season).cast(pl.Int64)
    new_cols["week"] = pl.lit(week).cast(pl.Int64)

    # Actually apply/override these columns.
    working = working.with_columns(
        [expr.alias(name) for name, expr in new_cols.items()]
    )

    # Now select EXACTLY columns defined in L1_SCHEMA, in that order.
    final_cols = []
    for col_def in L1_SCHEMA:
        col_name = col_def.name
        # if column doesn't exist after aliasing, create a default of right dtype
        if col_name not in working.columns:
            if col_def.dtype == pl.Int64:
                final_cols.append(pl.lit(0).cast(pl.Int64).alias(col_name))
            elif col_def.dtype == pl.Float64:
                final_cols.append(pl.lit(0.0).cast(pl.Float64).alias(col_name))
            elif col_def.dtype == pl.Utf8:
                final_cols.append(pl.lit("").cast(pl.Utf8).alias(col_name))
            else:
                # fallback – shouldn't really happen
                final_cols.append(pl.lit(None).cast(col_def.dtype).alias(col_name))
        else:
            final_cols.append(pl.col(col_name).cast(col_def.dtype).alias(col_name))

    working = working.select(final_cols)

    return working



def apply_team_aliases(df: pl.DataFrame, columns: Iterable[str]) -> pl.DataFrame:
    """Normalize historical team aliases to modern abbreviations."""

    replacements = {}
    for column in columns:
        if column not in df.columns:
            continue
        replacements[column] = (
            pl.col(column)
            .map_elements(lambda value: _TEAM_ALIAS_MAP.get(value, value), return_dtype=pl.Utf8)
            .str.to_uppercase()
        )
    return df.with_columns(list(replacements.values()))


import polars as pl

def prepare_l2(df_l1: pl.DataFrame, season: int, week: int) -> pl.DataFrame:
    """
    Take canonical L1 (per-play) and produce cleaned L2 with derived flags.

    Sprint 2 rules:
    - yards_gained: kopiujemy z L1 (koniec placeholderów 0.0)
    - is_turnover: interception OR fumble_lost
    - is_offensive_td: flaga touchdown z L1 (koniec zgadywania po tekście)
    - success_bin: binarna wersja success
    - TEAM / OPP: ustaw z posteam / defteam jeśli nie ma
    - filtrujemy tylko wskazany season/week
    - deduplikujemy (season, week, game_id, play_id)
    """

    if df_l1.is_empty():
        return pl.DataFrame(
            {
                "season": pl.Series([], dtype=pl.Int64),
                "week": pl.Series([], dtype=pl.Int64),
                "game_id": pl.Series([], dtype=pl.Utf8),
                "play_id": pl.Series([], dtype=pl.Int64),
                "TEAM": pl.Series([], dtype=pl.Utf8),
                "OPP": pl.Series([], dtype=pl.Utf8),
                "drive": pl.Series([], dtype=pl.Int64),
                "play_type": pl.Series([], dtype=pl.Utf8),
                "epa": pl.Series([], dtype=pl.Float64),
                "success": pl.Series([], dtype=pl.Float64),
                "yards_gained": pl.Series([], dtype=pl.Float64),
                "is_turnover": pl.Series([], dtype=pl.Int64),
                "is_offensive_td": pl.Series([], dtype=pl.Int64),
                "success_bin": pl.Series([], dtype=pl.Int64),
            }
        )

    working = df_l1.clone()

    # --- enforce season/week from args (safety if source had more weeks mixed)
    working = working.filter(
        (pl.col("season") == season) & (pl.col("week") == week)
    )

    # --- derive TEAM / OPP if not already present
    if "TEAM" not in working.columns:
        working = working.with_columns([
            pl.col("posteam").cast(pl.Utf8).alias("TEAM"),
        ])
    if "OPP" not in working.columns:
        working = working.with_columns([
            pl.col("defteam").cast(pl.Utf8).alias("OPP"),
        ])

    # --- core derived columns we need downstream
    working = working.with_columns([
        # yards_gained (REAL from L1, fallback 0.0 if null)
        pl.col("yards_gained")
        .cast(pl.Float64)
        .fill_null(0.0)
        .alias("yards_gained"),

        # turnover if INT or fumble_lost
        (
            (pl.col("interception").fill_null(0) > 0)
            | (pl.col("fumble_lost").fill_null(0) > 0)
        )
        .cast(pl.Int64)
        .alias("is_turnover"),

        # TD for offense directly from touchdown flag
        (pl.col("touchdown").fill_null(0) > 0)
        .cast(pl.Int64)
        .alias("is_offensive_td"),
    ])

    # success_bin (1/0) based on success > 0
    if "success" in working.columns:
        working = working.with_columns(
            (pl.col("success") > 0)
            .cast(pl.Int64)
            .alias("success_bin")
        )

    # --- now select canonical L2 columns (order matters for downstream)
    base_cols = [
        "season",
        "week",
        "game_id",
        "play_id",
        "TEAM",
        "OPP",
        "drive",
        "play_type",
        "epa",
        "success",
        "yards_gained",
        "is_turnover",
        "is_offensive_td",
        "success_bin",
    ]

    existing_cols = [c for c in base_cols if c in working.columns]
    cleaned = working.select(existing_cols)

    # --- deduplicate keys (safety)
    cleaned = cleaned.unique(
        subset=["season", "week", "game_id", "play_id"],
        keep="first",
    )

    return cleaned
