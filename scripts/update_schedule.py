"""
Utility script for appending weekly matchup schedules to data/schedules/<season>.parquet.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import polars as pl

# Default template matchups keyed by week (season 2025).
# Extend or override via data/schedule_templates/<season>.json.
_DEFAULT_WEEK_MATCHUPS: dict[int, list[tuple[str, str]]] = {}

_DEFAULT_TEMPLATE_SEASON = 2025


def _normalize_templates(raw: object, *, source: Path) -> dict[int, list[tuple[str, str]]]:
    if not isinstance(raw, dict):
        raise ValueError(f"Invalid template format in {source}: expected JSON object.")

    result: dict[int, list[tuple[str, str]]] = {}
    for week_key, matchups in raw.items():
        try:
            week = int(week_key)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"Invalid week key '{week_key}' in {source}. Expected integer-like key."
            ) from exc

        if not isinstance(matchups, list):
            raise ValueError(f"Invalid matchups for week {week} in {source}: expected list.")

        pairs: list[tuple[str, str]] = []
        for pair in matchups:
            if not isinstance(pair, list) or len(pair) != 2:
                raise ValueError(
                    f"Invalid matchup entry in week {week} in {source}: expected [home, away]."
                )
            home, away = pair
            if not isinstance(home, str) or not isinstance(away, str):
                raise ValueError(
                    f"Invalid matchup teams in week {week} in {source}: expected strings."
                )
            pairs.append((home, away))

        result[week] = pairs

    if not result:
        raise ValueError(f"Template in {source} is empty.")

    return result


def _load_week_matchups(season: int, templates_root: Path) -> dict[int, list[tuple[str, str]]]:
    template_path = templates_root / f"{season}.json"
    if template_path.exists():
        with template_path.open("r", encoding="utf-8") as fp:
            raw = json.load(fp)
        return _normalize_templates(raw, source=template_path)

    if season == _DEFAULT_TEMPLATE_SEASON:
        return _DEFAULT_WEEK_MATCHUPS

    raise ValueError(
        f"No schedule template found for season {season}: {template_path}. "
        f"Add this file or use built-in season {_DEFAULT_TEMPLATE_SEASON}."
    )


def _build_week_frame(
    season: int,
    week: int,
    week_matchups: dict[int, list[tuple[str, str]]],
) -> pl.DataFrame:
    """
    Create a DataFrame of matchups for the requested week based on templates.
    """
    try:
        matchups = week_matchups[week]
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


def update_schedule(
    *,
    season: int,
    week: int,
    data_root: Path = Path("data"),
    templates_root: Path = Path("data/schedule_templates"),
) -> Path:
    """
    Append the schedule for (season, week) into data_root/schedules/<season>.parquet.
    """
    if season <= 0 or week <= 0:
        raise ValueError("season and week must be positive integers.")

    week_matchups = _load_week_matchups(season=season, templates_root=templates_root)

    schedule_path = data_root / "schedules" / f"{season}.parquet"
    schedule_path.parent.mkdir(parents=True, exist_ok=True)

    new_games = _build_week_frame(season, week, week_matchups)

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
    parser.add_argument(
        "--templates-root",
        type=Path,
        default=Path("data/schedule_templates"),
        help="Directory with schedule templates named <season>.json",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv or sys.argv[1:])
    try:
        output = update_schedule(
            season=args.season,
            week=args.week,
            data_root=args.data_root,
            templates_root=args.templates_root,
        )
    except Exception as exc:  # pragma: no cover - CLI safety net
        print(f"[error] {exc}")
        raise SystemExit(1) from exc
    print(f"[ok] Saved schedule to {output}")


if __name__ == "__main__":
    main()
