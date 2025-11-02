import polars as pl

path = r"data/l1/2025/9.parquet"
df = pl.read_parquet(path)

print("=== COLUMNS L1 ===")
print(df.columns)

print("\n=== SAMPLE ROWS (first 10) ===")
print(df.head(10))
