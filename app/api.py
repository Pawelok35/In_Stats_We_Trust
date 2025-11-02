"""Minimal FastAPI application exposing health and Core12 preview endpoints."""

from __future__ import annotations

import polars as pl
from fastapi import FastAPI, HTTPException, Query

from utils.contracts import validate_df
from utils.dataframes import read_parquet_or_raise
from utils.logging import get_logger
from utils.paths import path_for

logger = get_logger(__name__)

app = FastAPI(title="In Stats We Trust API", version="0.1.0")


def _load_core12(season: int, week: int) -> pl.DataFrame:
    path = path_for("l4_core12", season, week)
    try:
        df = read_parquet_or_raise(path)
    except FileNotFoundError as exc:
        logger.error("Core12 artifact missing at %s", path)
        raise HTTPException(status_code=404, detail="Core12 dataset not found") from exc

    validate_df(df, "L4_CORE12")
    return df


@app.get("/health")
def health() -> dict[str, str]:
    """Health probe that indicates the API is reachable."""
    return {"status": "ok"}


@app.get("/metrics/core12/preview")
def core12_preview(
    season: int = Query(..., ge=1),
    week: int = Query(..., ge=1),
    n: int = Query(20, ge=1, le=100),
) -> list[dict[str, object]]:
    """Return the first N Core12 rows for the requested season/week."""
    df = _load_core12(season, week)
    preview = df.sort(["season", "week", "TEAM"]).head(n)
    logger.info(
        "Serving Core12 preview (season=%s, week=%s, rows=%s)",
        season,
        week,
        preview.height,
    )
    return preview.to_dicts()
