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
        ("LA", "BUF"),
        ("ATL", "NO"),
        ("CAR", "CLE"),
        ("CHI", "SF"),
        ("CIN", "PIT"),
        ("HOU", "IND"),
        ("DET", "PHI"),
        ("WAS", "JAX"),
        ("MIA", "NE"),
        ("NYJ", "BAL"),
        ("ARI", "KC"),
        ("MIN", "GB"),
        ("TEN", "NYG"),
        ("LAC", "LV"),
        ("DAL", "TB"),
        ("SEA", "DEN"),
    ],
    2: [
        ("KC", "LAC"),
        ("NYG", "CAR"),
        ("CLE", "NYJ"),
        ("JAX", "IND"),
        ("DET", "WAS"),
        ("BAL", "MIA"),
        ("NO", "TB"),
        ("PIT", "NE"),
        ("LA", "ATL"),
        ("SF", "SEA"),
        ("DAL", "CIN"),
        ("LV", "ARI"),
        ("DEN", "HOU"),
        ("GB", "CHI"),
        ("BUF", "TEN"),
        ("PHI", "MIN"),
    ],
    3: [
        ("CLE", "PIT"),
        ("MIA", "BUF"),
        ("CAR", "NO"),
        ("CHI", "HOU"),
        ("NYJ", "CIN"),
        ("IND", "KC"),
        ("MIN", "DET"),
        ("NE", "BAL"),
        ("TEN", "LV"),
        ("WAS", "PHI"),
        ("LAC", "JAX"),
        ("SEA", "ATL"),
        ("ARI", "LA"),
        ("TB", "GB"),
        ("DEN", "SF"),
        ("NYG", "DAL"),
    ],
    4: [
        ("CIN", "MIA"),
        ("NO", "MIN"),
        ("ATL", "CLE"),
        ("BAL", "BUF"),
        ("NYG", "CHI"),
        ("IND", "TEN"),
        ("DAL", "WAS"),
        ("DET", "SEA"),
        ("HOU", "LAC"),
        ("PHI", "JAX"),
        ("PIT", "NYJ"),
        ("CAR", "ARI"),
        ("LV", "DEN"),
        ("GB", "NE"),
        ("TB", "KC"),
        ("SF", "LA"),
    ],
    5: [
        ("DEN", "IND"),
        ("GB", "NYG"),
        ("TB", "ATL"),
        ("BUF", "PIT"),
        ("MIN", "CHI"),
        ("CLE", "LAC"),
        ("NE", "DET"),
        ("JAX", "HOU"),
        ("NYJ", "MIA"),
        ("NO", "SEA"),
        ("WAS", "TEN"),
        ("CAR", "SF"),
        ("ARI", "PHI"),
        ("LA", "DAL"),
        ("BAL", "CIN"),
        ("KC", "LV"),
    ],
    6: [
        ("CHI", "WAS"),
        ("ATL", "SF"),
        ("NO", "CIN"),
        ("CLE", "NE"),
        ("IND", "JAX"),
        ("GB", "NYJ"),
        ("MIA", "MIN"),
        ("NYG", "BAL"),
        ("PIT", "TB"),
        ("LA", "CAR"),
        ("SEA", "ARI"),
        ("KC", "BUF"),
        ("PHI", "DAL"),
        ("LAC", "DEN"),
    ],
    7: [
        ("ARI", "NO"),
        ("CIN", "ATL"),
        ("CAR", "TB"),
        ("BAL", "CLE"),
        ("TEN", "IND"),
        ("DAL", "DET"),
        ("WAS", "GB"),
        ("JAX", "NYG"),
        ("LV", "HOU"),
        ("NYJ", "DEN"),
        ("SF", "KC"),
        ("LAC", "SEA"),
        ("MIA", "PIT"),
        ("NE", "CHI"),
    ],
    8: [
        ("TB", "BAL"),
        ("DEN", "JAX"),
        ("DET", "MIA"),
        ("PHI", "PIT"),
        ("ATL", "CAR"),
        ("DAL", "CHI"),
        ("MIN", "ARI"),
        ("NO", "LV"),
        ("NYJ", "NE"),
        ("HOU", "TEN"),
        ("LA", "SF"),
        ("IND", "WAS"),
        ("SEA", "NYG"),
        ("BUF", "GB"),
        ("CLE", "CIN"),
    ],
    9: [
        ("PHI", "HOU"),
        ("NYJ", "BUF"),
        ("DET", "GB"),
        ("WAS", "MIN"),
        ("ATL", "LAC"),
        ("CIN", "CAR"),
        ("CHI", "MIA"),
        ("NE", "IND"),
        ("JAX", "LV"),
        ("ARI", "SEA"),
        ("TB", "LA"),
        ("KC", "TEN"),
        ("NO", "BAL"),
    ],
    10: [
        ("CAR", "ATL"),
        ("TB", "SEA"),
        ("BUF", "MIN"),
        ("MIA", "CLE"),
        ("TEN", "DEN"),
        ("NYG", "HOU"),
        ("CHI", "DET"),
        ("KC", "JAX"),
        ("PIT", "NO"),
        ("LV", "IND"),
        ("GB", "DAL"),
        ("LA", "ARI"),
        ("SF", "LAC"),
        ("PHI", "WAS"),
    ],
    11: [
        ("GB", "TEN"),
        ("BUF", "CLE"),
        ("NYG", "DET"),
        ("HOU", "WAS"),
        ("NE", "NYJ"),
        ("ATL", "CHI"),
        ("BAL", "CAR"),
        ("IND", "PHI"),
        ("NO", "LA"),
        ("DEN", "LV"),
        ("PIT", "CIN"),
        ("MIN", "DAL"),
        ("LAC", "KC"),
        ("ARI", "SF"),
    ],
    12: [
        ("DET", "BUF"),
        ("DAL", "NYG"),
        ("MIN", "NE"),
        ("TEN", "CIN"),
        ("CLE", "TB"),
        ("MIA", "HOU"),
        ("JAX", "BAL"),
        ("WAS", "ATL"),
        ("CAR", "DEN"),
        ("NYJ", "CHI"),
        ("SEA", "LV"),
        ("ARI", "LAC"),
        ("KC", "LA"),
        ("SF", "NO"),
        ("PHI", "GB"),
        ("IND", "PIT"),
    ],
    13: [
        ("NE", "BUF"),
        ("HOU", "CLE"),
        ("BAL", "DEN"),
        ("DET", "JAX"),
        ("MIN", "NYJ"),
        ("NYG", "WAS"),
        ("PHI", "TEN"),
        ("ATL", "PIT"),
        ("CHI", "GB"),
        ("SF", "MIA"),
        ("LA", "SEA"),
        ("CIN", "KC"),
        ("LV", "LAC"),
        ("DAL", "IND"),
        ("TB", "NO"),
    ],
    14: [
        ("LA", "LV"),
        ("BUF", "NYJ"),
        ("CIN", "CLE"),
        ("DAL", "HOU"),
        ("DET", "MIN"),
        ("TEN", "JAX"),
        ("PHI", "NYG"),
        ("BAL", "PIT"),
        ("DEN", "KC"),
        ("SEA", "CAR"),
        ("SF", "TB"),
        ("LAC", "MIA"),
        ("NE", "ARI"),
    ],
    15: [
        ("SF", "SEA"),
        ("MIN", "IND"),
        ("CLE", "BAL"),
        ("BUF", "MIA"),
        ("NO", "ATL"),
        ("CAR", "PIT"),
        ("CHI", "PHI"),
        ("JAX", "DAL"),
        ("NYJ", "DET"),
        ("HOU", "KC"),
        ("DEN", "ARI"),
        ("LV", "NE"),
        ("TB", "CIN"),
        ("LAC", "TEN"),
        ("WAS", "NYG"),
        ("GB", "LA"),
    ],
    16: [
        ("NYJ", "JAX"),
        ("BAL", "ATL"),
        ("CHI", "BUF"),
        ("CAR", "DET"),
        ("NE", "CIN"),
        ("CLE", "NO"),
        ("TEN", "HOU"),
        ("KC", "SEA"),
        ("MIN", "NYG"),
        ("SF", "WAS"),
        ("DAL", "PHI"),
        ("PIT", "LV"),
        ("MIA", "GB"),
        ("LA", "DEN"),
        ("ARI", "TB"),
        ("IND", "LAC"),
    ],
    17: [
        ("TEN", "DAL"),
        ("ATL", "ARI"),
        ("TB", "CAR"),
        ("DET", "CHI"),
        ("WAS", "CLE"),
        ("NYG", "IND"),
        ("KC", "DEN"),
        ("HOU", "JAX"),
        ("NE", "MIA"),
        ("PHI", "NO"),
        ("SEA", "NYJ"),
        ("LV", "SF"),
        ("GB", "MIN"),
        ("LAC", "LA"),
        ("BAL", "PIT"),
    ],
    18: [
        ("LV", "KC"),
        ("JAX", "TEN"),
        ("BUF", "NE"),
        ("CIN", "BAL"),
        ("ATL", "TB"),
        ("NO", "CAR"),
        ("CHI", "MIN"),
        ("PIT", "CLE"),
        ("IND", "HOU"),
        ("MIA", "NYJ"),
        ("SF", "ARI"),
        ("WAS", "DAL"),
        ("DEN", "LAC"),
        ("PHI", "NYG"),
        ("SEA", "LA"),
        ("GB", "DET"),
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
