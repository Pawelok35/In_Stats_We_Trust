from __future__ import annotations

import pytest

from live_scenario.forum_formatter import build_forum_post

FORBIDDEN = (
    "None",
    "null",
    "UNKNOWN",
    "nan",
    "Record:",
    "Sample:",
    "Sample quality:",
    " raw ",
    "Halftime margin",
    "sample_size",
    "raw_probability",
    "exact_spread_match",
    "spread_bucket_match",
    "role_only_match",
    "no_spread_baseline",
    "filters_relaxed",
    "probability_source_level",
)


def _report(
    *,
    path: str = "LEAD-LEAD",
    quarter_path: str = "WIN-WIN",
    margin: int = 11,
    margin_bucket: str = "LEADING_8_TO_14",
    team: str = "BUF",
    opponent: str = "HOU",
    team_score: int = 17,
    opponent_score: int = 6,
    q1: tuple[int, int] = (10, 3),
    q2: tuple[int, int] = (7, 3),
    broad_wins: int = 518,
    broad_losses: int = 78,
    broad_ties: int = 0,
    broad_probability: float = 0.869,
    team_wins: int = 25,
    team_losses: int = 3,
    team_sample: int = 28,
    team_quality: str = "LOW",
    team_raw: float = 0.893,
    team_adjusted: float = 0.883,
    opponent_wins: int = 4,
    opponent_losses: int = 13,
    opponent_sample: int = 17,
    opponent_quality: str = "LOW",
    opponent_raw: float = 0.2353,
    opponent_adjusted: float = 0.179,
    opponent_league: float = 0.131,
    spread: float | None = None,
    spread_selected_level: str = "spread_bucket_match",
    exact_sample: int = 0,
    exact_wins: int = 0,
    exact_losses: int = 0,
    exact_probability: float | None = None,
    bucket_sample: int = 80,
    bucket_wins: int = 58,
    bucket_losses: int = 22,
    bucket_probability: float = 0.721,
    role_sample: int = 120,
    role_wins: int = 73,
    role_losses: int = 47,
    role_probability: float = 0.611,
) -> dict:
    return {
        "seasons_included": list(range(2015, 2026)),
        "season_type": "REG",
        "current_state": {
            "team_a": team,
            "opponent": opponent,
            "team_a_score": team_score,
            "opponent_score": opponent_score,
            "margin": margin,
            "margin_bucket": margin_bucket,
            "team_a_quarter_result_path": quarter_path,
            "team_a_cumulative_state_path": path,
        },
        "forum_content_summary": {
            "quarter_scores_q1_q2_q3": {
                "q1": {"team_a_points": q1[0], "opponent_points": q1[1]},
                "q2": {"team_a_points": q2[0], "opponent_points": q2[1]},
                "q3": None,
            },
        },
        "broad_league_game_state_baseline": {
            "wins": broad_wins,
            "losses": broad_losses,
            "ties": broad_ties,
            "sample_size": broad_wins + broad_losses + broad_ties,
            "raw_probability": broad_probability,
            "sample_quality": "STRONG",
        },
        "team_a_history": {
            "wins": team_wins,
            "losses": team_losses,
            "ties": 0,
            "sample_size": team_sample,
            "sample_quality": team_quality,
            "raw_probability": team_raw if team_sample else None,
            "adjusted_probability": team_adjusted if team_sample else None,
        },
        "opponent_recovery_history": {
            "wins": opponent_wins,
            "losses": opponent_losses,
            "ties": 0,
            "sample_size": opponent_sample,
            "sample_quality": opponent_quality,
            "raw_probability": opponent_raw if opponent_sample else None,
            "adjusted_probability": opponent_adjusted if opponent_sample else None,
        },
        "opponent_league_reference": {
            "wins": 78,
            "losses": 518,
            "ties": 0,
            "sample_size": 596,
            "raw_probability": opponent_league,
        },
        "pregame_spread_context": {
            "team_a_closing_spread": spread,
            "team_a_role": "FAVORITE" if spread is not None and spread < 0 else "UNDERDOG",
        },
        "sample_and_reliability": {
            "spread_filter_levels": {
                "exact_spread_match": {
                    "wins": exact_wins,
                    "losses": exact_losses,
                    "ties": 0,
                    "sample_size": exact_sample,
                    "raw_probability": exact_probability,
                    "sample_quality": "STRONG" if exact_sample >= 30 else "LOW",
                },
                "spread_bucket_match": {
                    "wins": bucket_wins,
                    "losses": bucket_losses,
                    "ties": 0,
                    "sample_size": bucket_sample,
                    "raw_probability": bucket_probability,
                    "sample_quality": "STRONG",
                },
                "role_only_match": {
                    "wins": role_wins,
                    "losses": role_losses,
                    "ties": 0,
                    "sample_size": role_sample,
                    "raw_probability": role_probability,
                    "sample_quality": "STRONG",
                },
            },
        },
        "spread_conditioned_baseline": {
            "selected_level": spread_selected_level,
            "wins": bucket_wins,
            "losses": bucket_losses,
            "ties": 0,
            "sample_size": bucket_sample,
            "raw_probability": bucket_probability,
            "sample_quality": "STRONG",
        },
    }


def _assert_clean(post: str) -> None:
    for token in FORBIDDEN:
        assert token not in post


def test_forum_formatter_polish_snapshot_current_scenario():
    post = build_forum_post(_report())

    expected = (
        """🏈 NFL HALFTIME SCENARIO

BUF prowadzi z HOU 17–6 do przerwy.

Q1: BUF 10–3
Q2: BUF 7–3

BUF:
• Quarter Path: WIN-WIN
• Game State Path: LEAD-LEAD
• Przewaga do przerwy: +11

"""
        "W meczach sezonu regularnego w latach 2015–2025 drużyny, które "
        "prowadziły po Q1 i Q2 oraz miały "
        "8–14 punktów przewagi do przerwy, wygrywały 86,9% spotkań."
        """

Bilans: 518–78
Próba: 596

BUF w podobnych sytuacjach:

Bilans: 25–3
Surowy wynik: 89,3%
Po korekcie małej próby w stronę średniej ligowej: 88,3%
Próba: 28 — jakość: mała

HOU w lustrzanej sytuacji:

Bilans powrotów: 4–13
Surowy wynik: 23,5%
Po korekcie małej próby w stronę średniej ligowej: 17,9%
Średnia ligowa dla takich powrotów: 13,1%
Próba: 17 — jakość: mała

Historyczna ciekawostka — nie automatyczny typ live."""
    )

    assert post == expected
    _assert_clean(post)
    assert "–" in post
    assert "—" in post
    assert "86,9%" in post
    assert "89,3%" in post
    assert "23,5%" in post
    assert post.count("Próba: 28") == 1


@pytest.mark.parametrize(
    ("path", "bucket", "snippet"),
    [
        ("LEAD-LEAD", "LEADING_1_TO_7", "prowadziły po Q1 i Q2"),
        ("LEAD-TRAIL", "TRAILING_1_TO_7", "prowadziły po Q1, ale przegrywały"),
        ("LEAD-TIE", "TIED", "prowadziły po Q1, ale remisowały"),
        ("TRAIL-LEAD", "LEADING_1_TO_7", "przegrywały po Q1, ale objęły prowadzenie"),
        ("TRAIL-TRAIL", "TRAILING_1_TO_7", "przegrywające po Q1 i po Q2"),
        ("TRAIL-TIE", "TIED", "doprowadziły do remisu"),
        ("TIE-LEAD", "LEADING_1_TO_7", "remisujące po Q1, które prowadziły"),
        ("TIE-TRAIL", "TRAILING_1_TO_7", "remisujące po Q1, które przegrywały"),
        ("TIE-TIE", "TIED", "remisujące po Q1 i do przerwy"),
    ],
)
def test_forum_formatter_supports_all_q2_cumulative_paths(path, bucket, snippet):
    report = _report(path=path, margin_bucket=bucket, margin=0 if bucket == "TIED" else 3)
    post = build_forum_post(report)
    assert snippet in post
    _assert_clean(post)


def test_forum_formatter_formats_trailing_margin_as_loss():
    post = build_forum_post(
        _report(
            path="LEAD-TRAIL",
            quarter_path="WIN-LOSS",
            margin=-3,
            margin_bucket="TRAILING_1_TO_7",
            team="MIA",
            opponent="LV",
            team_score=7,
            opponent_score=10,
            q1=(7, 3),
            q2=(0, 7),
            opponent_wins=6,
            opponent_losses=2,
            opponent_sample=8,
            opponent_raw=0.75,
            opponent_adjusted=0.67674,
            opponent_league=0.647436,
        )
    )
    assert "MIA przegrywa z LV 7–10 do przerwy." in post
    assert "Q2: LV 7–0" in post
    assert "• Strata do przerwy: -3" in post
    assert "Bilans utrzymania prowadzenia: 6–2" in post
    assert "Surowy wynik: 75,0%" in post
    _assert_clean(post)


def test_forum_formatter_formats_tied_halftime():
    post = build_forum_post(
        _report(
            path="TIE-TIE",
            quarter_path="TIE-TIE",
            margin=0,
            margin_bucket="TIED",
            team_score=10,
            opponent_score=10,
            q1=(3, 3),
            q2=(7, 7),
        )
    )
    assert "BUF i HOU remisują 10–10 do przerwy." in post
    assert "• Przewaga do przerwy: 0" in post
    _assert_clean(post)


def test_forum_formatter_handles_team_a_history_no_data():
    post = build_forum_post(_report(team_sample=0, team_quality="NO_DATA"))
    assert "Brak wcześniejszych meczów BUF spełniających ten warunek." in post
    assert "0/0" not in post
    _assert_clean(post)


def test_forum_formatter_handles_quality_mapping_without_repetition():
    post = build_forum_post(_report(team_sample=3, team_quality="VERY_LOW"))
    assert "Próba: 3 — jakość: bardzo mała" in post
    assert "Mała próba:" not in post
    assert "ale próba obejmuje tylko 3 wcześniejsze przypadki" in post
    assert "Po korekcie bardzo małej próby w stronę średniej ligowej" in post
    assert "Sample quality" not in post
    _assert_clean(post)


def test_forum_formatter_handles_opponent_history_no_data():
    post = build_forum_post(_report(opponent_sample=0))
    assert "Brak wcześniejszych meczów HOU w lustrzanej sytuacji." in post
    _assert_clean(post)


def test_forum_formatter_omits_spread_when_unavailable():
    post = build_forum_post(_report(spread=None))
    assert "Kontekst spreadu" not in post
    assert "przed meczem" not in post
    _assert_clean(post)


def test_forum_formatter_uses_exact_spread_when_sample_is_large_enough():
    post = build_forum_post(
        _report(
            spread=-1.5,
            spread_selected_level="exact_spread_match",
            exact_sample=35,
            exact_wins=27,
            exact_losses=8,
            exact_probability=0.7714,
        )
    )
    assert "Pregame spread: BUF −1,5." in post
    assert "BUF było przed meczem faworytem." in post
    assert "Drużyny z dokładnie takim spreadem" in post
    assert "wygrywały 77,1% spotkań." in post
    assert "Bilans: 27–8" in post
    assert "Próba: 35" in post
    _assert_clean(post)


def test_forum_formatter_falls_back_from_small_exact_to_spread_bucket():
    post = build_forum_post(
        _report(
            spread=-1.5,
            exact_sample=13,
            exact_wins=1,
            exact_losses=12,
            exact_probability=0.077,
            bucket_sample=40,
            bucket_wins=28,
            bucket_losses=12,
            bucket_probability=0.7,
        )
    )
    assert "Drużyny z podobnego przedziału spreadu" in post
    assert "wygrywały 70,0% spotkań." in post
    assert "7,7%" not in post
    _assert_clean(post)


def test_forum_formatter_falls_back_from_small_bucket_to_role_only():
    post = build_forum_post(
        _report(
            spread=3.5,
            exact_sample=13,
            exact_probability=0.2,
            bucket_sample=20,
            bucket_probability=0.45,
            role_sample=45,
            role_wins=18,
            role_losses=27,
            role_probability=0.4,
        )
    )
    assert "Pregame spread: BUF +3,5." in post
    assert "BUF nie było przed meczem faworytem." in post
    assert "Przedmeczowe drużyny nienotowane jako faworyt" in post
    assert "wygrywały 40,0% spotkań." in post
    assert "45,0%" not in post
    _assert_clean(post)


def test_forum_formatter_warns_when_all_spread_samples_are_small():
    post = build_forum_post(
        _report(
            spread=-1.5,
            exact_sample=13,
            exact_probability=0.077,
            bucket_sample=18,
            bucket_probability=0.5,
            role_sample=22,
            role_probability=0.55,
        )
    )
    assert "wygrywały 7,7% spotkań." not in post
    assert "wygrywały 50,0% spotkań." not in post
    assert "wygrywały 55,0% spotkań." not in post
    assert "znaleziono tylko 22 podobnych przypadków" in post
    assert "należy traktować ostrożnie" in post
    _assert_clean(post)


def test_forum_formatter_opponent_very_low_includes_sample_and_raw_result():
    post = build_forum_post(
        _report(
            opponent_wins=2,
            opponent_losses=2,
            opponent_sample=4,
            opponent_quality="VERY_LOW",
            opponent_raw=0.5,
            opponent_adjusted=0.208,
            opponent_league=0.15,
        )
    )
    assert "Surowy wynik: 50,0%" in post
    assert "Po korekcie małej próby w stronę średniej ligowej: 20,8%" in post
    assert "Próba: 4 — jakość: bardzo mała" in post
    _assert_clean(post)


def test_forum_formatter_uses_polish_decimal_comma_without_changing_source_values():
    report = _report(broad_probability=0.86851, team_raw=0.89251, opponent_raw=0.23531)
    post = build_forum_post(report)
    assert "86,9%" in post
    assert "89,3%" in post
    assert "23,5%" in post
    assert report["broad_league_game_state_baseline"]["raw_probability"] == 0.86851
    assert report["team_a_history"]["raw_probability"] == 0.89251
    assert report["opponent_recovery_history"]["raw_probability"] == 0.23531
    _assert_clean(post)
