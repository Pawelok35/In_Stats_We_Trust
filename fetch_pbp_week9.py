import os
import polars as pl

# próbujemy zaimportować oficjalny play-by-play z nfl_data_py
from nfl_data_py import import_pbp_data

# ==== KONFIG ====
SEASON = 2025
WEEK = 8

# 1. Pobierz pełne play-by-play dla sezonu
print(f"[INFO] Fetching PBP for season {SEASON} ...")
pbp_df = import_pbp_data([SEASON], downcast=True)

# 2. Filtrowanie tylko interesującego tygodnia
pbp_week = pbp_df[pbp_df["week"] == WEEK].copy()

print(f"[INFO] Rows for week {WEEK}: {len(pbp_week)}")

# 3. My nie potrzebujemy WSZYSTKICH 200 kolumn, tylko te kluczowe.
#    Wybieramy minimalny zestaw, który nasz pipeline potrzebuje
wanted_cols = [
    "season",
    "week",
    "game_id",
    "play_id",

    "posteam",          # offense team
    "defteam",          # defense team

    "play_type",        # 'pass', 'run', 'sack', 'scramble', etc.

    "pass_attempt",     # 1 if QB attempted a pass
    "rush_attempt",     # 1 if designed run
    "sack",             # 1 if sack
    "qb_hit",           # 1 if QB hit
    "pressure",         # if available, pressure/hurry flag
    "scramble",         # 1 if QB scramble

    "yards_gained",     # yards on play
    "epa",              # Expected Points Added
    "success",          # 1 if successful play by EPA rules

    "yardline_100",     # field position
    "down",             # down (1,2,3,4)
    "ydstogo",          # distance to first down
]

# Czasem niektórych kolumn nie ma w każdej wersji danych (np. "pressure").
# Musimy więc bezpiecznie dodać brakujące kolumny jako None / 0,
# żeby nasz ETL się nie wywalił. To jest ważne.
for col in wanted_cols:
    if col not in pbp_week.columns:
        print(f"[WARN] Column {col} missing in source, filling with null/0")
        if col in ["pass_attempt", "rush_attempt", "sack", "qb_hit", "pressure", "scramble", "success"]:
            pbp_week[col] = 0
        else:
            pbp_week[col] = None

# Teraz bierzemy tylko te kolumny, w ustalonej kolejności
pbp_week_small = pbp_week[wanted_cols].copy()

# Dopasowanie nazewnictwa do Twojego L1:
# - w L1 masz 'distance', nie 'ydstogo', więc dorobimy kolumnę 'distance'
pbp_week_small["distance"] = pbp_week_small["ydstogo"]

# Konwersja pandas -> polars, bo reszta Twojego pipeline działa na polars
df_pl = pl.from_pandas(pbp_week_small)

# 4. Upewniamy się że folder docelowy istnieje
out_dir = os.path.join("data", "sources", "nfl", str(SEASON))
os.makedirs(out_dir, exist_ok=True)

out_path = os.path.join(out_dir, f"{SEASON}_{WEEK}.parquet")

# 5. Zapis do Parquet
df_pl.write_parquet(out_path)

print(f"[OK] Wrote {out_path}")
print("Columns in written file:")
print(df_pl.columns)
print(f"Rows: {df_pl.height}")
