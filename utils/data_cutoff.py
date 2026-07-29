"""Shared pre-game data cutoff and safe snapshot helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import polars as pl

SAFE = "SAFE"
AVAILABLE = "AVAILABLE"
PARTIAL_WINDOW = "PARTIAL_WINDOW"
INSUFFICIENT_CURRENT_SEASON_DATA = "INSUFFICIENT_CURRENT_SEASON_DATA"
MISSING_SOURCE_DATA = "MISSING_SOURCE_DATA"
CUTOFF_VIOLATION = "CUTOFF_VIOLATION"
MISSING_SAFE_SNAPSHOT = "MISSING_SAFE_SNAPSHOT"


@dataclass(frozen=True)
class DataCutoff:
    season: int
    analysis_week: int
    game_id: str | None = None
    game_start_utc: datetime | None = None
    strict_mode: bool = True

    @property
    def max_allowed_week(self) -> int:
        return self.analysis_week - 1


@dataclass(frozen=True)
class SafeSnapshotResolution:
    requested_through_week: int
    resolved_through_week: int | None
    path: Path | None
    fallback_used: bool
    fallback_reason: str | None
    cutoff_safe: bool
    status: str


@dataclass
class PreflightValidationResult:
    status: str
    season: int
    analysis_week: int
    maximum_feature_week: int | None = None
    cutoff_status: str = "PASS"
    data_quality_status: str = "PASS"
    missing_required_metrics: list[str] = field(default_factory=list)
    missing_optional_metrics: list[str] = field(default_factory=list)
    leakage_detected: bool = False
    duplicate_games: int = 0
    unsafe_fallbacks: int = 0
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "season": self.season,
            "analysis_week": self.analysis_week,
            "maximum_feature_week": self.maximum_feature_week,
            "cutoff_status": self.cutoff_status,
            "data_quality_status": self.data_quality_status,
            "missing_required_metrics": self.missing_required_metrics,
            "missing_optional_metrics": self.missing_optional_metrics,
            "leakage_detected": self.leakage_detected,
            "duplicate_games": self.duplicate_games,
            "unsafe_fallbacks": self.unsafe_fallbacks,
            "warnings": self.warnings,
            "errors": self.errors,
        }


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def resolve_allowed_weeks(season: int, analysis_week: int) -> list[int]:
    if season <= 0 or analysis_week <= 0:
        raise ValueError("season and analysis_week must be positive integers")
    return list(range(1, analysis_week))


def validate_pre_game_cutoff(
    df: pl.DataFrame,
    cutoff: DataCutoff,
    *,
    week_col: str = "week",
    season_col: str = "season",
    timestamp_col: str | None = None,
) -> dict[str, Any]:
    if week_col not in df.columns:
        return {
            "status": MISSING_SOURCE_DATA,
            "max_source_week": None,
            "violating_rows": 0,
            "reason": f"missing {week_col} column",
        }
    if season_col not in df.columns:
        return {
            "status": MISSING_SOURCE_DATA,
            "max_source_week": None,
            "violating_rows": 0,
            "reason": f"missing {season_col} column",
        }

    season_df = df.filter(pl.col(season_col) == cutoff.season)
    if season_df.is_empty():
        return {
            "status": MISSING_SOURCE_DATA,
            "max_source_week": None,
            "violating_rows": 0,
            "reason": f"no rows for season={cutoff.season}",
        }

    max_week = season_df.select(pl.col(week_col).max()).item()
    violations = season_df.filter(pl.col(week_col) >= cutoff.analysis_week)
    violating_rows = violations.height
    status = CUTOFF_VIOLATION if violating_rows else SAFE

    timestamp_violations = 0
    if timestamp_col and cutoff.game_start_utc and timestamp_col in season_df.columns:
        timestamp_violations = season_df.filter(
            pl.col(timestamp_col).is_not_null()
            & (pl.col(timestamp_col) >= cutoff.game_start_utc)
        ).height
        if timestamp_violations:
            status = CUTOFF_VIOLATION

    return {
        "status": status,
        "max_source_week": int(max_week) if max_week is not None else None,
        "violating_rows": violating_rows,
        "timestamp_violating_rows": timestamp_violations,
        "reason": None if status == SAFE else "source data includes analysis/future rows",
    }


def resolve_safe_snapshot(
    *,
    season: int,
    analysis_week: int,
    requested_through_week: int,
    path_factory,
    min_week: int = 1,
) -> SafeSnapshotResolution:
    max_allowed = analysis_week - 1
    if requested_through_week > max_allowed:
        return SafeSnapshotResolution(
            requested_through_week=requested_through_week,
            resolved_through_week=None,
            path=None,
            fallback_used=False,
            fallback_reason="requested snapshot is not before analysis week",
            cutoff_safe=False,
            status=CUTOFF_VIOLATION,
        )

    for candidate_week in range(requested_through_week, min_week - 1, -1):
        path = Path(path_factory(season, candidate_week))
        if path.exists():
            return SafeSnapshotResolution(
                requested_through_week=requested_through_week,
                resolved_through_week=candidate_week,
                path=path,
                fallback_used=candidate_week != requested_through_week,
                fallback_reason=(
                    None
                    if candidate_week == requested_through_week
                    else (
                        f"requested through_{requested_through_week} missing; "
                        f"using through_{candidate_week}"
                    )
                ),
                cutoff_safe=candidate_week < analysis_week,
                status=AVAILABLE,
            )

    return SafeSnapshotResolution(
        requested_through_week=requested_through_week,
        resolved_through_week=None,
        path=None,
        fallback_used=False,
        fallback_reason="no earlier safe snapshot exists",
        cutoff_safe=False,
        status=MISSING_SAFE_SNAPSHOT,
    )


def duplicate_count(df: pl.DataFrame, columns: Iterable[str]) -> int:
    cols = [col for col in columns if col in df.columns]
    if not cols or df.is_empty():
        return 0
    return df.height - df.unique(subset=cols, keep="first").height
