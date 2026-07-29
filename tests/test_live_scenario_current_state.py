import pytest

from live_scenario.state import (
    LiveCurrentState,
    QuarterScore,
    build_current_state_from_quarters,
    margin_bucket_v2,
    mirror_cumulative_state_path,
)


def test_build_current_state_after_q2_from_quarter_points():
    current = build_current_state_from_quarters(
        team_a="BUF",
        opponent="HOU",
        quarter_scores=[(7, 3), (10, 7)],
    )

    assert isinstance(current, LiveCurrentState)
    assert current.team_a == "BUF"
    assert current.opponent == "HOU"
    assert current.completed_quarters == 2
    assert current.quarter_scores == (QuarterScore(7, 3), QuarterScore(10, 7))
    assert current.team_a_quarter_result_path == "WIN-WIN"
    assert current.opponent_quarter_result_path == "LOSS-LOSS"
    assert current.team_a_cumulative_state_path == "LEAD-LEAD"
    assert current.opponent_cumulative_state_path == "TRAIL-TRAIL"
    assert current.team_a_path == "WIN-WIN"
    assert current.opponent_path == "LOSS-LOSS"
    assert current.team_a_score == 17
    assert current.opponent_score == 10
    assert current.margin == 7
    assert current.margin_bucket == "LEADING_1_TO_7"


def test_build_current_state_after_q3_handles_mixed_path_and_margin_bucket():
    current = build_current_state_from_quarters(
        team_a="sf",
        opponent="la",
        quarter_scores=[(7, 3), (0, 10), (14, 3)],
    )

    assert current.team_a == "SF"
    assert current.opponent == "LA"
    assert current.completed_quarters == 3
    assert current.team_a_quarter_result_path == "WIN-LOSS-WIN"
    assert current.opponent_quarter_result_path == "LOSS-WIN-LOSS"
    assert current.team_a_cumulative_state_path == "LEAD-TRAIL-LEAD"
    assert current.opponent_cumulative_state_path == "TRAIL-LEAD-TRAIL"
    assert current.team_a_path == "WIN-LOSS-WIN"
    assert current.opponent_path == "LOSS-WIN-LOSS"
    assert current.team_a_score == 21
    assert current.opponent_score == 16
    assert current.margin == 5
    assert current.margin_bucket == "LEADING_1_TO_7"


def test_build_current_state_handles_tied_quarters_and_tied_game():
    current = build_current_state_from_quarters(
        team_a="DAL",
        opponent="NYG",
        quarter_scores=[(7, 7), (3, 3)],
    )

    assert current.team_a_path == "TIE-TIE"
    assert current.opponent_path == "TIE-TIE"
    assert current.team_a_cumulative_state_path == "TIE-TIE"
    assert current.opponent_cumulative_state_path == "TIE-TIE"
    assert current.team_a_score == 10
    assert current.opponent_score == 10
    assert current.margin == 0
    assert current.margin_bucket == "TIED"


@pytest.mark.parametrize(
    ("margin", "bucket"),
    [
        (-21, "TRAILING_15_PLUS"),
        (-15, "TRAILING_15_PLUS"),
        (-14, "TRAILING_8_TO_14"),
        (-8, "TRAILING_8_TO_14"),
        (-7, "TRAILING_1_TO_7"),
        (-1, "TRAILING_1_TO_7"),
        (0, "TIED"),
        (1, "LEADING_1_TO_7"),
        (7, "LEADING_1_TO_7"),
        (8, "LEADING_8_TO_14"),
        (14, "LEADING_8_TO_14"),
        (15, "LEADING_15_PLUS"),
        (28, "LEADING_15_PLUS"),
    ],
)
def test_margin_bucket_v2_boundaries(margin, bucket):
    assert margin_bucket_v2(margin) == bucket


def test_build_current_state_validates_required_teams_and_scores():
    with pytest.raises(ValueError, match="team_a and opponent"):
        build_current_state_from_quarters(team_a="", opponent="HOU", quarter_scores=[(7, 3)])

    with pytest.raises(ValueError, match="At least one"):
        build_current_state_from_quarters(team_a="BUF", opponent="HOU", quarter_scores=[])

    with pytest.raises(ValueError, match="At most four"):
        build_current_state_from_quarters(
            team_a="BUF",
            opponent="HOU",
            quarter_scores=[(1, 0), (1, 0), (1, 0), (1, 0), (1, 0)],
        )

    with pytest.raises(ValueError, match="cannot be negative"):
        build_current_state_from_quarters(team_a="BUF", opponent="HOU", quarter_scores=[(-1, 0)])


def test_cumulative_state_path_distinguishes_quarter_result_from_game_state():
    current = build_current_state_from_quarters(
        team_a="BUF",
        opponent="HOU",
        quarter_scores=[(7, 3), (3, 7)],
    )

    assert current.team_a_quarter_result_path == "WIN-LOSS"
    assert current.opponent_quarter_result_path == "LOSS-WIN"
    assert current.team_a_cumulative_state_path == "LEAD-TIE"
    assert current.opponent_cumulative_state_path == "TRAIL-TIE"
    assert current.team_a_score == 10
    assert current.opponent_score == 10


def test_mirror_cumulative_state_path():
    assert mirror_cumulative_state_path("LEAD-TIE") == "TRAIL-TIE"
    assert mirror_cumulative_state_path("TRAIL-LEAD-TIE") == "LEAD-TRAIL-TIE"
