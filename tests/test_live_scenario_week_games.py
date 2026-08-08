from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from live_scenario.week_games import (
    ScheduleLoadError,
    invert_score_pair,
    label_for_active_pick,
    load_week_games,
    season_schedule_snapshot_path,
)


def _write_schedule(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        [
            {
                "game_id": "2026_01_BUF_HOU",
                "season": 2026,
                "game_type": "REG",
                "week": 1,
                "gameday": "2026-09-13",
                "gametime": "13:00",
                "away_team": "BUF",
                "home_team": "HOU",
                "location": "Home",
                "spread_line": -1.5,
            },
            {
                "game_id": "2026_01_MIA_LV",
                "season": 2026,
                "game_type": "REG",
                "week": 1,
                "gameday": "2026-09-13",
                "gametime": "16:25",
                "away_team": "MIA",
                "home_team": "LV",
                "location": "Home",
                "spread_line": None,
            },
            {
                "game_id": "2026_01_GB_MIN",
                "season": 2026,
                "game_type": "REG",
                "week": 1,
                "gameday": "2026-09-13",
                "gametime": "16:25",
                "away_team": "GB",
                "home_team": "MIN",
                "location": "Neutral",
                "spread_line": 1.0,
            },
            {
                "game_id": "2026_01_NE_SEA",
                "season": 2026,
                "game_type": "REG",
                "week": 1,
                "gameday": "2026-09-09",
                "gametime": "20:20",
                "away_team": "NE",
                "home_team": "SEA",
                "location": "Home",
                "spread_line": 3.5,
            },
        ]
    ).to_parquet(path, index=False)


def _write_picks(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        {
            "season": 2026,
            "week": 1,
            "away": "BUF",
            "home": "HOU",
            "tag": "VALUE PLAY",
            "model_winner": "BUF",
            "edge_vs_line": 4.88,
            "model_margin": -6.38,
        },
        {
            "season": 2026,
            "week": 1,
            "away": "MIA",
            "home": "LV",
            "tag": "GOM",
            "model_winner": "MIA",
            "edge_vs_line": 12.71,
            "model_margin": -8.0,
        },
        {
            "season": 2026,
            "week": 1,
            "away": "GB",
            "home": "MIN",
            "tag": "NEUTRAL",
            "model_winner": "GB",
            "edge_vs_line": 1.0,
            "model_margin": -0.5,
        },
    ]
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def test_all_week_games_load_from_schedule_independent_of_pick_file(tmp_path):
    _write_schedule(tmp_path / "schedules" / "2026.parquet")
    picks = tmp_path / "picks.jsonl"
    _write_picks(picks)

    games, metadata = load_week_games(
        data_root=tmp_path,
        season=2026,
        week=1,
        picks_path=picks,
        refresh_if_missing=False,
    )

    assert [game.label for game in games] == ["NE @ SEA", "BUF @ HOU", "GB @ MIN", "MIA @ LV"]
    assert metadata["games_found"] == 4
    assert Path(metadata["schedule_source"]).parts[-2:] == ("schedules", "2026.parquet")


def test_game_without_model_pick_is_available_and_not_blocked(tmp_path):
    _write_schedule(tmp_path / "schedules" / "2026.parquet")
    picks = tmp_path / "picks.jsonl"
    _write_picks(picks)

    games, _ = load_week_games(
        data_root=tmp_path,
        season=2026,
        week=1,
        picks_path=picks,
        refresh_if_missing=False,
    )
    ne_sea = {game.label: game for game in games}["NE @ SEA"]

    assert ne_sea.model_status == "NO MODEL PICK"
    assert ne_sea.perspective("NE").team == "NE"


def test_gom_tag_is_metadata_only_and_game_remains_available(tmp_path):
    _write_schedule(tmp_path / "schedules" / "2026.parquet")
    picks = tmp_path / "picks.jsonl"
    _write_picks(picks)

    games, _ = load_week_games(
        data_root=tmp_path,
        season=2026,
        week=1,
        picks_path=picks,
        refresh_if_missing=False,
    )
    mia_lv = {game.label: game for game in games}["MIA @ LV"]

    assert mia_lv.model_status == "MODEL PICK: MIA / GOM"
    assert mia_lv.perspective("LV").opponent == "MIA"


def test_neutral_no_action_game_remains_available(tmp_path):
    _write_schedule(tmp_path / "schedules" / "2026.parquet")
    picks = tmp_path / "picks.jsonl"
    _write_picks(picks)

    games, _ = load_week_games(
        data_root=tmp_path,
        season=2026,
        week=1,
        picks_path=picks,
        refresh_if_missing=False,
    )
    gb_min = {game.label: game for game in games}["GB @ MIN"]

    assert gb_min.neutral_site is True
    assert gb_min.model_status == "NEUTRAL / NO ACTION"


def test_perspective_flips_team_opponent_and_spread_sign(tmp_path):
    _write_schedule(tmp_path / "schedules" / "2026.parquet")

    games, _ = load_week_games(data_root=tmp_path, season=2026, week=1, refresh_if_missing=False)
    buf_hou = {game.label: game for game in games}["BUF @ HOU"]

    away = buf_hou.perspective("BUF")
    home = buf_hou.perspective("HOU")

    assert away.team == "BUF"
    assert away.opponent == "HOU"
    assert away.side == "away"
    assert away.spread == -1.5
    assert away.role == "FAVORITE"
    assert home.team == "HOU"
    assert home.opponent == "BUF"
    assert home.side == "home"
    assert home.spread == 1.5
    assert home.role == "UNDERDOG"


def test_missing_spread_does_not_block_perspective(tmp_path):
    _write_schedule(tmp_path / "schedules" / "2026.parquet")

    games, _ = load_week_games(data_root=tmp_path, season=2026, week=1, refresh_if_missing=False)
    mia_lv = {game.label: game for game in games}["MIA @ LV"]
    perspective = mia_lv.perspective("MIA")

    assert perspective.spread is None
    assert perspective.role == "PICKEM_OR_UNKNOWN"
    assert mia_lv.spread_status == "MISSING"


def test_use_active_pick_helper_selects_matching_game_without_mutating_pick(tmp_path):
    _write_schedule(tmp_path / "schedules" / "2026.parquet")
    games, _ = load_week_games(data_root=tmp_path, season=2026, week=1, refresh_if_missing=False)
    games_by_label = {game.label: game for game in games}
    record = {"away": "BUF", "home": "HOU", "tag": "VALUE PLAY"}

    assert label_for_active_pick(record, games_by_label) == "BUF @ HOU"
    assert record == {"away": "BUF", "home": "HOU", "tag": "VALUE PLAY"}


def test_quarter_score_pair_inverts_for_perspective_change():
    assert invert_score_pair("10-3") == "3-10"
    assert invert_score_pair("7:0") == "0-7"
    assert invert_score_pair("") == ""
    assert invert_score_pair("bad") == "bad"


def test_manual_entry_still_possible_when_schedule_missing(tmp_path):
    games, metadata = load_week_games(
        data_root=tmp_path,
        season=2026,
        week=1,
        refresh_if_missing=False,
    )

    assert games == []
    assert metadata["games_found"] == 0
    assert metadata["schedule_source"] == "MISSING"


class _RefreshProvider:
    def load_schedules(self, seasons):
        assert seasons == [2026]
        return pd.DataFrame(
            [
                {
                    "game_id": "2026_01_BUF_HOU",
                    "season": 2026,
                    "game_type": "REG",
                    "week": 1,
                    "gameday": "2026-09-13",
                    "gametime": "13:00",
                    "away_team": "BUF",
                    "home_team": "HOU",
                    "location": "Home",
                    "spread_line": -1.5,
                }
            ]
        )


class _FailingRefreshProvider:
    def load_schedules(self, seasons):
        raise RuntimeError(f"offline for {seasons}")


def test_missing_local_2026_refreshes_and_writes_season_snapshot(tmp_path):
    games, metadata = load_week_games(
        data_root=tmp_path,
        season=2026,
        week=1,
        refresh_provider=_RefreshProvider(),
    )

    assert [game.label for game in games] == ["BUF @ HOU"]
    assert season_schedule_snapshot_path(tmp_path, 2026).exists()
    assert Path(metadata["schedule_source"]).name == "schedules_2026.parquet"


def test_refresh_failure_without_local_schedule_raises_clear_error(tmp_path):
    try:
        load_week_games(
            data_root=tmp_path,
            season=2026,
            week=1,
            refresh_provider=_FailingRefreshProvider(),
        )
    except ScheduleLoadError as exc:
        assert "Schedule refresh failed" in str(exc)
        assert "offline" in str(exc)
    else:
        raise AssertionError("ScheduleLoadError was not raised")


def test_current_week_list_does_not_use_historical_processed_dataset(tmp_path):
    processed = tmp_path / "live_scenario" / "processed" / "team_game_scenario_rows.parquet"
    processed.parent.mkdir(parents=True)
    pd.DataFrame(
        [
            {
                "game_id": "historic",
                "season": 2026,
                "week": 1,
                "team": "BUF",
                "opponent": "HOU",
            }
        ]
    ).to_parquet(processed, index=False)

    games, metadata = load_week_games(
        data_root=tmp_path,
        season=2026,
        week=1,
        refresh_if_missing=False,
    )

    assert games == []
    assert metadata["schedule_source"] == "MISSING"


def test_preseason_schedule_is_loaded_separately_from_regular_schedule(tmp_path):
    path = tmp_path / "schedules" / "2026_pre.csv"
    path.parent.mkdir(parents=True)
    pd.DataFrame(
        [
            {
                "game_id": "2026_PRE1_DET_at_CIN",
                "season": 2026,
                "game_type": "PRE",
                "week": 1,
                "gameday": "2026-08-13",
                "gametime": "19:00",
                "away_team": "DET",
                "home_team": "CIN",
                "location": "Home",
            }
        ]
    ).to_csv(path, index=False)

    games, metadata = load_week_games(
        data_root=tmp_path,
        season=2026,
        week=1,
        season_type="PRE",
        refresh_if_missing=False,
    )

    assert [game.label for game in games] == ["DET @ CIN"]
    assert metadata["season_type"] == "PRE"
    assert metadata["schedule_source"].endswith("2026_pre.csv")
