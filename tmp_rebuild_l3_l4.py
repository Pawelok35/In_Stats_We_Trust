from etl.l3_aggregate import run as l3_run
from metrics.core12 import compute as core12_compute
from utils.paths import path_for
import polars as pl

season = 2025
for week in range(1, 9):
    l2_path = path_for('l2', season, week)
    l3_run(season, week, l2_result=l2_path)
    df_l3 = pl.read_parquet(path_for('l3_team_week', season, week))
    core12_compute(df_l3, season, week)
