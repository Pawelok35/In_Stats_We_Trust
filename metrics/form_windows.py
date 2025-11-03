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
        }
    )


def _load_team_weeks(season: int, current_week: int) -> pl.DataFrame:
    """
    Load all l3_team_week/<season>/<week>.parquet for weeks < current_week
    and return one big DataFrame with columns:
    [season, week, TEAM, epa_off_mean, success_rate_off, epa_def_mean,
     success_rate_def, tempo]
    """
    dfs = []
    for wk in range(1, current_week):
        p = Path(f"data/l3_team_week/{season}/{wk}.parquet")
        if not p.exists():
            # skip weeks we don't have yet
            continue
        df_w = pl.read_parquet(p).with_columns(
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
