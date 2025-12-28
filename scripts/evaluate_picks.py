from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import nfl_data_py as nfl
import pandas as pd
from urllib.error import URLError

from utils.config import load_settings


def load_picks(
    base_dir: Path, season: int, start_week: int | None, end_week: int | None
) -> List[Dict]:
    season_dir = base_dir / str(season)
    if not season_dir.exists():
        raise FileNotFoundError(f"Brak katalogu z pickami: {season_dir}")

    picks: List[Dict] = []
    for path in sorted(season_dir.glob("week_*.jsonl")):
        week = int(path.stem.split("_")[1])
        if start_week and week < start_week:
            continue
        if end_week and week > end_week:
            continue
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                record = json.loads(line)
                picks.append(record)
    return picks


def _load_schedule_df(season: int) -> pd.DataFrame:
    """
    Best-effort schedule loader: prefer local parquet (written by update_schedule.py),
    fall back to nfl_data_py only if needed. Protects against network timeouts when
    evaluating picks.
    """
    settings = load_settings()
    data_root = Path(settings.data_root)
    candidates = [
        data_root / "schedules" / f"{season}.parquet",
        data_root / "schedule" / f"{season}.parquet",
    ]
    for path in candidates:
        if path.exists():
            return pd.read_parquet(path)

    try:
        return nfl.import_schedules([season])
    except URLError as exc:
        raise RuntimeError(
            f"Failed to load schedule for season {season}: {exc.reason} "
            "(network unavailable and no local parquet found)."
        ) from exc


def load_results(
    season: int, manual_overrides: Dict[Tuple[int, str, str], Dict]
) -> Dict[Tuple[int, str, str], Dict]:
    df = _load_schedule_df(season)
    # Not every schedule parquet has game_type; filter only when present, otherwise use all rows.
    if "game_type" in df.columns:
        df = df[df["game_type"] == "REG"]
    results: Dict[Tuple[int, str, str], Dict] = {}
    for _, row in df.iterrows():
        week = int(row["week"])
        # Prefer standard naming; fall back to alternative column names if needed.
        home = str(row.get("home_team") or row.get("team_a") or row.get("TEAM") or "").upper()
        away = str(row.get("away_team") or row.get("team_b") or row.get("OPP") or "").upper()
        if not home or not away:
            continue
        results[(week, home, away)] = {
            "home_score": row.get("home_score"),
            "away_score": row.get("away_score"),
        }

    for key, value in manual_overrides.items():
        results[key] = value

    return results


def load_manual_results(path: Path | None, season: int | None = None) -> Dict[Tuple[int, str, str], Dict]:
    if not path or not path.exists():
        return {}
    overrides: Dict[Tuple[int, str, str], Dict] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        data = json.loads(line)
        season_val = int(data["season"])
        if season is not None and season_val != season:
            continue
        week = int(data["week"])
        # only override current season
        home = str(data["home_team"]).upper()
        away = str(data["away_team"]).upper()
        overrides[(week, home, away)] = {
            "home_score": data["home_score"],
            "away_score": data["away_score"],
        }
    return overrides


def evaluate_picks(
    picks: Iterable[Dict],
    results: Dict[Tuple[int, str, str], Dict],
    tags: set[str] | None,
) -> Dict[str, Dict]:
    summary: Dict[str, Dict[str, float]] = defaultdict(lambda: {"wins": 0, "losses": 0, "pushes": 0, "pending": 0})

    for pick in picks:
        tag = pick["tag"]
        if tags and tag not in tags:
            continue
        key = (int(pick["week"]), pick["home"], pick["away"])
        game = results.get(key)
        if not game or pd.isna(game["home_score"]) or pd.isna(game["away_score"]):
            summary[tag]["pending"] += 1
            continue

        home_score = int(game["home_score"])
        away_score = int(game["away_score"])

        if pick["model_winner"] == pick["home"]:
            pick_margin = home_score - away_score
        else:
            pick_margin = away_score - home_score

        handicap = float(pick.get("handicap", 0.0))
        ats_margin = pick_margin + handicap

        if ats_margin > 0:
            summary[tag]["wins"] += 1
        elif ats_margin == 0:
            summary[tag]["pushes"] += 1
        else:
            summary[tag]["losses"] += 1

    return summary


def print_summary(summary: Dict[str, Dict], tags: set[str] | None) -> None:
    header = f"{'Tag':<12} {'W':>4} {'L':>4} {'P':>4} {'Pend':>5} {'Win%':>6}"
    print(header)
    print("-" * len(header))
    keys = sorted(tags) if tags else sorted(summary.keys())
    for tag in keys:
        stats = summary.get(tag, {"wins": 0, "losses": 0, "pushes": 0, "pending": 0})
        wins = int(stats["wins"])
        losses = int(stats["losses"])
        pushes = int(stats["pushes"])
        pending = int(stats["pending"])
        total = wins + losses
        win_pct = (wins / total * 100) if total else 0.0
        print(f"{tag:<12} {wins:>4} {losses:>4} {pushes:>4} {pending:>5} {win_pct:>6.1f}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ewaluacja skuteczności tagów modelu.")
    parser.add_argument("--season", type=int, required=True, help="Sezon, np. 2025")
    parser.add_argument("--from-week", type=int, help="Tydzień początkowy (opcjonalnie)")
    parser.add_argument("--to-week", type=int, help="Tydzień końcowy (opcjonalnie)")
    parser.add_argument("--tag", action="append", help="Filtruj tylko wskazane tagi (parametr wielokrotny)")
    parser.add_argument(
        "--picks-dir",
        type=Path,
        default=Path("data/picks"),
        help="Katalog z plikami JSONL zawierającymi picki (domyślnie data/picks)",
    )
    parser.add_argument(
        "--manual-results",
        type=Path,
        help="Opcjonalny plik JSONL z wynikami (1 rekord na linię: season, week, home_team, away_team, home_score, away_score)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    tags = set(t.upper() for t in args.tag) if args.tag else None
    picks = load_picks(args.picks_dir, args.season, args.from_week, args.to_week)
    if not picks:
        print("Brak picków do ocenienia w zadanym zakresie.")
        return
    manual = load_manual_results(args.manual_results, season=args.season)
    results = load_results(args.season, manual)
    summary = evaluate_picks(picks, results, tags)
    print_summary(summary, tags)


if __name__ == "__main__":
    main()
