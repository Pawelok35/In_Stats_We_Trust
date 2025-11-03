import json
from types import SimpleNamespace

import polars as pl
import pytest

from etl.l3_aggregate import run as l3_run
from utils.paths import path_for, manifest_path


def _stub_settings(tmp_path):
    return SimpleNamespace(data_root=tmp_path)


def test_l3_aggregation_produces_team_metrics(tmp_path, monkeypatch):
    settings = _stub_settings(tmp_path)
    monkeypatch.setattr("utils.paths.load_settings", lambda *args, **kwargs: settings)

    l2_path = path_for("l2", 2025, 1)
    l2_path.parent.mkdir(parents=True, exist_ok=True)

    pl.DataFrame(
        {
            "season": [2025, 2025, 2025, 2025],
            "week": [1, 1, 1, 1],
            "game_id": ["G1", "G1", "G1", "G1"],
            "play_id": [1, 2, 3, 4],
            "TEAM": ["BAL", "BAL", "MIA", "MIA"],
            "OPP": ["MIA", "MIA", "BAL", "BAL"],
            "drive": [1, 1, 2, 3],
            "play_type": ["run", "pass", "run", "pass"],
            "epa": [0.2, -0.1, 0.05, -0.2],
            "success": [1.0, 0.0, 0.5, 0.0],
            "yards_gained": [5.0, 3.0, 4.0, 2.0],
            "success_bin": [1, 0, 0, 0],
            "is_turnover": [0, 0, 0, 0],
            "is_offensive_td": [0, 0, 0, 0],
            "play_description": [
                "Run for five yards.",
                "Pass incomplete.",
                "Run for four yards.",
                "Pass incomplete.",
            ],
        }
    ).write_parquet(l2_path)

    out_path = l3_run(2025, 1)
    assert out_path == path_for("l3_team_week", 2025, 1)
    assert out_path.exists()

    result = pl.read_parquet(out_path).sort("TEAM")
    assert result.height == 2
    assert set(result["TEAM"]) == {"BAL", "MIA"}
    bal = result.filter(pl.col("TEAM") == "BAL")

    # plays: 2 offensive plays, drives unique=1
    assert bal["plays"][0] == 2
    assert bal["drives"][0] == 1
    assert bal["tempo"][0] == pytest.approx(2.0)

    manifest = manifest_path("l3_team_week", 2025, 1)
    assert manifest.exists()
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    assert payload["rows"] == 2
    assert payload["layer"] == "l3_team_week"


def test_l3_aggregation_missing_l2(tmp_path, monkeypatch):
    settings = _stub_settings(tmp_path)
    monkeypatch.setattr("utils.paths.load_settings", lambda *args, **kwargs: settings)

    with pytest.raises(FileNotFoundError):
        l3_run(2025, 2)
