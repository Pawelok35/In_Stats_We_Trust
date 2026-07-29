from pathlib import Path

from metrics.strategy_search import (
    StrategyRule,
    summarize_rule_by_season,
    walk_forward_windows,
    write_fixed_strategy_report,
)


def test_gom_stable_rule_filters_week_and_large_spreads(tmp_path: Path):
    rows = [
        {
            "season": 2021,
            "week": 2,
            "variant": "variant_d_balanced",
            "tag": "GOM",
            "confidence": 90,
            "edge": 4,
            "handicap": -3.5,
            "outcome": "win",
            "profit": 2.7,
            "risk": 3.0,
        },
        {
            "season": 2021,
            "week": 3,
            "variant": "variant_d_balanced",
            "tag": "GOM",
            "confidence": 90,
            "edge": 4,
            "handicap": -8.5,
            "outcome": "win",
            "profit": 2.7,
            "risk": 3.0,
        },
        {
            "season": 2021,
            "week": 4,
            "variant": "variant_d_balanced",
            "tag": "GOM",
            "confidence": 90,
            "edge": 4,
            "handicap": -6.5,
            "outcome": "win",
            "profit": 2.7,
            "risk": 3.0,
        },
        {
            "season": 2022,
            "week": 4,
            "variant": "variant_d_balanced",
            "tag": "GOM",
            "confidence": 90,
            "edge": 4,
            "handicap": 3.5,
            "outcome": "loss",
            "profit": -3.0,
            "risk": 3.0,
        },
    ]
    rule = StrategyRule(
        variant="variant_d_balanced",
        tags=("GOM",),
        confidence_min=85,
        edge_min=0,
        handicap_mode="any",
        start_week=3,
        max_abs_handicap=7,
    )

    season_rows = summarize_rule_by_season(rows, rule, [2021, 2022])
    assert season_rows[0]["bets"] == 1
    assert season_rows[0]["profit"] == 2.7
    assert season_rows[1]["bets"] == 1
    assert season_rows[1]["profit"] == -3.0

    windows = walk_forward_windows(rows, rule, start_season=2021, end_season=2022)
    assert windows[0]["train"] == "2021-2021"
    assert windows[0]["test_season"] == 2022

    report = write_fixed_strategy_report(
        rows=rows,
        rule=rule,
        output_path=tmp_path / "report.md",
        start_season=2021,
        end_season=2022,
        title="GOM Stable",
    )
    text = report.read_text(encoding="utf-8")
    assert "## Season Results" in text
    assert "## Walk Forward" in text
