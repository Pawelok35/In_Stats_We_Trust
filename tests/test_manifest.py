import hashlib
import json
from pathlib import Path

from utils.manifest import compute_sha256, write_manifest


def test_compute_sha256_matches_reference(tmp_path: Path):
    artifact = tmp_path / "sample.bin"
    payload = b"abc123"
    artifact.write_bytes(payload)

    expected = hashlib.sha256(payload).hexdigest()
    assert compute_sha256(artifact) == expected


def test_write_manifest_creates_sidecar_with_defaults(tmp_path: Path):
    artifact = tmp_path / "l2" / "2025" / "8.parquet"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_bytes(b"payload")

    manifest = write_manifest(
        artifact,
        {"layer": "l2", "season": 2025, "week": 8, "rows": 10, "cols": 5},
    )

    assert manifest.exists()
    assert manifest.name == "8_manifest.json"

    payload = json.loads(manifest.read_text(encoding="utf-8"))
    assert payload["sha256"] == compute_sha256(artifact)
    assert payload["rows"] == 10
    assert payload["path"] == str(artifact.resolve())
    assert "created_at" in payload


def test_write_manifest_allows_custom_path(tmp_path: Path):
    artifact = tmp_path / "artifact.parquet"
    artifact.write_bytes(b"payload")
    custom = tmp_path / "manifests" / "custom_manifest.json"

    out_path = write_manifest(
        artifact,
        {"layer": "custom", "season": 2025, "week": 9, "rows": 0, "cols": 0},
        manifest_path=custom,
    )

    assert out_path == custom
    payload = json.loads(custom.read_text(encoding="utf-8"))
    assert payload["season"] == 2025
    assert payload["sha256"] == compute_sha256(artifact)
    assert payload["path"] == str(artifact.resolve())


def test_write_manifest_supports_file_entries(tmp_path: Path):
    artifact = tmp_path / "anchor.parquet"
    artifact.write_bytes(b"anchor")
    extra = tmp_path / "extra.png"
    extra.write_bytes(b"data")

    manifest_path = write_manifest(
        artifact,
        {"layer": "reports", "season": 2025, "week": 9, "rows": 1, "cols": 1},
        files=[artifact, extra],
    )

    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    files = {entry["path"]: entry for entry in payload["files"]}
    assert str(artifact.resolve()) in files
    assert str(extra.resolve()) in files
    assert files[str(extra.resolve())]["size"] == extra.stat().st_size
    assert files[str(extra.resolve())]["sha256"] == compute_sha256(extra)
