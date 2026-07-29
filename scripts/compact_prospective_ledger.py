from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def utc_now_compact() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def compact_ledger(ledger_path: Path, *, keep_not_qualified: bool = False) -> tuple[Path, int, int]:
    if not ledger_path.exists():
        raise FileNotFoundError(f"Ledger not found: {ledger_path}")

    records = load_jsonl(ledger_path)
    kept = [
        record
        for record in records
        if keep_not_qualified or bool(record.get("proof_qualified"))
    ]
    removed = len(records) - len(kept)

    archive_dir = ledger_path.parent / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    archive_path = archive_dir / f"{ledger_path.stem}_pre_compact_{utc_now_compact()}.jsonl"
    shutil.copy2(ledger_path, archive_path)

    ledger_path.write_text(
        "".join(canonical_json(record) + "\n" for record in kept),
        encoding="utf-8",
    )
    write_manifest(ledger_path, archive_path, len(records), len(kept), removed)
    return archive_path, len(kept), removed


def write_manifest(
    ledger_path: Path,
    archive_path: Path,
    original_count: int,
    kept_count: int,
    removed_count: int,
) -> None:
    manifest_path = ledger_path.with_name(ledger_path.stem.replace("_prospective", "") + "_compact_manifest.json")
    payload = {
        "schema_version": "prospective_ledger_compact_manifest.v1",
        "ledger_path": str(ledger_path),
        "ledger_sha256": sha256_file(ledger_path),
        "archive_path": str(archive_path),
        "archive_sha256": sha256_file(archive_path),
        "original_records": original_count,
        "kept_records": kept_count,
        "removed_records": removed_count,
        "created_at_utc": datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z"),
        "note": "Compaction archives the original ledger and rewrites active ledger for reporting hygiene.",
    }
    manifest_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Archive and compact a prospective ledger.")
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument(
        "--keep-not-qualified",
        action="store_true",
        help="Keep not-qualified records in the active ledger.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    archive_path, kept, removed = compact_ledger(
        args.ledger,
        keep_not_qualified=args.keep_not_qualified,
    )
    print(f"archive={archive_path}")
    print(f"kept={kept}")
    print(f"removed={removed}")


if __name__ == "__main__":
    main()
