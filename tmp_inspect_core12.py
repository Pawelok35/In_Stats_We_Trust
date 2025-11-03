import polars as pl
from metrics.core12 import compute as core12_compute
from utils.paths import path_for
from etl.l3_aggregate import run as l3_run

l2_path = path_for('l2', 2025, 8)
l3_path = l3_run(2025, 8, l2_result=l2_path)
l3_df = pl.read_parquet(l3_path)
result = core12_compute(l3_df, 2025, 8)
print(result.columns)
print(result.filter(pl.col('TEAM')=='BAL')['core_points_per_drive_diff'][0])
print(result.filter(pl.col('TEAM')=='MIA')['core_points_per_drive_diff'][0])
