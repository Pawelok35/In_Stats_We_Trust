"""Compare pick variant performance on train vs validation seasons.

Defaults:
    train = 2021 2022 2023
    val   = 2024 2025
    variants = picks_variant_* directories found in data/

Usage:
    python -X utf8 scripts/pick_variant_split_summary.py
    python -X utf8 scripts/pick_variant_split_summary.py --train 2021 2022 --val 2023 2024 --variants picks_variant_k picks_variant_j
"""

from __future__ import annotations

import argparse
import glob
import json
from pathlib import Path
from typing import Iterable, List, Tuple

import pandas as pd

import sys
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
import evaluate_picks  # type: ignore

DATA_DIR = ROOT / "data"
MANUAL_RESULTS = DATA_DIR / "results" / "manual_results.jsonl"


def detect_variants() -> List[str]:
    return sorted(p.name for p in DATA_DIR.glob("picks_variant_*") if p.is_dir())


def weeks_available(variant: str, season: int) -> Tuple[int, int] | None:
    pattern = DATA_DIR / variant / str(season) / "week_*.jsonl"
    weeks = []
    for path in glob.glob(str(pattern)):
        try:
            wk = int(Path(path).stem.replace("week_", ""))
            weeks.append(wk)
        except ValueError:
            continue
    if not weeks:
        return None
    return min(weeks), max(weeks)


def evaluate_variant(variant: str, seasons: Iterable[int], tags: set[str] | None) -> pd.DataFrame:
    rows: List[dict] = []
    for season in seasons:
        wk_range = weeks_available(variant, season)
        if not wk_range:
            continue
        start_week, end_week = wk_range
        picks = evaluate_picks.load_picks(DATA_DIR / variant, season, start_week, end_week)
        manual = evaluate_picks.load_manual_results(MANUAL_RESULTS, season=season)
        results = evaluate_picks.load_results(season, manual)
        summary = evaluate_picks.evaluate_picks(picks, results, tags=tags)
        # jeden wiersz per tag
        for tag, agg in summary.items():
            wins = agg["wins"]
            losses = agg["losses"]
            pushes = agg["pushes"]
            pending = agg["pending"]
            total = wins + losses
            win_pct = (wins / total * 100) if total else 0.0
            rows.append(
                {
                    "variant": variant,
                    "season": season,
                    "tag": tag,
                    "WIN": wins,
                    "LOSS": losses,
                    "PUSH": pushes,
                    "PENDING": pending,
                    "Win_pct": round(win_pct, 2),
                }
            )
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)


def summarize(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    agg = (
        df.groupby("variant")
        .agg(
            WIN=("WIN", "sum"),
            LOSS=("LOSS", "sum"),
            PUSH=("PUSH", "sum"),
            PENDING=("PENDING", "sum"),
        )
        .assign(Win_pct=lambda d: (d["WIN"] / (d["WIN"] + d["LOSS"])).fillna(0) * 100)
        .round(2)
        .sort_index()
    )
    return agg


def summarize_by_season(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    agg = (
        df.groupby(["variant", "season"])
        .agg(
            WIN=("WIN", "sum"),
            LOSS=("LOSS", "sum"),
            PUSH=("PUSH", "sum"),
            PENDING=("PENDING", "sum"),
        )
        .assign(Win_pct=lambda d: (d["WIN"] / (d["WIN"] + d["LOSS"])).fillna(0) * 100)
        .round(2)
        .sort_index()
    )
    return agg


def summarize_by_tag(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "tag" not in df.columns:
        return pd.DataFrame()
    agg = (
        df.groupby(["variant", "tag"])
        .agg(
            WIN=("WIN", "sum"),
            LOSS=("LOSS", "sum"),
            PUSH=("PUSH", "sum"),
            PENDING=("PENDING", "sum"),
        )
        .assign(Win_pct=lambda d: (d["WIN"] / (d["WIN"] + d["LOSS"])).fillna(0) * 100)
        .round(2)
        .sort_index()
    )
    return agg


def summarize_by_tag_season(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "tag" not in df.columns:
        return pd.DataFrame()
    agg = (
        df.groupby(["variant", "tag", "season"])
        .agg(
            WIN=("WIN", "sum"),
            LOSS=("LOSS", "sum"),
            PUSH=("PUSH", "sum"),
            PENDING=("PENDING", "sum"),
        )
        .assign(Win_pct=lambda d: (d["WIN"] / (d["WIN"] + d["LOSS"])).fillna(0) * 100)
        .round(2)
        .sort_index()
    )
    return agg


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare pick variant performance on train vs validation seasons."
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
    parser.add_argument(
        "--variants",
        type=str,
        nargs="*",
        help="Variants to include (default: auto-detect picks_variant_* dirs)",
    )
    parser.add_argument(
        "--tags",
        type=str,
        nargs="*",
        help="Optional list of tags to include (e.g., GOY GOM GOW 'VALUE PLAY'). "
        "If nie ustawisz, liczymy wszystkie tagi.",
    )
    return parser.parse_args()


def maybe_print(label: str, df: pd.DataFrame) -> None:
    if df.empty:
        print(f"[{label}] Brak danych WIN/LOSS.")
        return
    print(f"\n=== {label} (agg) ===")
    print(df.to_string())
    df_tag = summarize_by_tag(df)
    if not df_tag.empty:
        print(f"\n=== {label} by tag ===")
        print(df_tag.to_string())
    df_tag_season = summarize_by_tag_season(df)
    if not df_tag_season.empty:
        print(f"\n=== {label} by tag & season ===")
        print(df_tag_season.to_string())


def main() -> None:
    args = parse_args()
    variants = args.variants or detect_variants()
    if not variants:
        print("Brak katalogów picks_variant_* w data/")
        return

    tags = set(args.tags) if args.tags else None

    for label, seasons in [("TRAIN", args.train), ("VAL", args.val)]:
        frames: List[pd.DataFrame] = []
        for var in variants:
            df = evaluate_variant(var, seasons, tags)
            if df.empty:
                continue
            frames.append(df)
        if not frames:
            print(f"[{label}] Brak danych dla sezonów {seasons}")
            continue
        df_all = pd.concat(frames, ignore_index=True)
        maybe_print(f"{label}", summarize(df_all))
        maybe_print(f"{label} by season", summarize_by_season(df_all))


if __name__ == "__main__":
    main()
