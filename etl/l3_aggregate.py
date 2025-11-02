import logging
from pathlib import Path
import polars as pl

from utils.paths import path_for
from utils.manifest import write_manifest

logger = logging.getLogger(__name__)


def _safe_div(num_expr: pl.Expr, den_expr: pl.Expr) -> pl.Expr:
    """
    Bezpieczne dzielenie num/den, zwraca 0.0 jeśli den == 0 albo null.
    Zwracamy wyrażenie polarsowe (Expr).
    """
    return (
        pl.when((den_expr.is_null()) | (den_expr == 0))
        .then(0.0)
        .otherwise(num_expr / den_expr)
    )


def _empty_result() -> pl.DataFrame:
    """
    Zwraca pustą ramkę L3 z poprawnym schematem.
    """
    return pl.DataFrame(
        {
            "season": pl.Series([], dtype=pl.Int64),
            "week": pl.Series([], dtype=pl.Int64),
            "TEAM": pl.Series([], dtype=pl.Utf8),
            "drives": pl.Series([], dtype=pl.Int64),
            "plays": pl.Series([], dtype=pl.Int64),
            "epa_off_mean": pl.Series([], dtype=pl.Float64),
            "success_rate_off": pl.Series([], dtype=pl.Float64),
            "epa_def_mean": pl.Series([], dtype=pl.Float64),
            "success_rate_def": pl.Series([], dtype=pl.Float64),
            "tempo": pl.Series([], dtype=pl.Float64),
            "pressure_rate_def": pl.Series([], dtype=pl.Float64),
            "explosive_play_rate_off": pl.Series([], dtype=pl.Float64),
            "third_down_conv_off": pl.Series([], dtype=pl.Float64),
            "redzone_td_rate_off": pl.Series([], dtype=pl.Float64),
            "turnover_margin": pl.Series([], dtype=pl.Float64),
            "points_per_drive_off": pl.Series([], dtype=pl.Float64),
            "points_per_drive_def": pl.Series([], dtype=pl.Float64),
            "points_per_drive_diff": pl.Series([], dtype=pl.Float64),
            "ypp_off": pl.Series([], dtype=pl.Float64),
            "ypp_def": pl.Series([], dtype=pl.Float64),
            "ypp_diff": pl.Series([], dtype=pl.Float64),
        }
    )


def _aggregate(df: pl.DataFrame) -> pl.DataFrame:
    """
    Buduje tygodniową ramkę dla każdej drużyny (TEAM) z kompletem sygnałów:
    - EPA / success rate (atak i obrona)
    - tempo
    - pressure rate (defense)
    - explosive play rate (offense)
    - 3rd down conversion (offense)
    - red zone TD rate (proxy via explosive in RZ)
    - turnover margin
    - points per drive (off / def)
    - yards per play (off / def)
    """
    # ===== SAFETY PATCH: ensure all expected boolean/flag columns exist =====
    needed_flag_cols: dict[str, pl.DataType] = {
        "is_dropback": pl.Int64,
        "is_pressure": pl.Int64,
        "is_explosive": pl.Int64,
        "in_redzone": pl.Int64,
        "is_third_down": pl.Int64,
        "third_down_converted": pl.Int64,
        # te już mamy, ale dla spójności dbamy żeby były typu Int64
        "is_turnover": pl.Int64,
        "is_offensive_td": pl.Int64,
        "success_bin": pl.Int64,
    }

    # dla każdej kolumny: jeśli jej nie ma w df -> dodajemy z wartością 0
    safety_exprs = []
    for col_name, dtype in needed_flag_cols.items():
        if col_name not in df.columns:
            safety_exprs.append(pl.lit(0).cast(dtype).alias(col_name))
        else:
            safety_exprs.append(pl.col(col_name).cast(dtype).alias(col_name))

    # yards_gained też normalizujemy do Float64
    if "yards_gained" not in df.columns:
        safety_exprs.append(pl.lit(0.0).cast(pl.Float64).alias("yards_gained"))
    else:
        safety_exprs.append(pl.col("yards_gained").cast(pl.Float64).alias("yards_gained"))

    # epa w Float64 na pewno
    if "epa" not in df.columns:
        safety_exprs.append(pl.lit(0.0).cast(pl.Float64).alias("epa"))
    else:
        safety_exprs.append(pl.col("epa").cast(pl.Float64).alias("epa"))

    # run one with_columns to enforce presence/types
    df = df.with_columns(safety_exprs)

    base = df.with_columns(
        [
            pl.col("season").cast(pl.Int64),
            pl.col("week").cast(pl.Int64),
            pl.col("TEAM").cast(pl.Utf8),
            pl.col("OPP").cast(pl.Utf8),
            pl.col("drive").cast(pl.Int64),
            pl.col("epa").cast(pl.Float64).fill_null(0.0),
            pl.col("success").cast(pl.Float64).fill_null(0.0),
            pl.col("yards_gained").cast(pl.Float64),
            pl.col("is_dropback").cast(pl.Int64).fill_null(0),
            pl.col("is_pressure").cast(pl.Int64).fill_null(0),
            pl.col("is_explosive").cast(pl.Int64).fill_null(0),
            pl.col("is_turnover").cast(pl.Int64).fill_null(0),
            pl.col("in_redzone").cast(pl.Int64).fill_null(0),
            pl.col("is_third_down").cast(pl.Int64).fill_null(0),
            pl.col("third_down_converted").cast(pl.Int64).fill_null(0),
        ]
    )

    # OFFENSE (per TEAM)
    offense_base = (
        base.group_by(["season", "week", "TEAM"])
        .agg(
            [
                # drives ofensywne TEAMu
                pl.col("drive").n_unique().cast(pl.Int64).alias("drives"),

                # plays ofensywne TEAMu
                pl.len().cast(pl.Int64).alias("plays"),

                # średni EPA ofensywy TEAMu
                pl.col("epa").mean().cast(pl.Float64).alias("epa_off_mean"),

                # success rate ofensywy TEAMu
                pl.col("success").mean().cast(pl.Float64).alias("success_rate_off"),

                # yards/play (offense)
                pl.col("yards_gained").mean().cast(pl.Float64).alias("ypp_off"),

                # explosive play rate (offense)
                _safe_div(
                    pl.col("is_explosive").sum().cast(pl.Float64),
                    pl.len().cast(pl.Float64),
                )
                .cast(pl.Float64)
                .alias("explosive_play_rate_off"),

                # third down conversion rate (offense)
                _safe_div(
                    pl.col("third_down_converted").sum().cast(pl.Float64),
                    pl.col("is_third_down").sum().cast(pl.Float64),
                )
                .cast(pl.Float64)
                .alias("third_down_conv_off"),

                # red zone TD rate (proxy: explosive play in red zone / red zone plays)
                _safe_div(
                    (
                        (
                            ((pl.col("in_redzone") == 1) & (pl.col("is_explosive") == 1))
                            .cast(pl.Int64)
                        ).sum()
                    ).cast(pl.Float64),
                    pl.col("in_redzone").sum().cast(pl.Float64),
                )
                .cast(pl.Float64)
                .alias("redzone_td_rate_off"),

                # total EPA to later compute points per drive on offense
                pl.col("epa").sum().cast(pl.Float64).alias("_epa_total_off"),
            ]
        )
        .with_columns(
            _safe_div(
                pl.col("_epa_total_off"),
                pl.col("drives").cast(pl.Float64),
            )
            .cast(pl.Float64)
            .alias("points_per_drive_off")
        )
        .drop("_epa_total_off")
    )

    # DEFENSE (per TEAM)
    # tu patrzymy na to, co przeciwnik zrobił przeciwko TEAMowi
    defense_base = (
        base.group_by(["season", "week", "OPP"])
        .agg(
            [
                # jakiego EPA dopuścił TEAM (epa przeciwnika)
                pl.col("epa").mean().cast(pl.Float64).alias("epa_def_mean"),

                # success rate dopuszczony przez TEAM
                pl.col("success").mean().cast(pl.Float64).alias("success_rate_def"),

                # yards/play allowed
                pl.col("yards_gained").mean().cast(pl.Float64).alias("ypp_def"),

                # pressure rate DEF = presja / dropbacki przeciwnika
                _safe_div(
                    pl.col("is_pressure").sum().cast(pl.Float64),
                    pl.col("is_dropback").sum().cast(pl.Float64),
                )
                .cast(pl.Float64)
                .alias("pressure_rate_def"),

                # pomocnicze do points_per_drive_def
                pl.col("drive").n_unique().cast(pl.Int64).alias("_drives_faced"),
                pl.col("epa").sum().cast(pl.Float64).alias("_epa_allowed_total"),
            ]
        )
        .with_columns(
            _safe_div(
                pl.col("_epa_allowed_total"),
                pl.col("_drives_faced").cast(pl.Float64),
            )
            .cast(pl.Float64)
            .alias("points_per_drive_def")
        )
        .drop(["_drives_faced", "_epa_allowed_total"])
        .rename({"OPP": "TEAM"})
    )

    # TURNOVER MARGIN
    # giveaways = straty TEAMu
    # takeaways = straty przeciwnika wymuszone przez TEAM
    giveaways_per_pair = (
        base.group_by(["season", "week", "TEAM", "OPP"])
        .agg(pl.col("is_turnover").sum().cast(pl.Int64).alias("_giveaways"))
    )
    takeaways_per_pair = (
        base.group_by(["season", "week", "OPP", "TEAM"])
        .agg(pl.col("is_turnover").sum().cast(pl.Int64).alias("_takeaways"))
        .rename({"OPP": "TEAM", "TEAM": "OPP"})
    )

    turnover_team = (
        giveaways_per_pair.group_by(["season", "week", "TEAM"])
        .agg(pl.col("_giveaways").sum().alias("_giveaways_total"))
        .join(
            takeaways_per_pair.group_by(["season", "week", "TEAM"]).agg(
                pl.col("_takeaways").sum().alias("_takeaways_total")
            ),
            on=["season", "week", "TEAM"],
            how="outer",
        )
        .with_columns(
            pl.col("_giveaways_total").fill_null(0),
            pl.col("_takeaways_total").fill_null(0),
        )
        .with_columns(
            (
                pl.col("_takeaways_total") - pl.col("_giveaways_total")
            )
            .cast(pl.Float64)
            .alias("turnover_margin")
        )
        .select(["season", "week", "TEAM", "turnover_margin"])
    )

    # MERGE OFF + DEF
    combined = (
        offense_base.join(defense_base, on=["season", "week", "TEAM"], how="left")
        .join(turnover_team, on=["season", "week", "TEAM"], how="left")
    )

    # tempo = plays / drives
    combined = combined.with_columns(
        _safe_div(
            pl.col("plays").cast(pl.Float64),
            pl.col("drives").cast(pl.Float64),
        )
        .cast(pl.Float64)
        .alias("tempo")
    )

    # różnice / diffy
    combined = combined.with_columns(
        (
            pl.col("points_per_drive_off") - pl.col("points_per_drive_def")
        )
        .cast(pl.Float64)
        .alias("points_per_drive_diff"),
        (
            pl.col("ypp_off").fill_null(0.0) - pl.col("ypp_def").fill_null(0.0)
        )
        .cast(pl.Float64)
        .alias("ypp_diff"),
    )

    # fill_null liczbówek
    numeric_fill_cols = [
        "epa_off_mean",
        "success_rate_off",
        "epa_def_mean",
        "success_rate_def",
        "tempo",
        "pressure_rate_def",
        "explosive_play_rate_off",
        "third_down_conv_off",
        "redzone_td_rate_off",
        "turnover_margin",
        "points_per_drive_off",
        "points_per_drive_def",
        "points_per_drive_diff",
        "ypp_off",
        "ypp_def",
        "ypp_diff",
    ]
    combined = combined.with_columns(
        [
            pl.col(c).fill_null(0.0).cast(pl.Float64).alias(c)
            for c in numeric_fill_cols
            if c in combined.columns
        ]
    )

    return combined.select(
        "season",
        "week",
        "TEAM",
        "drives",
        "plays",
        "epa_off_mean",
        "success_rate_off",
        "epa_def_mean",
        "success_rate_def",
        "tempo",
        "pressure_rate_def",
        "explosive_play_rate_off",
        "third_down_conv_off",
        "redzone_td_rate_off",
        "turnover_margin",
        "points_per_drive_off",
        "points_per_drive_def",
        "points_per_drive_diff",
        "ypp_off",
        "ypp_def",
        "ypp_diff",
    )


def run(season: int, week: int, l2_result: Path) -> Path:
    """
    Ładuje L2 (play-level z flagami), robi agregację do L3 (team-week),
    zapisuje do data/l3_team_week/{season}/{week}.parquet,
    i zapisuje manifest.
    """
    l2_path = Path(l2_result)
    logger.info("Loading L2 artifact from %s", l2_path)
    df_l2 = pl.read_parquet(l2_path)

    if df_l2.is_empty():
        logger.warning("L3 aggregation received empty dataframe; emitting empty artifact.")
        result = _empty_result()
    else:
        result = _aggregate(df_l2)
        # Drop any rows where TEAM is null or empty
        result = result.filter(pl.col("TEAM").is_not_null() & (pl.col("TEAM") != ""))

    out_path = path_for("l3_team_week", season, week)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    result.write_parquet(out_path)

    write_manifest(
        path=out_path,
        manifest_path=path_for("l3_team_week_manifest", season, week),
        layer="l3_team_week",
        season=season,
        week=week,
        rows=result.height,
        cols=len(result.columns),
        files=[out_path],
    )

    logger.info(
        "L3 artifact written to %s (rows=%s cols=%s)",
        out_path,
        result.height,
        len(result.columns),
    )

    return out_path
