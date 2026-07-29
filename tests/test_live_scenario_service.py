import pandas as pd
import pytest

from live_scenario.config import METHODOLOGY_VERSION, SAMPLE_UNIT, SCHEMA_VERSION
from live_scenario.service import build_basic_after_q_report
from live_scenario.spread import build_pregame_spread_context
from live_scenario.state import build_current_state_from_quarters


def _row(
    *,
    game_id: str,
    season: int,
    team: str,
    q1: str,
    q2: str,
    bucket: str,
    final: str,
    role: str = "FAVORITE",
    spread_bucket: str = "2-3",
    team_a_closing_spread: float | None = None,
) -> dict:
    state_map = {
        "LEADING_1_TO_7": "LEAD",
        "LEADING_8_TO_14": "LEAD",
        "LEADING_15_PLUS": "LEAD",
        "TRAILING_1_TO_7": "TRAIL",
        "TRAILING_8_TO_14": "TRAIL",
        "TRAILING_15_PLUS": "TRAIL",
        "TIED": "TIE",
    }
    return {
        "game_id": game_id,
        "season": season,
        "team": team,
        "q1_result": q1,
        "q2_result": q2,
        "after_q1_state_v2": "LEAD" if q1 == "WIN" else "TRAIL" if q1 == "LOSS" else "TIE",
        "after_q2_state_v2": state_map[bucket],
        "after_q2_margin_bucket_v2": bucket,
        "role": role,
        "spread_bucket": spread_bucket,
        "team_a_closing_spread": team_a_closing_spread,
        "final_state": final,
    }


def _history() -> pd.DataFrame:
    return pd.DataFrame(
        [
            _row(
                game_id="g1",
                season=2020,
                team="BUF",
                q1="WIN",
                q2="WIN",
                bucket="LEADING_1_TO_7",
                final="WIN",
            ),
            _row(
                game_id="g2",
                season=2021,
                team="BUF",
                q1="WIN",
                q2="WIN",
                bucket="LEADING_1_TO_7",
                final="LOSS",
            ),
            _row(
                game_id="g3",
                season=2022,
                team="KC",
                q1="WIN",
                q2="WIN",
                bucket="LEADING_1_TO_7",
                final="WIN",
            ),
            _row(
                game_id="g4",
                season=2023,
                team="MIA",
                q1="WIN",
                q2="WIN",
                bucket="LEADING_1_TO_7",
                final="WIN",
                role="UNDERDOG",
                spread_bucket="2-3",
            ),
            _row(
                game_id="g5",
                season=2020,
                team="HOU",
                q1="LOSS",
                q2="LOSS",
                bucket="TRAILING_1_TO_7",
                final="LOSS",
            ),
            _row(
                game_id="g6",
                season=2021,
                team="HOU",
                q1="LOSS",
                q2="LOSS",
                bucket="TRAILING_1_TO_7",
                final="WIN",
            ),
            _row(
                game_id="g7",
                season=2024,
                team="PHI",
                q1="WIN",
                q2="LOSS",
                bucket="TIED",
                final="WIN",
                role="PICKEM",
                spread_bucket="PK_0.5-1.5",
            ),
            _row(
                game_id="g8",
                season=2024,
                team="BUF",
                q1="WIN",
                q2="WIN",
                bucket="LEADING_8_TO_14",
                final="WIN",
            ),
            _row(
                game_id="g9",
                season=2024,
                team="CIN",
                q1="WIN",
                q2="WIN",
                bucket="LEADING_8_TO_14",
                final="LOSS",
            ),
        ]
    )


def _current_state():
    return build_current_state_from_quarters(
        team_a="BUF",
        opponent="HOU",
        quarter_scores=[(7, 3), (10, 7)],
    )


def test_basic_after_q_report_contract_and_current_state():
    report = build_basic_after_q_report(
        current_state=_current_state(),
        historical_rows=_history(),
        data_cutoff_utc="2026-09-10T00:00:00Z",
        generated_at_utc="2026-09-10T00:01:00Z",
    )

    assert report.schema_version == SCHEMA_VERSION
    assert report.methodology_version == METHODOLOGY_VERSION
    assert report.sample_unit == SAMPLE_UNIT
    assert report.generated_at_utc == "2026-09-10T00:01:00Z"
    assert report.data_cutoff_utc == "2026-09-10T00:00:00Z"
    assert report.seasons_included == (2020, 2021, 2022, 2023, 2024)
    assert report.games_included == 9
    assert report.current_state == {
        "team_a": "BUF",
        "opponent": "HOU",
        "completed_quarters": 2,
        "team_a_quarter_result_path": "WIN-WIN",
        "opponent_quarter_result_path": "LOSS-LOSS",
        "team_a_cumulative_state_path": "LEAD-LEAD",
        "opponent_cumulative_state_path": "TRAIL-TRAIL",
        "team_a_path": "WIN-WIN",
        "opponent_path": "LOSS-LOSS",
        "team_a_score": 17,
        "opponent_score": 10,
        "margin": 7,
        "margin_bucket": "LEADING_1_TO_7",
    }
    assert report.pregame_spread_context == {
        "team_a_closing_spread": None,
        "opponent_closing_spread": None,
        "team_a_role": "UNKNOWN",
        "exact_spread": None,
        "spread_bucket": "UNKNOWN",
        "spread_source": None,
        "spread_captured_at_utc": None,
        "spread_quality": "UNKNOWN",
    }
    assert report.broad_baseline_without_spread["name"] == "no_spread_baseline"
    assert report.broad_baseline_without_spread["sample_size"] == 4
    assert report.spread_conditioned_baseline["selected_level"] == "no_spread_baseline"


def test_report_layers_keep_league_team_and_opponent_separate():
    report = build_basic_after_q_report(
        current_state=_current_state(),
        historical_rows=_history(),
        data_cutoff_utc="2026-09-10T00:00:00Z",
    )

    assert report.league_baseline.name == "league_baseline"
    assert report.league_baseline.filters_applied == ("cumulative_state_path", "margin_bucket")
    assert report.league_baseline.sample_size == 4
    assert report.league_baseline.wins == 3
    assert report.league_baseline.losses == 1
    assert report.league_baseline.raw_probability == 0.75
    assert report.opponent_league_reference.name == "opponent_league_reference"
    assert report.opponent_league_reference.sample_size == 2
    assert report.opponent_league_reference.wins == 1
    assert report.opponent_league_reference.losses == 1
    assert report.opponent_league_reference.raw_probability == 0.5

    assert report.team_a_history.name == "team_a_history"
    assert report.team_a_history.sample_size == 2
    assert report.team_a_history.wins == 1
    assert report.team_a_history.losses == 1
    assert report.team_a_history.raw_probability == 0.5
    assert report.team_a_history.delta_vs_league_pp == -25.0

    assert report.opponent_recovery_history.name == "opponent_recovery_history"
    assert report.opponent_recovery_history.sample_size == 2
    assert report.opponent_recovery_history.wins == 1
    assert report.opponent_recovery_history.losses == 1
    assert report.opponent_recovery_history.raw_probability == 0.5
    assert report.opponent_recovery_history.opponent_league_reference_probability == 0.5
    assert report.opponent_recovery_history.raw_delta_vs_opponent_league_pp == 0.0
    assert report.opponent_recovery_history.adjusted_probability == 0.5
    assert report.opponent_recovery_history.adjusted_delta_vs_opponent_league_pp == 0.0
    assert report.opponent_recovery_history.delta_vs_league_pp is None
    assert report.opponent_recovery_history.adjusted_probability != 0.727273

    payload = report.to_dict()
    assert "combined_probability" not in payload


def test_market_comparison_uses_league_baseline_as_primary_reference():
    report = build_basic_after_q_report(
        current_state=_current_state(),
        historical_rows=_history(),
        data_cutoff_utc="2026-09-10T00:00:00Z",
        team_a_live_decimal=1.8,
        opponent_live_decimal=2.2,
    )

    market = report.market_comparison
    assert market.market_available
    assert market.primary_probability_source == "league_baseline"
    assert market.tie_policy == "TIE_AS_LOSS"
    assert market.adjusted_historical_probability == 0.75
    assert market.historical_win_probability == 0.75
    assert market.historical_loss_probability == 0.25
    assert market.historical_tie_probability == 0
    assert market.team_a_implied_probability == pytest.approx(0.5555555556)
    assert market.opponent_implied_probability == pytest.approx(0.4545454545)
    assert market.team_a_no_vig_probability == pytest.approx(0.55)
    assert market.opponent_no_vig_probability == pytest.approx(0.45)
    assert market.historical_break_even_price == pytest.approx(1.3333333333)
    assert market.edge_vs_market_pp == 20.0
    assert market.estimated_ev == 0.35


def test_market_comparison_supports_tie_as_push_ev():
    history = pd.concat(
        [
            _history(),
            pd.DataFrame(
                [
                    _row(
                        game_id="g10",
                        season=2025,
                        team="LAC",
                        q1="WIN",
                        q2="WIN",
                        bucket="LEADING_1_TO_7",
                        final="TIE",
                    )
                ]
            ),
        ],
        ignore_index=True,
    )
    report = build_basic_after_q_report(
        current_state=_current_state(),
        historical_rows=history,
        data_cutoff_utc="2026-09-10T00:00:00Z",
        team_a_live_decimal=1.8,
        tie_policy="TIE_AS_PUSH",
    )

    market = report.market_comparison
    assert market.tie_policy == "TIE_AS_PUSH"
    assert market.adjusted_historical_probability == 0.6
    assert market.historical_loss_probability == 0.2
    assert market.historical_tie_probability == 0.2
    assert market.historical_break_even_price == pytest.approx(1.3333333333)
    assert market.estimated_ev == 0.28


def test_market_comparison_validates_tie_policy_and_decimal_prices():
    with pytest.raises(ValueError, match="Unsupported tie_policy"):
        build_basic_after_q_report(
            current_state=_current_state(),
            historical_rows=_history(),
            data_cutoff_utc="2026-09-10T00:00:00Z",
            tie_policy="BAD_POLICY",
        )

    with pytest.raises(ValueError, match="team_a_live_decimal"):
        build_basic_after_q_report(
            current_state=_current_state(),
            historical_rows=_history(),
            data_cutoff_utc="2026-09-10T00:00:00Z",
            team_a_live_decimal=1.0,
        )


def test_report_contains_required_warnings_and_reliability_blocks():
    report = build_basic_after_q_report(
        current_state=_current_state(),
        historical_rows=_history(),
        data_cutoff_utc="2026-09-10T00:00:00Z",
    )

    assert "Historical context only. No automatic betting recommendation." in report.warnings
    assert (
        "Historical live profitability cannot be validated without archived live market prices."
        in report.warnings
    )
    assert report.sample_and_reliability.exact_filtered_match["sample_size"] == 2
    assert report.sample_and_reliability.expanded_team_match["sample_size"] == 3
    assert report.sample_and_reliability.contextual_league_match["sample_size"] == 4
    assert report.sample_and_reliability.broad_league_baseline["sample_size"] == 6


def test_expanded_sample_levels_show_applied_and_relaxed_filters():
    report = build_basic_after_q_report(
        current_state=_current_state(),
        historical_rows=_history(),
        data_cutoff_utc="2026-09-10T00:00:00Z",
    )
    reliability = report.sample_and_reliability

    assert reliability.exact_filtered_match["filters_applied"] == [
        "team",
        "cumulative_state_path",
        "margin_bucket",
    ]
    assert reliability.exact_filtered_match["filters_relaxed"] == []
    assert reliability.exact_filtered_match["wins"] == 1
    assert reliability.exact_filtered_match["losses"] == 1

    assert reliability.expanded_team_match["filters_applied"] == ["team", "cumulative_state_path"]
    assert reliability.expanded_team_match["filters_relaxed"] == ["margin_bucket"]
    assert reliability.expanded_team_match["wins"] == 2
    assert reliability.expanded_team_match["losses"] == 1

    assert reliability.contextual_league_match["filters_applied"] == [
        "cumulative_state_path",
        "margin_bucket",
    ]
    assert reliability.contextual_league_match["filters_relaxed"] == ["team"]

    assert reliability.broad_league_baseline["filters_applied"] == ["cumulative_state_path"]
    assert reliability.broad_league_baseline["filters_relaxed"] == [
        "team",
        "margin_bucket",
    ]
    assert reliability.broad_league_baseline["wins"] == 4
    assert reliability.broad_league_baseline["losses"] == 2
    assert reliability.spread_filter_levels["no_spread_baseline"]["sample_size"] == 4


def test_spread_conditioned_baseline_selects_exact_spread_when_available():
    history = _history()
    history.loc[0, "team_a_closing_spread"] = -3.0
    history.loc[1, "team_a_closing_spread"] = -3.0
    report = build_basic_after_q_report(
        current_state=_current_state(),
        historical_rows=history,
        data_cutoff_utc="2026-09-10T00:00:00Z",
        pregame_spread_context=build_pregame_spread_context(
            team_a_closing_spread=-3.0,
            team_a_role="FAVORITE",
        ),
    )

    levels = report.sample_and_reliability.spread_filter_levels
    assert levels["exact_spread_match"]["sample_size"] == 2
    assert levels["spread_bucket_match"]["sample_size"] == 3
    assert levels["role_only_match"]["sample_size"] == 3
    assert levels["no_spread_baseline"]["sample_size"] == 4
    assert report.spread_conditioned_baseline["selected_level"] == "exact_spread_match"
    assert report.spread_conditioned_baseline["raw_probability"] == 0.5


def test_spread_conditioned_baseline_relaxes_to_bucket_then_role_then_no_spread():
    report = build_basic_after_q_report(
        current_state=_current_state(),
        historical_rows=_history().drop(columns=["team_a_closing_spread"]),
        data_cutoff_utc="2026-09-10T00:00:00Z",
        pregame_spread_context=build_pregame_spread_context(
            team_a_closing_spread=-3.0,
            team_a_role="FAVORITE",
        ),
    )

    levels = report.sample_and_reliability.spread_filter_levels
    assert levels["exact_spread_match"]["sample_size"] == 0
    assert levels["exact_spread_match"]["missing_columns"] == ["team_a_closing_spread"]
    assert levels["spread_bucket_match"]["sample_size"] == 3
    assert levels["role_only_match"]["sample_size"] == 3
    assert levels["no_spread_baseline"]["sample_size"] == 4
    assert report.spread_conditioned_baseline["selected_level"] == "spread_bucket_match"
    assert report.spread_conditioned_baseline["filters_relaxed"] == ["exact_spread"]


def test_spread_conditioned_baseline_falls_back_to_no_spread_when_role_missing():
    history = _history().drop(columns=["team_a_closing_spread", "role", "spread_bucket"])
    report = build_basic_after_q_report(
        current_state=_current_state(),
        historical_rows=history,
        data_cutoff_utc="2026-09-10T00:00:00Z",
        pregame_spread_context=build_pregame_spread_context(
            team_a_closing_spread=-3.0,
            team_a_role="FAVORITE",
        ),
    )

    levels = report.sample_and_reliability.spread_filter_levels
    assert levels["spread_bucket_match"]["missing_columns"] == ["team_a_role", "spread_bucket"]
    assert levels["role_only_match"]["missing_columns"] == ["team_a_role"]
    assert report.spread_conditioned_baseline["selected_level"] == "no_spread_baseline"
    assert report.spread_conditioned_baseline["sample_size"] == 4


def test_historical_windows_and_stability_are_reported():
    report = build_basic_after_q_report(
        current_state=_current_state(),
        historical_rows=_history(),
        data_cutoff_utc="2026-09-10T00:00:00Z",
    )

    windows = report.historical_windows
    assert windows["PRIMARY_WINDOW"]["historical_window"] == {"start": 2015, "end": 2025}
    assert windows["PRIMARY_WINDOW"]["sample_size"] == 4
    assert windows["PRIMARY_WINDOW"]["raw_probability"] == 0.75
    assert windows["RECENT_WINDOW"]["historical_window"] == {"start": 2021, "end": 2025}
    assert windows["RECENT_WINDOW"]["sample_size"] == 3
    assert windows["RECENT_WINDOW"]["raw_probability"] == 0.666667
    assert windows["EXTENDED_WINDOW"]["historical_window"] == {"start": 2012, "end": 2025}
    assert windows["EXTENDED_WINDOW"]["sample_size"] == 4

    stability = report.historical_window_stability
    assert stability["status"] == "STABLE"
    assert stability["threshold_pp"] == 15.0
    assert stability["max_difference_pp"] == 8.3333


def test_historical_window_stability_can_be_unstable():
    history = _history()
    history.loc[2, "final_state"] = "LOSS"
    history.loc[3, "final_state"] = "LOSS"
    report = build_basic_after_q_report(
        current_state=_current_state(),
        historical_rows=history,
        data_cutoff_utc="2026-09-10T00:00:00Z",
        stability_threshold_pp=15.0,
    )

    assert report.historical_windows["PRIMARY_WINDOW"]["raw_probability"] == 0.25
    assert report.historical_windows["RECENT_WINDOW"]["raw_probability"] == 0.0
    assert report.historical_window_stability["status"] == "UNSTABLE"
    assert report.historical_window_stability["max_difference_pp"] == 25.0


def test_historical_windows_do_not_pull_pre_2012_games_into_main_windows():
    old = _row(
        game_id="old",
        season=1999,
        team="BUF",
        q1="WIN",
        q2="WIN",
        bucket="LEADING_1_TO_7",
        final="WIN",
    )
    report = build_basic_after_q_report(
        current_state=_current_state(),
        historical_rows=pd.concat([_history(), pd.DataFrame([old])], ignore_index=True),
        data_cutoff_utc="2026-09-10T00:00:00Z",
    )

    assert report.league_baseline.sample_size == 5
    assert report.historical_windows["PRIMARY_WINDOW"]["sample_size"] == 4
    assert report.historical_windows["EXTENDED_WINDOW"]["sample_size"] == 4


def test_forum_content_summary_contains_publication_fields_without_recommendation():
    history = _history()
    history.loc[0, "team_a_closing_spread"] = -3.0
    history.loc[1, "team_a_closing_spread"] = -3.0
    report = build_basic_after_q_report(
        current_state=_current_state(),
        historical_rows=history,
        data_cutoff_utc="2026-09-10T00:00:00Z",
        pregame_spread_context=build_pregame_spread_context(
            team_a_closing_spread=-3.0,
            team_a_role="FAVORITE",
        ),
    )

    summary = report.forum_content_summary
    assert summary["matchup"] == "BUF vs HOU"
    assert summary["current_score"] == {"team_a": 17, "opponent": 10}
    assert summary["quarter_scores"] == [
        {"quarter": 1, "team_a_points": 7, "opponent_points": 3},
        {"quarter": 2, "team_a_points": 10, "opponent_points": 7},
    ]
    assert summary["quarter_result_path"] == "WIN-WIN"
    assert summary["opponent_quarter_result_path"] == "LOSS-LOSS"
    assert summary["cumulative_state_path"] == "LEAD-LEAD"
    assert summary["opponent_cumulative_state_path"] == "TRAIL-TRAIL"
    assert summary["pregame_spread"] == -3.0
    assert summary["spread_bucket"] == "FAV_2-3"
    assert summary["broad_final_win_probability"] == 0.75
    assert summary["broad_sample_size"] == 4
    assert summary["spread_conditioned_final_win_probability"] == 0.666667
    assert summary["spread_conditioned_sample_size"] == 3
    assert summary["spread_conditioned_level"] is None
    assert summary["difference_vs_broad_pp"] == -8.3333
    assert summary["team_specific_note"] == {
        "sample_size": 2,
        "raw_final_win_probability": 0.5,
        "raw_delta_vs_league_pp": -25.0,
        "adjusted_final_win_probability": 0.727273,
        "adjusted_delta_vs_league_pp": -2.2727,
    }
    assert summary["warning"] == "Small sample. Historical context only."

    rendered_values = " ".join(str(value).upper() for value in summary.values())
    assert "VALUE BET" not in rendered_values
    assert "PICK:" not in rendered_values


def test_forum_content_summary_uses_none_when_probability_is_missing():
    history = _history().iloc[0:0]
    report = build_basic_after_q_report(
        current_state=_current_state(),
        historical_rows=history,
        data_cutoff_utc="2026-09-10T00:00:00Z",
    )

    summary = report.forum_content_summary
    assert summary["broad_final_win_probability"] is None
    assert summary["spread_conditioned_final_win_probability"] is None
    assert summary["difference_vs_broad_pp"] is None
    assert summary["team_specific_note"] is None


def test_report_requires_v2_margin_bucket_column():
    history = _history().drop(columns=["after_q2_margin_bucket_v2"])
    with pytest.raises(ValueError, match="after_q2_margin_bucket_v2"):
        build_basic_after_q_report(
            current_state=_current_state(),
            historical_rows=history,
            data_cutoff_utc="2026-09-10T00:00:00Z",
        )


def test_report_requires_v2_cumulative_state_columns():
    history = _history().drop(columns=["after_q1_state_v2"])
    with pytest.raises(ValueError, match="after_q1_state_v2"):
        build_basic_after_q_report(
            current_state=_current_state(),
            historical_rows=history,
            data_cutoff_utc="2026-09-10T00:00:00Z",
        )
