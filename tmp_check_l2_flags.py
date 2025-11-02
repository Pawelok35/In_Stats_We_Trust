import polars as pl
from pathlib import Path

# Spróbujemy wziąć ten sam tydzień, czyli 2025/9.
# Jeśli nie masz 9.parquet w L2, zmienimy później, ale spróbujmy:
path = Path(r"data/l2/2025/9.parquet")

print("---- READING L2 WEEK 9 ----")
print("File exists:", path.exists())
print("Path:", path)

df = pl.read_parquet(path)

print("\nCOLUMNS:")
for c in df.columns:
    print(" -", c)

print("\nSAMPLE ROWS (first 20):")
print(df.head(20))

# pokażmy potencjalne ciekawe kolumny boole'owskie
candidate_cols = [
    "qb_hit",
    "qb_hurry",
    "pressure",
    "is_pressure",
    "is_scramble",
    "scramble",
    "play_type",
    "pass",
    "sack",
    "passer",
    "rusher",
]

present = [c for c in candidate_cols if c in df.columns]
print("\nPRESENT CANDIDATE COLS:")
print(present)

if present:
    print("\nUNIQUE VALUES PER CANDIDATE:")
    for c in present:
        print(f"\n-- {c} --")
        print(df.select(pl.col(c).unique()))
else:
    print("\n[WARN] None of the known candidate columns found. We'll need to inspect manually.")
