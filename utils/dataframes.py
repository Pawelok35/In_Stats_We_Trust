"""Utility helpers for working with Polars DataFrames and parquet artifacts."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any

import polars as pl

from utils.logging import get_logger

logger = get_logger(__name__)


def read_parquet_or_raise(path: Path) -> pl.DataFrame:
    """Read a parquet file ensuring it exists."""
    if not path.exists():
        raise FileNotFoundError(f"Parquet file not found at {path}")
    return pl.read_parquet(path)


def preview_dataframe(
    df: pl.DataFrame,
    columns: Sequence[str],
    *,
    limit: int,
    sort_by: Sequence[str] | None = None,
    descending: bool | Sequence[bool] = False,
) -> list[dict[str, Any]]:
    """Return a limited preview for the requested columns."""
    available_columns = [col for col in columns if col in df.columns]
    if not available_columns:
        logger.debug("No requested columns available for preview: %s", columns)
        return []

    working = df.select(available_columns)

    if sort_by:
        existing_sort_columns = [col for col in sort_by if col in working.columns]
        if existing_sort_columns:
            working = working.sort(existing_sort_columns, descending=descending)

    return working.head(limit).to_dicts()
