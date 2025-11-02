import polars as pl

season = 2025
current_week = 9  # przygotowujemy raport "przed week 9"

# 1. zbierz tygodnie 1..(current_week-1) z l3_team_week
dfs = []
for wk in range(1, current_week):
    path = f"data/l3_team_week/{season}/{wk}.parquet"
    df_w = pl.read_parquet(path).with_columns([
        pl.lit(season).alias("season"),
        pl.lit(wk).alias("week"),
    ])
    dfs.append(df_w)

team_weeks = pl.concat(dfs, how="vertical")

# 2. helper: policz średnie dla drużyny w danym zakresie tygodni
def summarize_team(df_team: pl.DataFrame, label: str) -> pl.DataFrame:
    return (
        df_team.select([
            pl.first("TEAM").alias("TEAM"),
            pl.lit(label).alias("window"),
            pl.col("epa_off_mean").mean().alias("epa_off_mean_avg"),
            pl.col("success_rate_off").mean().alias("success_rate_off_avg"),
            pl.col("epa_def_mean").mean().alias("epa_def_mean_avg"),
            pl.col("success_rate_def").mean().alias("success_rate_def_avg"),
            pl.col("tempo").mean().alias("tempo_avg"),
            pl.count().alias("games_in_window"),
        ])
    )

def make_windows(df_all: pl.DataFrame, team_code: str, current_week: int):
    # wszystkie tygodnie do current_week-1
    df_team_full = df_all.filter(pl.col("TEAM") == team_code)

    # full season-to-date
    full_summary = summarize_team(df_team_full, f"weeks 1-{current_week-1}")

    # last 5 games (N ostatnich wystąpień, nie 'tygodni kalendarzowych',
    # żeby bye nie psuł okna)
    df_last5 = (
        df_team_full
        .sort("week")
        .tail(5)
    )
    last5_summary = summarize_team(df_last5, "last 5 games")

    # last 3 games (też fajne do formy)
    df_last3 = (
        df_team_full
        .sort("week")
        .tail(3)
    )
    last3_summary = summarize_team(df_last3, "last 3 games")

    return pl.concat([full_summary, last5_summary, last3_summary], how="vertical")

bal_windows = make_windows(team_weeks, "BAL", current_week)
mia_windows = make_windows(team_weeks, "MIA", current_week)

# 3. połącz BAL i MIA bok w bok żeby wyglądało jak raport matchup
joined = (
    bal_windows.join(
        mia_windows,
        on="window",
        how="inner",
        suffix="_MIA",
    )
    .rename({
        "TEAM": "TEAM_BAL",
        "TEAM_MIA": "TEAM_MIA",
    })
)

print("=== BAL/MIA FORM SUMMARY up to week", current_week-1, "===")
print(joined)

# 4. dodatkowo pokaż surowe tygodnie BAL/MIA żebyśmy widzieli kolejność
print("\n=== BAL weekly history ===")
print(
    team_weeks.filter(pl.col("TEAM")=="BAL")
    .select(["week","epa_off_mean","success_rate_off","epa_def_mean","success_rate_def","tempo"])
    .sort("week")
)

print("\n=== MIA weekly history ===")
print(
    team_weeks.filter(pl.col("TEAM")=="MIA")
    .select(["week","epa_off_mean","success_rate_off","epa_def_mean","success_rate_def","tempo"])
    .sort("week")
)
