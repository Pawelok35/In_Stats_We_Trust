"""Command-line entrypoints for orchestrating ETL and reporting flows."""

from __future__ import annotations

from importlib import import_module
from typing import Callable, Optional

import polars as pl
import typer
from metrics.rolling import build_cumulative_core12

import app.reports as reports
from metrics.core12 import compute as compute_core12
from metrics.power_score import compute as compute_power_score
from utils.config import load_settings
from utils.logging import get_logger
from utils.paths import path_for

app = typer.Typer(add_completion=False, invoke_without_command=False)
logger = get_logger(__name__)







def _resolve_season_week(season: Optional[int], week: Optional[int]) -> tuple[int, int]:
    settings = load_settings()
    resolved_season = season or settings.default_season
    resolved_week = week or settings.default_week
    if resolved_season <= 0 or resolved_week <= 0:
        raise typer.BadParameter("season and week must be positive integers")
    return resolved_season, resolved_week


def _invoke(module_path: str, func_name: str, *args, **kwargs):
    module = import_module(module_path)
    func: Callable = getattr(module, func_name)
    return func(*args, **kwargs)


@app.command("build-week")
def build_week(
    season: Optional[int] = typer.Option(None, min=1, help="Season to process"),
    week: Optional[int] = typer.Option(None, min=1, help="Week to process"),
    require_complete_schedule: bool = typer.Option(
        True,
        help="Fail if the matchup schedule is missing or incomplete for the requested week.",
        show_default=True,
    ),
    skip_l4: bool = typer.Option(
        False,
        "--skip-l4",
        help="Skip L4 metric computation (Core12/PowerScore) after L3 aggregation.",
        show_default=True,
    ),
) -> None:
    """Run the week build pipeline from ingestion through report generation."""

    resolved_season, resolved_week = _resolve_season_week(season, week)
    logger.info("Starting build-week for season %s, week %s", resolved_season, resolved_week)

    logger.info("Running L1 ingestion stage")
    l1_result = _invoke("etl.l1_ingest", "run", resolved_season, resolved_week)

    logger.info("Running L2 clean stage")
    l2_result = _invoke("etl.l2_clean", "run", resolved_season, resolved_week, l1_result=l1_result)

    logger.info("Running L3 aggregate stage")
    l3_result = _invoke(
        "etl.l3_aggregate",
        "run",
        resolved_season,
        resolved_week,
        l2_result=l2_result,
    )

    if skip_l4:
        logger.info("Skipping L4 stages (Core12/PowerScore) for season %s week %s", resolved_season, resolved_week)
    else:
        logger.info("Computing L4 Core12 metrics")
        try:
            l3_df = pl.read_parquet(l3_result)
        except Exception as exc:
            logger.error("Failed to read L3 artifact from %s: %s", l3_result, exc)
            raise typer.Exit(code=1) from exc

        try:
            core12_df = compute_core12(l3_df, resolved_season, resolved_week)
            logger.info(
                "Core12 metrics computed for season %s week %s (rows=%s cols=%s)",
                resolved_season,
                resolved_week,
                core12_df.height,
                core12_df.width,
            )
            compute_power_score(core12_df, resolved_season, resolved_week)
            logger.info(
                "PowerScore metrics computed for season %s week %s",
                resolved_season,
                resolved_week,
            )
        except Exception as exc:
            logger.error("Failed to compute L4 metrics: %s", exc)
            raise typer.Exit(code=1) from exc

    try:
        reports.validate_schedule_for_week(
            resolved_season,
            resolved_week,
            require_complete_schedule=require_complete_schedule,
        )
    except Exception as exc:
        logger.error("Schedule validation failed: %s", exc)
        raise typer.Exit(code=1) from exc

    logger.info("Generating report snapshot")
    _invoke("app.reports", "generate_report", resolved_season, resolved_week, l3_result=l3_result)

    logger.info("Completed build-week for season %s, week %s", resolved_season, resolved_week)


@app.command("team-report")
def team_report(
    season: Optional[int] = typer.Option(None, min=1, help="Season to process"),
    week: Optional[int] = typer.Option(None, min=1, help="Week to process"),
    team: str = typer.Option(..., "--team", "-t", help="Team code to generate a report for"),
) -> None:
    # Ustal sezon/tydzień
    resolved_season, resolved_week = _resolve_season_week(season, week)

    # 1) Wygeneruj raport drużyny (zakładam, że ta funkcja istnieje w app.reports)
    reports.generate_team_report(resolved_season, resolved_week, team)

    # 2) Zbuduj/uzupełnij manifest dla team reports
    from utils.manifest import write_manifest
    from utils.paths import (
        team_report_assets_dir,
        team_report_path,
        team_reports_manifest_path,
    )

    report_file = team_report_path(resolved_season, resolved_week, team)
    assets_dir = team_report_assets_dir(resolved_season, resolved_week, team)
    asset_files = list(assets_dir.glob("*.png")) if assets_dir.exists() else []

    manifest_out = team_reports_manifest_path(resolved_season, resolved_week)

    write_manifest(
        path=report_file,  # plik do zhashowania
        manifest_path=manifest_out,  # gdzie zapisać manifest
        layer="team_reports",
        season=resolved_season,
        week=resolved_week,
        rows=None,
        cols=None,
        files=[report_file, *asset_files],  # raport + wygenerowane PNG
    )

    typer.echo(
        f"Generated team report for {team} at season {resolved_season}, week {resolved_week}"
    )

    """Generate an individual team report for the specified week."""

    resolved_season, resolved_week = _resolve_season_week(season, week)
    team_input = (team or "").strip()
    if not team_input:
        raise typer.BadParameter("team must be provided")

    try:
        teams = reports.available_teams(resolved_season, resolved_week)
    except FileNotFoundError as exc:
        typer.echo(f"Required data missing: {exc}")
        raise typer.Exit(code=1) from exc

    if not teams:
        typer.echo("No teams available for the requested season/week.")
        raise typer.Exit(code=1)

    team_code = team_input.upper()
    if team_code not in teams:
        typer.echo(f"Unknown team '{team_input}'. Available teams: {', '.join(teams)}")
        raise typer.Exit(code=1)

    path = reports.generate_team_report(resolved_season, resolved_week, team_code)
    logger.info("Team report written to %s", path)


@app.command("compare-report")
def compare_report(
    season: Optional[int] = typer.Option(None, min=1, help="Season to process"),
    week: Optional[int] = typer.Option(None, min=1, help="Week to process"),
    team_a: str = typer.Option(..., "--team-a", help="First team code"),
    team_b: str = typer.Option(..., "--team-b", help="Second team code"),
) -> None:
    """
    Generate a comparison report between two teams.
    Uses live Core12/PowerScore data from the given week.
    """

    resolved_season, resolved_week = _resolve_season_week(season, week)
    team_a_code = (team_a or "").strip().upper()
    team_b_code = (team_b or "").strip().upper()

    if not team_a_code or not team_b_code:
        raise typer.BadParameter("Both --team-a and --team-b must be provided")
    if team_a_code == team_b_code:
        raise typer.BadParameter("--team-a and --team-b must be different")

    import logging
    logging.basicConfig(level=logging.INFO)

    try:
        paths = reports.generate_comparison_report(
            season=resolved_season,
            week=resolved_week,
            team_a=team_a_code,
            team_b=team_b_code,
        )
    except Exception as exc:
        logger.error(
            "compare-report failed for %s vs %s (season=%s week=%s): %s",
            team_a_code, team_b_code, resolved_season, resolved_week, exc,
        )
        raise typer.Exit(code=1)

    if paths:
        typer.echo(f"[OK] Comparison report generated: {paths[0]}")
    else:
        typer.echo("[WARN] No report generated (empty paths)")


@app.command("build-weekly-reports")
def build_weekly_reports(
    season: Optional[int] = typer.Option(None, min=1, help="Season to process"),
    week: Optional[int] = typer.Option(None, min=1, help="Week to process"),
    pairs_only: bool = typer.Option(
        False,
        "--pairs-only",
        help="Generate only matchup comparison reports using schedule data when available.",
    ),
    require_complete_schedule: bool = typer.Option(
        True,
        help="Fail if the matchup schedule is missing or incomplete for the requested week.",
        show_default=True,
    ),
) -> None:
    """Batch-generate team or comparison reports for the requested week."""

    resolved_season, resolved_week = _resolve_season_week(season, week)

    try:
        reports.validate_schedule_for_week(
            resolved_season,
            resolved_week,
            require_complete_schedule=require_complete_schedule,
        )
    except Exception as exc:
        if pairs_only or require_complete_schedule:
            logger.error("Schedule validation failed: %s", exc)
            raise typer.Exit(code=1) from exc
        logger.warning("Schedule validation warning: %s", exc)

    if pairs_only:
        try:
            generated = reports.generate_comparison_reports_from_schedule(
                resolved_season,
                resolved_week,
                require_complete_schedule=require_complete_schedule,
            )
        except Exception as exc:
            logger.error("Failed to generate comparison reports: %s", exc)
            raise typer.Exit(code=1) from exc
        if generated:
            logger.info(
                "Generated %s comparison reports for season=%s week=%s",
                len(generated),
                resolved_season,
                resolved_week,
            )
        else:
            logger.info(
                "No comparison reports generated; schedule data unavailable or empty for "
                "season=%s week=%s",
                resolved_season,
                resolved_week,
            )
        reports.generate_weekly_summary(resolved_season, resolved_week)
        return

    generated = reports.build_weekly_team_reports(resolved_season, resolved_week)
    if generated:
        logger.info(
            "Generated %s team reports for season=%s week=%s",
            len(generated),
            resolved_season,
            resolved_week,
        )
    else:
        logger.info(
            "No team reports generated for season=%s week=%s",
            resolved_season,
            resolved_week,
        )

    reports.generate_weekly_summary(resolved_season, resolved_week)


def main(argv: Optional[list[str]] = None) -> None:
    """Entry-point for `python -m app.cli`."""
    import sys

    args = list(argv if argv is not None else sys.argv[1:])
    app(args=args)


@app.command("build-cumulative")
def build_cumulative_cmd(
    season: int = typer.Option(..., "--season", help="Season to process"),
    through_week: int = typer.Option(..., "--through-week", help="Include data up to and including this week"),
) -> None:
    """
    Build rolling snapshot(s) for Core12 up to through_week, and write parquet to data/rolling_core12/.
    """
    df = build_cumulative_core12(season, through_week)

    # proste info w konsoli żebyś wiedział co powstało
    import logging
    log = logging.getLogger(__name__)
    log.setLevel(logging.INFO)
    if not log.handlers:
        h = logging.StreamHandler()
        h.setLevel(logging.INFO)
        log.addHandler(h)

    log.info("Rolling Core12 built for season=%s through_week=%s", season, through_week)
    log.info("Rows: %s | Cols: %s", len(df), len(df.columns))
    log.info("Teams: %s", df.select("TEAM").to_series().to_list() if "TEAM" in df.columns else "N/A")




if __name__ == "__main__":
    main()
