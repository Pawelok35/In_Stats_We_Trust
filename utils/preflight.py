"""Pre-model validation for feature cutoff and source safety."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import polars as pl

from utils.data_cutoff import (
    CUTOFF_VIOLATION,
    DataCutoff,
    PreflightValidationResult,
    duplicate_count,
    validate_pre_game_cutoff,
)
from utils.model_metrics import (
    OPTIONAL_CORE12_MODEL_METRICS,
    OPTIONAL_L3_MODEL_METRICS,
    REQUIRED_CORE12_MODEL_METRICS,
    REQUIRED_L3_MODEL_METRICS,
    missing_metrics_for_df,
)


def _read_parquet_if_exists(path: Path) -> pl.DataFrame | None:
    if not path.exists():
        return None
    return pl.read_parquet(path)


def validate_model_preflight(
    *,
    season: int,
    analysis_week: int,
    data_root: Path = Path("data"),
    lines_path: Path | None = None,
    strict_mode: bool = True,
) -> PreflightValidationResult:
    cutoff = DataCutoff(season=season, analysis_week=analysis_week, strict_mode=strict_mode)
    errors: list[str] = []
    warnings: list[str] = []
    missing_required_metrics: set[str] = set()
    missing_optional_metrics: set[str] = set()
    max_feature_week: int | None = None
    duplicate_games = 0

    l3_root = data_root / "l3_team_week" / str(season)
    if l3_root.exists():
        source_paths = [l3_root / f"{week}.parquet" for week in range(1, analysis_week)]
        for path in source_paths:
            df = _read_parquet_if_exists(path)
            if df is None or df.is_empty():
                continue
            check = validate_pre_game_cutoff(df, cutoff)
            source_max = check.get("max_source_week")
            if source_max is not None:
                max_feature_week = max(int(source_max), max_feature_week or 0)
            if check["status"] == CUTOFF_VIOLATION:
                errors.append(f"{path} contains week >= analysis_week ({analysis_week})")
            completeness = missing_metrics_for_df(
                df,
                required=REQUIRED_L3_MODEL_METRICS,
                optional=OPTIONAL_L3_MODEL_METRICS,
            )
            missing_required_metrics.update(completeness.missing_required_metrics)
            missing_optional_metrics.update(completeness.missing_optional_metrics)
            duplicate_key = (
                ["season", "week", "TEAM", "game_id"]
                if "game_id" in df.columns
                else ["season", "week", "TEAM"]
            )
            duplicate_games += duplicate_count(df, duplicate_key)
    else:
        warnings.append(f"missing l3 source directory: {l3_root}")

    rolling_root = data_root / "rolling_core12" / str(season)
    if rolling_root.exists():
        requested = analysis_week - 1
        if requested > 0:
            safe_snapshot = rolling_root / f"through_{requested}.parquet"
            if safe_snapshot.exists():
                df = _read_parquet_if_exists(safe_snapshot)
                if df is not None and "rolling_through_week" in df.columns:
                    max_rolling = df.select(pl.col("rolling_through_week").max()).item()
                    if max_rolling is not None and int(max_rolling) >= analysis_week:
                        errors.append(f"unsafe rolling snapshot content: {safe_snapshot}")
                if df is not None:
                    completeness = missing_metrics_for_df(
                        df,
                        required=[c for c in REQUIRED_CORE12_MODEL_METRICS if c in df.columns],
                        optional=[c for c in OPTIONAL_CORE12_MODEL_METRICS if c in df.columns],
                    )
                    missing_required_metrics.update(completeness.missing_required_metrics)
                    missing_optional_metrics.update(completeness.missing_optional_metrics)
    else:
        warnings.append(f"missing rolling source directory: {rolling_root}")

    if lines_path is not None and not lines_path.exists():
        warnings.append(f"missing lines file: {lines_path}")

    for metric in sorted(missing_required_metrics):
        errors.append(f"missing required model metric: {metric}")
    for metric in sorted(missing_optional_metrics):
        warnings.append(f"missing optional model metric: {metric}")

    leakage = any("week >= analysis_week" in item or "rolling snapshot" in item for item in errors)
    status = "BLOCKED" if errors else "PASS"
    return PreflightValidationResult(
        status=status,
        season=season,
        analysis_week=analysis_week,
        maximum_feature_week=max_feature_week,
        cutoff_status="FAIL" if leakage else "PASS",
        data_quality_status="FAIL"
        if missing_required_metrics
        else ("PASS_WITH_WARNINGS" if missing_optional_metrics else "PASS"),
        missing_required_metrics=sorted(missing_required_metrics),
        missing_optional_metrics=sorted(missing_optional_metrics),
        leakage_detected=leakage,
        duplicate_games=duplicate_games,
        unsafe_fallbacks=sum(1 for item in errors if "rolling snapshot" in item),
        warnings=warnings,
        errors=errors,
    )


def require_model_preflight(**kwargs: Any) -> PreflightValidationResult:
    result = validate_model_preflight(**kwargs)
    if result.status == "BLOCKED":
        raise RuntimeError(f"preflight validation blocked model run: {result.to_dict()}")
    return result
