"""Placeholder implementation for Hidden Trends analytics."""

from __future__ import annotations

import polars as pl

from utils.logging import get_logger

logger = get_logger(__name__)


def compute(
    df_l3: pl.DataFrame | None = None, df_l4_core: pl.DataFrame | None = None
) -> pl.DataFrame:
    """Return an empty frame placeholder until the HiddenTrends model is implemented."""
    logger.info(
        "HiddenTrends stub invoked (l3_rows=%s, core_rows=%s)",
        0 if df_l3 is None else df_l3.height,
        0 if df_l4_core is None else df_l4_core.height,
    )
    return pl.DataFrame()
