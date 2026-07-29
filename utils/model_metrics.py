"""Central classification of model metrics and missing-data behavior."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import polars as pl

REQUIRED_L3_MODEL_METRICS: tuple[str, ...] = (
    "epa_off_mean",
    "epa_def_mean",
    "success_rate_off",
    "success_rate_def",
    "ypp_off",
    "ypp_def",
    "ypp_diff",
    "tempo",
)

OPTIONAL_L3_MODEL_METRICS: tuple[str, ...] = (
    "pass_success_rate_off",
    "rush_success_rate_off",
    "pass_success_rate_def",
    "rush_success_rate_def",
    "pressure_rate_def",
    "pressure_rate_allowed",
    "explosive_play_rate_off",
    "explosive_play_rate_def",
    "third_down_conv_off",
    "third_down_conv_def",
    "redzone_td_rate_off",
    "redzone_td_rate_def",
    "points_per_drive_off",
    "points_per_drive_def",
    "points_per_drive_diff",
    "pass_rate_off",
    "rush_rate_off",
    "avg_start_yd100_off",
    "avg_start_yd100_def",
    "start_field_position_edge",
)

COUNT_METRICS_ALLOWING_ZERO: tuple[str, ...] = (
    "drives",
    "plays",
)

RATE_METRICS_ALLOWING_TRUE_ZERO: tuple[str, ...] = (
    "success_rate_off",
    "success_rate_def",
    "pass_success_rate_off",
    "rush_success_rate_off",
    "pass_success_rate_def",
    "rush_success_rate_def",
    "pressure_rate_def",
    "pressure_rate_allowed",
    "explosive_play_rate_off",
    "explosive_play_rate_def",
    "third_down_conv_off",
    "third_down_conv_def",
    "redzone_td_rate_off",
    "redzone_td_rate_def",
    "pass_rate_off",
    "rush_rate_off",
)

DERIVED_METRICS: tuple[str, ...] = (
    "points_per_drive_diff",
    "ypp_diff",
    "start_field_position_edge",
)

REQUIRED_CORE12_MODEL_METRICS: tuple[str, ...] = (
    "core_epa_off",
    "core_epa_def",
    "core_sr_off",
    "core_sr_def",
    "core_ypp_diff",
)

OPTIONAL_CORE12_MODEL_METRICS: tuple[str, ...] = (
    "core_explosive_play_rate_off",
    "core_third_down_conv",
    "core_turnover_margin",
    "core_points_per_drive_diff",
    "core_redzone_td_rate",
    "core_pressure_rate_def",
    "core_ed_sr_off",
    "tempo",
)


@dataclass(frozen=True)
class MetricCompleteness:
    missing_required_metrics: tuple[str, ...]
    missing_optional_metrics: tuple[str, ...]

    @property
    def required_complete(self) -> bool:
        return not self.missing_required_metrics

    @property
    def status(self) -> str:
        if self.missing_required_metrics:
            return "MISSING_REQUIRED_METRICS"
        if self.missing_optional_metrics:
            return "PASS_WITH_WARNINGS"
        return "OK"


def safe_div(num_expr: pl.Expr, den_expr: pl.Expr) -> pl.Expr:
    """Return null when there is no denominator/sample; preserve real 0 / n = 0."""
    return (
        pl.when(den_expr.is_null() | (den_expr <= 0))
        .then(pl.lit(None).cast(pl.Float64))
        .otherwise(num_expr / den_expr)
    )


def missing_metrics_for_df(
    df: pl.DataFrame,
    *,
    required: Iterable[str],
    optional: Iterable[str] = (),
) -> MetricCompleteness:
    missing_required: list[str] = []
    missing_optional: list[str] = []
    for col in required:
        if col not in df.columns or df.filter(pl.col(col).is_null()).height > 0:
            missing_required.append(col)
    for col in optional:
        if col not in df.columns or df.filter(pl.col(col).is_null()).height > 0:
            missing_optional.append(col)
    return MetricCompleteness(tuple(missing_required), tuple(missing_optional))


def row_missing_metrics(row: dict, metrics: Iterable[str]) -> list[str]:
    missing: list[str] = []
    for metric in metrics:
        value = row.get(metric)
        if value is None:
            missing.append(metric)
            continue
        try:
            if value != value:
                missing.append(metric)
        except TypeError:
            pass
    return missing
