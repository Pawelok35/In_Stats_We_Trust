from __future__ import annotations

import pytest

from metrics.ats_features import load_core_gom_picks

EXPECTED_BETS = 74
EXPECTED_WINS = 61
EXPECTED_LOSSES = 12
EXPECTED_PUSHES = 1
EXPECTED_PROFIT_UNITS = 128.70
EXPECTED_RISK_UNITS = 222.00
EXPECTED_ROI = EXPECTED_PROFIT_UNITS / EXPECTED_RISK_UNITS
EXPECTED_MAX_DRAWDOWN_UNITS = -6.30


def _summary(rows: list[dict]) -> dict[str, float | int]:
    equity = 0.0
    peak = 0.0
    max_drawdown = 0.0

    def sort_key(item: dict) -> tuple[int, int, str, str]:
        return item["season"], item["week"], item["home"], item["away"]

    for row in sorted(rows, key=sort_key):
        equity += float(row["profit"])
        peak = max(peak, equity)
        max_drawdown = min(max_drawdown, equity - peak)

    profit = sum(float(row["profit"]) for row in rows)
    risk = sum(float(row["risk"]) for row in rows)
    return {
        "bets": len(rows),
        "wins": sum(1 for row in rows if row["outcome"] == "win"),
        "losses": sum(1 for row in rows if row["outcome"] == "loss"),
        "pushes": sum(1 for row in rows if row["outcome"] == "push"),
        "profit_units": profit,
        "risk_units": risk,
        "roi": profit / risk if risk else 0.0,
        "max_drawdown_units": max_drawdown,
    }


def test_champion_core_regression_matches_frozen_baseline():
    rows = load_core_gom_picks()
    summary = _summary(rows)

    assert summary["bets"] == EXPECTED_BETS
    assert summary["wins"] == EXPECTED_WINS
    assert summary["losses"] == EXPECTED_LOSSES
    assert summary["pushes"] == EXPECTED_PUSHES
    assert summary["profit_units"] == pytest.approx(EXPECTED_PROFIT_UNITS)
    assert summary["risk_units"] == pytest.approx(EXPECTED_RISK_UNITS)
    assert summary["roi"] == pytest.approx(EXPECTED_ROI)
    assert summary["max_drawdown_units"] == pytest.approx(EXPECTED_MAX_DRAWDOWN_UNITS)
