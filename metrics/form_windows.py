from pathlib import Path

import polars as pl

from utils.data_cutoff import (
    AVAILABLE,
    CUTOFF_VIOLATION,
    INSUFFICIENT_CURRENT_SEASON_DATA,
    MISSING_SOURCE_DATA,
    PARTIAL_WINDOW,
    DataCutoff,
    duplicate_count,
    validate_pre_game_cutoff,
)


def _empty_team_weeks_frame() -> pl.DataFrame:
    """
    Return an empty frame matching the subset of L3 columns used for form calculations.
    """
    return pl.DataFrame(
        {
            "season": pl.Series([], dtype=pl.Int64),
            "week": pl.Series([], dtype=pl.Int64),
            "TEAM": pl.Series([], dtype=pl.Utf8),
            "epa_off_mean": pl.Series([], dtype=pl.Float64),
            "success_rate_off": pl.Series([], dtype=pl.Float64),
            "epa_def_mean": pl.Series([], dtype=pl.Float64),
            "success_rate_def": pl.Series([], dtype=pl.Float64),
            "tempo": pl.Series([], dtype=pl.Float64),
            "pass_rate_off": pl.Series([], dtype=pl.Float64),
            "pass_success_rate_off": pl.Series([], dtype=pl.Float64),
            "pass_success_rate_def": pl.Series([], dtype=pl.Float64),
            "rush_success_rate_off": pl.Series([], dtype=pl.Float64),
            "rush_success_rate_def": pl.Series([], dtype=pl.Float64),
            "explosive_play_rate_off": pl.Series([], dtype=pl.Float64),
            "explosive_play_rate_def": pl.Series([], dtype=pl.Float64),
            "third_down_conv_off": pl.Series([], dtype=pl.Float64),
            "third_down_conv_def": pl.Series([], dtype=pl.Float64),
            "redzone_td_rate_off": pl.Series([], dtype=pl.Float64),
            "redzone_td_rate_def": pl.Series([], dtype=pl.Float64),
            "pressure_rate_def": pl.Series([], dtype=pl.Float64),
            "pressure_rate_allowed": pl.Series([], dtype=pl.Float64),
            "avg_start_yd100_off": pl.Series([], dtype=pl.Float64),
            "avg_start_yd100_def": pl.Series([], dtype=pl.Float64),
            "start_field_position_edge": pl.Series([], dtype=pl.Float64),
            "points_per_drive_off": pl.Series([], dtype=pl.Float64),
            "points_per_drive_def": pl.Series([], dtype=pl.Float64),
            "points_per_drive_diff": pl.Series([], dtype=pl.Float64),
            "game_id": pl.Series([], dtype=pl.Utf8),
        }
    )


def _load_team_weeks(season: int, current_week: int) -> pl.DataFrame:
    """
    Load all l3_team_week/<season>/<week>.parquet for weeks < current_week
    and return one big DataFrame with columns:
    [season, week, TEAM, epa_off_mean, success_rate_off, epa_def_mean,
     success_rate_def, tempo]
    """
    required_columns: list[tuple[str, pl.DataType]] = [
        ("TEAM", pl.Utf8),
        ("epa_off_mean", pl.Float64),
        ("success_rate_off", pl.Float64),
        ("epa_def_mean", pl.Float64),
        ("success_rate_def", pl.Float64),
        ("tempo", pl.Float64),
        ("pass_rate_off", pl.Float64),
        ("pass_success_rate_off", pl.Float64),
        ("pass_success_rate_def", pl.Float64),
        ("rush_success_rate_off", pl.Float64),
        ("rush_success_rate_def", pl.Float64),
        ("explosive_play_rate_off", pl.Float64),
        ("explosive_play_rate_def", pl.Float64),
        ("third_down_conv_off", pl.Float64),
        ("third_down_conv_def", pl.Float64),
        ("redzone_td_rate_off", pl.Float64),
        ("redzone_td_rate_def", pl.Float64),
        ("pressure_rate_def", pl.Float64),
        ("pressure_rate_allowed", pl.Float64),
        ("avg_start_yd100_off", pl.Float64),
        ("avg_start_yd100_def", pl.Float64),
        ("start_field_position_edge", pl.Float64),
        ("points_per_drive_off", pl.Float64),
        ("points_per_drive_def", pl.Float64),
        ("points_per_drive_diff", pl.Float64),
    ]

    cutoff = DataCutoff(season=season, analysis_week=current_week, strict_mode=True)
    dfs = []
    for wk in range(1, current_week):
        p = Path(f"data/l3_team_week/{season}/{wk}.parquet")
        if not p.exists():
            # skip weeks we don't have yet
            continue
        df_raw = pl.read_parquet(p)
        cutoff_check = validate_pre_game_cutoff(df_raw, cutoff)
        if cutoff_check["status"] == CUTOFF_VIOLATION:
            raise ValueError(
                "CUTOFF_VIOLATION in form windows: "
                f"{p} contains max_source_week={cutoff_check['max_source_week']} "
                f"for analysis_week={current_week}"
            )
        if "week" in df_raw.columns:
            df_raw = df_raw.filter(pl.col("week") < current_week)
        if "season" in df_raw.columns:
            df_raw = df_raw.filter(pl.col("season") == season)
        if df_raw.is_empty():
            continue
        duplicate_keys = (
            ["season", "week", "TEAM", "game_id"]
            if "game_id" in df_raw.columns
            else ["season", "week", "TEAM"]
        )
        duplicates = duplicate_count(df_raw, duplicate_keys)
        if duplicates:
            raise ValueError(
                f"Duplicate rolling source rows detected in {p}: "
                f"duplicates={duplicates}, key={duplicate_keys}"
            )
        # ensure all required columns exist, filling missing ones with nulls
        select_exprs = []
        for col_name, dtype in required_columns:
            if col_name in df_raw.columns:
                select_exprs.append(pl.col(col_name).cast(dtype).alias(col_name))
            else:
                select_exprs.append(pl.lit(None).cast(dtype).alias(col_name))
        if "game_id" in df_raw.columns:
            select_exprs.append(pl.col("game_id").cast(pl.Utf8).alias("game_id"))
        else:
            select_exprs.append(pl.lit(None).cast(pl.Utf8).alias("game_id"))
        if "week" in df_raw.columns:
            select_exprs.append(pl.col("week").cast(pl.Int64).alias("_source_week"))
        else:
            select_exprs.append(pl.lit(wk).cast(pl.Int64).alias("_source_week"))
        df_w = df_raw.select(select_exprs).with_columns(
            [
                pl.lit(season).alias("season"),
                pl.col("_source_week").cast(pl.Int64).alias("week"),
            ]
        ).drop("_source_week")
        dfs.append(df_w)

    if not dfs:
        return _empty_team_weeks_frame()

    return pl.concat(dfs, how="vertical")


def _summarize_window(df_team: pl.DataFrame, label: str) -> pl.DataFrame:
    """Aggregate means for one team over some subset of its rows."""
    if df_team.is_empty():
        return pl.DataFrame(
            {
                "TEAM": [None],
                "window": [label],
                "epa_off_mean_avg": [None],
                "success_rate_off_avg": [None],
                "epa_def_mean_avg": [None],
                "success_rate_def_avg": [None],
                "tempo_avg": [None],
                "pass_rate_off_avg": [None],
                "pass_success_rate_off_avg": [None],
                "pass_success_rate_def_avg": [None],
                "rush_success_rate_off_avg": [None],
                "rush_success_rate_def_avg": [None],
                "explosive_play_rate_off_avg": [None],
                "explosive_play_rate_def_avg": [None],
                "third_down_conv_off_avg": [None],
                "third_down_conv_def_avg": [None],
                "redzone_td_rate_off_avg": [None],
                "redzone_td_rate_def_avg": [None],
                "pressure_rate_def_avg": [None],
                "pressure_rate_allowed_avg": [None],
                "avg_start_yd100_off_avg": [None],
                "avg_start_yd100_def_avg": [None],
                "start_field_position_edge_avg": [None],
                "points_per_drive_off_avg": [None],
                "points_per_drive_def_avg": [None],
                "points_per_drive_diff_avg": [None],
                "games_in_window": [0],
                "source_weeks": [""],
                "max_source_week": [None],
            }
        )
    source_weeks = sorted(
        {
            int(value)
            for value in df_team.select("week").to_series().to_list()
            if value is not None
        }
    )
    max_source_week = max(source_weeks) if source_weeks else None
    games_used_expr = (
        pl.col("game_id").n_unique()
        if "game_id" in df_team.columns and df_team.select("game_id").drop_nulls().height
        else pl.len()
    )
    return df_team.select(
        [
            pl.first("TEAM").alias("TEAM"),
            pl.lit(label).alias("window"),
            pl.col("epa_off_mean").mean().alias("epa_off_mean_avg"),
            pl.col("success_rate_off").mean().alias("success_rate_off_avg"),
            pl.col("epa_def_mean").mean().alias("epa_def_mean_avg"),
            pl.col("success_rate_def").mean().alias("success_rate_def_avg"),
            pl.col("tempo").mean().alias("tempo_avg"),
            pl.col("pass_rate_off").mean().alias("pass_rate_off_avg"),
            pl.col("pass_success_rate_off").mean().alias("pass_success_rate_off_avg"),
            pl.col("pass_success_rate_def").mean().alias("pass_success_rate_def_avg"),
            pl.col("rush_success_rate_off").mean().alias("rush_success_rate_off_avg"),
            pl.col("rush_success_rate_def").mean().alias("rush_success_rate_def_avg"),
            pl.col("explosive_play_rate_off").mean().alias("explosive_play_rate_off_avg"),
            pl.col("explosive_play_rate_def").mean().alias("explosive_play_rate_def_avg"),
            pl.col("third_down_conv_off").mean().alias("third_down_conv_off_avg"),
            pl.col("third_down_conv_def").mean().alias("third_down_conv_def_avg"),
            pl.col("redzone_td_rate_off").mean().alias("redzone_td_rate_off_avg"),
            pl.col("redzone_td_rate_def").mean().alias("redzone_td_rate_def_avg"),
            pl.col("pressure_rate_def").mean().alias("pressure_rate_def_avg"),
            pl.col("pressure_rate_allowed").mean().alias("pressure_rate_allowed_avg"),
            pl.col("avg_start_yd100_off").mean().alias("avg_start_yd100_off_avg"),
            pl.col("avg_start_yd100_def").mean().alias("avg_start_yd100_def_avg"),
            pl.col("start_field_position_edge").mean().alias("start_field_position_edge_avg"),
            pl.col("points_per_drive_off").mean().alias("points_per_drive_off_avg"),
            pl.col("points_per_drive_def").mean().alias("points_per_drive_def_avg"),
            pl.col("points_per_drive_diff").mean().alias("points_per_drive_diff_avg"),
            games_used_expr.alias("games_in_window"),
            pl.lit(",".join(str(week) for week in source_weeks)).alias("source_weeks"),
            pl.lit(max_source_week).cast(pl.Int64).alias("max_source_week"),
        ]
    )


def _window_status(actual_games: int, requested_games: int, current_week: int) -> str:
    if actual_games <= 0:
        return INSUFFICIENT_CURRENT_SEASON_DATA if current_week <= 5 else MISSING_SOURCE_DATA
    if actual_games < requested_games:
        return PARTIAL_WINDOW
    return AVAILABLE


def _add_window_metadata(
    df: pl.DataFrame,
    *,
    analysis_season: int,
    analysis_week: int,
    requested_games: int,
) -> pl.DataFrame:
    if df.is_empty():
        return df
    games = int(df.select("games_in_window").item())
    max_source_week = df.select("max_source_week").item()
    cutoff_status = (
        CUTOFF_VIOLATION
        if max_source_week is not None and int(max_source_week) >= analysis_week
        else _window_status(games, requested_games, analysis_week)
    )
    return df.with_columns(
        [
            pl.lit(analysis_season).cast(pl.Int64).alias("analysis_season"),
            pl.lit(analysis_week).cast(pl.Int64).alias("analysis_week"),
            pl.lit(requested_games).cast(pl.Int64).alias("window_size_requested"),
            pl.lit(games).cast(pl.Int64).alias("window_size_actual"),
            pl.lit(cutoff_status).alias("data_cutoff_status"),
            pl.lit(False).alias("prior_used"),
            pl.lit("").alias("prior_source"),
            pl.lit(None).cast(pl.Float64).alias("prior_weight"),
        ]
    )


def _team_windows(df_all: pl.DataFrame, team_code: str, current_week: int, season: int):
    """
    Build 3 windows for a given team:
    - full season-to-date (1..current_week-1)
    - last 5 games
    - last 3 games
    Returns one DataFrame with 3 rows.
    """
    df_team_full = (
        df_all.filter((pl.col("TEAM") == team_code) & (pl.col("week") < current_week))
        .sort(["season", "week"])
    )

    full_summary = _add_window_metadata(
        _summarize_window(
            df_team_full,
            f"weeks 1-{current_week-1}",
        ),
        analysis_season=season,
        analysis_week=current_week,
        requested_games=max(current_week - 1, 0),
    )

    last5_summary = _add_window_metadata(
        _summarize_window(
            df_team_full.tail(5),
            "last 5 games",
        ),
        analysis_season=season,
        analysis_week=current_week,
        requested_games=5,
    )

    last3_summary = _add_window_metadata(
        _summarize_window(
            df_team_full.tail(3),
            "last 3 games",
        ),
        analysis_season=season,
        analysis_week=current_week,
        requested_games=3,
    )

    summary = pl.concat([full_summary, last5_summary, last3_summary], how="vertical")

    return summary.with_columns(pl.lit(team_code).alias("TEAM"))


def compute_form_windows(season: int, current_week: int, teams: list[str]) -> pl.DataFrame:
    """
    Return a wide BAL vs MIA style table for all requested teams, aligned by 'window'.
    If you pass 2 teams, you get 3 rows (one per window) with both teams side by side.
    If you pass 1 team, you just get that team's form windows.
    """
    df_all = _load_team_weeks(season, current_week)

    team_summaries = []
    for t in teams:
        w = _team_windows(df_all, t, current_week, season)
        # namespace columns with team code so we can join later
        w = w.rename(
            {
                "epa_off_mean_avg": f"epa_off_mean_avg_{t}",
                "success_rate_off_avg": f"success_rate_off_avg_{t}",
                "epa_def_mean_avg": f"epa_def_mean_avg_{t}",
                "success_rate_def_avg": f"success_rate_def_avg_{t}",
                "tempo_avg": f"tempo_avg_{t}",
                "pass_rate_off_avg": f"pass_rate_off_avg_{t}",
                "pass_success_rate_off_avg": f"pass_success_rate_off_avg_{t}",
                "pass_success_rate_def_avg": f"pass_success_rate_def_avg_{t}",
                "rush_success_rate_off_avg": f"rush_success_rate_off_avg_{t}",
                "rush_success_rate_def_avg": f"rush_success_rate_def_avg_{t}",
                "explosive_play_rate_off_avg": f"explosive_play_rate_off_avg_{t}",
                "explosive_play_rate_def_avg": f"explosive_play_rate_def_avg_{t}",
                "third_down_conv_off_avg": f"third_down_conv_off_avg_{t}",
                "third_down_conv_def_avg": f"third_down_conv_def_avg_{t}",
                "redzone_td_rate_off_avg": f"redzone_td_rate_off_avg_{t}",
                "redzone_td_rate_def_avg": f"redzone_td_rate_def_avg_{t}",
                "pressure_rate_def_avg": f"pressure_rate_def_avg_{t}",
                "pressure_rate_allowed_avg": f"pressure_rate_allowed_avg_{t}",
                "avg_start_yd100_off_avg": f"avg_start_yd100_off_avg_{t}",
                "avg_start_yd100_def_avg": f"avg_start_yd100_def_avg_{t}",
                "start_field_position_edge_avg": f"start_field_position_edge_avg_{t}",
                "points_per_drive_off_avg": f"points_per_drive_off_avg_{t}",
                "points_per_drive_def_avg": f"points_per_drive_def_avg_{t}",
                "points_per_drive_diff_avg": f"points_per_drive_diff_avg_{t}",
                "games_in_window": f"games_in_window_{t}",
                "source_weeks": f"source_weeks_{t}",
                "max_source_week": f"max_source_week_{t}",
                "window_size_requested": f"window_size_requested_{t}",
                "window_size_actual": f"window_size_actual_{t}",
                "data_cutoff_status": f"data_cutoff_status_{t}",
                "prior_used": f"prior_used_{t}",
                "prior_source": f"prior_source_{t}",
                "prior_weight": f"prior_weight_{t}",
                "TEAM": f"TEAM_{t}",
            }
        )
        team_summaries.append(w)

    if not team_summaries:
        return pl.DataFrame()

    # join everything on "window"
    out = team_summaries[0]
    for extra in team_summaries[1:]:
        out = out.join(extra, on="window", how="inner")

    return out


# manual test runner (so you can run this file directly)
if __name__ == "__main__":
    season = 2025
    current_week = 9
    teams = ["BAL", "MIA"]

    result = compute_form_windows(season, current_week, teams)
    print("=== FORM WINDOWS TEST ===")
    print(result)
