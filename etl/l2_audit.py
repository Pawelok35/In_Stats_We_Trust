"""Utilities for recording L2 audit trail information."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class AuditEntry:
    step: str
    details: str
    rows: int
    cols: int | None = None
    extras: dict | None = None
    timestamp: str = ""

    def serializable(self) -> dict:
        payload = {
            "step": self.step,
            "details": self.details,
            "rows": self.rows,
        }
        if self.cols is not None:
            payload["cols"] = self.cols
        if self.extras:
            payload.update(self.extras)
        payload["timestamp"] = self.timestamp or datetime.now(timezone.utc).isoformat()
        return payload


def write_audit(entries: Iterable[AuditEntry], path: Path) -> None:
    """Persist audit entries to a JSONL file."""

    serialized = [entry.serializable() for entry in entries]
    if not serialized:
        logger.warning("No audit entries to write for %s", path)
        return

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in serialized:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    logger.info("Wrote L2 audit log with %s entries to %s", len(serialized), path)
