import polars as pl
from utils.paths import path_for

season = 2025
week = 8
l2 = pl.read_parquet(path_for("l2", season, week))

print("UNIQUE play_type VALUES:")
print(l2.select(pl.col("play_type").unique()).to_series())

print("\nSAMPLE ROWS WITH play_type, TEAM, OPP, epa:")
print(l2.select(["TEAM", "OPP", "play_type", "epa"]).head(20))
