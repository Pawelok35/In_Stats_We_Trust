import polars as pl
from pathlib import Path


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

    dfs = []
    for wk in range(1, current_week):
        p = Path(f"data/l3_team_week/{season}/{wk}.parquet")
        if not p.exists():
            # skip weeks we don't have yet
            continue
        df_raw = pl.read_parquet(p)
        # ensure all required columns exist, filling missing ones with nulls
        select_exprs = []
        for col_name, dtype in required_columns:
            if col_name in df_raw.columns:
                select_exprs.append(pl.col(col_name).cast(dtype).alias(col_name))
            else:
                select_exprs.append(pl.lit(None).cast(dtype).alias(col_name))
        df_w = df_raw.select(select_exprs).with_columns(
            [
                pl.lit(season).alias("season"),
                pl.lit(wk).alias("week"),
            ]
        )
        dfs.append(df_w)

    if not dfs:
        return _empty_team_weeks_frame()

    return pl.concat(dfs, how="vertical")


def _summarize_window(df_team: pl.DataFrame, label: str) -> pl.DataFrame:
    """Aggregate means for one team over some subset of its rows."""
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
            pl.len().alias("games_in_window"),
        ]
    )


def _team_windows(df_all: pl.DataFrame, team_code: str, current_week: int):
    """
    Build 3 windows for a given team:
    - full season-to-date (1..current_week-1)
    - last 5 games
    - last 3 games
    Returns one DataFrame with 3 rows.
    """
    df_team_full = df_all.filter(pl.col("TEAM") == team_code).sort("week")

    full_summary = _summarize_window(
        df_team_full,
        f"weeks 1-{current_week-1}",
    )

    last5_summary = _summarize_window(
        df_team_full.tail(5),
        "last 5 games",
    )

    last3_summary = _summarize_window(
        df_team_full.tail(3),
        "last 3 games",
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
        w = _team_windows(df_all, t, current_week)
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
