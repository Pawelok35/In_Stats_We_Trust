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
        1: [
        ("PHI", "DAL"),
        ("LAC", "KC"),
        ("ATL", "TB"),
        ("JAX", "CAR"),
        ("CLE", "CIN"),
        ("IND", "MIA"),
        ("NO", "ARI"),
        ("NE", "LV"),
        ("WAS", "NYG"),
        ("NYJ", "PIT"),
        ("DEN", "TEN"),
        ("SEA", "SF"),
        ("GB", "DET"),
        ("LA", "HOU"),
        ("BUF", "BAL"),
        ("CHI", "MIN"),
        ],
        2: [
        ("GB", "WAS"),
        ("NYJ", "BUF"),
        ("DET", "CHI"),
        ("CIN", "JAX"),
        ("BAL", "CLE"),
        ("DAL", "NYG"),
        ("MIA", "NE"),
        ("NO", "SF"),
        ("TEN", "LA"),
        ("PIT", "SEA"),
        ("ARI", "CAR"),
        ("IND", "DEN"),
        ("KC", "PHI"),
        ("MIN", "ATL"),
        ("HOU", "TB"),
        ("LV", "LAC"),
    ],
    3: [
        ("BUF", "MIA"),
        ("CAR", "ATL"),
        ("MIN", "CIN"),
        ("CLE", "GB"),
        ("TEN", "IND"),
        ("JAX", "HOU"),
        ("NE", "PIT"),
        ("TB", "NYJ"),
        ("PHI", "LA"),
        ("WAS", "LV"),
        ("LAC", "DEN"),
        ("SEA", "NO"),
        ("CHI", "DAL"),
        ("SF", "ARI"),
        ("NYG", "KC"),
        ("BAL", "DET"),
    ],
    4: [
        ("ARI", "SEA"),
        ("PIT", "MIN"),
        ("ATL", "WAS"),
        ("BUF", "NO"),
        ("NE", "CAR"),
        ("DET", "CLE"),
        ("HOU", "TEN"),
        ("NYG", "LAC"),
        ("TB", "PHI"),
        ("LA", "IND"),
        ("SF", "JAX"),
        ("LV", "CHI"),
        ("KC", "BAL"),
        ("DAL", "GB"),
        ("MIA", "NYJ"),
        ("DEN", "CIN"),
    ],
    5: [
        ("LA", "SF"),
        ("CLE", "MIN"),
        ("CAR", "MIA"),
        ("IND", "LV"),
        ("NYJ", "DAL"),
        ("PHI", "DEN"),
        ("BAL", "HOU"),
        ("NO", "NYG"),
        ("ARI", "TEN"),
        ("SEA", "TB"),
        ("CIN", "DET"),
        ("LAC", "WAS"),
        ("BUF", "NE"),
        ("JAX", "KC"),
    ],
    6: [
        ("NYG", "PHI"),
        ("NYJ", "DEN"),
        ("CAR", "DAL"),
        ("PIT", "CLE"),
        ("IND", "ARI"),
        ("JAX", "SEA"),
        ("MIA", "LAC"),
        ("NO", "NE"),
        ("BAL", "LA"),
        ("LV", "TEN"),
        ("GB", "CIN"),
        ("TB", "SF"),
        ("KC", "DET"),
        ("ATL", "BUF"),
        ("WAS", "CHI"),
    ],
    7: [
        ("CIN", "PIT"),
        ("JAX", "LA"),
        ("CHI", "NO"),
        ("MIN", "PHI"),
        ("NYJ", "CAR"),
        ("CLE", "MIA"),
        ("KC", "LV"),
        ("TEN", "NE"),
        ("LAC", "IND"),
        ("DEN", "NYG"),
        ("ARI", "GB"),
        ("DAL", "WAS"),
        ("SF", "ATL"),
        ("DET", "TB"),
        ("SEA", "HOU"),
    ],
    8: [
        ("LAC", "MIN"),
        ("ATL", "MIA"),
        ("CAR", "BUF"),
        ("BAL", "CHI"),
        ("HOU", "SF"),
        ("CIN", "NYJ"),
        ("NE", "CLE"),
        ("PHI", "NYG"),
        ("NO", "TB"),
        ("IND", "TEN"),
        ("DEN", "DAL"),
        ("PIT", "GB"),
        ("KC", "WAS"),
    ],
    9: [
        ("MIA", "BAL"),
        ("NE", "ATL"),
        ("CIN", "CHI"),
        ("DET", "MIN"),
        ("GB", "CAR"),
        ("PIT", "IND"),
        ("HOU", "DEN"),
        ("NYG", "SF"),
        ("TEN", "LAC"),
        ("LV", "JAX"),
        ("LA", "NO"),
        ("BUF", "KC"),
        ("WAS", "SEA"),
        ("DAL", "ARI"),
    ],
    10: [
        ("DEN", "LV"),
        ("IND", "ATL"),
        ("MIA", "BUF"),
        ("CHI", "NYG"),
        ("NYJ", "CLE"),
        ("MIN", "BAL"),
        ("CAR", "NO"),
        ("TB", "NE"),
        ("SEA", "ARI"),
        ("WAS", "DET"),
        ("SF", "LA"),
        ("LAC", "PIT"),
        ("GB", "PHI"),
    ],
    11: [
        ("NE", "NYJ"),
        ("MIA", "WAS"),
        ("ATL", "CAR"),
        ("BUF", "TB"),
        ("MIN", "CHI"),
        ("PIT", "CIN"),
        ("NYG", "GB"),
        ("TEN", "HOU"),
        ("JAX", "LAC"),
        ("ARI", "SF"),
        ("LA", "SEA"),
        ("CLE", "BAL"),
        ("DEN", "KC"),
        ("PHI", "DET"),
        ("LV", "DAL"),
    ],
    12: [
        ("HOU", "BUF"),
        ("CHI", "PIT"),
        ("CIN", "NE"),
        ("KC", "IND"),
        ("DET", "NYG"),
        ("GB", "MIN"),
        ("BAL", "NYJ"),
        ("TEN", "SEA"),
        ("LV", "CLE"),
        ("ARI", "JAX"),
        ("NO", "ATL"),
        ("DAL", "PHI"),
        ("LA", "TB"),
        ("SF", "CAR"),
    ],
    13: [
        ("DET", "GB"),
        ("DAL", "KC"),
        ("BAL", "CIN"),
        ("PHI", "CHI"),
        ("CLE", "SF"),
        ("TEN", "JAX"),
        ("MIA", "NO"),
        ("TB", "ARI"),
        ("NYJ", "ATL"),
        ("CAR", "LA"),
        ("IND", "HOU"),
        ("SEA", "MIN"),
        ("LAC", "LV"),
        ("PIT", "BUF"),
        ("WAS", "DEN"),
        ("NE", "NYG"),
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
        existing = existing.filter(pl.col("week") != week)
        schedule = pl.concat([existing, new_games], how="vertical")
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
