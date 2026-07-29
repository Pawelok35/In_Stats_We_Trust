"""Variant registry helpers for champion/challenger workflows."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import yaml

ACTIVE_STATUSES = {"champion", "challenger"}
VALID_STATUSES = {"champion", "challenger", "experimental", "retired"}


def load_variants(path: Path) -> list[dict[str, Any]]:
    """Load and validate variant registry entries."""

    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not data or "variants" not in data:
        raise ValueError(f"Variant file {path} must contain a 'variants' list.")

    variants = list(data["variants"])
    seen_names: set[str] = set()
    champions = 0
    for variant in variants:
        name = str(variant.get("name", "")).strip()
        if not name:
            raise ValueError("Each variant must include a non-empty name.")
        if name in seen_names:
            raise ValueError(f"Duplicate variant name: {name}")
        seen_names.add(name)

        status = str(variant.get("status", "experimental")).strip().lower()
        if status not in VALID_STATUSES:
            raise ValueError(
                f"Variant {name} has invalid status {status!r}; "
                f"expected one of {sorted(VALID_STATUSES)}."
            )
        variant["status"] = status
        if status == "champion":
            champions += 1

        for key in ("tag_config", "picks_dir"):
            if not variant.get(key):
                raise ValueError(f"Variant {name} must include {key}.")

    if champions != 1:
        raise ValueError(f"Expected exactly one champion variant, found {champions}.")
    return variants


def filter_variants(
    variants: list[dict[str, Any]],
    statuses: Optional[set[str]] = None,
    names: Optional[set[str]] = None,
) -> list[dict[str, Any]]:
    """Filter variants by lifecycle status and/or explicit names."""

    normalized_statuses = {status.lower() for status in statuses} if statuses else None
    normalized_names = {name.lower() for name in names} if names else None

    selected = []
    for variant in variants:
        if normalized_statuses and variant["status"] not in normalized_statuses:
            continue
        if normalized_names and variant["name"].lower() not in normalized_names:
            continue
        selected.append(variant)
    return selected


def active_variants(variants: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return champion and challenger variants."""

    return filter_variants(variants, statuses=ACTIVE_STATUSES)
