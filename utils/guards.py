"""Data quality guardrails for ETL safety checks."""

from __future__ import annotations

import math
from typing import Iterable

import polars as pl

from utils.logging import get_logger

logger = get_logger(__name__)

_FLOAT_DTYPES = (pl.Float32, pl.Float64)


def _ensure_dataframe(df: pl.DataFrame) -> pl.DataFrame:
    if not isinstance(df, pl.DataFrame):
        raise TypeError("Guard functions expect a polars.DataFrame instance")
    return df


def check_no_nan_in_keys(df: pl.DataFrame, keys: Iterable[str]) -> None:
    """Ensure key columns contain neither NULL nor NaN values."""

    _ensure_dataframe(df)

    for key in keys:
        if key not in df.columns:
            raise ValueError(f"Key column '{key}' not present in DataFrame")

        series = df.get_column(key)
        if series.is_null().any():
            raise ValueError(f"NULL detected in key column '{key}'")
        if series.dtype in _FLOAT_DTYPES and series.is_nan().any():
            raise ValueError(f"NaN detected in key column '{key}'")

    logger.debug("Guard check_no_nan_in_keys passed for keys=%s", list(keys))


def check_no_inf(df: pl.DataFrame) -> None:
    """Raise if any floating point column contains +/- infinity."""

    _ensure_dataframe(df)

    for column, dtype in df.schema.items():
        if dtype not in _FLOAT_DTYPES:
            continue
        series = df.get_column(column)
        # Polars 0.20 exposes Series.is_infinite; fall back to Python for compatibility.
        if hasattr(series, "is_infinite"):
            if series.is_infinite().any():
                raise ValueError(f"INF detected in column '{column}'")
        else:
            for value in series.to_list():
                if value is None:
                    continue
                if isinstance(value, float) and math.isinf(value):
                    raise ValueError(f"INF detected in column '{column}'")

    logger.debug("Guard check_no_inf passed for DataFrame with columns=%s", list(df.columns))
