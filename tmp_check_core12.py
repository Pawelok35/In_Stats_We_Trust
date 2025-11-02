import polars as pl
from pathlib import Path

path = Path(r"data/l4_core12/2025/9.parquet")

print("---- READING CORE12 WEEK 9 ----")
print("File exists:", path.exists())
print("Path:", path)

df = pl.read_parquet(path)

print("\nCOLUMNS:")
for c in df.columns:
    print(" -", c)

print("\nSAMPLE ROWS (first 10):")
print(df.head(10))

interesting_cols = [
    "team",
    "opp",
    "core_pressure_rate_def",
    "core_explosive_play_rate_off",
]

print("\nSELECTED COLS (first 10):")
missing = [c for c in interesting_cols if c not in df.columns]
if missing:
    print("WARN: missing columns ->", missing)

present_cols = [c for c in interesting_cols if c in df.columns]
print(df.select(present_cols).head(10))

if "core_pressure_rate_def" in df.columns:
    uniq = df.select(pl.col("core_pressure_rate_def").unique())
    print("\nUNIQUE core_pressure_rate_def VALUES:")
    print(uniq)
else:
    print("\n[WARN] no core_pressure_rate_def in this file")
