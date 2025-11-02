# metrics/rolling.py
"""
Rolling / cumulative snapshots for Core12.

Goal:
Given a season and a "through_week", build a dataframe that represents
"team state up to that week", not just that single last week.

Example:
through_week = 8
=> we aggregate weeks 1..8 for every team
=> save result to data/rolling_core12/<season>/through_<through_week>.parquet
"""

from __future__ import annotations

import polars as pl
from pathlib import Path

from utils.paths import core12_path  # we assume you already have something like data/l4_core12/<season>/<week>.parquet
from utils.paths import rolling_core12_through_path  # we'll add this helper soon if you don't have it yet


def _load_core12_up_to(season: int, through_week: int) -> pl.DataFrame:
    """
    Read Core12 parquet files for all weeks <= through_week and concatenate,
    even if older weeks have fewer columns (we allow schema drift).
    """
    dfs: list[pl.DataFrame] = []

    for wk in range(1, through_week + 1):
        path = core12_path(season, wk)
        p = Path(path)
        if p.exists():
            df_wk = pl.read_parquet(p)
            # dołączę też informację o week, żebyśmy nie zgubili po drodze
            if "week" not in df_wk.columns:
                df_wk = df_wk.with_columns(pl.lit(wk).alias("week"))
            if "season" not in df_wk.columns:
                df_wk = df_wk.with_columns(pl.lit(season).alias("season"))
            dfs.append(df_wk)
        else:
            # brak pliku dla tego tygodnia = pomijamy
            continue

    if not dfs:
        raise FileNotFoundError(
            f"No Core12 data found for season={season} up to week={through_week}"
        )

    # ważne: dopasuj kolumny po nazwie i wstawiaj null dla brakujących
    return pl.concat(dfs, how="diagonal_relaxed", rechunk=True)



def _aggregate_core12(df_all: pl.DataFrame, through_week: int) -> pl.DataFrame:
    """
    Zwijamy wiele tygodni (1..through_week) do jednego wiersza na drużynę.

    Zasady:
    - metryki efektywności (epa, success rate, itd.) -> średnia z tygodni
    - presja:
        jeśli mamy raw counts w przyszłości, policzymy sum(pressures)/sum(dropbacks)
        na razie fallback = średnia core_pressure_rate_def
    """

    # identyfikatory w Twoich danych:
    id_cols = ["season", "TEAM"]

    # kolumny, które widzieliśmy w df_all:
    mean_cols = [
        "core_epa_off",
        "core_epa_def",
        "core_sr_off",
        "core_sr_def",
        "core_ed_sr_off",
        "core_third_down_conv",
        "core_ypp_diff",
        "core_turnover_margin",
        "core_points_per_drive_diff",
        "core_redzone_td_rate",
        "core_explosive_play_rate_off",
    ]

    pressure_rate_col = "core_pressure_rate_def"
    # Surowych liczników presji jeszcze nie mamy (core_pressures_def / core_dropbacks_def),
    # więc na razie tylko fallback.

    agg_exprs = []

    # średnia dla wszystkich metryk, które istnieją
    for col in mean_cols:
        if col in df_all.columns:
            agg_exprs.append(pl.col(col).mean().alias(col))

    # fallback: średnia z core_pressure_rate_def
    if pressure_rate_col in df_all.columns:
        agg_exprs.append(
            pl.col(pressure_rate_col).mean().alias(pressure_rate_col)
        )

    # oznaczamy do którego tygodnia to liczone
    agg_exprs.append(pl.lit(through_week).alias("through_week"))

    grouped = (
        df_all
        .group_by(id_cols)
        .agg(agg_exprs)
    )

    return grouped



def build_cumulative_core12(season: int, through_week: int) -> pl.DataFrame:
    """
    Public API.

    1. load all core12 weeks <= through_week
    2. aggregate per team
    3. write parquet out to data/rolling_core12/<season>/through_<through_week>.parquet
    4. return the final df
    """
    df_all = _load_core12_up_to(season, through_week)
    df_roll = _aggregate_core12(df_all, through_week)

    out_path = rolling_core12_through_path(season, through_week)
    out_dir = Path(out_path).parent
    out_dir.mkdir(parents=True, exist_ok=True)

    df_roll.write_parquet(out_path)

    return df_roll
