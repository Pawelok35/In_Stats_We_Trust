"""ETL stage for ingesting raw play data into the canonical L1 schema."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Dict, Optional

import polars as pl

from etl.mappers import canonicalize_l1
from etl.sources import filesystem as filesystem_source
from etl.sources import nfl_data_py as nfl_source
from utils.config import load_settings
from utils.contracts import validate_df
from utils.guards import check_no_nan_in_keys
from utils.logging import get_logger
from utils.manifest import write_manifest
from utils.paths import manifest_path, path_for

logger = get_logger(__name__)

ProviderFn = Callable[[int, int], pl.DataFrame]


def _filesystem_loader(season: int, week: int) -> pl.DataFrame:
    settings = load_settings()
    base_dir: Path = settings.data_sources.filesystem.l1_raw_dir
    return filesystem_source.load_week(base_dir, season, week)


def _nfl_loader(season: int, week: int) -> pl.DataFrame:
    return nfl_source.load_week(season, week)


_PROVIDERS: Dict[str, ProviderFn] = {
    "filesystem": _filesystem_loader,
    "nfl_data_py": _nfl_loader,
}


def run(season: int, week: int, *, source_override: Optional[str] = None) -> Path:
    """Execute L1 ingestion and persist the canonical layer artifact."""

    provider_name = source_override or load_settings().data_sources.provider
    loader = _PROVIDERS.get(provider_name)
    if loader is None:
        raise ValueError(f"Unsupported L1 source provider: {provider_name}")

    logger.info("Running L1 ingest using provider '%s'", provider_name)
    raw_df = loader(season, week)

    logger.debug("Raw dataframe shape before mapping: rows=%s cols=%s", raw_df.height, raw_df.width)
    l1_df = canonicalize_l1(raw_df, season, week)
    validate_df(l1_df, "L1")
    check_no_nan_in_keys(l1_df, ["season", "week", "game_id", "play_id"])

    target = path_for("l1", season, week)
    l1_df.write_parquet(target)

    write_manifest(
        target,
        {
            "layer": "l1",
            "season": season,
            "week": week,
            "provider": provider_name,
            "rows": l1_df.height,
            "cols": l1_df.width,
        },
        manifest_path=manifest_path("l1", season, week),
    )

    logger.info("L1 artifact written to %s (rows=%s cols=%s)", target, l1_df.height, l1_df.width)
    return target
