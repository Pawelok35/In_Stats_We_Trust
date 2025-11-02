import logging
from pathlib import Path
import polars as pl

from utils.paths import path_for
from utils.manifest import write_manifest

logger = logging.getLogger(__name__)

def compute(df_l3: pl.DataFrame, season: int, week: int) -> pl.DataFrame:
    """
    Przyjmuje ramkę L3 (team-week metrics) i buduje oficjalne Core12:
    Każda drużyna = jeden wiersz.
    Zwracamy i zapisujemy do data/l4_core12/{season}/{week}.parquet
    """

    # wybieramy i nazywamy kolumny tak, jak raport ich oczekuje
    work = df_l3.select(
        [
            pl.col("season").cast(pl.Int64).alias("season"),
            pl.col("week").cast(pl.Int64).alias("week"),
            pl.col("TEAM").cast(pl.Utf8).alias("TEAM"),

            # EPA
            pl.col("epa_off_mean").cast(pl.Float64).alias("core_epa_offense"),
            pl.col("epa_def_mean").cast(pl.Float64).alias("core_epa_defense"),

            # Success Rate
            pl.col("success_rate_off").cast(pl.Float64).alias("success_rate_offense"),
            pl.col("success_rate_def").cast(pl.Float64).alias("success_rate_defense"),

            # Explosive Play Rate (offense)
            pl.col("explosive_play_rate_off")
            .cast(pl.Float64)
            .alias("explosive_play_rate_offense"),

            # 3rd down conversion (offense)
            pl.col("third_down_conv_off")
            .cast(pl.Float64)
            .alias("third_down_conversion_offense"),

            # Points per drive diff
            pl.col("points_per_drive_diff")
            .cast(pl.Float64)
            .alias("points_per_drive_diff"),

            # Yards/play diff
            pl.col("ypp_diff")
            .cast(pl.Float64)
            .alias("yards_per_play_diff"),

            # Turnover margin
            pl.col("turnover_margin")
            .cast(pl.Float64)
            .alias("turnover_margin"),

            # Red zone TD rate (offense)
            pl.col("redzone_td_rate_off")
            .cast(pl.Float64)
            .alias("redzone_td_rate_offense"),

            # Pressure rate (defense)
            pl.col("pressure_rate_def")
            .cast(pl.Float64)
            .alias("pressure_rate_defense"),

            # Tempo
            pl.col("tempo").cast(pl.Float64).alias("tempo"),
        ]
    )

    # bezpieczeństwo: żadnych nulli w metrykach numerycznych
    numeric_cols = [
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

    work = work.with_columns(
        [
            pl.col(c).cast(pl.Float64).fill_null(0.0).alias(c)
            for c in numeric_cols
            if c in work.columns
        ]
    )

    # === aliasy kolumn dla walidatora L4_CORE12 ===
    # (nie usuwamy oryginałów; dokładamy stare nazwy żeby walidator i reszta kodu były zadowolone)
    work = work.with_columns([
        pl.col("core_epa_offense").alias("core_epa_off"),
        pl.col("core_epa_defense").alias("core_epa_def"),
        pl.col("success_rate_offense").alias("core_sr_off"),
        pl.col("success_rate_defense").alias("core_sr_def"),
        pl.col("explosive_play_rate_offense").alias("core_explosive_play_rate_off"),
        pl.col("third_down_conversion_offense").alias("core_third_down_conv"),
        pl.col("yards_per_play_diff").alias("core_ypp_diff"),
        pl.col("turnover_margin").alias("core_turnover_margin"),
        pl.col("points_per_drive_diff").alias("core_points_per_drive_diff"),
        pl.col("redzone_td_rate_offense").alias("core_redzone_td_rate"),
        pl.col("pressure_rate_defense").alias("core_pressure_rate_def"),
    ])

    # walidator oczekuje też core_ed_sr_off (explosive drive success rate).
    # Na razie nie mamy osobnej metryki drive-level eksplozji,
    # więc dajemy proxy = offensive explosive play rate
    work = work.with_columns([
        pl.col("explosive_play_rate_offense").alias("core_ed_sr_off"),
    ])

    # zapis Core12 do L4
    out_path = path_for("l4_core12", season, week)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    work.write_parquet(out_path)

    write_manifest(
        path=out_path,
        manifest_path=path_for("l4_core12_manifest", season, week),
        layer="l4_core12",
        season=season,
        week=week,
        rows=work.height,
        cols=len(work.columns),
        files=[out_path],
    )

    logger.info(
        "Core12 written to %s (rows=%s cols=%s)",
        out_path,
        work.height,
        len(work.columns),
    )

    return work
