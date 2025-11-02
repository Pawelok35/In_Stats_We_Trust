from types import SimpleNamespace

import pytest

from utils.config import Settings, load_settings
from utils.paths import path_for, report_path


def test_load_settings_defaults(tmp_path, monkeypatch):
    fallback_config = tmp_path / "settings.yaml"
    fallback_config.write_text(
        """
DATA_ROOT: data
default_season: 2025
default_week: 8
data_sources:
  provider: nfl_data_py
  filesystem:
    l1_raw_dir: data/sources/nfl
weights:
  offense_epa: 0.35
""",
        encoding="utf-8",
    )
    monkeypatch.setattr("utils.config.DEFAULT_SETTINGS_PATH", fallback_config)

    settings = load_settings(force_reload=True)
    assert isinstance(settings, Settings)
    assert settings.default_season == 2025
    assert settings.data_sources.provider == "nfl_data_py"


def test_path_helpers_use_data_root(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "utils.paths.load_settings",
        lambda: SimpleNamespace(data_root=tmp_path),
    )

    artifact = path_for("l1", 2024, 3)
    manifest = path_for("l2", 2024, 3, suffix=".parquet")
    report = report_path(2024, 3)

    assert artifact == tmp_path / "l1" / "2024" / "3.parquet"
    assert manifest.parent.is_dir()
    assert report == tmp_path / "reports" / "2024_w3_summary.md"


@pytest.mark.parametrize("season,week", [(-1, 1), (1, 0)])
def test_path_for_validates_inputs(monkeypatch, tmp_path, season, week):
    monkeypatch.setattr(
        "utils.paths.load_settings",
        lambda: SimpleNamespace(data_root=tmp_path),
    )

    with pytest.raises(ValueError):
        path_for("l1", season, week)
