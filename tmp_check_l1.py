import polars as pl
from utils.paths import path_for

season = 2025
week = 9

l1_path = path_for("l1", season, week)
print("=== L1 PATH ===")
print(l1_path)

df = pl.read_parquet(l1_path)

print("\nCOLUMNS:")
print(df.columns)

print("\nSAMPLE ROWS (first 20):")
print(df.select(["season", "week", "game_id", "play_id", "TEAM", "OPP", "play_type", "epa", "yards_gained"]).head(20))
