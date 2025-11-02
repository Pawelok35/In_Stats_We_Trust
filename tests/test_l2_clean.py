import json
from types import SimpleNamespace

import polars as pl
import pytest

from etl.l2_clean import run as l2_run
from utils.paths import l2_audit_path, manifest_path, path_for


def _stub_settings(tmp_path):
    return SimpleNamespace(data_root=tmp_path)


def test_l2_clean_generates_normalized_artifacts(tmp_path, monkeypatch):
    settings = _stub_settings(tmp_path)
    monkeypatch.setattr("utils.paths.load_settings", lambda *args, **kwargs: settings)

    l1_path = path_for("l1", 2025, 1)
    l1_path.parent.mkdir(parents=True, exist_ok=True)

    pl.DataFrame(
        {
            "season": [2025, 2025, 2025],
            "week": [1, 1, 1],
            "game_id": ["G1", "G1", "G1"],
            "play_id": [1, 1, 2],
            "posteam": ["WAS", "WAS", "SD"],
            "defteam": ["NYG", "NYG", "DEN"],
            "drive": [1, 1, 2],
            "play_type": ["run", "run", "pass"],
            "epa": [0.1, 0.1, 0.2],
            "success": [1.0, 1.0, None],
            "yardline_100": [75.0, 75.0, 68.0],
            "down": [1, 1, 2],
            "distance": [10, 10, 8],
        }
    ).write_parquet(l1_path)

    output_path = l2_run(2025, 1)
    assert output_path == path_for("l2", 2025, 1)
    assert output_path.exists()

    result = pl.read_parquet(output_path)
    assert result.height == 2
    assert set(result["TEAM"]) == {"WSH", "LAC"}
    assert result.filter(pl.col("TEAM") == "LAC")["success"].item() == 0.0
    assert "success_bin" in result.columns

    manifest = manifest_path("l2", 2025, 1)
    assert manifest.exists()
    manifest_payload = json.loads(manifest.read_text(encoding="utf-8"))
    assert manifest_payload["rows"] == 2
    assert manifest_payload["layer"] == "l2"

    audit_file = l2_audit_path(2025, 1)
    assert audit_file.exists()
    audit_lines = audit_file.read_text(encoding="utf-8").splitlines()
    assert len(audit_lines) >= 3
    assert any('"step": "validate"' in line for line in audit_lines)


def test_l2_clean_missing_l1_raises(tmp_path, monkeypatch):
    settings = _stub_settings(tmp_path)
    monkeypatch.setattr("utils.paths.load_settings", lambda *args, **kwargs: settings)

    with pytest.raises(FileNotFoundError):
        l2_run(2025, 2)
