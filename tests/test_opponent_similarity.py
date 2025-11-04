from types import SimpleNamespace

import polars as pl
import pytest

from metrics.opponent_similarity import compute_team_analogs


def _settings(tmp_path, weights=None):
    return SimpleNamespace(
        data_root=tmp_path,
        analog_profile_weights=weights or {"core_epa_off": 0.6, "core_sr_off": 0.4},
    )


def test_compute_team_analogs_prioritizes_closest_profile(tmp_path, monkeypatch):
    settings = _settings(tmp_path)
    monkeypatch.setattr("metrics.opponent_similarity.load_settings", lambda *args, **kwargs: settings)
    monkeypatch.setattr("utils.paths.load_settings", lambda *args, **kwargs: settings)
    monkeypatch.setattr(
        "metrics.opponent_similarity.rolling_core12_through_path",
        lambda season, through_week: str(
            tmp_path / "rolling_core12" / f"{season}" / f"through_{through_week}.parquet"
        ),
    )

    schedule_dir = tmp_path / "schedules"
    schedule_dir.mkdir(parents=True, exist_ok=True)
    pl.DataFrame(
        {
            "week": [1, 2, 3],
            "home_team": ["TEAM_A", "TEAM_D", "TEAM_X"],
            "away_team": ["TEAM_C", "TEAM_A", "TEAM_Y"],
        }
    ).write_parquet(schedule_dir / "2025.parquet")

    roll_dir = tmp_path / "rolling_core12" / "2025"
    roll_dir.mkdir(parents=True, exist_ok=True)
    pl.DataFrame(
        {
            "TEAM": ["TEAM_B", "TEAM_C", "TEAM_D"],
            "season": [2025, 2025, 2025],
            "through_week": [3, 3, 3],
            "core_epa_off": [0.20, 0.18, -0.35],
            "core_sr_off": [0.52, 0.51, 0.37],
        }
    ).write_parquet(roll_dir / "through_3.parquet")

    l3_dir = tmp_path / "l3_team_week" / "2025"
    l3_dir.mkdir(parents=True, exist_ok=True)
    pl.DataFrame(
        {
            "season": [2025],
            "week": [1],
            "TEAM": ["TEAM_A"],
            "epa_off_mean": [0.12],
            "success_rate_off": [0.55],
            "points_per_drive_diff": [0.40],
            "drives": [10],
            "points_per_drive_off": [2.0],
            "points_per_drive_def": [1.6],
        }
    ).write_parquet(l3_dir / "1.parquet")
    pl.DataFrame(
        {
            "season": [2025],
            "week": [2],
            "TEAM": ["TEAM_A"],
            "epa_off_mean": [0.05],
            "success_rate_off": [0.48],
            "points_per_drive_diff": [-0.10],
            "drives": [12],
            "points_per_drive_off": [1.3],
            "points_per_drive_def": [1.4],
        }
    ).write_parquet(l3_dir / "2.parquet")

    analogs = compute_team_analogs(
        season=2025,
        current_week=4,
        team="TEAM_A",
        target_opponent="TEAM_B",
    )

    assert analogs
    primary = analogs[0]
    assert primary.opponent == "TEAM_C"
    assert primary.week == 1
    assert primary.location == "home"
    assert primary.epa_off == pytest.approx(0.12)
    assert primary.success_rate == pytest.approx(0.55)
    assert primary.points_per_drive_diff == pytest.approx(0.40)
    assert primary.points_for == pytest.approx(20.0)
    assert primary.points_against == pytest.approx(16.0)
    assert primary.winner == "TEAM_A"


def test_compute_team_analogs_handles_missing_schedule(tmp_path, monkeypatch):
    settings = _settings(tmp_path)
    monkeypatch.setattr("metrics.opponent_similarity.load_settings", lambda *args, **kwargs: settings)
    monkeypatch.setattr("utils.paths.load_settings", lambda *args, **kwargs: settings)
    monkeypatch.setattr(
        "metrics.opponent_similarity.rolling_core12_through_path",
        lambda season, through_week: str(
            tmp_path / "rolling_core12" / f"{season}" / f"through_{through_week}.parquet"
        ),
    )

    roll_dir = tmp_path / "rolling_core12" / "2025"
    roll_dir.mkdir(parents=True, exist_ok=True)
    pl.DataFrame(
        {
            "TEAM": ["TEAM_B"],
            "season": [2025],
            "through_week": [3],
            "core_epa_off": [0.20],
            "core_sr_off": [0.52],
        }
    ).write_parquet(roll_dir / "through_3.parquet")

    analogs = compute_team_analogs(
        season=2025,
        current_week=4,
        team="TEAM_A",
        target_opponent="TEAM_B",
    )
    assert analogs == []


def test_compute_team_analogs_uses_l2_fallback(tmp_path, monkeypatch):
    settings = _settings(tmp_path)
    monkeypatch.setattr("metrics.opponent_similarity.load_settings", lambda *args, **kwargs: settings)
    monkeypatch.setattr("utils.paths.load_settings", lambda *args, **kwargs: settings)
    monkeypatch.setattr(
        "metrics.opponent_similarity.rolling_core12_through_path",
        lambda season, through_week: str(
            tmp_path / "rolling_core12" / f"{season}" / f"through_{through_week}.parquet"
        ),
    )

    # No schedule written -> forces fallback.

    roll_dir = tmp_path / "rolling_core12" / "2025"
    roll_dir.mkdir(parents=True, exist_ok=True)
    pl.DataFrame(
        {
            "TEAM": ["TEAM_B", "TEAM_C", "TEAM_D"],
            "season": [2025, 2025, 2025],
            "through_week": [3, 3, 3],
            "core_epa_off": [0.20, 0.205, 0.18],
            "core_sr_off": [0.52, 0.521, 0.49],
        }
    ).write_parquet(roll_dir / "through_3.parquet")

    l2_dir = tmp_path / "l2" / "2025"
    l2_dir.mkdir(parents=True, exist_ok=True)
    pl.DataFrame(
        {
            "posteam": ["TEAM_A", "TEAM_C", "TEAM_A", "TEAM_D"],
            "defteam": ["TEAM_C", "TEAM_A", "TEAM_D", "TEAM_A"],
        }
    ).write_parquet(l2_dir / "1.parquet")
    pl.DataFrame(
        {
            "posteam": ["TEAM_A", "TEAM_E"],
            "defteam": ["TEAM_E", "TEAM_A"],
        }
    ).write_parquet(l2_dir / "2.parquet")

    l3_dir = tmp_path / "l3_team_week" / "2025"
    l3_dir.mkdir(parents=True, exist_ok=True)
    pl.DataFrame(
        {
            "season": [2025],
            "week": [1],
            "TEAM": ["TEAM_A"],
            "epa_off_mean": [0.1],
            "success_rate_off": [0.5],
            "points_per_drive_diff": [0.2],
            "drives": [9],
            "points_per_drive_off": [1.8],
            "points_per_drive_def": [1.6],
        }
    ).write_parquet(l3_dir / "1.parquet")
    pl.DataFrame(
        {
            "season": [2025],
            "week": [2],
            "TEAM": ["TEAM_A"],
            "epa_off_mean": [-0.05],
            "success_rate_off": [0.45],
            "points_per_drive_diff": [-0.3],
            "drives": [11],
            "points_per_drive_off": [1.2],
            "points_per_drive_def": [1.5],
        }
    ).write_parquet(l3_dir / "2.parquet")

    analogs = compute_team_analogs(
        season=2025,
        current_week=4,
        team="TEAM_A",
        target_opponent="TEAM_B",
    )

    assert analogs
    assert any(match.opponent in {"TEAM_C", "TEAM_D", "TEAM_E"} for match in analogs)
