import polars as pl

from metrics.power_score import compute

l3_path = r"data/l3_team_week/2025/8.parquet"
df = pl.read_parquet(l3_path)

# Safe alias swap for fixtures; no effect if already BAL/MIA
df = df.with_columns(pl.col("TEAM").replace({"AAA": "BAL", "BBB": "MIA"}))

# Recompute L4 and write to data/l4_powerscore/2025/8.parquet
compute(df, 2025, 8)
print("Recomputed L4 PowerScore from L3 (2025 W8).")
