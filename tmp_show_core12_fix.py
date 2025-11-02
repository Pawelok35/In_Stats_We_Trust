import polars as pl

df = pl.read_parquet(r"data/l4_core12/2025/8.parquet")

print("COLUMNS:")
print(df.columns)

print("\nSAMPLE ROWS (first 10):")
print(df.head(10))
