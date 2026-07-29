import math

import pytest

from live_scenario import events, state, stats
from scripts import live_quarter_scenario_matrix as legacy


def test_state_helpers_match_legacy_behavior():
    for margin in [-21, -10, -7, -3, -1, 0, 1, 3, 7, 10, 15]:
        assert state.result_from_margin(margin) == legacy.result_from_margin(margin)
        assert state.state_after_margin(margin) == legacy.state_after_margin(margin)
        assert state.margin_bucket_legacy(margin) == legacy.margin_bucket(margin)


def test_spread_and_phase_helpers_match_legacy_behavior():
    for spread in [None, math.nan, 0.5, 1.5, 2, 3, 4.5, 6, 7, 9.5, 13.5, 14]:
        assert state.spread_bucket(spread) == legacy.spread_bucket(spread)
    for week in [0, 1, 5, 6, 11, 12, 18, 22]:
        assert state.season_phase_legacy(week) == legacy.season_phase(week)


def test_path_helpers_match_legacy_for_valid_paths():
    for raw in [None, "", "START", "WIN", "WIN-WIN", "WIN>LOSS>TIE"]:
        assert state.parse_path(raw) == legacy.parse_path(raw)
    for path in [(), ("WIN",), ("WIN", "LOSS"), ("LOSS", "TIE", "WIN")]:
        assert state.path_key(path) == legacy.path_key(path)


def test_new_core_parse_path_raises_value_error_instead_of_system_exit():
    with pytest.raises(ValueError):
        state.parse_path("WIN-BAD")
    with pytest.raises(SystemExit):
        legacy.parse_path("WIN-BAD")


def test_mirror_path_maps_team_a_path_to_opponent_path():
    assert state.mirror_path("START") == "START"
    assert state.mirror_path("WIN-WIN") == "LOSS-LOSS"
    assert state.mirror_path("WIN-LOSS-TIE") == "LOSS-WIN-TIE"
    assert state.mirror_path(("LOSS", "TIE", "WIN")) == "WIN-TIE-LOSS"


def test_stats_helpers_match_legacy_behavior():
    for sample_size in [0, 1, 19, 20, 49, 50, 99, 100]:
        assert stats.sample_quality_legacy(sample_size) == legacy.sample_quality(sample_size)

    for decimal_price in [None, math.nan, 1, 1.5, 1.91, 2, 3.25]:
        assert stats.decimal_to_american(decimal_price) == legacy.decimal_to_american(decimal_price)

    for american_price in [None, math.nan, 0, -200, -110, 100, 250]:
        assert stats.american_to_decimal(american_price) == legacy.american_to_decimal(
            american_price
        )

    for win_probability in [None, 0, 0.25, 0.5, 0.75]:
        assert stats.fair_decimal_no_push(win_probability) == legacy.fair_decimal_no_push(
            win_probability
        )


def test_probability_set_matches_legacy_properties():
    core_set = stats.ProbabilitySet(wins=4, losses=5, ties=1, sample_size=10)
    legacy_set = legacy.ProbabilitySet(wins=4, losses=5, ties=1, sample_size=10)

    assert core_set.win_probability == legacy_set.win_probability
    assert core_set.loss_probability == legacy_set.loss_probability
    assert core_set.tie_probability == legacy_set.tie_probability


def test_event_lookup_matches_legacy_behavior():
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

    for event in [
        "TEAM_A_WIN_NEXT_QUARTER",
        "TEAM_A_LEAD_AFTER_NEXT_QUARTER",
        "TEAM_A_WIN_FINAL",
    ]:
        for settlement in ["TIE_IS_PUSH", "TIE_IS_LOSS"]:
            assert events.event_probability_from_lookup(node, event, settlement) == (
                legacy.event_probability_from_lookup(node, event, settlement)
            )


def test_new_core_event_lookup_raises_value_error_instead_of_system_exit():
    with pytest.raises(ValueError):
        events.event_probability_from_lookup({}, "BAD_EVENT", "TIE_IS_LOSS")
    with pytest.raises(SystemExit):
        legacy.event_probability_from_lookup({}, "BAD_EVENT", "TIE_IS_LOSS")
