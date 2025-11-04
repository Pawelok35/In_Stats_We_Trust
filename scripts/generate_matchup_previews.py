"""
Generate matchup comparison reports for every scheduled game in a given week.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable, Optional

import polars as pl

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from utils.config import load_settings  # noqa: E402
from utils.logging import get_logger  # noqa: E402
import app.reports as reports  # noqa: E402

logger = get_logger(__name__)


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build comparison (matchup) reports for all scheduled games in the selected week. "
            "Ideal for pre-game previews when rolling metrics are refreshed through the prior week."
        )
    )
    parser.add_argument("--season", type=int, default=2025, help="Season to process (default: 2025)")
    parser.add_argument("--week", type=int, required=True, help="Week to process")
    parser.add_argument(
        "--reference-week",
        type=int,
        help=(
            "Week whose metrics should power the previews (defaults to week-1). "
            "Use when the target week has not been played yet."
        ),
    )
    parser.add_argument(
        "--require-complete-schedule",
        action="store_true",
        help="Fail if the schedule references teams without available metrics (default: warn and skip).",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Also refresh the weekly summary after generating matchup reports.",
    )
    return parser.parse_args(argv)


def _load_schedule_pairs(data_root: Path, season: int, week: int) -> tuple[pl.DataFrame, Path]:
    candidates = [
        data_root / "schedules" / f"{season}.parquet",
        data_root / "schedule" / f"{season}.parquet",
    ]
    schedule_path = next((path for path in candidates if path.exists()), None)
    if schedule_path is None:
        raise FileNotFoundError(f"Schedule dataset not found for season {season}.")

    schedule_df = pl.read_parquet(schedule_path)
    if schedule_df.is_empty():
        raise ValueError(f"Schedule dataset at {schedule_path} is empty.")

    if "week" in schedule_df.columns:
        schedule_df = schedule_df.filter(pl.col("week") == week)
    if schedule_df.is_empty():
        raise ValueError(f"No schedule entries for season {season} week {week}.")

    if {"home_team", "away_team"}.issubset(schedule_df.columns):
        pairs = schedule_df.select(
            [
                pl.col("home_team").alias("team_a"),
                pl.col("away_team").alias("team_b"),
            ]
        )
    elif {"team_a", "team_b"}.issubset(schedule_df.columns):
        pairs = schedule_df.select(["team_a", "team_b"])
    elif {"TEAM", "OPP"}.issubset(schedule_df.columns):
        pairs = schedule_df.select(["TEAM", "OPP"]).rename({"TEAM": "team_a", "OPP": "team_b"})
    else:
        raise ValueError(
            f"Schedule dataset {schedule_path} must include columns "
            "home_team/away_team or team_a/team_b."
        )

    pairs = (
        pairs.drop_nulls()
        .with_columns(
            [
                pl.col("team_a").cast(pl.Utf8).str.to_uppercase().str.strip_chars(),
                pl.col("team_b").cast(pl.Utf8).str.to_uppercase().str.strip_chars(),
            ]
        )
        .filter(pl.col("team_a") != pl.col("team_b"))
        .unique()
    )
    if pairs.is_empty():
        raise ValueError(f"No matchup pairs remain for season {season} week {week}.")
    return pairs, schedule_path


def _frames_with_fallback(
    season: int,
    target_week: int,
    reference_week: Optional[int],
) -> tuple[dict[str, Optional[pl.DataFrame]], int]:
    """
    Try to load metrics for `target_week`; if empty, fall back to `reference_week`
    (or target_week-1 when not provided).
    """
    frames = reports._load_metric_frames(season, target_week)
    teams = reports.available_teams(season, target_week, frames=frames)
    if teams:
        return frames, target_week

    ref_week = reference_week if reference_week is not None else max(1, target_week - 1)
    if ref_week <= 0:
        return frames, target_week

    fallback_frames = reports._load_metric_frames(season, ref_week)
    fallback_teams = reports.available_teams(season, ref_week, frames=fallback_frames)
    if fallback_teams:
        logger.info(
            "Using metrics from week %s as fallback for previews targeting week %s.",
            ref_week,
            target_week,
        )
        return fallback_frames, ref_week

    return frames, target_week


def _ensure_team_available(
    teams: Iterable[str],
    team: str,
    *,
    require_complete_schedule: bool,
) -> bool:
    if team in teams:
        return True
    message = f"Metrics unavailable for team {team}; skipping preview."
    if require_complete_schedule:
        raise ValueError(message)
    logger.warning(message)
    return False


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv or sys.argv[1:])
    if args.season <= 0 or args.week <= 0:
        raise SystemExit("[error] season and week must be positive integers")

    settings = load_settings()
    data_root = Path(settings.data_root)

    try:
        pairs, schedule_path = _load_schedule_pairs(data_root, args.season, args.week)
    except Exception as exc:
        raise SystemExit(f"[error] {exc}") from exc

    frames, source_week = _frames_with_fallback(args.season, args.week, args.reference_week)
    available = set(reports.available_teams(args.season, source_week, frames=frames))
    if not available:
        raise SystemExit(
            f"[error] No metrics available for season {args.season} "
            f"through week {source_week}; cannot build previews."
        )

    logger.info(
        "Generating matchup previews for season=%s week=%s using metrics from week=%s (schedule=%s).",
        args.season,
        args.week,
        source_week,
        schedule_path,
    )

    generated_assets: list[Path] = []
    generated_markdown: list[Path] = []

    for row in pairs.to_dicts():
        team_a = row.get("team_a")
        team_b = row.get("team_b")
        if not team_a or not team_b:
            logger.warning("Skipping matchup with missing team codes: %s", row)
            continue

        if not (
            _ensure_team_available(available, team_a, require_complete_schedule=args.require_complete_schedule)
            and _ensure_team_available(available, team_b, require_complete_schedule=args.require_complete_schedule)
        ):
            continue

        try:
            outputs = reports.generate_comparison_report(
                season=args.season,
                week=args.week,
                team_a=team_a,
                team_b=team_b,
                frames=frames,
            )
        except Exception as exc:  # pragma: no cover - defensive CLI guard
            logger.warning("Failed to generate matchup %s vs %s: %s", team_a, team_b, exc)
            continue

        if outputs:
            generated_markdown.append(Path(outputs[0]))
            generated_assets.extend(Path(p) for p in outputs)

    if generated_markdown:
        logger.info(
            "Generated %s matchup reports for season=%s week=%s.",
            len(generated_markdown),
            args.season,
            args.week,
        )
    else:
        logger.warning(
            "No matchup reports produced for season=%s week=%s (after filtering unavailable teams).",
            args.season,
            args.week,
        )

    if args.summary:
        try:
            reports.generate_weekly_summary(args.season, args.week, comparison_reports=generated_markdown)
        except Exception as exc:  # pragma: no cover
            logger.warning("Weekly summary refresh failed: %s", exc)


if __name__ == "__main__":
    main()
