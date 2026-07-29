import pytest

from live_scenario.spread import build_pregame_spread_context, role_from_team_a_spread


def test_role_from_team_a_spread():
    assert role_from_team_a_spread(-3.0) == "FAVORITE"
    assert role_from_team_a_spread(3.5) == "UNDERDOG"
    assert role_from_team_a_spread(0.0) == "PICKEM"
    assert role_from_team_a_spread(None) == "UNKNOWN"


def test_build_pregame_spread_context_from_team_a_perspective():
    context = build_pregame_spread_context(
        team_a_closing_spread=-3.0,
        team_a_role="FAVORITE",
        spread_source="PREGAME_COM",
        spread_captured_at_utc="2026-09-10T00:00:00Z",
        spread_quality="displayed_unverified",
    )

    assert context.team_a_closing_spread == -3.0
    assert context.opponent_closing_spread == 3.0
    assert context.team_a_role == "FAVORITE"
    assert context.exact_spread == 3.0
    assert context.spread_bucket == "FAV_2-3"
    assert context.spread_source == "PREGAME_COM"
    assert context.spread_captured_at_utc == "2026-09-10T00:00:00Z"
    assert context.spread_quality == "DISPLAYED_UNVERIFIED"


def test_build_pregame_spread_context_rejects_conflicting_manual_role():
    with pytest.raises(ValueError, match="conflicts"):
        build_pregame_spread_context(team_a_closing_spread=-3.0, team_a_role="UNDERDOG")


def test_build_pregame_spread_context_allows_unknown_spread():
    context = build_pregame_spread_context()
    assert context.team_a_closing_spread is None
    assert context.opponent_closing_spread is None
    assert context.team_a_role == "UNKNOWN"
    assert context.exact_spread is None
    assert context.spread_bucket == "UNKNOWN"
    assert context.spread_quality == "UNKNOWN"
