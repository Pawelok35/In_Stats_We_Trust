import json
from types import SimpleNamespace

import polars as pl
import pytest

from metrics.core12 import compute as core12_compute
from utils.paths import manifest_path, path_for


def _settings(tmp_path):
    return SimpleNamespace(data_root=tmp_path)


def test_core12_compute_generates_expected_columns(tmp_path, monkeypatch):
    settings = _settings(tmp_path)
    monkeypatch.setattr("utils.paths.load_settings", lambda *args, **kwargs: settings)

    l3_df = pl.DataFrame(
        {
            "season": [2025, 2025],
            "week": [8, 8],
            "TEAM": ["BAL", "MIA"],
            "drives": [10, 8],
            "plays": [65, 58],
            "epa_off_mean": [0.12, -0.05],
            "success_rate_off": [0.48, 0.52],
            "epa_def_mean": [-0.08, 0.03],
            "success_rate_def": [0.43, 0.51],
            "tempo": [2.3, 2.0],
        }
    )

    # Prepare supporting L2/L1 artifacts
    l2_path = path_for("l2", 2025, 8)
    l2_path.parent.mkdir(parents=True, exist_ok=True)
    pl.DataFrame(
        {
            "season": [2025] * 6,
            "week": [8] * 6,
            "game_id": ["G1", "G1", "G1", "G1", "G1", "G1"],
            "play_id": [1, 2, 3, 4, 5, 6],
            "TEAM": ["BAL", "BAL", "BAL", "MIA", "MIA", "MIA"],
            "OPP": ["MIA", "MIA", "MIA", "BAL", "BAL", "BAL"],
            "drive": [1, 1, 2, 1, 1, 2],
            "play_type": ["pass", "run", "interception", "pass", "pass", "pass"],
            "epa": [-0.6, 0.3, -2.0, 0.8, -0.5, 0.4],
            "success": [0.0, 1.0, 0.0, 1.0, 0.0, 1.0],
            "yards_gained": [-7.0, 4.0, -5.0, 25.0, -3.0, 10.0],
            "success_bin": [0, 1, 0, 1, 0, 1],
        }
    ).write_parquet(l2_path)

    l1_path = path_for("l1", 2025, 8)
    l1_path.parent.mkdir(parents=True, exist_ok=True)
    pl.DataFrame(
        {
            "season": [2025, 2025],
            "week": [8, 8],
            "posteam": ["BAL", "MIA"],
            "play_type": ["touchdown pass", "run"],
            "yardline_100": [15.0, 30.0],
        }
    ).write_parquet(l1_path)

    result = core12_compute(l3_df, 2025, 8)
    expected_columns = {
        "season",
        "week",
        "TEAM",
        "core_epa_off",
        "core_epa_def",
        "core_sr_off",
        "core_sr_def",
        "core_ed_sr_off",
        "core_third_down_conv",
        "core_ypp_diff",
        "core_turnover_margin",
        "core_points_per_drive_diff",
        "core_redzone_td_rate",
        "core_pressure_rate_def",
        "core_explosive_play_rate_off",
    }
    assert set(result.columns) == expected_columns
    assert result.shape == (2, len(expected_columns))
    for column, dtype in result.schema.items():
        if column in {"season", "week"}:
            assert dtype == pl.Int64
        elif column == "TEAM":
            assert dtype == pl.Utf8
        else:
            assert dtype == pl.Float64

    bal = result.filter(pl.col("TEAM") == "BAL").row(0, named=True)
    mia = result.filter(pl.col("TEAM") == "MIA").row(0, named=True)

    assert pytest.approx(bal["core_pressure_rate_def"], rel=1e-6) == 0.333333
    assert pytest.approx(mia["core_pressure_rate_def"], rel=1e-6) == 1.0
    assert pytest.approx(bal["core_explosive_play_rate_off"], rel=1e-6) == 0.333333
    assert pytest.approx(mia["core_explosive_play_rate_off"], rel=1e-6) == 0.666667
    assert pytest.approx(bal["core_ypp_diff"], rel=1e-6) == -13.333333
    assert pytest.approx(mia["core_ypp_diff"], rel=1e-6) == 13.333333
    assert pytest.approx(bal["core_turnover_margin"], rel=1e-6) == 0.0
    assert pytest.approx(mia["core_turnover_margin"], rel=1e-6) == 1.0
    assert pytest.approx(bal["core_points_per_drive_diff"], rel=1e-6) == -1.5
    assert pytest.approx(mia["core_points_per_drive_diff"], rel=1e-6) == 1.5
    assert pytest.approx(bal["core_redzone_td_rate"], rel=1e-6) == 1.0
    assert pytest.approx(mia["core_redzone_td_rate"], rel=1e-6) == 0.0

    out_path = path_for("l4_core12", 2025, 8)
    assert out_path.exists()
    manifest = manifest_path("l4_core12", 2025, 8)
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    assert payload["rows"] == 2
    assert payload["layer"] == "l4_core12"


def test_core12_handles_empty_input(tmp_path, monkeypatch):
    settings = _settings(tmp_path)
    monkeypatch.setattr("utils.paths.load_settings", lambda *args, **kwargs: settings)

    empty_l3 = pl.DataFrame(
        {
            "season": [],
            "week": [],
            "TEAM": [],
            "drives": [],
            "plays": [],
            "epa_off_mean": [],
            "success_rate_off": [],
            "epa_def_mean": [],
            "success_rate_def": [],
            "tempo": [],
        },
        schema={
            "season": pl.Int64,
            "week": pl.Int64,
            "TEAM": pl.Utf8,
            "drives": pl.Int64,
            "plays": pl.Int64,
            "epa_off_mean": pl.Float64,
            "success_rate_off": pl.Float64,
            "epa_def_mean": pl.Float64,
            "success_rate_def": pl.Float64,
            "tempo": pl.Float64,
        },
    )

    # create empty L1/L2 artifacts to avoid file-not-found
    path_for("l1", 2025, 8).parent.mkdir(parents=True, exist_ok=True)
    pl.DataFrame(
        {
            "season": pl.Series([], dtype=pl.Int64),
            "week": pl.Series([], dtype=pl.Int64),
            "posteam": pl.Series([], dtype=pl.Utf8),
            "play_type": pl.Series([], dtype=pl.Utf8),
            "yardline_100": pl.Series([], dtype=pl.Float64),
        }
    ).write_parquet(path_for("l1", 2025, 8))

    pl.DataFrame(
        {
            "season": pl.Series([], dtype=pl.Int64),
            "week": pl.Series([], dtype=pl.Int64),
            "game_id": pl.Series([], dtype=pl.Utf8),
            "play_id": pl.Series([], dtype=pl.Int64),
            "TEAM": pl.Series([], dtype=pl.Utf8),
            "OPP": pl.Series([], dtype=pl.Utf8),
            "drive": pl.Series([], dtype=pl.Int64),
            "play_type": pl.Series([], dtype=pl.Utf8),
            "epa": pl.Series([], dtype=pl.Float64),
            "success": pl.Series([], dtype=pl.Float64),
            "yards_gained": pl.Series([], dtype=pl.Float64),
            "success_bin": pl.Series([], dtype=pl.Int64),
        }
    ).write_parquet(path_for("l2", 2025, 8))

    result = core12_compute(empty_l3, 2025, 8)
    assert result.is_empty()
    assert set(result.columns) == {
        "season",
        "week",
        "TEAM",
        "core_epa_off",
        "core_epa_def",
        "core_sr_off",
        "core_sr_def",
        "core_ed_sr_off",
        "core_third_down_conv",
        "core_ypp_diff",
        "core_turnover_margin",
        "core_points_per_drive_diff",
        "core_redzone_td_rate",
        "core_pressure_rate_def",
        "core_explosive_play_rate_off",
    }
