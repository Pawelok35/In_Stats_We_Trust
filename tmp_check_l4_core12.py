import polars as pl
from utils.paths import path_for

season = 2025
week = 9

core12_path = path_for("l4_core12", season, week)
print("=== CORE12 PATH ===")
print(core12_path)

core = pl.read_parquet(core12_path)

print("\n=== CORE12 RAW COLUMNS ===")
print(core.columns)

subset = (
    core
    .filter(pl.col("TEAM").is_in(["BAL", "MIA"]))
    .select([
        "TEAM",
        "core_epa_offense",
        "core_epa_defense",
        "success_rate_offense",
        "success_rate_defense",
        "explosive_play_rate_offense",
        "third_down_conversion_offense",
        "points_per_drive_diff",
        "yards_per_play_diff",
        "turnover_margin",
        "redzone_td_rate_offense",
        "pressure_rate_defense",
        "tempo",
    ])
)

print("\n=== CORE12 ROWS FOR BAL / MIA (FROM DISK) ===")
print(subset)

print("\n=== CORE12 AS DICT (easier to read) ===")
print(subset.to_dicts())
