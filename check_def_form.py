import polars as pl
from pathlib import Path

season = 2025
current_week = 9          # raport DET vs MIN był dla Week 9
cutoff_week = current_week - 1  # "up to Week 8"
teams_to_check = ["DET", "MIN"]

# ========== 1. wczytaj L4 tygodnie 1..8 ==========
frames = []
for wk in range(1, cutoff_week + 1):
    path = Path(f"data/l4_core12/{season}/{wk}.parquet")
    if not path.exists():
        continue
    df = pl.read_parquet(path).with_columns(
        pl.lit(wk).alias("week")
    )
    frames.append(df)

if not frames:
    raise RuntimeError("Nie mam żadnych plików L4, sprawdź ścieżki data/l4_core12/...")

l4_all = pl.concat(frames, how="vertical")

print("=== [RAW DEF] tygodniowe core_epa_def DET/MIN (weeks 1..8) ===")
print(
    l4_all
    .filter(pl.col("TEAM").is_in(teams_to_check))
    .select(["TEAM", "week", "core_epa_def"])
    .sort(["TEAM", "week"])
)

# ========== 2. funkcja licząca średnie ==========
def summarize_def(df_team: pl.DataFrame) -> dict:
    df_team = df_team.sort("week")
    col = df_team["core_epa_def"]

    def _safe_mean(series: pl.Series):
        if series.len() == 0:
            return None
        return float(series.mean())

    return {
        "Season-to-date": _safe_mean(col),
        "Last 5": _safe_mean(col.tail(5)),
        "Last 3": _safe_mean(col.tail(3)),
    }

# ========== 3. policz DET / MIN i wydrukuj ==========
print("\n=== [CHECK DEF] Podsumowanie DET / MIN ===")
for t in teams_to_check:
    team_df = l4_all.filter(pl.col("TEAM") == t)
    stats = summarize_def(team_df)

    s2d  = stats["Season-to-date"]
    l5   = stats["Last 5"]
    l3   = stats["Last 3"]

    print(
        f"{t} -> "
        f"S2D={s2d:.3f}  "
        f"Last5={l5:.3f}  "
        f"Last3={l3:.3f}"
    )

# ========== 4. kontrola ile tygodni weszło ==========
print("\n=== [COVERAGE DEF] Ile tygodni było użytych ===")
print(
    l4_all
    .filter(pl.col("TEAM").is_in(teams_to_check))
    .group_by("TEAM")
    .agg([
        pl.col("week").min().alias("min_week"),
        pl.col("week").max().alias("max_week"),
        pl.len().alias("num_weeks_included"),
    ])
    .sort("TEAM")
)
