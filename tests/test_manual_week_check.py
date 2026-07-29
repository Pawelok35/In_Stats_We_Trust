import json
from pathlib import Path
from types import SimpleNamespace

import polars as pl
import pytest

from app.manual_week_check import run_manual_week_check


def _settings(tmp_path: Path):
    return SimpleNamespace(data_root=tmp_path)


def _write_schedule(root: Path) -> None:
    path = root / "schedules" / "2025.parquet"
    path.parent.mkdir(parents=True)
    pl.DataFrame(
        {
            "season": [2025, 2025],
            "week": [1, 2],
            "home_team": ["BAL", "MIA"],
            "away_team": ["KC", "BUF"],
        }
    ).write_parquet(path)


def _write_lines(path: Path, *, include_duplicate: bool = False) -> None:
    duplicate = (
        """
  - home: "MIA"
    away: "BUF"
    spread: 3.0
    total: 46.5
"""
        if include_duplicate
        else ""
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"""matchups:
  - home: "MIA"
    away: "BUF"
    spread: 3.0
    total: 46.5
{duplicate}""",
        encoding="utf-8",
    )


def _write_results(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "season": 2025,
        "week": 1,
        "home_team": "BAL",
        "away_team": "KC",
        "home_score": 24,
        "away_score": 21,
    }
    path.write_text(json.dumps(record) + "\n", encoding="utf-8")


def test_manual_week_check_passes_for_complete_inputs(tmp_path, monkeypatch):
    monkeypatch.setattr("app.manual_week_check.load_settings", lambda: _settings(tmp_path))
    _write_schedule(tmp_path)
    lines_path = tmp_path / "lines.yaml"
    results_path = tmp_path / "manual_results.jsonl"
    _write_lines(lines_path)
    _write_results(results_path)

    result = run_manual_week_check(
        season=2025,
        week=2,
        manual_results_path=results_path,
        data_root=tmp_path,
        lines_path=lines_path,
    )

    assert result.ok
    assert result.schedule_games == 1
    assert result.lines_games == 1
    assert result.previous_results == 1


def test_manual_week_check_fails_for_missing_line(tmp_path, monkeypatch):
    monkeypatch.setattr("app.manual_week_check.load_settings", lambda: _settings(tmp_path))
    _write_schedule(tmp_path)
    lines_path = tmp_path / "lines.yaml"
    results_path = tmp_path / "manual_results.jsonl"
    lines_path.write_text("matchups: []\n", encoding="utf-8")
    _write_results(results_path)

    result = run_manual_week_check(
        season=2025,
        week=2,
        manual_results_path=results_path,
        data_root=tmp_path,
        lines_path=lines_path,
    )

    assert not result.ok
    assert any("Missing line for scheduled game" in issue.message for issue in result.errors)


def test_manual_week_check_fails_for_duplicate_line_and_missing_result(tmp_path, monkeypatch):
    monkeypatch.setattr("app.manual_week_check.load_settings", lambda: _settings(tmp_path))
    _write_schedule(tmp_path)
    lines_path = tmp_path / "lines.yaml"
    results_path = tmp_path / "manual_results.jsonl"
    _write_lines(lines_path, include_duplicate=True)
    results_path.parent.mkdir(parents=True, exist_ok=True)
    results_path.write_text("", encoding="utf-8")

    result = run_manual_week_check(
        season=2025,
        week=2,
        manual_results_path=results_path,
        data_root=tmp_path,
        lines_path=lines_path,
    )

    assert not result.ok
    messages = [issue.message for issue in result.errors]
    assert any("Duplicate lines matchup" in message for message in messages)
    assert any("Missing previous-week result" in message for message in messages)


def test_manual_week_check_rejects_invalid_week():
    with pytest.raises(ValueError):
        run_manual_week_check(season=2025, week=0)
