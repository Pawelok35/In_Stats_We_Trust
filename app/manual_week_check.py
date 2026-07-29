"""Validation helpers for the manual weekly data workflow."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import polars as pl
import yaml

from utils.config import load_settings
from utils.paths import week_lines_path


@dataclass(frozen=True)
class CheckIssue:
    level: str
    message: str


@dataclass(frozen=True)
class ManualWeekCheckResult:
    season: int
    week: int
    schedule_path: Path
    lines_path: Path
    manual_results_path: Path
    schedule_games: int
    lines_games: int
    previous_results: int
    issues: tuple[CheckIssue, ...]

    @property
    def errors(self) -> tuple[CheckIssue, ...]:
        return tuple(issue for issue in self.issues if issue.level == "ERROR")

    @property
    def warnings(self) -> tuple[CheckIssue, ...]:
        return tuple(issue for issue in self.issues if issue.level == "WARN")

    @property
    def ok(self) -> bool:
        return not self.errors


def _team(value: Any) -> str:
    return str(value or "").strip().upper()


def _matchup_key(home: Any, away: Any) -> tuple[str, str]:
    return (_team(home), _team(away))


def _load_schedule(data_root: Path, season: int, week: int) -> tuple[pl.DataFrame, Path]:
    candidates = [
        data_root / "schedules" / f"{season}.parquet",
        data_root / "schedule" / f"{season}.parquet",
    ]
    schedule_path = next((path for path in candidates if path.exists()), candidates[0])
    if not schedule_path.exists():
        return pl.DataFrame(), schedule_path

    df = pl.read_parquet(schedule_path)
    if "week" in df.columns:
        df = df.filter(pl.col("week") == week)
    return df, schedule_path


def _schedule_keys(df: pl.DataFrame) -> list[tuple[str, str]]:
    if df.is_empty():
        return []
    if {"home_team", "away_team"}.issubset(df.columns):
        rows = df.select(["home_team", "away_team"]).iter_rows()
    elif {"team_a", "team_b"}.issubset(df.columns):
        rows = df.select(["team_a", "team_b"]).iter_rows()
    elif {"TEAM", "OPP"}.issubset(df.columns):
        rows = df.select(["TEAM", "OPP"]).iter_rows()
    else:
        return []
    return [_matchup_key(home, away) for home, away in rows]


def _load_lines(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    matchups = raw.get("matchups", [])
    if not isinstance(matchups, list):
        raise ValueError(f"Invalid lines file {path}: 'matchups' must be a list.")
    return [item for item in matchups if isinstance(item, dict)]


def _line_keys(lines: Iterable[dict[str, Any]]) -> list[tuple[str, str]]:
    return [_matchup_key(item.get("home"), item.get("away")) for item in lines]


def _is_number(value: Any) -> bool:
    if value in (None, ""):
        return False
    try:
        float(value)
    except (TypeError, ValueError):
        return False
    return True


def _load_manual_results(path: Path, season: int) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            records.append({"_line_error": f"line {line_no}: {exc}"})
            continue
        try:
            if int(record.get("season")) == season:
                records.append(record)
        except (TypeError, ValueError):
            records.append({"_line_error": f"line {line_no}: missing/invalid season"})
    return records


def _duplicate_keys(keys: Iterable[tuple[str, str]]) -> set[tuple[str, str]]:
    seen: set[tuple[str, str]] = set()
    duplicates: set[tuple[str, str]] = set()
    for key in keys:
        if key in seen:
            duplicates.add(key)
        seen.add(key)
    return duplicates


def _unordered_key(key: tuple[str, str]) -> frozenset[str]:
    return frozenset(key)


def _fmt_key(key: tuple[str, str]) -> str:
    return f"{key[1]} @ {key[0]}"


def run_manual_week_check(
    *,
    season: int,
    week: int,
    manual_results_path: Path = Path("data/results/manual_results.jsonl"),
    data_root: Path | None = None,
    lines_path: Path | None = None,
) -> ManualWeekCheckResult:
    """Validate the hand-maintained inputs needed before generating a target week."""

    if season <= 0 or week <= 0:
        raise ValueError("season and week must be positive integers.")

    settings = load_settings()
    resolved_data_root = data_root or Path(settings.data_root)
    resolved_lines_path = lines_path or week_lines_path(season, week)
    issues: list[CheckIssue] = []

    schedule_df, schedule_path = _load_schedule(resolved_data_root, season, week)
    schedule_keys = _schedule_keys(schedule_df)
    if not schedule_path.exists():
        issues.append(CheckIssue("ERROR", f"Missing schedule file: {schedule_path}"))
    elif not schedule_keys:
        issues.append(
            CheckIssue(
                "ERROR",
                f"No readable schedule matchups for season={season} week={week} in {schedule_path}",
            )
        )

    for key in sorted(_duplicate_keys(schedule_keys)):
        issues.append(CheckIssue("ERROR", f"Duplicate schedule matchup: {_fmt_key(key)}"))

    try:
        lines = _load_lines(resolved_lines_path)
    except Exception as exc:
        lines = []
        issues.append(CheckIssue("ERROR", str(exc)))

    line_keys = _line_keys(lines)
    if not resolved_lines_path.exists():
        issues.append(CheckIssue("ERROR", f"Missing lines file: {resolved_lines_path}"))
    elif not lines:
        issues.append(
            CheckIssue("ERROR", f"No matchups found in lines file: {resolved_lines_path}")
        )

    for key in sorted(_duplicate_keys(line_keys)):
        issues.append(CheckIssue("ERROR", f"Duplicate lines matchup: {_fmt_key(key)}"))

    for index, item in enumerate(lines, start=1):
        key = _matchup_key(item.get("home"), item.get("away"))
        if not key[0] or not key[1]:
            issues.append(CheckIssue("ERROR", f"Lines row {index} has missing home/away team."))
        if not _is_number(item.get("spread")):
            issues.append(CheckIssue("ERROR", f"Lines row {index} has missing/invalid spread."))
        if not _is_number(item.get("total")):
            issues.append(CheckIssue("ERROR", f"Lines row {index} has missing/invalid total."))

    schedule_set = set(schedule_keys)
    line_set = set(line_keys)
    for key in sorted(schedule_set - line_set):
        issues.append(CheckIssue("ERROR", f"Missing line for scheduled game: {_fmt_key(key)}"))
    for key in sorted(line_set - schedule_set):
        issues.append(CheckIssue("ERROR", f"Line has no scheduled game: {_fmt_key(key)}"))

    manual_records = _load_manual_results(manual_results_path, season)
    for record in manual_records:
        if "_line_error" in record:
            issues.append(
                CheckIssue("ERROR", f"Invalid manual results JSONL: {record['_line_error']}")
            )

    previous_week = week - 1
    previous_results = 0
    if previous_week >= 1:
        previous_schedule_df, _ = _load_schedule(resolved_data_root, season, previous_week)
        previous_schedule_keys = set(_schedule_keys(previous_schedule_df))
        previous_schedule_by_pair = {
            _unordered_key(key): key for key in previous_schedule_keys if key[0] and key[1]
        }
        previous_result_keys: set[tuple[str, str]] = set()
        future_result_weeks: set[int] = set()
        reversed_result_keys: set[tuple[str, str]] = set()
        for record in manual_records:
            try:
                record_week = int(record.get("week"))
            except (TypeError, ValueError):
                continue
            if record_week > previous_week:
                future_result_weeks.add(record_week)
            if record_week != previous_week:
                continue
            key = _matchup_key(record.get("home_team"), record.get("away_team"))
            previous_result_keys.add(key)
            if key not in previous_schedule_keys:
                scheduled_key = previous_schedule_by_pair.get(_unordered_key(key))
                if scheduled_key:
                    reversed_result_keys.add(key)
                    issues.append(
                        CheckIssue(
                            "ERROR",
                            "Previous-week result home/away does not match schedule: "
                            f"result={_fmt_key(key)}, schedule={_fmt_key(scheduled_key)}",
                        )
                    )
                else:
                    issues.append(
                        CheckIssue(
                            "ERROR",
                            f"Previous-week result has no scheduled game: {_fmt_key(key)}",
                        )
                    )
            if not _is_number(record.get("home_score")) or not _is_number(record.get("away_score")):
                issues.append(
                    CheckIssue("ERROR", f"Previous-week result has invalid score: {_fmt_key(key)}")
                )

        if future_result_weeks:
            formatted_weeks = ", ".join(str(item) for item in sorted(future_result_weeks))
            issues.append(
                CheckIssue(
                    "WARN",
                    "Manual results contain entries after the previous completed week: "
                    f"weeks {formatted_weeks}.",
                )
            )

        previous_results = len(previous_result_keys)
        result_pairs = {_unordered_key(key) for key in previous_result_keys}
        missing_results = [
            key for key in previous_schedule_keys if _unordered_key(key) not in result_pairs
        ]
        for key in sorted(missing_results):
            issues.append(CheckIssue("ERROR", f"Missing previous-week result: {_fmt_key(key)}"))
    else:
        issues.append(CheckIssue("WARN", "Week 1 has no previous week to settle."))

    return ManualWeekCheckResult(
        season=season,
        week=week,
        schedule_path=schedule_path,
        lines_path=resolved_lines_path,
        manual_results_path=manual_results_path,
        schedule_games=len(schedule_keys),
        lines_games=len(line_keys),
        previous_results=previous_results,
        issues=tuple(issues),
    )


def format_manual_week_check(result: ManualWeekCheckResult) -> str:
    """Render a concise human-readable check report."""

    status = "OK" if result.ok else "FAILED"
    lines = [
        f"Manual week check: {status}",
        f"Season/week: {result.season} / W{result.week}",
        f"Schedule: {result.schedule_path} ({result.schedule_games} games)",
        f"Lines: {result.lines_path} ({result.lines_games} games)",
        "Manual results: "
        f"{result.manual_results_path} ({result.previous_results} previous-week results)",
    ]
    if result.issues:
        lines.append("")
        for issue in result.issues:
            lines.append(f"[{issue.level}] {issue.message}")
    return "\n".join(lines)
