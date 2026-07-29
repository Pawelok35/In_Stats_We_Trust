from metrics.gom_calibration import _is_core, _is_near_miss, _score_pick


def _record(**overrides):
    base = {
        "season": 2025,
        "week": 3,
        "home": "BAL",
        "away": "MIA",
        "tag": "GOM",
        "confidence": 85,
        "edge_vs_line": 4,
        "handicap": -6.5,
    }
    base.update(overrides)
    return base


def test_core_and_near_miss_rules_are_disjoint():
    assert _is_core(_record())
    assert not _is_near_miss(_record())

    near = _record(confidence=83, edge_vs_line=3.5)
    assert not _is_core(near)
    assert _is_near_miss(near)


def test_shadow_score_rewards_edge_and_consensus():
    weak = _score_pick(
        confidence=80,
        edge=3,
        consensus_count=2,
        margin_dispersion=10,
        pressure=0.10,
        third_down=0.10,
        residual_bias_edge=-3,
        residual_volatility=18,
    )
    strong = _score_pick(
        confidence=88,
        edge=6,
        consensus_count=6,
        margin_dispersion=2,
        pressure=-0.02,
        third_down=0.0,
        residual_bias_edge=3,
        residual_volatility=10,
    )

    assert strong > weak
