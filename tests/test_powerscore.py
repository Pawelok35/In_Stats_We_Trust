import json
from types import SimpleNamespace

import polars as pl

from metrics.power_score import compute as ps_compute


def _settings(root):
    return SimpleNamespace(data_root=root)


def test_powerscore_monotonic(tmp_path, monkeypatch):
    monkeypatch.setattr("utils.paths.load_settings", lambda *_, **__: _settings(tmp_path))
    monkeypatch.setattr(
        "metrics.power_score.load_settings",
        lambda: type(
            "Cfg",
            (),
            {
                "weights": {
                    "offense_epa": 0.4,
                    "offense_success_rate": 0.3,
                    "defense_epa": 0.2,
                    "tempo": 0.1,
                }
            },
        )(),
    )

    df_core = pl.DataFrame(
        {
            "season": [2025, 2025],
            "week": [8, 8],
            "TEAM": ["A", "B"],
            "core_epa_off": [0.1, 0.6],
            "core_epa_def": [0.0, 0.0],
            "core_sr_off": [0.2, 0.2],
            "core_sr_def": [0.8, 0.8],
            "core_ed_sr_off": [0.1, 0.2],
            "core_third_down_conv": [0.3, 0.3],
            "core_pressure_rate_def": [0.25, 0.5],
            "core_explosive_play_rate_off": [0.2, 0.4],
            "core_ypp_diff": [0.05, 0.1],
            "core_turnover_margin": [0.0, 1.0],
            "core_points_per_drive_diff": [0.5, 1.2],
            "core_redzone_td_rate": [0.2, 0.3],
        }
    )

    out = ps_compute(df_core, 2025, 8).sort("power_score")
    assert out["power_score"][0] <= out["power_score"][-1]
    assert out.columns == ["season", "week", "team", "power_score"]
    assert all(code.isupper() for code in out["team"])

    manifest_path = tmp_path / "l4_powerscore" / "2025" / "8_manifest.json"
    assert manifest_path.exists()
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert payload["layer"] == "l4_powerscore"
    assert payload["rows"] == 2
