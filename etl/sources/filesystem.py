"""Filesystem-backed source loader for L1 ingestion."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import polars as pl

from utils.logging import get_logger

logger = get_logger(__name__)

_PARQUET_EXTENSIONS = {".parquet"}
_CSV_EXTENSIONS = {".csv", ".csv.gz"}


def _candidate_paths(base_dir: Path, season: int, week: int) -> Iterable[Path]:
    season_dir = base_dir / f"{season}"
    week_str = f"{week}"
    for ext in list(_PARQUET_EXTENSIONS | _CSV_EXTENSIONS):
        yield season_dir / f"{week_str}{ext}"

    # Support raw dumps named with prefixes, e.g. week_08.parquet
    for ext in list(_PARQUET_EXTENSIONS | _CSV_EXTENSIONS):
        yield season_dir / f"week_{week_str}{ext}"
        yield season_dir / f"{season}_{week_str}{ext}"


def _read_file(path: Path) -> pl.DataFrame:
    if path.suffix in _PARQUET_EXTENSIONS:
        return pl.read_parquet(path)
    if path.suffix in _CSV_EXTENSIONS:
        return pl.read_csv(path)
    raise ValueError(f"Unsupported file extension for raw ingest: {path.suffix}")


def load_week(base_dir: Path, season: int, week: int) -> pl.DataFrame:
    """Load raw play data from disk for the requested season/week."""

    resolved = base_dir.resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"Filesystem source directory not found: {resolved}")

    for candidate in _candidate_paths(resolved, season, week):
        if candidate.exists():
            logger.info("Loading filesystem raw data from %s", candidate)
            return _read_file(candidate)

    raise FileNotFoundError(
        f"No raw data file found for season={season}, week={week} under {resolved}"
    )
