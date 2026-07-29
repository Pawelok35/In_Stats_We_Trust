"""Command-line entrypoints for orchestrating ETL and reporting flows."""

from __future__ import annotations

import subprocess
import sys
from importlib import import_module
from pathlib import Path
from typing import Callable, Optional

import polars as pl
import typer

import app.reports as reports
from app.manual_week_check import format_manual_week_check, run_manual_week_check
from app.nfl_data_sync import (
    export_week_lines_from_schedule,
    sync_results_from_nfl,
    sync_schedule_from_nfl,
)
from metrics.backtest import (
    backtest_picks,
    format_summary_table,
    load_picks,
    load_results,
    summarize,
)
from metrics.core12 import compute as compute_core12
from metrics.gom_calibration import write_gom_calibration_shadow_report
from metrics.power_score import compute as compute_power_score
from metrics.rolling import build_cumulative_core12
from metrics.strategy_search import (
    DEFAULT_VARIANT_DIRS,
    load_pick_rows,
    load_strategy_rule,
    search_strategies,
    write_fixed_strategy_report,
    write_strategy_search_outputs,
)
from utils.config import load_settings
from utils.logging import get_logger

app = typer.Typer(add_completion=False, invoke_without_command=False)
logger = get_logger(__name__)
DEFAULT_MANUAL_RESULTS_PATH = Path("data/results/manual_results.jsonl")
DEFAULT_PICKS_DIR = Path("data/picks")


def _run_python_command(args: list[str]) -> None:
    """Run a repository Python command and forward its exit code through Typer."""

    result = subprocess.run([sys.executable, *args], check=False)
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)


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
        logger.info(
            "Skipping L4 stages (Core12/PowerScore) for season %s week %s",
            resolved_season,
            resolved_week,
        )
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


@app.command("weekly-pipeline")
def weekly_pipeline(
    season: int = typer.Option(..., "--season", min=1, help="Season to process"),
    week: int = typer.Option(..., "--week", min=1, help="Target week to generate"),
    ingest_week: Optional[int] = typer.Option(
        None,
        "--ingest-week",
        min=1,
        help="Week to fully ingest/build. Defaults to week-1 in the underlying workflow.",
    ),
    reference_week: Optional[int] = typer.Option(
        None,
        "--reference-week",
        min=1,
        help="Week whose metrics power previews. Defaults to the workflow's reference logic.",
    ),
    picks_start_week: int = typer.Option(
        1,
        "--picks-start-week",
        min=1,
        help="Earliest week to regenerate pick variants.",
    ),
    manual_results: Path = typer.Option(  # noqa: B008
        DEFAULT_MANUAL_RESULTS_PATH,
        "--manual-results",
        help="Manual results JSONL used by pick evaluation/regeneration.",
    ),
    run_convergence: bool = typer.Option(
        False,
        "--run-convergence",
        help="Run convergence analyzer after generating picks.",
    ),
) -> None:
    """Run the canonical weekly workflow through the CLI."""

    args = [
        "-X",
        "utf8",
        "-m",
        "app.workflows.run_week_pipeline",
        "--season",
        str(season),
        "--week",
        str(week),
        "--picks-start-week",
        str(picks_start_week),
        "--manual-results",
        str(manual_results),
    ]
    if ingest_week is not None:
        args.extend(["--ingest-week", str(ingest_week)])
    if reference_week is not None:
        args.extend(["--reference-week", str(reference_week)])
    if run_convergence:
        args.append("--run-convergence")

    _run_python_command(args)


@app.command("manual-week-check")
def manual_week_check_cmd(
    season: int = typer.Option(..., "--season", min=1, help="Season to validate"),
    week: int = typer.Option(..., "--week", min=1, help="Target week to generate"),
    manual_results: Path = typer.Option(  # noqa: B008
        DEFAULT_MANUAL_RESULTS_PATH,
        "--manual-results",
        help="Manual results JSONL used to settle the previous week.",
    ),
    lines_path: Optional[Path] = typer.Option(  # noqa: B008
        None,
        "--lines-path",
        help="Override the target week lines YAML path.",
    ),
) -> None:
    """Validate manual schedule, lines and previous-week result inputs."""

    try:
        result = run_manual_week_check(
            season=season,
            week=week,
            manual_results_path=manual_results,
            lines_path=lines_path,
        )
    except Exception as exc:
        logger.error("manual-week-check failed: %s", exc)
        raise typer.Exit(code=1) from exc

    typer.echo(format_manual_week_check(result))
    if not result.ok:
        raise typer.Exit(code=1)


@app.command("sync-nfl-schedule")
def sync_nfl_schedule_cmd(
    season: int = typer.Option(..., "--season", min=1, help="Season to sync from nfl_data_py"),
) -> None:
    """Download and store the nfl_data_py season schedule locally."""

    try:
        result = sync_schedule_from_nfl(season)
    except Exception as exc:
        logger.error("sync-nfl-schedule failed: %s", exc)
        raise typer.Exit(code=1) from exc
    typer.echo(f"[OK] Saved schedule: {result.path} ({result.rows} rows)")


@app.command("export-lines-from-nfl")
def export_lines_from_nfl_cmd(
    season: int = typer.Option(..., "--season", min=1, help="Season to export"),
    week: int = typer.Option(..., "--week", min=1, help="Week to export"),
    no_overwrite: bool = typer.Option(
        False,
        "--no-overwrite",
        help="Fail if the target YAML already exists.",
    ),
) -> None:
    """Export spread/total lines from the synced nfl_data_py schedule into YAML."""

    try:
        result = export_week_lines_from_schedule(
            season,
            week,
            overwrite=not no_overwrite,
        )
    except Exception as exc:
        logger.error("export-lines-from-nfl failed: %s", exc)
        raise typer.Exit(code=1) from exc
    typer.echo(f"[OK] Saved lines: {result.path} ({result.games} games)")


@app.command("sync-nfl-results")
def sync_nfl_results_cmd(
    season: int = typer.Option(..., "--season", min=1, help="Season to refresh results for"),
) -> None:
    """Refresh local schedule results from nfl_data_py final scores."""

    try:
        result = sync_results_from_nfl(season)
    except Exception as exc:
        logger.error("sync-nfl-results failed: %s", exc)
        raise typer.Exit(code=1) from exc
    typer.echo(
        f"[OK] Refreshed results: {result.path} "
        f"({result.completed_games}/{result.rows} games completed)"
    )


@app.command("variant-b-daily-bot")
def variant_b_daily_bot_cmd(
    season: int = typer.Option(..., "--season", min=1, help="Season to process"),
    week: int = typer.Option(..., "--week", min=1, help="Target week"),
    day: Optional[str] = typer.Option(None, "--day", help="Override day key, e.g. tuesday"),
    run_date: Optional[str] = typer.Option(None, "--date", help="Override date YYYY-MM-DD"),
    execute: bool = typer.Option(False, "--execute", help="Run command tasks"),
) -> None:
    """Run the Variant B daily workflow bot."""

    args = [
        "scripts/variant_b_daily_bot.py",
        "--season",
        str(season),
        "--week",
        str(week),
    ]
    if day:
        args.extend(["--day", day])
    if run_date:
        args.extend(["--date", run_date])
    if execute:
        args.append("--execute")
    _run_python_command(args)


@app.command("generate-matchups")
def generate_matchups(
    season: int = typer.Option(..., "--season", min=1, help="Season to process"),
    week: int = typer.Option(..., "--week", min=1, help="Target week to generate"),
    reference_week: Optional[int] = typer.Option(
        None,
        "--reference-week",
        min=1,
        help="Week whose metrics power previews. Defaults to week-1.",
    ),
    require_complete_schedule: bool = typer.Option(
        False,
        "--require-complete-schedule",
        help="Fail if scheduled teams are missing metrics.",
    ),
    summary: bool = typer.Option(
        True,
        "--summary/--no-summary",
        help="Refresh weekly summary after generating matchup previews.",
    ),
) -> None:
    """Generate matchup preview reports for the requested week."""

    args = [
        "-X",
        "utf8",
        "-m",
        "app.workflows.generate_matchup_previews",
        "--season",
        str(season),
        "--week",
        str(week),
    ]
    if reference_week is not None:
        args.extend(["--reference-week", str(reference_week)])
    if require_complete_schedule:
        args.append("--require-complete-schedule")
    if summary:
        args.append("--summary")

    _run_python_command(args)


@app.command("evaluate-picks")
def evaluate_picks_cmd(
    season: int = typer.Option(..., "--season", min=1, help="Season to evaluate"),
    from_week: Optional[int] = typer.Option(
        None, "--from-week", min=1, help="First week to include"
    ),
    to_week: Optional[int] = typer.Option(None, "--to-week", min=1, help="Last week to include"),
    tag: Optional[list[str]] = typer.Option(  # noqa: B008
        None,
        "--tag",
        help="Filter by tag. Can be provided multiple times.",
    ),
    picks_dir: Path = typer.Option(  # noqa: B008
        DEFAULT_PICKS_DIR,
        "--picks-dir",
        help="Directory containing pick JSONL files.",
    ),
    manual_results: Optional[Path] = typer.Option(  # noqa: B008
        None,
        "--manual-results",
        help="Optional manual results JSONL.",
    ),
) -> None:
    """Evaluate pick results through the canonical CLI."""

    settings = load_settings()
    tags = {item.upper() for item in tag} if tag else None

    try:
        picks = load_picks(picks_dir, season, from_week=from_week, to_week=to_week)
        results = load_results(Path(settings.data_root), season, manual_results=manual_results)
        rows = backtest_picks(picks, results, tags=tags)
    except Exception as exc:
        logger.error("evaluate-picks failed: %s", exc)
        raise typer.Exit(code=1) from exc

    if not rows:
        typer.echo("No picks found for the requested filters.")
        return

    typer.echo("Backtest by tag")
    typer.echo(format_summary_table(summarize(rows, group_by="tag"), label="tag"))
    typer.echo("")
    typer.echo("Backtest by confidence bucket")
    typer.echo(
        format_summary_table(
            summarize(rows, group_by="confidence_bucket"),
            label="confidence_bucket",
        )
    )


@app.command("evaluate-variants")
def evaluate_variants_cmd(
    season: int = typer.Option(..., "--season", min=1, help="Season to evaluate"),
    start_week: int = typer.Option(..., "--start-week", min=1, help="First week to include"),
    end_week: int = typer.Option(..., "--end-week", min=1, help="Last week to include"),
    manual_results: Path = typer.Option(  # noqa: B008
        DEFAULT_MANUAL_RESULTS_PATH,
        "--manual-results",
        help="Manual results JSONL used for evaluation.",
    ),
    regenerate: bool = typer.Option(
        False,
        "--regenerate",
        help="Regenerate variant picks before evaluating.",
    ),
    status: Optional[list[str]] = typer.Option(  # noqa: B008
        None,
        "--status",
        help="Variant lifecycle status to include. Can be provided multiple times.",
    ),
    variant: Optional[list[str]] = typer.Option(  # noqa: B008
        None,
        "--variant",
        help="Specific variant name to include. Can be provided multiple times.",
    ),
) -> None:
    """Evaluate champion/challenger variant performance."""

    args = [
        "-X",
        "utf8",
        "-m",
        "app.workflows.tag_variant_runner",
        "--season",
        str(season),
        "--start-week",
        str(start_week),
        "--end-week",
        str(end_week),
        "--manual-results",
        str(manual_results),
    ]
    if regenerate:
        args.append("--regenerate")
    for item in status or []:
        args.extend(["--status", item])
    for item in variant or []:
        args.extend(["--variant", item])

    _run_python_command(args)


@app.command("search-strategies")
def search_strategies_cmd(
    train_start: int = typer.Option(..., "--train-start", min=1, help="First train season"),
    train_end: int = typer.Option(..., "--train-end", min=1, help="Last train season"),
    holdout_start: int = typer.Option(..., "--holdout-start", min=1, help="First holdout season"),
    holdout_end: int = typer.Option(..., "--holdout-end", min=1, help="Last holdout season"),
    output_dir: Path = typer.Option(  # noqa: B008
        Path("data/results/strategy_search"),
        "--output-dir",
        help="Directory for CSV and Markdown search outputs.",
    ),
    top_n: int = typer.Option(50, "--top-n", min=1, help="Number of candidates to save."),
) -> None:
    """Search simple historical strategy filters with a train/holdout split."""

    if train_end < train_start:
        raise typer.BadParameter("--train-end must be >= --train-start")
    if holdout_end < holdout_start:
        raise typer.BadParameter("--holdout-end must be >= --holdout-start")

    settings = load_settings()
    train_seasons = list(range(train_start, train_end + 1))
    holdout_seasons = list(range(holdout_start, holdout_end + 1))
    try:
        candidates = search_strategies(
            data_root=Path(settings.data_root),
            train_seasons=train_seasons,
            holdout_seasons=holdout_seasons,
            top_n=top_n,
        )
        csv_path, md_path = write_strategy_search_outputs(
            candidates,
            output_dir=output_dir,
            train_seasons=train_seasons,
            holdout_seasons=holdout_seasons,
        )
    except Exception as exc:
        logger.error("search-strategies failed: %s", exc)
        raise typer.Exit(code=1) from exc

    typer.echo(f"[OK] Found {len(candidates)} candidate strategies")
    typer.echo(f"CSV: {csv_path}")
    typer.echo(f"Markdown: {md_path}")
    if candidates:
        best = candidates[0]
        typer.echo(
            "Best: {rule} | train={train:+.1f}u | holdout={holdout:+.1f}u".format(
                rule=best["description"],
                train=best["train"]["units"],
                holdout=best["holdout"]["units"],
            )
        )


@app.command("strategy-report")
def strategy_report_cmd(
    strategy_path: Path = typer.Option(  # noqa: B008
        Path("config/strategy_rules/gom_stable.yaml"),
        "--strategy",
        help="YAML file with a fixed strategy rule.",
    ),
    start_season: int = typer.Option(..., "--start-season", min=1, help="First season"),
    end_season: int = typer.Option(..., "--end-season", min=1, help="Last season"),
    output_path: Path = typer.Option(  # noqa: B008
        Path("data/results/strategy_search/gom_stable_report.md"),
        "--output",
        help="Markdown report output path.",
    ),
) -> None:
    """Generate a fixed strategy season and walk-forward report."""

    if end_season < start_season:
        raise typer.BadParameter("--end-season must be >= --start-season")

    settings = load_settings()
    seasons = list(range(start_season, end_season + 1))
    try:
        rule = load_strategy_rule(strategy_path)
        rows = load_pick_rows(
            data_root=Path(settings.data_root),
            seasons=seasons,
            variant_dirs=DEFAULT_VARIANT_DIRS,
        )
        report_path = write_fixed_strategy_report(
            rows=rows,
            rule=rule,
            output_path=output_path,
            start_season=start_season,
            end_season=end_season,
            title=f"{strategy_path.stem} Strategy Report",
        )
    except Exception as exc:
        logger.error("strategy-report failed: %s", exc)
        raise typer.Exit(code=1) from exc

    typer.echo(f"[OK] Strategy report saved: {report_path}")


@app.command("gom-calibration-shadow")
def gom_calibration_shadow_cmd(
    output_path: Path = typer.Option(  # noqa: B008
        Path("data/results/strategy_search/gom_calibration_shadow_report.md"),
        "--output",
        help="Markdown report output path.",
    ),
) -> None:
    """Generate the GOM near-miss shadow calibration report."""

    try:
        report_path = write_gom_calibration_shadow_report(output_path)
    except Exception as exc:
        logger.error("gom-calibration-shadow failed: %s", exc)
        raise typer.Exit(code=1) from exc

    typer.echo(f"[OK] GOM calibration shadow report saved: {report_path}")


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
            team_a_code,
            team_b_code,
            resolved_season,
            resolved_week,
            exc,
        )
        raise typer.Exit(code=1) from exc

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
    through_week: int = typer.Option(
        ..., "--through-week", help="Include data up to and including this week"
    ),
) -> None:
    """Build rolling Core12 through the selected week."""
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
    log.info(
        "Teams: %s", df.select("TEAM").to_series().to_list() if "TEAM" in df.columns else "N/A"
    )


if __name__ == "__main__":
    main()
