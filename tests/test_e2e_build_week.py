import json
from types import SimpleNamespace

import polars as pl
import pytest

import app.cli as cli
from utils.paths import (
    l2_audit_path,
    manifest_path,
    path_for,
    report_assets_dir,
    report_manifest_path,
    report_path,
)


def _settings(tmp_path, raw_root):
    return SimpleNamespace(
        default_season=2025,
        default_week=1,
        data_root=tmp_path,
        data_sources=SimpleNamespace(
            provider="filesystem",
            filesystem=SimpleNamespace(l1_raw_dir=raw_root),
        ),
    )


def test_build_week_end_to_end(tmp_path, monkeypatch):
    raw_root = tmp_path / "sources"
    season_dir = raw_root / "2025"
    season_dir.mkdir(parents=True, exist_ok=True)

    pl.DataFrame(
        {
            "game_id": ["G1", "G1", "G1", "G1"],
            "play_id": [1, 2, 3, 4],
            "posteam": ["AAA", "AAA", "BBB", "BBB"],
            "defteam": ["BBB", "BBB", "AAA", "AAA"],
            "drive": [1, 1, 2, 3],
            "play_type": ["run", "pass", "run", "pass"],
            "epa": [0.3, -0.1, 0.05, -0.2],
            "success": [1.0, 0.0, 0.5, 0.0],
            "yardline_100": [75.0, 68.0, 50.0, 43.0],
            "down": [1, 2, 1, 3],
            "distance": [10, 8, 7, 5],
        }
    ).write_parquet(season_dir / "1.parquet")

    schedule_dir = tmp_path / "schedules"
    schedule_dir.mkdir(parents=True, exist_ok=True)
    pl.DataFrame(
        {
            "season": [2025],
            "week": [1],
            "home_team": ["BAL"],
            "away_team": ["MIA"],
        }
    ).write_parquet(schedule_dir / "2025.parquet")

    settings = _settings(tmp_path, raw_root)
    monkeypatch.setattr(cli, "load_settings", lambda: settings)
    monkeypatch.setattr("etl.l1_ingest.load_settings", lambda *args, **kwargs: settings)
    monkeypatch.setattr("app.reports.load_settings", lambda *args, **kwargs: settings)
    monkeypatch.setattr("utils.paths.load_settings", lambda *args, **kwargs: settings)

    with pytest.raises(SystemExit) as exc:
        cli.main(["build-week", "--season", "2025", "--week", "1"])
    assert exc.value.code == 0

    artifacts = [
        ("l1", path_for("l1", 2025, 1)),
        ("l2", path_for("l2", 2025, 1)),
        ("l3_team_week", path_for("l3_team_week", 2025, 1)),
    ]

    for layer, artifact in artifacts:
        assert artifact.exists()
        manifest = manifest_path(layer, 2025, 1)
        assert manifest.exists()
        payload = json.loads(manifest.read_text(encoding="utf-8"))
        assert payload["layer"] == layer
        assert payload["rows"] > 0
        assert payload["sha256"]

    l3_df = pl.read_parquet(path_for("l3_team_week", 2025, 1))
    assert set(l3_df["TEAM"]) == {"BAL", "MIA"}
    assert "tempo" in l3_df.columns

    audit_file = l2_audit_path(2025, 1)
    assert audit_file.exists()
    audit_lines = audit_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(audit_lines) >= 3

    report = report_path(2025, 1)
    assert report.exists()
    report_text = report.read_text(encoding="utf-8")
    assert "Weekly Report" in report_text
    assets_dir = report_assets_dir(2025, 1)
    assert assets_dir.exists()
    chart_files = list(assets_dir.glob("*.png"))
    assert chart_files
    assert "assets" in chart_files[0].as_posix()
    assert ("PowerScore Top 10" in report_text) or ("L3 Tempo Leaders" in report_text)

    report_manifest = report_manifest_path(2025, 1)
    assert report_manifest.exists()
    manifest_payload = json.loads(report_manifest.read_text(encoding="utf-8"))
    assert any(entry["path"].endswith("2025_w1_summary.md") for entry in manifest_payload["files"])
    assert all("sha256" in entry for entry in manifest_payload["files"])
