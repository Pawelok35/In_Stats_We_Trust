# scripts/patch_week8_aliases.py
import polars as pl

src = "data/sources/nfl/2025/8.parquet"

df = pl.read_parquet(src)
map_team = {"AAA": "BAL", "BBB": "MIA"}

for col in ("posteam", "defteam"):
    if col in df.columns:
        df = df.with_columns(pl.col(col).map_elements(lambda x: map_team.get(x, x)))

df.write_parquet(src)
print("Patched", src, "rows=", len(df))
