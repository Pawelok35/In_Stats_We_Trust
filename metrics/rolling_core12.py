import polars as pl
from pathlib import Path


CORE12_COLS = [
    "season",
    "week",
    "TEAM",
    "core_epa_offense",
    "core_epa_defense",
    "success_rate_offense",
    "success_rate_defense",
    "explosive_play_rate_offense",
    "third_down_conversion_offense",
    "points_per_drive_diff",
    "yards_per_play_diff",
    "turnover_margin",
    "redzone_td_rate_offense",
    "pressure_rate_defense",
    "tempo",
]


def _load_core12_for_week(season: int, week: int) -> pl.DataFrame:
    """
    Wczytaj snapshot Core12 dla konkretnego tygodnia z L4.
    Jeśli brak pliku, zwróć pusty DataFrame o poprawnym schemacie.
    """
    path = Path(f"data/l4_core12/{season}/{week}.parquet")
    if not path.exists():
        print(f"⚠️ Brak pliku Core12 dla week={week}")
        return pl.DataFrame(schema={c: pl.Float64 for c in CORE12_COLS}).with_columns(
            [
                pl.lit(season).alias("season").cast(pl.Int64),
                pl.lit(week).alias("week").cast(pl.Int64),
                pl.lit("").alias("TEAM").cast(pl.Utf8),
            ]
        )

    df = pl.read_parquet(path)
    return df.select([c for c in CORE12_COLS if c in df.columns])


def build_core12_rolling_through(season: int, through_week: int) -> pl.DataFrame:
    """
    Zbiera Core12 z tygodni 1..through_week i liczy średnią formę drużyn.
    """
    weekly_frames = []
    for w in range(1, through_week + 1):
        df_w = _load_core12_for_week(season, w)
        df_w = df_w.filter(pl.col("TEAM") != "")
        if df_w.height > 0:
            weekly_frames.append(df_w)

    if not weekly_frames:
        raise RuntimeError(f"Brak danych Core12 dla season={season} (do week={through_week})")

    all_weeks = pl.concat(weekly_frames, how="vertical")

    rolled = (
        all_weeks.group_by("TEAM").agg(
            [
                pl.col("season").max().alias("season"),
                pl.lit(through_week).alias("through_week"),

                # Średnie wartości metryk
                pl.col("core_epa_offense").mean().alias("core_epa_offense"),
                pl.col("core_epa_defense").mean().alias("core_epa_defense"),
                pl.col("success_rate_offense").mean().alias("success_rate_offense"),
                pl.col("success_rate_defense").mean().alias("success_rate_defense"),
                pl.col("explosive_play_rate_offense").mean().alias("explosive_play_rate_offense"),
                pl.col("third_down_conversion_offense").mean().alias("third_down_conversion_offense"),
                pl.col("points_per_drive_diff").mean().alias("points_per_drive_diff"),
                pl.col("yards_per_play_diff").mean().alias("yards_per_play_diff"),
                pl.col("turnover_margin").mean().alias("turnover_margin"),
                pl.col("redzone_td_rate_offense").mean().alias("redzone_td_rate_offense"),
                pl.col("pressure_rate_defense").mean().alias("pressure_rate_defense"),
                pl.col("tempo").mean().alias("tempo"),

                pl.col("week").n_unique().alias("games_played_window"),
            ]
        )
    )

    return rolled


def write_rolling_core12(season: int, through_week: int) -> Path:
    """
    Zapisuje snapshot rolling_core12 do:
    data/rolling_core12/{season}/through_{through_week}.parquet
    """
    rolled = build_core12_rolling_through(season, through_week)

    out_path = Path(f"data/rolling_core12/{season}/through_{through_week}.parquet")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    rolled.write_parquet(out_path)

    print(f"✅ Rolling Core12 zapisany: {out_path} (rows={rolled.height}, cols={len(rolled.columns)})")
    return out_path
