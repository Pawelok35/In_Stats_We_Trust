from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def seed_snapshot(
    *,
    source: Path,
    destination: Path,
    manifest: Path | None = None,
    overwrite: bool = False,
) -> tuple[Path, Path]:
    if not source.exists():
        raise FileNotFoundError(f"Source snapshot not found: {source}")
    if destination.exists() and not overwrite:
        raise FileExistsError(f"Destination already exists; pass --overwrite: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(source.read_bytes())
    manifest_path = manifest or destination.with_name(destination.stem + "_preseason_seed_manifest.json")
    payload = {
        "schema_version": "preseason_rolling_seed.v1",
        "source": str(source),
        "destination": str(destination),
        "source_sha256": sha256_file(source),
        "destination_sha256": sha256_file(destination),
        "created_at_utc": datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z"),
        "note": "Preseason seed for Week 1 previews. Do not treat as current-season performance.",
    }
    manifest_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return destination, manifest_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed a preseason rolling snapshot from prior season.")
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    destination, manifest = seed_snapshot(
        source=args.source,
        destination=args.destination,
        manifest=args.manifest,
        overwrite=args.overwrite,
    )
    print(f"destination={destination}")
    print(f"manifest={manifest}")


if __name__ == "__main__":
    main()
