import polars as pl
from pathlib import Path

def build_core12_weekly(season: int, week: int) -> pl.DataFrame:
    """
    Produkuje tygodniowy Core12 z rozszerzonymi metrykami dla KAŻDEJ drużyny
    dla danego (season, week).
    Zakładamy dwa źródła:
    - L3 (team/week summary per team)
    - L2 (play-level, potrzebne redzone/pressure/explosive/turnover/yards)

    Zwraca wide DF z kolumnami:
    TEAM,
    core_epa_off, core_epa_def,
    core_sr_off, core_sr_def,
    core_ed_sr_off,
    core_third_down_conv,
    core_points_per_drive_diff,
    core_ypp_diff,
    core_turnover_margin,
    core_redzone_td_rate,
    core_pressure_rate_def,
    core_explosive_play_rate_off,
    tempo,
    drives, plays,
    season, week
    """
    l3_path = Path(f"data/l3_team_week/{season}/{week}.parquet")
    l2_path = Path(f"data/l2_team_play/{season}/{week}.parquet")

    if not l3_path.exists():
        raise FileNotFoundError(f"L3 not found: {l3_path}")

    df_l3 = pl.read_parquet(l3_path)

    # === START: bazowe core12 z L3 (to masz już dziś)
    # core_epa_off / def, success rates
    base = df_l3.select([
        pl.col("TEAM"),
        pl.col("epa_off_mean").alias("core_epa_off"),
        pl.col("epa_def_mean").alias("core_epa_def"),
        pl.col("success_rate_off").alias("core_sr_off"),
        pl.col("success_rate_def").alias("core_sr_def"),
        pl.col("tempo"),
        pl.col("drives"),
        pl.col("plays"),
    ])

    # placeholdery na weekly extras
    extras = pl.DataFrame({
        "TEAM": base["TEAM"],
        # te kolumny będą nadpisane jeśli mamy L2
        "core_ed_sr_off": [None] * base.height,              # Explosive Drive Success Rate (drive-level explosiveness)
        "core_third_down_conv": [None] * base.height,        # 3rd down conv rate
        "core_points_per_drive_diff": [None] * base.height,  # Points per drive diff
        "core_ypp_diff": [None] * base.height,
        "core_turnover_margin": [None] * base.height,
        "core_redzone_td_rate": [None] * base.height,
        "core_pressure_rate_def": [None] * base.height,
        "core_explosive_play_rate_off": [None] * base.height,
    })

    if l2_path.exists():
        df_l2 = pl.read_parquet(l2_path)

        # --- Offense side per TEAM ---
        off_agg = (
            df_l2.groupby("TEAM").agg([
                # yards per play
                (pl.col("yards_gained").sum() / pl.count()).alias("ypp_off"),

                # explosive play rate off
                (pl.col("is_explosive").cast(pl.Int64).sum() / pl.count()).alias("explosive_play_rate_off"),

                # red zone trips / TD
                pl.col("rz_trip").cast(pl.Int64).sum().alias("rz_trips"),
                pl.col("rz_td").cast(pl.Int64).sum().alias("rz_tds"),

                # 3rd down conv rate (off)
                (pl.col("third_down_conv").cast(pl.Int64).sum()
                 / pl.col("third_down_att").cast(pl.Float64).sum()
                ).alias("third_down_conv_rate"),

                # points per drive (off)
                (pl.col("points").sum() / pl.col("drive_id").n_unique()).alias("points_per_drive_off"),

                # giveaways (turnovers lost by offense)
                pl.col("turnover_lost").cast(pl.Int64).sum().alias("giveaways"),
            ])
        )

        # --- Defense side per TEAM (treat OPP columns) ---
        # Zakładamy że df_l2 ma też kolumny z perspektywy przeciwnika,
        # np. OPP, yards_allowed, dropbacks_faced, pressures, takeaways, points_allowed, itp.
        # Jeśli nie masz OPP, tylko TEAM i "is_defense", to będziesz musiał filtrować po roli.
        def_agg = (
            df_l2.groupby("TEAM").agg([
                # yards per play allowed
                (pl.col("yards_allowed").sum() / pl.col("snap_def").sum()).alias("ypp_def_allowed"),

                # pressure rate def
                (pl.col("pressures").cast(pl.Float64).sum()
                 / pl.col("dropbacks_faced").cast(pl.Float64).sum()
                ).alias("pressure_rate_def"),

                # takeaways (turnovers gained by defense)
                pl.col("turnover_gained").cast(pl.Int64).sum().alias("takeaways"),

                # points per drive allowed
                (pl.col("points_allowed").sum()
                 / pl.col("opp_drive_id").n_unique()
                ).alias("points_per_drive_def"),
            ])
        )

        # --- Join offense + defense
        combined = off_agg.join(def_agg, on="TEAM", how="outer")

        # --- Compute derived fields that need both sides
        combined = combined.with_columns([
            # turnover margin per game:
            (pl.col("takeaways") - pl.col("giveaways")).alias("turnover_margin_raw"),

            # red zone td rate
            pl.when(pl.col("rz_trips") > 0)
            .then(pl.col("rz_tds") / pl.col("rz_trips"))
            .otherwise(None)
            .alias("redzone_td_rate_off"),

            # points per drive differential
            (pl.col("points_per_drive_off") - pl.col("points_per_drive_def")).alias("points_per_drive_diff"),

            # yards/play differential
            (pl.col("ypp_off") - pl.col("ypp_def_allowed")).alias("ypp_diff"),
        ])

        # Teraz sprowadź to do nazw z których korzysta reports.py
        extras = combined.select([
            pl.col("TEAM"),
            pl.col("explosive_play_rate_off").alias("core_explosive_play_rate_off"),
            pl.col("third_down_conv_rate").alias("core_third_down_conv"),
            pl.col("points_per_drive_diff").alias("core_points_per_drive_diff"),
            pl.col("ypp_diff").alias("core_ypp_diff"),
            pl.col("turnover_margin_raw").alias("core_turnover_margin"),
            pl.col("redzone_td_rate_off").alias("core_redzone_td_rate"),
            pl.col("pressure_rate_def").alias("core_pressure_rate_def"),
        ])

        # UWAGA: Explosive Drive Success Rate (core_ed_sr_off)
        # Jeśli masz w df_l2 informację per-drive typu "drive_had_explosive", policz:
        # % drives with explosive gain.
        if "drive_had_explosive" in df_l2.columns:
            drive_level = (
                df_l2.groupby(["TEAM", "drive_id"]).agg([
                    pl.col("drive_had_explosive").max().alias("drive_explosive_flag")
                ])
                .groupby("TEAM")
                .agg([
                    (pl.col("drive_explosive_flag").sum() / pl.count()).alias("core_ed_sr_off")
                ])
            )

            extras = extras.join(drive_level, on="TEAM", how="left")
        else:
            # jeśli nie mamy danych – zostaw None, raport sam pominie
            extras = extras.with_columns(
                pl.lit(None).alias("core_ed_sr_off")
            )

    # scal bazę z extras
    out = base.join(extras, on="TEAM", how="left")

    # dopisz meta
    out = out.with_columns([
        pl.lit(season).alias("season"),
        pl.lit(week).alias("week"),
    ])

    return out
