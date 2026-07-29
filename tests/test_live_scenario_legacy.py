import math

import pandas as pd
import pytest

from scripts.live_quarter_scenario_matrix import (
    build_team_game_rows,
    event_probability_from_lookup,
    margin_bucket,
    parse_path,
    path_key,
    result_from_margin,
    sample_quality,
)


def _pbp_row(
    *,
    play_id: int,
    qtr: int,
    total_home_score: float,
    total_away_score: float,
    home_score: float = 27,
    away_score: float = 24,
) -> dict:
    return {
        "game_id": "2020_01_HOU_BUF",
        "play_id": play_id,
        "season": 2020,
        "week": 1,
        "qtr": qtr,
        "home_team": "BUF",
        "away_team": "HOU",
        "total_home_score": total_home_score,
        "total_away_score": total_away_score,
        "home_score": home_score,
        "away_score": away_score,
        "spread_line": 2.5,
    }


def _sample_pbp() -> pd.DataFrame:
    return pd.DataFrame(
        [
            _pbp_row(play_id=10, qtr=1, total_home_score=7, total_away_score=3),
            _pbp_row(play_id=20, qtr=2, total_home_score=17, total_away_score=10),
            _pbp_row(play_id=30, qtr=3, total_home_score=20, total_away_score=17),
            _pbp_row(play_id=40, qtr=4, total_home_score=27, total_away_score=24),
        ]
    )


def test_result_from_margin():
    assert result_from_margin(1) == "WIN"
    assert result_from_margin(0) == "TIE"
    assert result_from_margin(-1) == "LOSS"


def test_parse_path_and_path_key():
    assert parse_path("WIN-WIN") == ("WIN", "WIN")
    assert parse_path("WIN>LOSS>TIE") == ("WIN", "LOSS", "TIE")
    assert path_key(("WIN", "LOSS")) == "WIN-LOSS"
    assert path_key(()) == "START"
    with pytest.raises(SystemExit):
        parse_path("WIN-BAD")


def test_legacy_margin_bucket_boundaries():
    assert margin_bucket(3) == "LEAD_1_3"
    assert margin_bucket(7) == "LEAD_4_7"
    assert margin_bucket(0) == "TIE"
    assert margin_bucket(-10) == "TRAIL_8_14"
    assert margin_bucket(15) == "LEAD_15_PLUS"


def test_legacy_sample_quality_thresholds():
    assert sample_quality(0) == "NO_DATA"
    assert sample_quality(1) == "VERY_LOW"
    assert sample_quality(19) == "VERY_LOW"
    assert sample_quality(20) == "LOW"
    assert sample_quality(49) == "LOW"
    assert sample_quality(50) == "MODERATE"
    assert sample_quality(99) == "MODERATE"
    assert sample_quality(100) == "STRONG"


def test_build_team_game_rows_calculates_quarter_path_and_final_state():
    rows = build_team_game_rows(_sample_pbp())
    assert len(rows) == 2

    buf = rows[rows["team"] == "BUF"].iloc[0]
    assert buf["q1_result"] == "WIN"
    assert buf["q2_result"] == "WIN"
    assert buf["q3_result"] == "LOSS"
    assert buf["q4_result"] == "TIE"
    assert buf["path4"] == "WIN-WIN-LOSS-TIE"
    assert buf["after_q2_margin"] == 7
    assert buf["after_q2_margin_bucket"] == "LEAD_4_7"
    assert buf["final_state"] == "WIN"
    assert buf["final_margin"] == 3
    assert buf["role"] == "FAVORITE"

    hou = rows[rows["team"] == "HOU"].iloc[0]
    assert hou["q1_result"] == "LOSS"
    assert hou["q2_result"] == "LOSS"
    assert hou["q3_result"] == "WIN"
    assert hou["q4_result"] == "TIE"
    assert hou["path4"] == "LOSS-LOSS-WIN-TIE"
    assert hou["final_state"] == "LOSS"


def test_quarter_points_sum_to_regulation_score_in_clean_legacy_pbp():
    rows = build_team_game_rows(_sample_pbp())
    buf = rows[rows["team"] == "BUF"].iloc[0]
    hou = rows[rows["team"] == "HOU"].iloc[0]

    assert sum(buf[f"q{idx}_points_for"] for idx in range(1, 5)) == 27
    assert sum(hou[f"q{idx}_points_for"] for idx in range(1, 5)) == 24
    assert buf["after_q4_margin"] == 3
    assert hou["after_q4_margin"] == -3


def test_event_probability_from_lookup_selects_event_blocks_and_tie_policy():
    node = {
        "next_quarter_distribution": {
            "win_probability": 0.4,
            "loss_probability": 0.5,
            "tie_probability": 0.1,
        },
        "cumulative_after_next_quarter": {
            "win_probability": 0.7,
            "loss_probability": 0.2,
            "tie_probability": 0.1,
        },
        "final_including_overtime": {
            "win_probability": 0.8,
            "loss_probability": 0.15,
            "tie_probability": 0.05,
        },
    }

    assert event_probability_from_lookup(
        node,
        "TEAM_A_WIN_NEXT_QUARTER",
        "TIE_IS_PUSH",
    ) == (0.4, 0.5, 0.1)
    assert event_probability_from_lookup(
        node,
        "TEAM_A_LEAD_AFTER_NEXT_QUARTER",
        "TIE_IS_PUSH",
    ) == (0.7, 0.2, 0.1)
    assert event_probability_from_lookup(
        node,
        "TEAM_A_WIN_FINAL",
        "TIE_IS_LOSS",
    ) == (0.8, 0.2, 0.0)


def test_v2_requires_last_non_empty_cumulative_score_within_quarter():
    pbp = pd.DataFrame(
        [
            _pbp_row(play_id=10, qtr=1, total_home_score=7, total_away_score=3),
            _pbp_row(play_id=20, qtr=2, total_home_score=17, total_away_score=10),
            _pbp_row(
                play_id=21,
                qtr=2,
                total_home_score=math.nan,
                total_away_score=math.nan,
            ),
            _pbp_row(play_id=30, qtr=3, total_home_score=20, total_away_score=17),
            _pbp_row(play_id=40, qtr=4, total_home_score=27, total_away_score=24),
        ]
    )

    rows = build_team_game_rows(pbp)
    buf = rows[rows["team"] == "BUF"].iloc[0]

    assert buf["q2_result"] == "WIN"
    assert buf["after_q2_margin"] == 7
