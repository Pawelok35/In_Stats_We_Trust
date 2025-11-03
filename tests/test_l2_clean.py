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
            "play_id": [1, 2, 3],
            "posteam": ["WAS", "WAS", "SD"],
            "defteam": ["NYG", "NYG", "DEN"],
            "drive": [1, 1, 2],
            "play_type": ["run", "run", "pass"],
            "epa": [0.1, 0.1, 0.2],
            "success": [1.0, 1.0, None],
            "yardline_100": [75.0, 18.0, 68.0],
            "down": [1, 3, 3],
            "distance": [10, 2, 8],
            "yards_gained": [4.0, 6.0, 4.0],
            "touchdown": [0, 0, 0],
            "interception": [0, 0, 1],
            "fumble_lost": [0, 0, 0],
            "play_description": [
                "Run for four yards.",
                "Run for six yards.",
                "Pass intercepted by defender.",
            ],
        }
    ).write_parquet(l1_path)

    output_path = l2_run(2025, 1)
    assert output_path == path_for("l2", 2025, 1)
    assert output_path.exists()

    result = pl.read_parquet(output_path)
    assert result.height == 3
    assert set(result["TEAM"]) == {"WAS", "SD"}
    sd_row = result.filter(pl.col("TEAM") == "SD")["success"]
    assert sd_row.len() == 1
    assert sd_row.item() is None
    assert "success_bin" in result.columns
    assert "is_explosive" in result.columns
    assert "is_third_down" in result.columns
    assert "third_down_converted" in result.columns
    assert "is_dropback" in result.columns
    assert "is_pressure" in result.columns
    assert "in_redzone" in result.columns
    # second row is third-and-2 run for 6 yards -> conversion
    assert result.filter(pl.col("TEAM") == "WAS")["third_down_converted"].sum() == 1
    # SD play is third down but interception before gain -> no conversion
    assert result.filter(pl.col("TEAM") == "SD")["third_down_converted"].sum() == 0
    assert "is_explosive" in result.columns
    assert result["is_explosive"].sum() == 0
    assert result.filter(pl.col("TEAM") == "SD")["is_dropback"].sum() == 1
    assert result["is_pressure"].sum() == 0
    assert result.filter(pl.col("TEAM") == "WAS")["in_redzone"].sum() == 1
    assert result.filter(pl.col("TEAM") == "SD")["in_redzone"].sum() == 0

    manifest = manifest_path("l2", 2025, 1)
    assert manifest.exists()
    manifest_payload = json.loads(manifest.read_text(encoding="utf-8"))
    assert manifest_payload["rows"] == 3
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
