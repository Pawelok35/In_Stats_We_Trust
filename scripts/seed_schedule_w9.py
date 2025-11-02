# scripts/seed_schedule_w9.py
import polars as pl

pairs = [
    # Dodaj tutaj swoje mecze Week 9:
    {"season": 2025, "week": 9, "home_team": "BAL", "away_team": "MIA"},
    {"season": 2025, "week": 9, "home_team": "BUF", "away_team": "KC"},
]
df = pl.DataFrame(pairs)
out = "data/schedules/2025.parquet"
df.write_parquet(out)
print(f"Wrote {out} with {len(df)} rows")
