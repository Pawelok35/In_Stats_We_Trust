from types import SimpleNamespace

import polars as pl
import pytest
from typer.testing import CliRunner

import app.cli as cli


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(cli.app, ["--help"])

    assert result.exit_code == 0
    assert "Usage:" in result.stdout


def test_build_week_stub_pipeline(tmp_path, monkeypatch):
    raw_dir = tmp_path / "sources"
    season_dir = raw_dir / "2025"
    season_dir.mkdir(parents=True, exist_ok=True)

    pl.DataFrame(
        {
            "game_id": ["G1", "G1"],
            "play_id": [1, 2],
            "posteam": ["BAL", "MIA"],
            "defteam": ["MIA", "BAL"],
            "drive": [1, 1],
            "play_type": ["run", "pass"],
            "epa": [0.1, -0.05],
            "success": [1.0, 0.0],
            "yardline_100": [75.0, 68.0],
            "down": [1, 2],
            "distance": [10, 8],
            "yards_gained": [5.0, 12.0],
            "touchdown": [0, 0],
            "interception": [0, 0],
            "fumble_lost": [0, 0],
            "play_description": [
                "Run for five yards.",
                "Pass complete for twelve yards.",
            ],
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

    stub_settings = SimpleNamespace(
        default_season=2025,
        default_week=8,
        data_root=tmp_path,
        data_sources=SimpleNamespace(
            provider="filesystem",
            filesystem=SimpleNamespace(l1_raw_dir=raw_dir),
        ),
    )

    monkeypatch.setattr(cli, "load_settings", lambda: stub_settings)
    monkeypatch.setattr("etl.l1_ingest.load_settings", lambda *args, **kwargs: stub_settings)
    monkeypatch.setattr("utils.paths.load_settings", lambda *args, **kwargs: stub_settings)
    monkeypatch.setattr("app.reports.load_settings", lambda *args, **kwargs: stub_settings)
    monkeypatch.setattr(
        "app.reports._load_team_state_before_week",
        lambda *args, **kwargs: pl.DataFrame(),
    )

    with pytest.raises(SystemExit) as exc:
        cli.main(["build-week", "--season", "2025", "--week", "1"])

    assert exc.value.code == 0

    assert (tmp_path / "l1" / "2025" / "1.parquet").is_file()
    assert (tmp_path / "l2" / "2025" / "1.parquet").is_file()
    assert (tmp_path / "l3_team_week" / "2025" / "1.parquet").is_file()
    assert (tmp_path / "reports" / "2025_w1_summary.md").is_file()
    report_text = (tmp_path / "reports" / "2025_w1_summary.md").read_text(encoding="utf-8")
    assert "# Weekly Report" in report_text
