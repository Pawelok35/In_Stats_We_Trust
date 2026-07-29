"""Deterministic Polish forum-post formatter for Live Scenario V2 reports."""

from __future__ import annotations

import math
from typing import Any

EN_DASH = "–"
EM_DASH = "—"

QUALITY_PL = {
    "NO_DATA": "brak danych",
    "VERY_LOW": "bardzo mała",
    "LOW": "mała",
    "MODERATE": "umiarkowana",
    "STRONG": "duża",
}

FORUM_SPREAD_MIN_SAMPLE = 30


def build_forum_post(report: dict, language: str = "pl") -> str:
    """Build a ready-to-copy forum post from an existing V2 report JSON."""
    if language != "pl":
        raise ValueError("Only Polish forum formatting is supported.")

    state = _as_dict(report.get("current_state"))
    forum = _as_dict(report.get("forum_content_summary"))
    broad = _as_dict(report.get("broad_league_game_state_baseline"))
    team_history = _as_dict(report.get("team_a_history"))
    opponent_history = _as_dict(report.get("opponent_recovery_history"))
    opponent_reference = _as_dict(report.get("opponent_league_reference"))
    pregame = _as_dict(report.get("pregame_spread_context"))
    spread_levels = _as_dict(
        _as_dict(report.get("sample_and_reliability")).get("spread_filter_levels")
    )
    spread_selected = _as_dict(report.get("spread_conditioned_baseline"))

    team = _clean_text(state.get("team_a") or forum.get("matchup", "TEAM").split(" vs ")[0])
    opponent = _clean_text(state.get("opponent") or "OPP")
    team_score = _int_or_none(state.get("team_a_score"))
    opponent_score = _int_or_none(state.get("opponent_score"))
    margin = _int_or_none(state.get("margin"))
    quarter_path = _clean_text(
        state.get("team_a_quarter_result_path")
        or state.get("team_a_path")
        or forum.get("quarter_result_path")
    )
    cumulative_path = _clean_text(
        state.get("team_a_cumulative_state_path")
        or forum.get("cumulative_state_path")
    )
    margin_bucket = _clean_text(state.get("margin_bucket") or forum.get("margin_bucket"))
    start_year, end_year = _history_year_range(report)
    season_scope = _season_scope_phrase(report, start_year, end_year)

    lines = [
        "🏈 NFL HALFTIME SCENARIO",
        "",
        _score_sentence(team, opponent, team_score, opponent_score, margin),
        "",
        _quarter_line("Q1", team, opponent, report, 1),
        _quarter_line("Q2", team, opponent, report, 2),
        "",
        f"{team}:",
        f"• Quarter Path: {_safe_display(quarter_path)}",
        f"• Game State Path: {_safe_display(cumulative_path)}",
        f"• {_margin_label(margin)}: {_signed_margin(margin)}",
        "",
        _broad_sentence(season_scope, cumulative_path, margin_bucket, broad),
        "",
        f"Bilans: {_record(broad)}",
        f"Próba: {_sample_text(broad)}",
    ]

    team_block = _team_history_block(team, team_history)
    if team_block:
        lines.extend(["", *team_block])

    opponent_block = _opponent_history_block(opponent, margin, opponent_history, opponent_reference)
    if opponent_block:
        lines.extend(["", *opponent_block])

    spread_block = _spread_block(team, pregame, spread_levels, spread_selected)
    if spread_block:
        lines.extend(["", *spread_block])

    lines.extend(["", f"Historyczna ciekawostka {EM_DASH} nie automatyczny typ live."])
    post = "\n".join(_strip_bad_tokens(line) for line in lines)
    return _remove_forbidden_terms(post).strip()


def _as_dict(value: Any) -> dict:
    return value if isinstance(value, dict) else {}


def _clean_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return "" if text.lower() in {"none", "null", "nan", "unknown"} else text


def _strip_bad_tokens(text: str) -> str:
    for token in ("None", "null", "UNKNOWN", "nan"):
        text = text.replace(token, "")
    return text


def _remove_forbidden_terms(text: str) -> str:
    replacements = {
        "BET": "B.T",
        "PICK": "P.CK",
        "VALUE BET": "V.B.",
        "LOCK": "L.CK",
        "pewny typ": "pewna teza",
    }
    for forbidden, replacement in replacements.items():
        text = text.replace(forbidden, replacement)
    return text


def _int_or_none(value: Any) -> int | None:
    try:
        if value is None:
            return None
        number = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(number):
        return None
    return int(number)


def _float_or_none(value: Any) -> float | None:
    try:
        if value is None:
            return None
        number = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(number):
        return None
    return number


def _pct(value: Any) -> str | None:
    number = _float_or_none(value)
    if number is None:
        return None
    return f"{number * 100:.1f}%".replace(".", ",")


def _record(node: dict) -> str:
    wins = _int_or_none(node.get("wins")) or 0
    losses = _int_or_none(node.get("losses")) or 0
    ties = _int_or_none(node.get("ties")) or 0
    if ties:
        return f"{wins}{EN_DASH}{losses}{EN_DASH}{ties}"
    return f"{wins}{EN_DASH}{losses}"


def _sample_text(node: dict) -> str:
    sample = _int_or_none(node.get("sample_size"))
    return str(sample) if sample is not None else "0"


def _quality_text(value: Any) -> str:
    return QUALITY_PL.get(_clean_text(value), "brak danych")


def _safe_display(value: str) -> str:
    return value or "brak danych"


def _signed_margin(margin: int | None) -> str:
    if margin is None:
        return "brak danych"
    if margin > 0:
        return f"+{margin}"
    return str(margin)


def _margin_label(margin: int | None) -> str:
    if margin is None or margin >= 0:
        return "Przewaga do przerwy"
    return "Strata do przerwy"


def _score(team_score: int | None, opponent_score: int | None) -> str:
    if team_score is None or opponent_score is None:
        return "wynik niepodany"
    return f"{team_score}{EN_DASH}{opponent_score}"


def _score_sentence(
    team: str,
    opponent: str,
    team_score: int | None,
    opponent_score: int | None,
    margin: int | None,
) -> str:
    score = _score(team_score, opponent_score)
    if margin is None and team_score is not None and opponent_score is not None:
        margin = team_score - opponent_score
    if margin is None:
        return f"{team} vs {opponent}: sytuacja do przerwy."
    if margin > 0:
        return f"{team} prowadzi z {opponent} {score} do przerwy."
    if margin < 0:
        return f"{team} przegrywa z {opponent} {score} do przerwy."
    return f"{team} i {opponent} remisują {score} do przerwy."


def _quarter_line(label: str, team: str, opponent: str, report: dict, quarter: int) -> str:
    scores = _as_dict(
        _as_dict(report.get("forum_content_summary")).get("quarter_scores_q1_q2_q3")
    )
    node = _as_dict(scores.get(f"q{quarter}"))
    if not node:
        for row in _as_dict(report.get("forum_content_summary")).get("quarter_scores", []) or []:
            if isinstance(row, dict) and _int_or_none(row.get("quarter")) == quarter:
                node = row
                break
    team_points = _int_or_none(node.get("team_a_points"))
    opponent_points = _int_or_none(node.get("opponent_points"))
    if team_points is None or opponent_points is None:
        return f"{label}: brak danych"
    if team_points >= opponent_points:
        return f"{label}: {team} {_score(team_points, opponent_points)}"
    return f"{label}: {opponent} {_score(opponent_points, team_points)}"


def _history_year_range(report: dict) -> tuple[int, int]:
    seasons = report.get("seasons_included")
    if isinstance(seasons, list) and seasons:
        numbers = [_int_or_none(season) for season in seasons]
        numbers = [number for number in numbers if number is not None]
        if numbers:
            return min(numbers), max(numbers)
    return 2015, 2025


def _season_scope_phrase(report: dict, start_year: int, end_year: int) -> str:
    season_type = _season_type(report)
    year_range = f"{start_year}{EN_DASH}{end_year}"
    if season_type in {"REG", "REGULAR", "REGULAR_SEASON"}:
        return f"W meczach sezonu regularnego w latach {year_range}"
    if season_type in {"POST", "PLAYOFF", "PLAYOFFS"}:
        return f"W meczach playoff w latach {year_range}"
    if season_type:
        return f"W meczach typu {season_type} w latach {year_range}"
    return f"W meczach sezonu regularnego w latach {year_range}"


def _season_type(report: dict) -> str:
    candidates = [
        report.get("season_type"),
        report.get("game_type"),
        _as_dict(report.get("dataset_metadata")).get("season_type"),
        _as_dict(report.get("metadata")).get("season_type"),
        _as_dict(report.get("metadata")).get("game_type"),
    ]
    for value in candidates:
        text = _clean_text(value).upper()
        if text:
            return text
    return "REG"


def _margin_phrase(path: str, bucket: str) -> str:
    if bucket == "TIED" or path.endswith("TIE"):
        return "remisując do przerwy"
    if bucket.endswith("1_TO_7"):
        return f"różnicą 1{EN_DASH}7 punktów"
    if bucket.endswith("8_TO_14"):
        return f"różnicą 8{EN_DASH}14 punktów"
    if bucket.endswith("15_PLUS"):
        return "różnicą co najmniej 15 punktów"
    return "w takim przedziale punktowym"


def _state_description(path: str, bucket: str) -> str:
    margin = _margin_phrase(path, bucket)
    descriptions = {
        "LEAD-LEAD": (
            "drużyny, które prowadziły po Q1 i Q2 oraz miały "
            f"{margin.replace('różnicą ', '')} przewagi do przerwy"
        ),
        "LEAD-TRAIL": (
            "drużyny, które prowadziły po Q1, ale przegrywały do przerwy "
            f"{margin}"
        ),
        "LEAD-TIE": "drużyny, które prowadziły po Q1, ale remisowały do przerwy",
        "TRAIL-LEAD": (
            "drużyny, które przegrywały po Q1, ale objęły prowadzenie do przerwy "
            f"{margin}"
        ),
        "TRAIL-TRAIL": f"drużyny przegrywające po Q1 i po Q2 {margin}",
        "TRAIL-TIE": (
            "drużyny, które przegrywały po Q1, ale doprowadziły do remisu do przerwy"
        ),
        "TIE-LEAD": f"drużyny remisujące po Q1, które prowadziły do przerwy {margin}",
        "TIE-TRAIL": (
            f"drużyny remisujące po Q1, które przegrywały do przerwy {margin}"
        ),
        "TIE-TIE": "drużyny remisujące po Q1 i do przerwy",
    }
    return descriptions.get(path, "drużyny w takim stanie meczu")


def _broad_sentence(
    season_scope: str,
    path: str,
    bucket: str,
    broad: dict,
) -> str:
    probability = _pct(broad.get("raw_probability")) or "brak danych"
    description = _state_description(path, bucket)
    return f"{season_scope} {description}, wygrywały {probability} spotkań."


def _team_history_block(team: str, node: dict) -> list[str]:
    sample = _int_or_none(node.get("sample_size")) or 0
    if sample == 0:
        return [f"Brak wcześniejszych meczów {team} spełniających ten warunek."]
    adjusted = _pct(node.get("adjusted_probability")) or "brak danych"
    quality = _quality_text(node.get("sample_quality"))
    if _clean_text(node.get("sample_quality")) == "VERY_LOW":
        return [
            f"{team} w podobnych sytuacjach:",
            "",
            (
                f"{team} miało w takim położeniu bilans {_record(node)}, "
                f"ale próba obejmuje tylko {sample} wcześniejsze przypadki."
            ),
            f"Po korekcie bardzo małej próby w stronę średniej ligowej: {adjusted}",
            f"Próba: {sample} {EM_DASH} jakość: {quality}",
        ]
    raw = _pct(node.get("raw_probability")) or "brak danych"
    return [
        f"{team} w podobnych sytuacjach:",
        "",
        f"Bilans: {_record(node)}",
        f"Surowy wynik: {raw}",
        f"Po korekcie małej próby w stronę średniej ligowej: {adjusted}",
        f"Próba: {sample} {EM_DASH} jakość: {quality}",
    ]


def _opponent_history_block(
    opponent: str,
    team_margin: int | None,
    node: dict,
    reference: dict,
) -> list[str]:
    sample = _int_or_none(node.get("sample_size")) or 0
    if sample == 0:
        return [f"Brak wcześniejszych meczów {opponent} w lustrzanej sytuacji."]
    raw = _pct(node.get("raw_probability")) or "brak danych"
    adjusted = _pct(node.get("adjusted_probability")) or "brak danych"
    quality = _quality_text(node.get("sample_quality"))
    baseline = _pct(
        reference.get("raw_probability") or node.get("opponent_league_reference_probability")
    )
    if team_margin is not None and team_margin > 0:
        balance_label = "Bilans powrotów"
        league_label = "Średnia ligowa dla takich powrotów"
    elif team_margin is not None and team_margin < 0:
        balance_label = "Bilans utrzymania prowadzenia"
        league_label = "Średnia ligowa dla utrzymania takiego prowadzenia"
    else:
        balance_label = "Bilans zwycięstw z lustrzanej remisowej sytuacji"
        league_label = "Średnia ligowa dla takich remisowych sytuacji"

    lines = [
        f"{opponent} w lustrzanej sytuacji:",
        "",
        f"{balance_label}: {_record(node)}",
        f"Surowy wynik: {raw}",
        f"Po korekcie małej próby w stronę średniej ligowej: {adjusted}",
    ]
    if baseline:
        lines.append(f"{league_label}: {baseline}")
    lines.append(f"Próba: {sample} {EM_DASH} jakość: {quality}")
    return lines


def _spread_block(team: str, pregame: dict, levels: dict, selected: dict) -> list[str]:
    spread = _float_or_none(pregame.get("team_a_closing_spread"))
    if spread is None:
        return []
    role = _clean_text(pregame.get("team_a_role"))
    lines = [f"Pregame spread: {team} {_signed_spread(spread)}."]

    selected_context = _select_forum_spread_context(levels, selected)
    if selected_context is None:
        low_sample = _best_low_sample_spread_context(levels, selected)
        if low_sample:
            label, node = low_sample
            lines.append(_low_sample_spread_sentence(label, spread, node))
        return lines

    label, node = selected_context
    probability = _pct(node.get("raw_probability"))
    if probability:
        quality = _quality_text(node.get("sample_quality"))
        if _clean_text(node.get("sample_quality")) == "VERY_LOW":
            sample = _int_or_none(node.get("sample_size")) or 0
            lines.append(
                f"Znaleziono tylko {sample} podobnych przypadków, dlatego ten fragment "
                "należy traktować wyłącznie jako ciekawostkę."
            )
        lines.append(_spread_context_sentence(label, role, probability, pregame, node))
        lines.append(f"Bilans: {_record(node)}")
        lines.append(f"Próba: {_sample_text(node)} {EM_DASH} jakość: {quality}")
    return lines


def _signed_spread(spread: float) -> str:
    value = f"{abs(spread):g}".replace(".", ",")
    if spread > 0:
        return f"+{value}"
    if spread < 0:
        return f"−{value}"
    return "0"


def _select_forum_spread_context(levels: dict, selected: dict) -> tuple[str, dict] | None:
    for label in ("exact_spread_match", "spread_bucket_match", "role_only_match"):
        node = _as_dict(levels.get(label))
        if (_int_or_none(node.get("sample_size")) or 0) >= FORUM_SPREAD_MIN_SAMPLE:
            return label, node
    selected_level = _clean_text(selected.get("selected_level") or selected.get("name"))
    selected_sample = _int_or_none(selected.get("sample_size")) or 0
    if selected_level in {
        "exact_spread_match",
        "spread_bucket_match",
        "role_only_match",
    } and selected_sample >= FORUM_SPREAD_MIN_SAMPLE:
        return selected_level, selected
    return None


def _best_low_sample_spread_context(
    levels: dict,
    selected: dict,
) -> tuple[str, dict] | None:
    candidates: list[tuple[str, dict]] = []
    for label in ("exact_spread_match", "spread_bucket_match", "role_only_match"):
        node = _as_dict(levels.get(label))
        sample = _int_or_none(node.get("sample_size")) or 0
        if sample > 0:
            candidates.append((label, node))
    if not candidates and (_int_or_none(selected.get("sample_size")) or 0) > 0:
        label = _clean_text(selected.get("selected_level") or selected.get("name"))
        candidates.append((label, selected))
    if not candidates:
        return None
    return max(candidates, key=lambda item: _int_or_none(item[1].get("sample_size")) or 0)


def _spread_context_sentence(
    label: str,
    role: str,
    probability: str,
    pregame: dict,
    node: dict,
) -> str:
    if label == "exact_spread_match":
        return (
            "Drużyny z dokładnie takim spreadem, które znalazły się w tej sytuacji, "
            f"wygrywały {probability} spotkań."
        )
    if label == "spread_bucket_match":
        bucket_label = _spread_bucket_display_label(pregame, node)
        if bucket_label:
            return (
                f"Drużyny ze spreadem {bucket_label}, które znalazły się w tej sytuacji, "
                f"wygrywały {probability} spotkań."
            )
        return (
            "Drużyny z podobnego przedziału spreadu, które znalazły się w tej sytuacji, "
            f"wygrywały {probability} spotkań."
        )
    if role == "UNDERDOG":
        return (
            "Przedmeczowi underdogowie znajdujący się w tej sytuacji wygrywali "
            f"{probability} spotkań."
        )
    if role == "PICKEM":
        return (
            "Drużyny z przedmeczową linią pick'em znajdujące się w tej sytuacji "
            f"wygrywały {probability} spotkań."
        )
    return f"Przedmeczowi faworyci w tej sytuacji wygrywali {probability} spotkań."


def _low_sample_spread_sentence(label: str, spread: float, node: dict) -> str:
    sample = _int_or_none(node.get("sample_size")) or 0
    if label == "exact_spread_match":
        line_label = f"dokładnego spreadu {_signed_spread(spread)}"
    elif label == "spread_bucket_match":
        line_label = "podobnego przedziału spreadu"
    else:
        line_label = "samej roli przedmeczowej"
    return (
        f"Dla {line_label} znaleziono tylko {sample} podobnych przypadków, "
        "dlatego ten fragment należy traktować ostrożnie."
    )


def _spread_bucket_display_label(pregame: dict, node: dict) -> str | None:
    direct_label = _clean_text(
        node.get("spread_bucket_display_label")
        or pregame.get("spread_bucket_display_label")
        or node.get("display_label")
    )
    if direct_label:
        return direct_label

    role = _clean_text(pregame.get("team_a_role"))
    min_value = _float_or_none(node.get("spread_bucket_min") or pregame.get("spread_bucket_min"))
    max_value = _float_or_none(node.get("spread_bucket_max") or pregame.get("spread_bucket_max"))
    if min_value is not None or max_value is not None:
        return _spread_range_label(
            role=role,
            min_abs=min_value,
            max_abs=max_value,
        )

    bucket = _clean_text(
        node.get("spread_bucket_name")
        or pregame.get("spread_bucket_name")
        or pregame.get("spread_bucket")
    )
    if not bucket:
        return None
    role_from_bucket, bucket_body = _split_spread_bucket(bucket)
    role = role_from_bucket or role
    if bucket_body in {"PK", "PICKEM", "0"}:
        return "pick'em"
    if bucket_body.endswith("+"):
        min_abs = _float_or_none(bucket_body[:-1])
        return _spread_range_label(role=role, min_abs=min_abs, max_abs=None)
    if "-" in bucket_body:
        left, right = bucket_body.split("-", 1)
        return _spread_range_label(
            role=role,
            min_abs=_float_or_none(left),
            max_abs=_float_or_none(right),
        )
    exact = _float_or_none(bucket_body)
    if exact is not None:
        return f"dokładnie {_signed_spread(_signed_abs_for_role(exact, role))}"
    return None


def _split_spread_bucket(bucket: str) -> tuple[str | None, str]:
    text = bucket.upper()
    for prefix, role in (("FAV_", "FAVORITE"), ("DOG_", "UNDERDOG"), ("PK_", "PICKEM")):
        if text.startswith(prefix):
            return role, bucket[len(prefix) :]
    return None, bucket


def _spread_range_label(
    *,
    role: str,
    min_abs: float | None,
    max_abs: float | None,
) -> str | None:
    if min_abs is None and max_abs is None:
        return None
    if min_abs is None:
        boundary = _signed_spread(_signed_abs_for_role(max_abs or 0.0, role))
        return f"{boundary} lub niższym" if role == "FAVORITE" else f"{boundary} lub mniejszym"
    if max_abs is None:
        boundary = _signed_spread(_signed_abs_for_role(min_abs, role))
        return f"{boundary} lub niżej" if role == "FAVORITE" else f"{boundary} lub większym"
    start = _signed_spread(_signed_abs_for_role(min_abs, role))
    end = _signed_spread(_signed_abs_for_role(max_abs, role))
    if role == "FAVORITE":
        start, end = end, start
    return f"od {start} do {end}"


def _signed_abs_for_role(value: float, role: str) -> float:
    if role == "FAVORITE":
        return -abs(value)
    if role == "UNDERDOG":
        return abs(value)
    return 0.0
