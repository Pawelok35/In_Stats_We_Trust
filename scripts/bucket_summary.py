"""Summarize weather bucket performance by season.

Reads `data/results/weather_bucket_games_season{season}.csv` files (2022–2025 by
default), aggregates only settled picks (WIN/LOSS), and prints per-bucket
stats: WIN, LOSS, Total, Win%, PnL (stake 0.9/-1).

Usage:
    python -X utf8 scripts/bucket_summary.py           # all seasons found
    python -X utf8 scripts/bucket_summary.py --season 2024
    python -X utf8 scripts/bucket_summary.py --season 2022 2023 2024 2025
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable, List

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = ROOT / "data" / "results"


def load_season_df(season: int) -> pd.DataFrame | None:
    """Load bucket CSV for a given season; return None if missing."""
    path = RESULTS_DIR / f"weather_bucket_games_season{season}.csv"
    if not path.exists():
        return None
    df = pd.read_csv(path)
    # Consider only resolved picks
    df = df[df["result"].isin(["WIN", "LOSS"])].copy()
    if df.empty:
        return df
    # PnL with 0.9/-1 staking
    df["pnl"] = df.apply(
        lambda r: 0.9 * r["stake_u"] if r["result"] == "WIN" else -1 * r["stake_u"],
        axis=1,
    )
    return df


def summarize(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate WIN/LOSS counts, winrate, and pnl by bucket."""
    counts = (
        df.groupby("bucket")["result"]
        .value_counts()
        .unstack(fill_value=0)[["WIN", "LOSS"]]
        .rename_axis(None, axis=1)
    )
    winrate = df.groupby("bucket")["result"].apply(
        lambda s: (s == "WIN").mean() * 100
    )
    pnl = df.groupby("bucket")["pnl"].sum()

    table = counts.copy()
    table["Total"] = table["WIN"] + table["LOSS"]
    table["Win%"] = winrate.round(1)
    table["PnL_0.9/-1"] = pnl.round(2)
    # Reorder columns for readability
    table = table[["WIN", "LOSS", "Total", "Win%", "PnL_0.9/-1"]]
    return table.sort_index()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Summarize weather bucket performance by season."
    )
    parser.add_argument(
        "--season",
        type=int,
        nargs="*",
        help="Seasons to include (e.g., 2022 2023 2024 2025). "
        "Default: auto-detect files in data/results.",
    )
    return parser.parse_args()


def detect_seasons() -> List[int]:
    seasons: List[int] = []
    for path in RESULTS_DIR.glob("weather_bucket_games_season*.csv"):
        try:
            seasons.append(int(path.stem.replace("weather_bucket_games_season", "")))
        except ValueError:
            continue
    return sorted(seasons)


def main() -> None:
    args = parse_args()
    seasons: Iterable[int] = args.season if args.season else detect_seasons()
    if not seasons:
        print("Brak plików weather_bucket_games_season*.csv w data/results/")
        return

    for season in seasons:
        df = load_season_df(season)
        if df is None:
            print(f"[{season}] Plik nie istnieje – pomijam.")
            continue
        if df.empty:
            print(f"[{season}] Brak rozliczonych picków (WIN/LOSS) – pomijam.")
            continue

        summary = summarize(df)
        print(f"\n=== Season {season} ===")
        print(summary.to_string())


if __name__ == "__main__":
    main()
