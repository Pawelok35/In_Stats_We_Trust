"""
Utility script for appending weekly matchup schedules to data/schedules/<season>.parquet.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import polars as pl

# Template matchups keyed by week. Extend this mapping as new weeks are available.
_WEEK_MATCHUPS: dict[int, list[tuple[str, str]]] = {
    10: [
        ("DEN", "LV"),
        ("IND", "ATL"),
        ("CAR", "NO"),
        ("CHI", "NYG"),
        ("HOU", "JAX"),
        ("MIA", "BUF"),
        ("MIN", "BAL"),
        ("NYJ", "CLE"),
        ("TB", "NE"),
        ("SEA", "ARI"),
        ("SF", "LAR"),
        ("WAS", "DET"),
        ("LAC", "PIT"),
        ("GB", "PHI"),
    ],
}


def _build_week_frame(season: int, week: int) -> pl.DataFrame:
    """
    Create a DataFrame of matchups for the requested week based on the templates above.
    """
    try:
        matchups = _WEEK_MATCHUPS[week]
    except KeyError as exc:
        raise ValueError(f"No schedule template defined for week {week}.") from exc

    return pl.DataFrame(
        {
            "season": [season] * len(matchups),
            "week": [week] * len(matchups),
            "home_team": [home for home, _ in matchups],
            "away_team": [away for _, away in matchups],
        }
    )


def update_schedule(*, season: int, week: int, data_root: Path = Path("data")) -> Path:
    """
    Append the schedule for (season, week) into data_root/schedules/<season>.parquet.
    """
    if season <= 0 or week <= 0:
        raise ValueError("season and week must be positive integers.")

    schedule_path = data_root / "schedules" / f"{season}.parquet"
    schedule_path.parent.mkdir(parents=True, exist_ok=True)

    new_games = _build_week_frame(season, week)

    if schedule_path.exists():
        existing = pl.read_parquet(schedule_path)
        schedule = pl.concat([existing, new_games], how="vertical").unique(
            subset=["season", "week", "home_team", "away_team"]
        )
    else:
        schedule = new_games

    schedule.write_parquet(schedule_path)
    return schedule_path


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Append matchup schedules to data/schedules/<season>.parquet"
    )
    parser.add_argument("--season", type=int, default=2025, help="Season to update (default: 2025)")
    parser.add_argument("--week", type=int, required=True, help="Week number to append")
    parser.add_argument(
        "--data-root",
        type=Path,
        default=Path("data"),
        help="Root directory containing the schedules/ folder (default: data)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv or sys.argv[1:])
    try:
        output = update_schedule(season=args.season, week=args.week, data_root=args.data_root)
    except Exception as exc:  # pragma: no cover - CLI safety net
        print(f"[error] {exc}")
        raise SystemExit(1) from exc
    print(f"[ok] Saved schedule to {output}")


if __name__ == "__main__":
    main()
