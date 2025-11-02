"""ETL stage for normalizing L1 data into the L2 cleaned schema."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import polars as pl

from etl.l2_audit import AuditEntry, write_audit
from etl.mappers import prepare_l2
from utils.contracts import validate_df
from utils.guards import check_no_inf, check_no_nan_in_keys
from utils.logging import get_logger
from utils.manifest import write_manifest
from utils.paths import l2_audit_path, manifest_path, path_for

logger = get_logger(__name__)


def run(season: int, week: int, *, l1_result: Optional[Any] = None) -> Path:
    """Execute L2 cleaning and emit normalized parquet + audit outputs."""

    if l1_result is None:
        source_path = path_for("l1", season, week)
    else:
        source_path = Path(l1_result)

    if not source_path.exists():
        raise FileNotFoundError(f"L1 artifact not found at {source_path}")

    logger.info("Loading L1 artifact from %s", source_path)
    l1_df = pl.read_parquet(source_path)

    audit_entries: list[AuditEntry] = [
        AuditEntry(step="load", details="Loaded L1 parquet", rows=l1_df.height, cols=l1_df.width)
    ]

    cleaned = prepare_l2(l1_df, season, week)
    audit_entries.append(
        AuditEntry(
            step="prepare",
            details="Normalized team aliases, filtered season/week, deduplicated keys",
            rows=cleaned.height,
            cols=cleaned.width,
            extras={"rows_removed": l1_df.height - cleaned.height},
        )
    )

    validate_df(cleaned, "L2")
    check_no_nan_in_keys(cleaned, ["season", "week", "game_id", "play_id"])
    check_no_inf(cleaned)

    audit_entries.append(
        AuditEntry(
            step="validate",
            details="Validated against L2 contract and guardrails",
            rows=cleaned.height,
            cols=cleaned.width,
        )
    )

    target = path_for("l2", season, week)
    cleaned.write_parquet(target)

    write_manifest(
        target,
        {
            "layer": "l2",
            "season": season,
            "week": week,
            "rows": cleaned.height,
            "cols": cleaned.width,
        },
        manifest_path=manifest_path("l2", season, week),
    )

    audit_file = l2_audit_path(season, week)
    write_audit(audit_entries, audit_file)

    logger.info(
        "L2 artifact written to %s (rows=%s cols=%s)",
        target,
        cleaned.height,
        cleaned.width,
    )
    return target
