import polars as pl
from pathlib import Path

from etl.mappers import _TEAM_ALIAS_MAP


CORE12_COLS = [
    "season",
    "week",
    "TEAM",
    "core_epa_off",
    "core_epa_def",
    "core_sr_off",
    "core_sr_def",
    "core_explosive_play_rate_off",
    "core_third_down_conv",
    "core_points_per_drive_diff",
    "core_ypp_diff",
    "core_turnover_margin",
    "core_redzone_td_rate",
    "core_pressure_rate_def",
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
                pl.col("core_epa_off").mean().alias("core_epa_off"),
                pl.col("core_epa_def").mean().alias("core_epa_def"),
                pl.col("core_sr_off").mean().alias("core_sr_off"),
                pl.col("core_sr_def").mean().alias("core_sr_def"),
                pl.col("core_explosive_play_rate_off").mean().alias("core_explosive_play_rate_off"),
                pl.col("core_third_down_conv").mean().alias("core_third_down_conv"),
                pl.col("core_points_per_drive_diff").mean().alias("core_points_per_drive_diff"),
                pl.col("core_ypp_diff").mean().alias("core_ypp_diff"),
                pl.col("core_turnover_margin").mean().alias("core_turnover_margin"),
                pl.col("core_redzone_td_rate").mean().alias("core_redzone_td_rate"),
                pl.col("core_pressure_rate_def").mean().alias("core_pressure_rate_def"),
                pl.col("tempo").mean().alias("tempo"),

                pl.col("week").n_unique().alias("games_played_window"),
            ]
        )
    )

    def _normalize(team: str) -> str:
        canonical = (team or "").upper()
        return _TEAM_ALIAS_MAP.get(canonical, canonical)

    rolled = rolled.with_columns(
        pl.col("TEAM")
        .cast(pl.Utf8)
        .str.to_uppercase()
        .map_elements(_normalize, return_dtype=pl.Utf8)
    )

    rolled = (
        rolled.group_by("TEAM")
        .agg(
            [
                pl.col("season").max().alias("season"),
                pl.col("through_week").max().alias("through_week"),
                pl.col("core_epa_off").mean().alias("core_epa_off"),
                pl.col("core_epa_def").mean().alias("core_epa_def"),
                pl.col("core_sr_off").mean().alias("core_sr_off"),
                pl.col("core_sr_def").mean().alias("core_sr_def"),
                pl.col("core_explosive_play_rate_off").mean().alias("core_explosive_play_rate_off"),
                pl.col("core_third_down_conv").mean().alias("core_third_down_conv"),
                pl.col("core_points_per_drive_diff").mean().alias("core_points_per_drive_diff"),
                pl.col("core_ypp_diff").mean().alias("core_ypp_diff"),
                pl.col("core_turnover_margin").mean().alias("core_turnover_margin"),
                pl.col("core_redzone_td_rate").mean().alias("core_redzone_td_rate"),
                pl.col("core_pressure_rate_def").mean().alias("core_pressure_rate_def"),
                pl.col("tempo").mean().alias("tempo"),
                pl.col("games_played_window").max().alias("games_played_window"),
            ]
        )
        .sort("TEAM")
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
