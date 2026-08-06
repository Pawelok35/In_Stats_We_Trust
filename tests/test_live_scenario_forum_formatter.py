from __future__ import annotations

import copy

import pytest

from live_scenario.forum_formatter import build_forum_post


def report() -> dict:
    return {
        "seasons_included": list(range(2015, 2026)),
        "current_state": {
            "team_a": "CLE",
            "opponent": "JAX",
            "team_a_score": 17,
            "opponent_score": 27,
            "margin": -10,
            "margin_bucket": "TRAILING_8_TO_14",
            "team_a_quarter_result_path": "WIN-LOSS",
            "team_a_cumulative_state_path": "LEAD-TRAIL",
        },
        "forum_content_summary": {
            "quarter_scores_q1_q2_q3": {
                "q1": {"team_a_points": 10, "opponent_points": 3},
                "q2": {"team_a_points": 7, "opponent_points": 24},
                "q3": None,
            }
        },
        "broad_league_game_state_baseline": {
            "wins": 518,
            "losses": 78,
            "ties": 0,
            "sample_size": 596,
            "raw_probability": 0.869,
        },
        "team_a_history": {
            "wins": 25,
            "losses": 3,
            "ties": 0,
            "sample_size": 28,
            "sample_quality": "LOW",
            "raw_probability": 0.893,
            "adjusted_probability": 0.883,
        },
        "opponent_recovery_history": {
            "wins": 4,
            "losses": 13,
            "ties": 0,
            "sample_size": 17,
            "sample_quality": "LOW",
            "raw_probability": 0.2353,
            "adjusted_probability": 0.179,
        },
        "opponent_league_reference": {"raw_probability": 0.131},
        "pregame_spread_context": {"team_a_closing_spread": -3.5},
    }


def test_polish_contract_and_team_a_first_quarters() -> None:
    text = build_forum_post(report())
    assert "CLE 17–27 JAX" in text
    assert "Q1: CLE 10–3 JAX" in text
    assert "Q2: CLE 7–24 JAX" in text
    assert "Strata do przerwy: 10 punktów" in text
    assert "W sezonach 2015–2025" in text
    assert "Surowy wynik: 89,3%" in text
    assert "Po korekcie wielkości próby: 88,3%" in text
    assert "Historyczne dane — nie są automatycznymi typami live." in text


def test_english_locale_uses_dot_decimal_and_english_labels() -> None:
    text = build_forum_post(report(), locale="en-US")
    assert "CLE 17–27 JAX — HALFTIME" in text
    assert "Q2: CLE 7–24 JAX" in text
    assert "Halftime deficit: 10 points" in text
    assert "Raw result: 89.3%" in text
    assert "Adjusted for sample size: 88.3%" in text
    assert "Record:" in text
    assert "not an automatic live decision" in text


def test_backward_compatible_language_alias_and_no_disclaimer() -> None:
    text = build_forum_post(report(), language="pl", include_disclaimer=False)
    assert "Historyczne dane" not in text
    assert "Próba: 28 — jakość: mała" in text


def test_locale_validation() -> None:
    with pytest.raises(ValueError, match="Unsupported locale"):
        build_forum_post(report(), locale="de-DE")


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("LEAD-LEAD", "prowadziło po Q1 i utrzymało prowadzenie"),
        ("TRAIL-LEAD", "przegrywało po Q1, ale do przerwy prowadzi"),
        ("TRAIL-TRAIL", "nadal przegrywa"),
    ],
)
def test_flow_sentence_covers_main_paths(path: str, expected: str) -> None:
    data = report()
    data["current_state"]["team_a_cumulative_state_path"] = path
    assert expected in build_forum_post(data)


def test_no_forbidden_missing_value_tokens_or_json_fields() -> None:
    data = copy.deepcopy(report())
    data["team_a_history"]["adjusted_probability"] = None
    text = build_forum_post(data)
    for token in ("None", "null", "UNKNOWN", "nan", "sample_size", "raw_probability"):
        assert token not in text


def test_spread_is_localized_without_changing_source_value() -> None:
    data = report()
    data["pregame_spread_context"]["team_a_closing_spread"] = 7.5
    text = build_forum_post(data)
    assert "CLE +7,5" in text
    assert data["pregame_spread_context"]["team_a_closing_spread"] == 7.5
