"""Utilities for computing artifact hashes and writing manifest metadata."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, MutableMapping

from utils.logging import get_logger

logger = get_logger(__name__)

_READ_CHUNK_SIZE = 1024 * 1024  # 1 MiB


def compute_sha256(path: Path) -> str:
    """Return the hexadecimal SHA-256 hash for the given file."""

    resolved = path.resolve()
    if not resolved.is_file():
        raise FileNotFoundError(f"Cannot compute hash; file not found at {resolved}")

    digest = hashlib.sha256()
    with resolved.open("rb") as handle:
        for chunk in iter(lambda: handle.read(_READ_CHUNK_SIZE), b""):
            digest.update(chunk)

    hex_digest = digest.hexdigest()
    logger.debug("Computed SHA-256 for %s: %s", resolved, hex_digest)
    return hex_digest


def write_manifest(
    artifact_path: Path | str | None = None,
    payload: Mapping[str, Any] | None = None,
    *,
    manifest_path: Path | None = None,
    path: Path | str | None = None,
    layer: str | None = None,
    rows: int | None = None,
    cols: int | None = None,
    files: Iterable[Path | str] | None = None,
    **extra_metadata: Any,
) -> Path:
    """Write a manifest JSON file alongside the provided artifact.

    Parameters
    ----------
    artifact_path:
        The produced data artifact for which metadata should be recorded.
    payload:
        Base metadata that must at least contain ``layer``, ``season``, ``week``,
        ``rows``, and ``cols``. Additional fields will be preserved.
    manifest_path:
        Optional override for the manifest output location. Defaults to
        ``<artifact_stem>_manifest.json`` next to the artifact.

    Returns
    -------
    Path
        The path where the manifest was written.
    """

    if artifact_path is None and path is None:
        raise ValueError("write_manifest requires an artifact path")

    if artifact_path is None and path is not None:
        artifact_path = path

    resolved_artifact = Path(artifact_path).resolve()
    if not resolved_artifact.exists():
        raise FileNotFoundError(f"Artifact not found at {resolved_artifact}")

    hash_cache: dict[Path, str] = {}

    def _hash_for(file_path: Path) -> str:
        cached = hash_cache.get(file_path)
        if cached is None:
            hash_cache[file_path] = compute_sha256(file_path)
            cached = hash_cache[file_path]
        return cached

    manifest_target = (
        Path(manifest_path).resolve()
        if manifest_path is not None
        else _default_manifest_path(resolved_artifact)
    )
    manifest_target.parent.mkdir(parents=True, exist_ok=True)

    manifest_payload: MutableMapping[str, Any] = dict(payload or {})
    if layer is not None:
        manifest_payload.setdefault("layer", layer)
    if rows is not None:
        manifest_payload.setdefault("rows", rows)
    if cols is not None:
        manifest_payload.setdefault("cols", cols)

    for key, value in extra_metadata.items():
        if value is not None:
            manifest_payload.setdefault(key, value)

    if "layer" not in manifest_payload:
        raise ValueError("Manifest payload must include a 'layer' field")

    manifest_payload.setdefault("path", str(resolved_artifact))
    manifest_payload.setdefault("sha256", _hash_for(resolved_artifact))
    manifest_payload.setdefault("created_at", datetime.now(timezone.utc).isoformat())

    file_entries: list[dict[str, Any]] = []
    if files:
        seen: set[Path] = set()
        for file_item in files:
            resolved_file = Path(file_item).resolve()
            if resolved_file in seen:
                continue
            if not resolved_file.exists():
                raise FileNotFoundError(f"Manifest file entry not found: {resolved_file}")
            seen.add(resolved_file)
            file_entries.append(
                {
                    "path": str(resolved_file),
                    "sha256": _hash_for(resolved_file),
                    "size": resolved_file.stat().st_size,
                }
            )

    if file_entries:
        manifest_payload["files"] = sorted(file_entries, key=lambda entry: entry["path"])

    with manifest_target.open("w", encoding="utf-8") as handle:
        json.dump(manifest_payload, handle, indent=2, ensure_ascii=False, sort_keys=True)

    logger.info("Manifest written for layer %s.", manifest_payload.get("layer"))
    logger.debug("Manifest for %s saved to %s", manifest_payload.get("layer"), manifest_target)

    return manifest_target


def _default_manifest_path(artifact_path: Path) -> Path:
    return artifact_path.with_name(f"{artifact_path.stem}_manifest.json")
