from metrics.ats_features import PickFeatureRow, _quantile, _summarize


def _row(season: int, outcome: str, profit: float) -> PickFeatureRow:
    return PickFeatureRow(
        season=season,
        week=3,
        home="BAL",
        away="MIA",
        pick_team="BAL",
        opponent="MIA",
        outcome=outcome,
        profit=profit,
        risk=3.0,
        early_down_matchup_edge=0.1,
        off_early_down_success_edge=0.02,
        def_early_down_epa_allowed_edge=0.03,
        off_early_down_success_pick=0.5,
        off_early_down_success_opp=0.48,
        def_early_down_epa_allowed_pick=0.0,
        def_early_down_epa_allowed_opp=0.03,
    )


def test_quantile_interpolates_values():
    assert _quantile([1.0, 2.0, 3.0, 4.0], 0.5) == 2.5


def test_summarize_tracks_profit_roi_and_drawdown():
    summary = _summarize(
        [
            _row(2017, "win", 2.7),
            _row(2017, "loss", -3.0),
            _row(2018, "push", 0.0),
        ]
    )

    assert summary["bets"] == 3
    assert summary["wins"] == 1
    assert summary["losses"] == 1
    assert summary["pushes"] == 1
    assert round(summary["profit"], 1) == -0.3
    assert summary["drawdown"] == -3.0
