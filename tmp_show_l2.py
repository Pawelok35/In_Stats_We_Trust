import polars as pl

path = r"data/l2/2025/9.parquet"
df = pl.read_parquet(path)

print("=== COLUMNS ===")
print(df.columns)

print("\n=== SAMPLE ROWS (first 10) ===")
print(df.head(10))
