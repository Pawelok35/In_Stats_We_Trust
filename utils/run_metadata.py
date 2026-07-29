"""Runtime metadata helpers for reproducible artifacts."""

from __future__ import annotations

import hashlib
import subprocess
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
UNKNOWN = "unknown"


def file_sha256(path: Path | str) -> str:
    """Return SHA-256 for a file."""

    resolved = Path(path)
    if not resolved.is_absolute():
        resolved = PROJECT_ROOT / resolved
    if not resolved.exists():
        raise FileNotFoundError(f"Cannot hash missing file: {resolved}")

    digest = hashlib.sha256()
    with resolved.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


@lru_cache(maxsize=1)
def git_metadata() -> dict[str, Any]:
    """Return best-effort git metadata without failing artifact generation."""

    commit_sha = _run_git(["rev-parse", "HEAD"])
    dirty_result = _run_git(["status", "--porcelain"], allow_failure=True)
    return {
        "commit_sha": commit_sha or UNKNOWN,
        "code_is_dirty": bool(dirty_result),
    }


def build_run_metadata(
    *,
    model_version: Optional[str] = None,
    config_paths: Optional[Iterable[Path | str]] = None,
    data_cutoff: Optional[str] = None,
) -> dict[str, Any]:
    """Build reproducibility metadata for manifests, picks, and reports."""

    metadata = dict(git_metadata())
    if model_version:
        metadata["model_version"] = model_version
    if data_cutoff:
        metadata["data_cutoff"] = data_cutoff

    config_hashes: dict[str, str] = {}
    for path in config_paths or []:
        resolved = Path(path)
        if not resolved.is_absolute():
            resolved = PROJECT_ROOT / resolved
        if not resolved.exists():
            continue
        try:
            key = str(resolved.relative_to(PROJECT_ROOT)).replace("\\", "/")
        except ValueError:
            key = str(resolved)
        config_hashes[key] = file_sha256(resolved)

    if config_hashes:
        metadata["config_hashes"] = config_hashes
        joined = "|".join(f"{key}:{value}" for key, value in sorted(config_hashes.items()))
        metadata["config_sha256"] = hashlib.sha256(joined.encode("utf-8")).hexdigest()

    return metadata


def _run_git(args: list[str], *, allow_failure: bool = False) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=PROJECT_ROOT,
            check=False,
            capture_output=True,
            text=True,
            timeout=2,
        )
    except (OSError, subprocess.TimeoutExpired):
        return "" if allow_failure else UNKNOWN

    if result.returncode != 0:
        return "" if allow_failure else UNKNOWN
    return result.stdout.strip()
