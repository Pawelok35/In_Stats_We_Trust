import json
from types import SimpleNamespace

import polars as pl
import pytest

import app.cli as cli
from utils.paths import (
    comparison_report_assets_dir,
    comparison_report_path,
    comparison_reports_manifest_path,
    path_for,
    report_manifest_path,
    team_report_assets_dir,
    team_report_path,
    team_reports_manifest_path,
    weekly_summary_path,
)

TEAM_A = "BAL"
TEAM_B = "MIA"


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


def _prepare_pipeline(tmp_path, monkeypatch):
    raw_root = tmp_path / "sources"
    season_dir = raw_root / "2025"
    season_dir.mkdir(parents=True, exist_ok=True)

    pl.DataFrame(
        {
            "game_id": ["G1", "G1", "G1", "G1", "G2", "G2"],
            "play_id": [1, 2, 3, 4, 1, 2],
            "posteam": [TEAM_A, TEAM_A, TEAM_B, TEAM_B, TEAM_A, TEAM_B],
            "defteam": [TEAM_B, TEAM_B, TEAM_A, TEAM_A, TEAM_B, TEAM_A],
            "drive": [1, 1, 2, 3, 1, 1],
            "play_type": ["run", "pass", "run", "pass", "run", "pass"],
            "epa": [0.3, -0.1, 0.05, -0.2, 0.4, 0.1],
            "success": [1.0, 0.0, 0.5, 0.0, 1.0, 0.5],
            "yardline_100": [75.0, 68.0, 50.0, 43.0, 40.0, 30.0],
            "down": [1, 2, 1, 3, 1, 2],
            "distance": [10, 8, 7, 5, 10, 8],
            "yards_gained": [4.0, 7.0, 5.0, 12.0, 6.0, 9.0],
            "touchdown": [0, 0, 0, 0, 0, 0],
            "interception": [0, 0, 0, 0, 0, 0],
            "fumble_lost": [0, 0, 0, 0, 0, 0],
            "play_description": [
                "Run for four yards.",
                "Short pass incomplete.",
                "Run for five yards.",
                "Deep pass incomplete.",
                "Run for six yards.",
                "Quick pass for nine yards.",
            ],
        }
    ).write_parquet(season_dir / "1.parquet")

    schedule_dir = tmp_path / "schedules"
    schedule_dir.mkdir(parents=True, exist_ok=True)
    pl.DataFrame(
        {
            "season": [2025],
            "week": [1],
            "home_team": [TEAM_A],
            "away_team": [TEAM_B],
        }
    ).write_parquet(schedule_dir / "2025.parquet")

    settings = _settings(tmp_path, raw_root)

    monkeypatch.setattr(cli, "load_settings", lambda: settings)
    monkeypatch.setattr("etl.l1_ingest.load_settings", lambda *args, **kwargs: settings)
    monkeypatch.setattr("app.reports.load_settings", lambda *args, **kwargs: settings)
    monkeypatch.setattr("utils.paths.load_settings", lambda *args, **kwargs: settings)
    monkeypatch.setattr(
        "app.reports._load_team_state_before_week",
        lambda *args, **kwargs: pl.DataFrame(),
    )

    with pytest.raises(SystemExit) as exc:
        cli.main(["build-week", "--season", "2025", "--week", "1"])
    assert exc.value.code == 0

    return settings


def test_build_week_schedule_validation(tmp_path, monkeypatch):
    raw_root = tmp_path / "sources"
    season_dir = raw_root / "2025"
    season_dir.mkdir(parents=True, exist_ok=True)

    pl.DataFrame(
        {
            "game_id": ["G1", "G1", "G1", "G1"],
            "play_id": [1, 2, 3, 4],
            "posteam": [TEAM_A, TEAM_A, TEAM_B, TEAM_B],
            "defteam": [TEAM_B, TEAM_B, TEAM_A, TEAM_A],
            "drive": [1, 1, 2, 3],
            "play_type": ["run", "pass", "run", "pass"],
            "epa": [0.3, -0.1, 0.05, -0.2],
            "success": [1.0, 0.0, 0.5, 0.0],
            "yardline_100": [75.0, 68.0, 50.0, 43.0],
            "down": [1, 2, 1, 3],
            "distance": [10, 8, 7, 5],
            "yards_gained": [4.0, 7.0, 5.0, 12.0],
            "touchdown": [0, 0, 0, 0],
            "interception": [0, 0, 0, 0],
            "fumble_lost": [0, 0, 0, 0],
            "play_description": [
                "Run for four yards.",
                "Short pass incomplete.",
                "Run for five yards.",
                "Deep pass incomplete.",
            ],
        }
    ).write_parquet(season_dir / "1.parquet")

    settings = _settings(tmp_path, raw_root)
    monkeypatch.setattr(cli, "load_settings", lambda: settings)
    monkeypatch.setattr("etl.l1_ingest.load_settings", lambda *args, **kwargs: settings)
    monkeypatch.setattr("app.reports.load_settings", lambda *args, **kwargs: settings)
    monkeypatch.setattr("utils.paths.load_settings", lambda *args, **kwargs: settings)

    with pytest.raises(SystemExit) as exc:
        cli.main(["build-week", "--season", "2025", "--week", "1"])
    assert exc.value.code == 1

    with pytest.raises(SystemExit) as exc:
        cli.main(
            [
                "build-week",
                "--season",
                "2025",
                "--week",
                "1",
                "--no-require-complete-schedule",
            ]
        )
    assert exc.value.code == 0


def test_build_weekly_reports_pairs_only_requires_schedule(tmp_path, monkeypatch):
    settings = _prepare_pipeline(tmp_path, monkeypatch)

    schedule_path = settings.data_root / "schedules" / "2025.parquet"
    schedule_path.unlink()

    with pytest.raises(SystemExit) as exc:
        cli.main(
            [
                "build-weekly-reports",
                "--season",
                "2025",
                "--week",
                "1",
                "--pairs-only",
            ]
        )
    assert exc.value.code == 1


def test_team_report_command(tmp_path, monkeypatch):
    _prepare_pipeline(tmp_path, monkeypatch)

    weekly_manifest = report_manifest_path(2025, 1)
    assert weekly_manifest.exists()
    weekly_payload = json.loads(weekly_manifest.read_text(encoding="utf-8"))
    assert any(entry["path"].endswith("2025_w1_summary.md") for entry in weekly_payload["files"])

    with pytest.raises(SystemExit) as exc:
        cli.main(
            [
                "team-report",
                "--season",
                "2025",
                "--week",
                "1",
                "--team",
                TEAM_A,
            ]
        )
    assert exc.value.code == 0

    report_path = team_report_path(2025, 1, TEAM_A)
    assert report_path.exists()
    content = report_path.read_text(encoding="utf-8")
    assert f"Team Report - {TEAM_A}" in content

    assets_dir = team_report_assets_dir(2025, 1, TEAM_A)
    charts = list(assets_dir.glob("*.png"))
    assert charts

    manifest_path = team_reports_manifest_path(2025, 1)
    assert manifest_path.exists()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert any(entry["path"].endswith(f"{TEAM_A}.md") for entry in manifest["files"])
    assert any(entry["path"].endswith(".png") for entry in manifest["files"])


def test_compare_report_command(tmp_path, monkeypatch):
    _prepare_pipeline(tmp_path, monkeypatch)

    weekly_manifest = report_manifest_path(2025, 1)
    assert weekly_manifest.exists()

    with pytest.raises(SystemExit) as exc:
        cli.main(
            [
                "compare-report",
                "--season",
                "2025",
                "--week",
                "1",
                "--team-a",
                TEAM_A,
                "--team-b",
                TEAM_B,
            ]
        )
    assert exc.value.code == 0

    report_path = comparison_report_path(2025, 1, TEAM_A, TEAM_B)
    assert report_path.exists()
    content = report_path.read_text(encoding="utf-8")
    assert f"Matchup Report - {TEAM_A} vs {TEAM_B}" in content
    assert "## Edge Summary" not in content
    assert "## Metric Comparison" in content
    assert f"| Metric | {TEAM_A} | {TEAM_B} | Δ |" in content
    assert "| PowerScore |" in content
    assert "Yards per Play Differential" in content
    assert "Turnover Margin" in content
    assert "Points per Drive Differential" in content
    assert "Red Zone TD Rate" in content

    assets_dir = comparison_report_assets_dir(2025, 1, TEAM_A, TEAM_B)
    charts = list(assets_dir.glob("*.png"))
    assert charts

    manifest_path = comparison_reports_manifest_path(2025, 1)
    assert manifest_path.exists()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert any(entry["path"].endswith(f"{TEAM_A}_vs_{TEAM_B}.md") for entry in manifest["files"])
    assert any(entry["path"].endswith(".png") for entry in manifest["files"])


def test_compare_report_command_with_edges(tmp_path, monkeypatch):
    _prepare_pipeline(tmp_path, monkeypatch)

    edges_path = path_for("edge_team_vs_team", 2025, 1)
    edges_path.parent.mkdir(parents=True, exist_ok=True)
    pl.DataFrame(
        {
            "team_a": [TEAM_A],
            "team_b": [TEAM_B],
            "metric": ["Explosive Edge"],
            "team_a_value": [0.18],
            "team_b_value": [0.12],
            "delta": [0.06],
        }
    ).write_parquet(edges_path)

    with pytest.raises(SystemExit) as exc:
        cli.main(
            [
                "compare-report",
                "--season",
                "2025",
                "--week",
                "1",
                "--team-a",
                TEAM_A,
                "--team-b",
                TEAM_B,
            ]
        )
    assert exc.value.code == 0

    report_path = comparison_report_path(2025, 1, TEAM_A, TEAM_B)
    content = report_path.read_text(encoding="utf-8")
    assert "## Edge Summary" in content
    assert "Explosive Edge" in content
    assert "↑ +0.060" in content
    assert "## Metric Comparison" in content
    assert f"| Metric | {TEAM_A} | {TEAM_B} | Δ |" in content


def test_build_weekly_reports_command(tmp_path, monkeypatch):
    _prepare_pipeline(tmp_path, monkeypatch)

    with pytest.raises(SystemExit) as exc:
        cli.main(
            [
                "build-weekly-reports",
                "--season",
                "2025",
                "--week",
                "1",
            ]
        )
    assert exc.value.code == 0

    for team in (TEAM_A, TEAM_B):
        report = team_report_path(2025, 1, team)
        assert report.exists()
        assert report.read_text(encoding="utf-8")
        charts = list(team_report_assets_dir(2025, 1, team).glob("*.png"))
        assert charts

    manifest_path = team_reports_manifest_path(2025, 1)
    assert manifest_path.exists()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    paths = {entry["path"] for entry in manifest["files"]}
    assert any(path.endswith(f"{TEAM_A}.md") for path in paths)
    assert any(path.endswith(f"{TEAM_B}.md") for path in paths)

    summary_path = weekly_summary_path(2025, 1)
    assert summary_path.exists()
    summary = summary_path.read_text(encoding="utf-8")
    assert "Weekly Summary" in summary
    assert f"teams/2025_w1/{TEAM_A}.md" in summary
    assert "## PowerScore Movers" in summary


def test_build_weekly_reports_pairs_only(tmp_path, monkeypatch):
    _prepare_pipeline(tmp_path, monkeypatch)

    with pytest.raises(SystemExit) as exc:
        cli.main(
            [
                "build-weekly-reports",
                "--season",
                "2025",
                "--week",
                "1",
                "--pairs-only",
            ]
        )
    assert exc.value.code == 0

    comparison = comparison_report_path(2025, 1, TEAM_A, TEAM_B)
    assert comparison.exists()
    assert comparison.read_text(encoding="utf-8")

    team_report = team_report_path(2025, 1, TEAM_A)
    assert not team_report.exists()

    manifest = comparison_reports_manifest_path(2025, 1)
    assert manifest.exists()
    data = json.loads(manifest.read_text(encoding="utf-8"))
    assert any(entry["path"].endswith(f"{TEAM_A}_vs_{TEAM_B}.md") for entry in data["files"])

    summary_path = weekly_summary_path(2025, 1)
    assert summary_path.exists()
    summary = summary_path.read_text(encoding="utf-8")
    assert "Matchup Reports" in summary
    assert f"comparisons/2025_w1/{TEAM_A}_vs_{TEAM_B}.md" in summary
