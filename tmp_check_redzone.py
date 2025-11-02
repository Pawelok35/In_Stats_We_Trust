import polars as pl

df = pl.read_parquet(r"data/l1/2025/8.parquet")

print("COLUMNS:", df.columns)
print("\nYARDLINE_100 summary:")
print(df.select([
    pl.col("yardline_100").min().alias("min"),
    pl.col("yardline_100").max().alias("max"),
    pl.col("yardline_100").is_null().sum().alias("nulls"),
    pl.len().alias("total_rows")
]))
