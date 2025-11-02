import json
from pathlib import Path
from types import SimpleNamespace

import polars as pl
import pytest

from etl.l1_ingest import run as l1_run
from utils.manifest import compute_sha256
from utils.paths import manifest_path, path_for


def _stub_settings(tmp_path: Path, raw_dir: Path):
    return SimpleNamespace(
        data_root=tmp_path,
        data_sources=SimpleNamespace(
            provider="filesystem",
            filesystem=SimpleNamespace(l1_raw_dir=raw_dir),
        ),
    )


def test_l1_ingest_filesystem_roundtrip(tmp_path, monkeypatch):
    raw_dir = tmp_path / "sources"
    season_dir = raw_dir / "2025"
    season_dir.mkdir(parents=True)

    raw_df = pl.DataFrame(
        {
            "game_id": ["G1", "G1"],
            "play_id": [1, 2],
            "posteam": ["AAA", "AAA"],
            "defteam": ["BBB", "BBB"],
            "drive": [1, 1],
            "play_type": ["run", "pass"],
            "epa": [0.1, -0.2],
            "success": [1.0, 0.0],
            "yardline_100": [75.0, 68.0],
            "down": [1, 2],
            "distance": [10, 8],
        }
    )
    raw_path = season_dir / "1.parquet"
    raw_df.write_parquet(raw_path)

    settings = _stub_settings(tmp_path, raw_dir)
    monkeypatch.setattr("etl.l1_ingest.load_settings", lambda *args, **kwargs: settings)
    monkeypatch.setattr("utils.paths.load_settings", lambda *args, **kwargs: settings)

    output_path = l1_run(2025, 1)
    assert output_path == path_for("l1", 2025, 1)
    assert output_path.exists()

    result_df = pl.read_parquet(output_path)
    assert result_df.height == 2
    assert result_df["season"].to_list() == [2025, 2025]
    assert "game_id" in result_df.columns

    manifest = manifest_path("l1", 2025, 1)
    assert manifest.exists()
    manifest_sha = compute_sha256(output_path)
    assert manifest_sha
    manifest_payload = json.loads(manifest.read_text(encoding="utf-8"))
    assert manifest_payload["layer"] == "l1"
    assert manifest_payload["sha256"] == manifest_sha


def test_l1_ingest_missing_file_raises(tmp_path, monkeypatch):
    raw_dir = tmp_path / "missing_sources"
    raw_dir.mkdir()
    settings = _stub_settings(tmp_path, raw_dir)
    monkeypatch.setattr("etl.l1_ingest.load_settings", lambda *args, **kwargs: settings)
    monkeypatch.setattr("utils.paths.load_settings", lambda *args, **kwargs: settings)

    with pytest.raises(FileNotFoundError):
        l1_run(2025, 2)
