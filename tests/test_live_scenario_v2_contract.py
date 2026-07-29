import pytest

from live_scenario.config import (
    DEFAULT_STABILITY_THRESHOLD_PP,
    HISTORICAL_WINDOWS,
    METHODOLOGY_VERSION,
    SAMPLE_UNIT,
    SCHEMA_VERSION,
    SHRINKAGE_PRIOR_WEIGHT,
    STATE_RESULTS,
    TIE_POLICIES,
    V2_MARGIN_BUCKETS,
    V2_SAMPLE_QUALITY_THRESHOLDS,
    V2_SEASON_PHASES,
)
from live_scenario.spread import build_pregame_spread_context
from live_scenario.state import margin_bucket_v2, season_phase_v2


def test_v2_contract_constants_are_explicit():
    assert SCHEMA_VERSION == "live_scenario.v2"
    assert METHODOLOGY_VERSION == "live_scenario_methodology.v1"
    assert SAMPLE_UNIT == "team-game observations"
    assert SHRINKAGE_PRIOR_WEIGHT == 20
    assert DEFAULT_STABILITY_THRESHOLD_PP == 15.0


def test_v2_historical_windows_are_explicit():
    assert HISTORICAL_WINDOWS == {
        "PRIMARY_WINDOW": (2015, 2025),
        "RECENT_WINDOW": (2021, 2025),
        "EXTENDED_WINDOW": (2012, 2025),
    }


def test_v2_tie_policies_are_explicit():
    assert TIE_POLICIES == ("TIE_AS_PUSH", "TIE_AS_LOSS", "THREE_WAY_DISTRIBUTION")


def test_v2_cumulative_state_results_are_explicit():
    assert STATE_RESULTS == ("LEAD", "TRAIL", "TIE")


def test_v2_margin_buckets_are_ordered_contract():
    assert V2_MARGIN_BUCKETS == (
        "TRAILING_15_PLUS",
        "TRAILING_8_TO_14",
        "TRAILING_1_TO_7",
        "TIED",
        "LEADING_1_TO_7",
        "LEADING_8_TO_14",
        "LEADING_15_PLUS",
    )


def test_v2_margin_bucket_function_only_returns_contract_values():
    for margin in range(-35, 36):
        assert margin_bucket_v2(margin) in V2_MARGIN_BUCKETS


def test_v2_pregame_spread_context_contract_fields():
    payload = build_pregame_spread_context(team_a_closing_spread=3.5).to_dict()
    assert tuple(payload.keys()) == (
        "team_a_closing_spread",
        "opponent_closing_spread",
        "team_a_role",
        "exact_spread",
        "spread_bucket",
        "spread_source",
        "spread_captured_at_utc",
        "spread_quality",
    )


def test_v2_sample_quality_threshold_contract():
    assert V2_SAMPLE_QUALITY_THRESHOLDS == {
        "NO_DATA": (None, 0),
        "VERY_LOW": (1, 9),
        "LOW": (10, 29),
        "MODERATE": (30, 74),
        "STRONG": (75, None),
    }


def test_v2_season_phase_contract():
    assert V2_SEASON_PHASES == ("EARLY", "MID", "LATE", "PLAYOFFS")


@pytest.mark.parametrize(
    ("week", "phase"),
    [
        (1, "EARLY"),
        (4, "EARLY"),
        (5, "MID"),
        (12, "MID"),
        (13, "LATE"),
        (18, "LATE"),
    ],
)
def test_season_phase_v2_regular_season_boundaries(week, phase):
    assert season_phase_v2(week) == phase


def test_season_phase_v2_playoffs_are_explicit():
    assert season_phase_v2(19, is_playoff=True) == "PLAYOFFS"
    assert season_phase_v2(22, is_playoff=True) == "PLAYOFFS"


def test_season_phase_v2_rejects_invalid_regular_season_weeks():
    with pytest.raises(ValueError, match=">= 1"):
        season_phase_v2(0)
    with pytest.raises(ValueError, match="Week > 18"):
        season_phase_v2(19)
