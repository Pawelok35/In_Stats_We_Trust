import polars as pl
from metrics.core12 import _pressure_and_explosive_rates
from utils.paths import path_for

season = 2025
week = 8

l2_path = path_for("l2", season, week)
print("L2 PATH:", l2_path)

l2 = pl.read_parquet(l2_path)
print("L2 COLUMNS:", l2.columns)
print("L2 SAMPLE:")
print(l2.head(5))

pressure_def, explosive_off = _pressure_and_explosive_rates(l2, season, week)

print("\n=== PRESSURE_DEF ===")
print(pressure_def)

print("\n=== EXPLOSIVE_OFF ===")
print(explosive_off)
