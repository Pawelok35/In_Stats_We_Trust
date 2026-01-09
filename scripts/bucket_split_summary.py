"""Compare bucket performance on train vs validation seasons to reduce overfitting risk.

Usage:
    python -X utf8 scripts/bucket_split_summary.py \
        --train 2021 2022 2023 --val 2024 2025

Defaults:
    train = 2021 2022 2023
    val   = 2024 2025
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable, List

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = ROOT / "data" / "results"


def load_season(season: int) -> pd.DataFrame | None:
    path = RESULTS_DIR / f"weather_bucket_games_season{season}.csv"
    if not path.exists():
        return None
    df = pd.read_csv(path)
    df = df[df["result"].isin(["WIN", "LOSS"])].copy()
    if df.empty:
        return df
    df["pnl"] = df.apply(
        lambda r: 0.9 * r["stake_u"] if r["result"] == "WIN" else -1 * r["stake_u"],
        axis=1,
    )
    return df


def summarize(df: pd.DataFrame) -> pd.DataFrame:
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
    table = table[["WIN", "LOSS", "Total", "Win%", "PnL_0.9/-1"]]
    return table.sort_index()


def combine(seasons: Iterable[int]) -> pd.DataFrame:
    dfs: List[pd.DataFrame] = []
    for season in seasons:
        df = load_season(season)
        if df is None or df.empty:
            continue
        df["season"] = season
        dfs.append(df)
    if not dfs:
        return pd.DataFrame()
    return pd.concat(dfs, ignore_index=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare bucket performance on train vs validation seasons."
    )
    parser.add_argument(
        "--train",
        type=int,
        nargs="*",
        default=[2021, 2022, 2023],
        help="Train seasons (default: 2021 2022 2023)",
    )
    parser.add_argument(
        "--val",
        type=int,
        nargs="*",
        default=[2024, 2025],
        help="Validation seasons (default: 2024 2025)",
    )
    return parser.parse_args()


def maybe_print(label: str, seasons: Iterable[int]) -> None:
    df = combine(seasons)
    if df.empty:
        print(f"[{label}] Brak danych WIN/LOSS dla sezonów: {list(seasons)}")
        return
    summary = summarize(df)
    print(f"\n=== {label} ({','.join(map(str, seasons))}) ===")
    print(summary.to_string())


def main() -> None:
    args = parse_args()
    maybe_print("TRAIN", args.train)
    maybe_print("VAL", args.val)


if __name__ == "__main__":
    main()
