from pathlib import Path

import pandas as pd

from live_scenario.data_provider import processed_dataset_path
from live_scenario.dataset import (
    build_team_game_scenario_rows,
    dataset_status,
    rebuild_processed_dataset,
    save_raw_pbp,
    save_raw_schedules,
    validate_processed_dataset,
)


def _pbp_game(
    *,
    game_id: str,
    season: int,
    week: int,
    home: str = "BUF",
    away: str = "HOU",
    spread_line: float = -3.0,
) -> list[dict]:
    rows = []
    scores = {
        1: (7, 3),
        2: (14, 10),
        3: (20, 17),
        4: (24, 20),
    }
    for qtr, (home_total, away_total) in scores.items():
        rows.append(
            {
                "game_id": game_id,
                "play_id": qtr * 100,
                "qtr": qtr,
                "home_team": home,
                "away_team": away,
                "season": season,
                "week": week,
                "total_home_score": home_total,
                "total_away_score": away_total,
                "home_score": 24,
                "away_score": 20,
                "spread_line": spread_line,
            }
        )
    return rows


def _schedule(game_id: str, *, season: int, week: int, home: str = "BUF", away: str = "HOU"):
    return {
        "game_id": game_id,
        "season": season,
        "game_type": "REG",
        "week": week,
        "gameday": f"{season}-09-10",
        "home_team": home,
        "away_team": away,
        "home_score": 24,
        "away_score": 20,
        "spread_line": -3.0,
    }


def test_build_team_game_rows_creates_two_perspectives_and_reverses_spread():
    pbp = pd.DataFrame(_pbp_game(game_id="2025_01_HOU_BUF", season=2025, week=1))
    schedules = pd.DataFrame([_schedule("2025_01_HOU_BUF", season=2025, week=1)])

    rows, audit = build_team_game_scenario_rows(pbp, schedules, seasons=[2025])

    assert audit["excluded_games"] == []
    assert len(rows) == 2
    home = rows[rows["team"] == "BUF"].iloc[0]
    away = rows[rows["team"] == "HOU"].iloc[0]
    assert home["team_a_closing_spread"] == 3.0
    assert away["team_a_closing_spread"] == -3.0
    assert home["opponent_closing_spread"] == -3.0
    assert away["opponent_closing_spread"] == 3.0
    assert home["team_a_role"] == "UNDERDOG"
    assert away["team_a_role"] == "FAVORITE"
    assert home["q1_result"] == "WIN"
    assert home["q2_result"] == "TIE"
    assert home["after_q2_state_v2"] == "LEAD"
    assert home["after_q2_margin_bucket_v2"] == "LEADING_1_TO_7"
    assert home["final_state"] == "WIN"
    assert home["score_reconciliation_status"] == "MATCH"
    assert home["pbp_after_q4_score"] == "20-24"
    assert home["schedule_final_score"] == "20-24"
    assert bool(home["play_level_events_eligible"]) is True
    assert home["data_quality_warnings"] == []


def test_validate_processed_dataset_rejects_partial_47_rows_and_missing_seasons():
    rows = pd.DataFrame(
        {
            "game_id": [f"g{i//2}" for i in range(47)],
            "season": [2025] * 47,
            "team": [f"T{i}" for i in range(47)],
            "after_q1_team_score": [0] * 47,
            "after_q1_opponent_score": [0] * 47,
            "after_q2_team_score": [0] * 47,
            "after_q2_opponent_score": [0] * 47,
            "after_q3_team_score": [0] * 47,
            "after_q3_opponent_score": [0] * 47,
            "after_q4_team_score": [0] * 47,
            "after_q4_opponent_score": [0] * 47,
            "q1_points_for": [0] * 47,
            "q2_points_for": [0] * 47,
            "q3_points_for": [0] * 47,
            "q4_points_for": [0] * 47,
        }
    )
    schedules = pd.DataFrame([_schedule("g0", season=2025, week=1)])

    validation = validate_processed_dataset(rows, schedules, seasons=list(range(2015, 2026)))

    assert validation["status"] == "FAILED"
    assert "season_2015_missing" in validation["errors"]
    assert "season_2020_missing" in validation["errors"]
    assert any(error.startswith("processed_dataset_too_small") for error in validation["errors"])


def test_rebuild_processed_manifest_and_status(tmp_path: Path):
    seasons = [2025]
    pbp = pd.DataFrame(_pbp_game(game_id="2025_01_HOU_BUF", season=2025, week=1))
    schedules = pd.DataFrame([_schedule("2025_01_HOU_BUF", season=2025, week=1)])
    save_raw_pbp(tmp_path, 2025, pbp, force=True)
    save_raw_schedules(tmp_path, schedules, force=True)

    rows, manifest = rebuild_processed_dataset(
        tmp_path,
        seasons=seasons,
        provider_name="fixture",
        provider_version="test",
    )

    assert processed_dataset_path(tmp_path).exists()
    assert len(rows) == 2
    assert manifest["validation_status"] == "FAILED"
    assert manifest["team_game_observations"] == 2
    assert dataset_status(tmp_path, seasons=seasons).status == "FAILED"


def test_data_cutoff_removes_later_games():
    pbp = pd.DataFrame(
        _pbp_game(game_id="2025_01_HOU_BUF", season=2025, week=1)
        + _pbp_game(game_id="2025_02_HOU_BUF", season=2025, week=2)
    )
    schedules = pd.DataFrame(
        [
            _schedule("2025_01_HOU_BUF", season=2025, week=1),
            {**_schedule("2025_02_HOU_BUF", season=2025, week=2), "gameday": "2025-09-20"},
        ]
    )

    rows, _audit = build_team_game_scenario_rows(
        pbp,
        schedules,
        seasons=[2025],
        data_cutoff_utc="2025-09-15T00:00:00Z",
    )

    assert set(rows["game_id"]) == {"2025_01_HOU_BUF"}
    assert len(rows) == 2
