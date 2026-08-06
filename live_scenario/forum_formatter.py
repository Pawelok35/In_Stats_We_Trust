"""Deterministic bilingual forum formatter for Live Scenario V2 reports."""

from __future__ import annotations

import math
from typing import Any

EN_DASH = "–"
EM_DASH = "—"
FORUM_SPREAD_MIN_SAMPLE = 30
DEFAULT_LOCALE = "pl-PL"
SUPPORTED_LOCALES = ("pl-PL", "en-US")

QUALITY = {
    "pl-PL": {
        "NO_DATA": "brak danych",
        "VERY_LOW": "bardzo mała",
        "LOW": "mała",
        "MODERATE": "umiarkowana",
        "STRONG": "duża",
    },
    "en-US": {
        "NO_DATA": "no data",
        "VERY_LOW": "very small",
        "LOW": "small",
        "MODERATE": "moderate",
        "STRONG": "large",
    },
}


def build_forum_post(
    report: dict,
    language: str = "pl",
    *,
    locale: str | None = None,
    include_disclaimer: bool = True,
) -> str:
    """Build a forum post from one report without recalculating statistics.

    ``language`` is retained for backward compatibility. New callers should
    pass ``locale="pl-PL"`` or ``locale="en-US"``.
    """
    selected_locale = _resolve_locale(locale or language)
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

    team = _clean_text(
        state.get("team_a") or forum.get("matchup", "TEAM").split(" vs ")[0]
    ) or _unavailable(selected_locale)
    opponent = _clean_text(state.get("opponent")) or _unavailable(selected_locale)
    team_score = _int_or_none(state.get("team_a_score"))
    opponent_score = _int_or_none(state.get("opponent_score"))
    margin = _int_or_none(state.get("margin"))
    quarter_path = _clean_text(
        state.get("team_a_quarter_result_path")
        or state.get("team_a_path")
        or forum.get("quarter_result_path")
    )
    cumulative_path = _clean_text(
        state.get("team_a_cumulative_state_path") or forum.get("cumulative_state_path")
    )
    margin_bucket = _clean_text(state.get("margin_bucket") or forum.get("margin_bucket"))
    start_year, end_year = _history_year_range(report)

    lines = [
        "🏈 NFL HALFTIME SCENARIO",
        "",
        _score_header(selected_locale, team, opponent, team_score, opponent_score),
        "",
        _quarter_line("Q1", team, opponent, report, 1, selected_locale),
        _quarter_line("Q2", team, opponent, report, 2, selected_locale),
        "",
        _flow_sentence(
            selected_locale,
            team,
            quarter_path,
            cumulative_path,
            margin,
            margin_bucket,
        ),
        "",
        _scenario_block(selected_locale, quarter_path, cumulative_path, margin),
        "",
        _league_block(
            selected_locale,
            report,
            start_year,
            end_year,
            cumulative_path,
            margin_bucket,
            broad,
        ),
        "",
        *_team_history_block(selected_locale, team, team_history),
        "",
        *_opponent_history_block(
            selected_locale,
            opponent,
            margin,
            opponent_history,
            opponent_reference,
        ),
        "",
        *_spread_block(
            selected_locale,
            team,
            pregame,
            spread_levels,
            spread_selected,
        ),
    ]
    if include_disclaimer:
        lines.extend(["", _disclaimer(selected_locale)])
    return _remove_forbidden_terms("\n".join(lines)).strip()


def _resolve_locale(value: str) -> str:
    aliases = {"pl": "pl-PL", "en": "en-US", "pl-pl": "pl-PL", "en-us": "en-US"}
    normalized = aliases.get(str(value).strip().lower(), value)
    if normalized not in SUPPORTED_LOCALES:
        raise ValueError(f"Unsupported locale {value!r}; use pl-PL or en-US.")
    return normalized


def _as_dict(value: Any) -> dict:
    return value if isinstance(value, dict) else {}


def _clean_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return "" if text.lower() in {"none", "null", "nan", "unknown"} else text


def _remove_forbidden_terms(text: str) -> str:
    replacements = {"BET": "B.T", "PICK": "P.CK", "VALUE BET": "V.B.", "LOCK": "L.CK"}
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


def _pct(value: Any, locale: str) -> str | None:
    number = _float_or_none(value)
    if number is None:
        return None
    rendered = f"{number * 100:.1f}"
    if locale == "pl-PL":
        rendered = rendered.replace(".", ",")
    return f"{rendered}%"


def _record(node: dict) -> str:
    wins = _int_or_none(node.get("wins")) or 0
    losses = _int_or_none(node.get("losses")) or 0
    ties = _int_or_none(node.get("ties")) or 0
    return f"{wins}{EN_DASH}{losses}{EN_DASH}{ties}" if ties else f"{wins}{EN_DASH}{losses}"


def _sample(node: dict) -> int | None:
    return _int_or_none(node.get("sample_size"))


def _quality(value: Any, locale: str) -> str:
    return QUALITY[locale].get(_clean_text(value), QUALITY[locale]["NO_DATA"])


def _unavailable(locale: str) -> str:
    return "brak danych" if locale == "pl-PL" else "unavailable"


def _score(team_score: int | None, opponent_score: int | None, locale: str) -> str:
    if team_score is None or opponent_score is None:
        return _unavailable(locale)
    return f"{team_score}{EN_DASH}{opponent_score}"


def _score_header(
    locale: str,
    team: str,
    opponent: str,
    team_score: int | None,
    opponent_score: int | None,
) -> str:
    suffix = "przerwa" if locale == "pl-PL" else "HALFTIME"
    return f"{team} {_score(team_score, opponent_score, locale)} {opponent} {EM_DASH} {suffix}"


def _quarter_line(
    label: str,
    team: str,
    opponent: str,
    report: dict,
    quarter: int,
    locale: str,
) -> str:
    summary = _as_dict(report.get("forum_content_summary"))
    scores = _as_dict(summary.get("quarter_scores_q1_q2_q3"))
    node = _as_dict(scores.get(f"q{quarter}"))
    if not node:
        for row in summary.get("quarter_scores", []) or []:
            if isinstance(row, dict) and _int_or_none(row.get("quarter")) == quarter:
                node = row
                break
    team_points = _int_or_none(node.get("team_a_points"))
    opponent_points = _int_or_none(node.get("opponent_points"))
    return f"{label}: {team} {_score(team_points, opponent_points, locale)} {opponent}"


def _flow_sentence(
    locale: str,
    team: str,
    quarter_path: str,
    cumulative_path: str,
    margin: int | None,
    bucket: str,
) -> str:
    deficit = abs(margin or 0)
    points = _points(deficit, locale)
    if locale == "pl-PL":
        if cumulative_path == "LEAD-TRAIL":
            return f"{team} prowadziło po Q1, ale do przerwy przegrywa różnicą {points}."
        if cumulative_path == "TRAIL-LEAD":
            return f"{team} przegrywało po Q1, ale do przerwy prowadzi różnicą {points}."
        if cumulative_path == "LEAD-LEAD":
            return f"{team} prowadziło po Q1 i utrzymało prowadzenie do przerwy."
        if cumulative_path == "TRAIL-TRAIL":
            return f"{team} przegrywało po Q1 i nadal przegrywa do przerwy."
        if cumulative_path.endswith("TIE"):
            return f"{team} doprowadziło do remisu do przerwy."
        return f"Przebieg meczu {team}: {quarter_path or 'brak danych'}."
    if cumulative_path == "LEAD-TRAIL":
        return f"{team} led after the first quarter but trails by {points} at halftime."
    if cumulative_path == "TRAIL-LEAD":
        return f"{team} trailed after the first quarter but leads by {points} at halftime."
    if cumulative_path == "LEAD-LEAD":
        return f"{team} led after the first quarter and still leads at halftime."
    if cumulative_path == "TRAIL-TRAIL":
        return f"{team} trailed after the first quarter and still trails at halftime."
    if cumulative_path.endswith("TIE"):
        return f"{team} reached a tie at halftime."
    return f"Game flow for {team}: {quarter_path or 'unavailable'}."


def _scenario_block(
    locale: str, quarter_path: str, cumulative_path: str, margin: int | None
) -> str:
    label = "SCENARIUSZ" if locale == "pl-PL" else "SCENARIO"
    if margin is None:
        margin_line = (
            "• Margin do przerwy: brak danych"
            if locale == "pl-PL"
            else "• Halftime margin: unavailable"
        )
    elif margin < 0:
        margin_line = (
            f"• Strata do przerwy: {_points(abs(margin), locale)}"
            if locale == "pl-PL"
            else f"• Halftime deficit: {_points(abs(margin), locale)}"
        )
    else:
        margin_line = (
            f"• Przewaga do przerwy: {_points(margin, locale)}"
            if locale == "pl-PL"
            else f"• Halftime lead: {_points(margin, locale)}"
        )
    return "\n".join(
        [
            label,
            "",
            f"• Quarter Path: {_display(quarter_path, locale)}",
            f"• Game State Path: {_display(cumulative_path, locale)}",
            margin_line,
        ]
    )


def _league_block(
    locale: str,
    report: dict,
    start_year: int,
    end_year: int,
    path: str,
    bucket: str,
    node: dict,
) -> str:
    if locale == "pl-PL":
        heading = f"📊 LIGA — SEZONY REGULARNE {start_year}{EN_DASH}{end_year}"
        description = (
            f"W sezonach {start_year}{EN_DASH}{end_year} {_state_description_pl(path, bucket)}"
        )
        labels = ("Bilans", "Wygrane", "Próba")
    else:
        heading = f"📊 LEAGUE — {start_year}{EN_DASH}{end_year} REGULAR SEASONS"
        description = (
            f"In seasons {start_year}{EN_DASH}{end_year}, {_state_description_en(path, bucket)}"
        )
        labels = ("Record", "Win rate", "Sample")
    probability = _pct(node.get("raw_probability"), locale) or _unavailable(locale)
    sample = _sample(node)
    sample_text = str(sample) if sample is not None else _unavailable(locale)
    return "\n".join(
        [
            heading,
            "",
            description,
            "",
            f"{labels[0]}: {_record(node)}",
            f"{labels[1]}: {probability}",
            f"{labels[2]}: {sample_text}",
        ]
    )


def _team_history_block(locale: str, team: str, node: dict) -> list[str]:
    heading = (
        f"🔹 {team} W PODOBNYCH SYTUACJACH"
        if locale == "pl-PL"
        else f"🔹 {team} IN SIMILAR SITUATIONS"
    )
    sample = _sample(node)
    if not sample:
        message = (
            f"Brak wcześniejszych przypadków {team}."
            if locale == "pl-PL"
            else f"No previous {team} cases."
        )
        return [heading, "", message]
    quality = _quality(node.get("sample_quality"), locale)
    raw = _pct(node.get("raw_probability"), locale) or _unavailable(locale)
    adjusted = _pct(node.get("adjusted_probability"), locale) or _unavailable(locale)
    if locale == "pl-PL":
        correction = f"Po korekcie wielkości próby: {adjusted}"
        return [
            heading,
            "",
            f"Bilans: {_record(node)}",
            f"Surowy wynik: {raw}",
            correction,
            "",
            f"Próba: {sample} — jakość: {quality}",
        ]
    correction = f"Adjusted for sample size: {adjusted}"
    return [
        heading,
        "",
        f"Record: {_record(node)}",
        f"Raw result: {raw}",
        correction,
        "",
        f"Sample: {sample} — quality: {quality}",
    ]


def _opponent_history_block(
    locale: str,
    opponent: str,
    team_margin: int | None,
    node: dict,
    reference: dict,
) -> list[str]:
    heading = (
        f"🔹 {opponent} W SYTUACJI LUSTRZANEJ"
        if locale == "pl-PL"
        else f"🔹 {opponent} IN THE MIRROR SITUATION"
    )
    sample = _sample(node)
    if not sample:
        message = (
            f"Brak wcześniejszych przypadków {opponent} w sytuacji lustrzanej."
            if locale == "pl-PL"
            else f"No previous {opponent} mirror cases."
        )
        return [heading, "", message]
    raw = _pct(node.get("raw_probability"), locale) or _unavailable(locale)
    adjusted = _pct(node.get("adjusted_probability"), locale) or _unavailable(locale)
    baseline = _pct(
        reference.get("raw_probability") or node.get("opponent_league_reference_probability"),
        locale,
    ) or _unavailable(locale)
    quality = _quality(node.get("sample_quality"), locale)
    if team_margin is not None and team_margin > 0:
        balance_pl, balance_en = "Bilans powrotów", "Comeback record"
        average_pl, average_en = "Średnia ligowa dla takich powrotów", "League average"
    elif team_margin is not None and team_margin < 0:
        balance_pl, balance_en = "Bilans utrzymania prowadzenia", "Lead-hold record"
        average_pl, average_en = "Średnia ligowa dla utrzymania prowadzenia", "League average"
    else:
        balance_pl, balance_en = "Bilans w lustrzanej sytuacji", "Mirror-situation record"
        average_pl, average_en = "Średnia ligowa", "League average"
    if locale == "pl-PL":
        return [
            heading,
            "",
            f"{balance_pl}: {_record(node)}",
            f"Surowy wynik: {raw}",
            f"Po korekcie wielkości próby: {adjusted}",
            "",
            f"{average_pl}: {baseline}",
            f"Próba: {sample} — jakość: {quality}",
        ]
    return [
        heading,
        "",
        f"{balance_en}: {_record(node)}",
        f"Raw result: {raw}",
        f"Adjusted for sample size: {adjusted}",
        "",
        f"{average_en}: {baseline}",
        f"Sample: {sample} — quality: {quality}",
    ]


def _spread_block(locale: str, team: str, pregame: dict, levels: dict, selected: dict) -> list[str]:
    heading = "💰 PREGAME SPREAD"
    spread = _float_or_none(pregame.get("team_a_closing_spread"))
    if spread is None:
        return [
            heading,
            "",
            "Pregame spread: brak danych." if locale == "pl-PL" else "Pregame spread: unavailable.",
        ]
    lines = [heading, "", f"{team} {_signed_spread(spread, locale)}", ""]
    selected_context = _select_forum_spread_context(levels, selected)
    if selected_context is None:
        low_sample = _best_low_sample_spread_context(levels, selected)
        if low_sample:
            label, node = low_sample
            lines.append(_low_sample_spread_sentence(label, spread, node, locale))
        return lines
    label, node = selected_context
    probability = _pct(node.get("raw_probability"), locale)
    if probability is None:
        return lines
    role = _clean_text(pregame.get("team_a_role"))
    quality = _quality(node.get("sample_quality"), locale)
    if label == "role_only_match" and role == "UNDERDOG":
        sentence = (
            "Przedmeczowi underdogowie w takim położeniu " f"wygrywali {probability} spotkań."
            if locale == "pl-PL"
            else f"Pregame underdogs in this situation had a {probability} win rate."
        )
    elif locale == "pl-PL":
        sentence = f"Drużyny z podobnym kontekstem spreadu wygrywały {probability} spotkań."
    else:
        sentence = f"Teams with this spread context had a {probability} win rate."
    lines.extend(
        [
            sentence,
            (f"Bilans: {_record(node)}" if locale == "pl-PL" else f"Record: {_record(node)}"),
            (
                f"Próba: {_sample(node)} — jakość: {quality}"
                if locale == "pl-PL"
                else f"Sample: {_sample(node)} — quality: {quality}"
            ),
        ]
    )
    return lines


def _history_year_range(report: dict) -> tuple[int, int]:
    seasons = report.get("seasons_included")
    if isinstance(seasons, list) and seasons:
        numbers = [_int_or_none(season) for season in seasons]
        numbers = [number for number in numbers if number is not None]
        if numbers:
            return min(numbers), max(numbers)
    return 2015, 2025


def _state_description_pl(path: str, bucket: str) -> str:
    margin = _bucket_text(bucket, "pl-PL")
    descriptions = {
        "LEAD-TRAIL": f"drużyny, które prowadziły po Q1, ale do przerwy przegrywały {margin}:",
        "LEAD-LEAD": (
            f"drużyny, które prowadziły po Q1 i Q2 oraz miały " f"{margin} przewagi do przerwy:"
        ),
        "TRAIL-LEAD": f"drużyny, które przegrywały po Q1, ale do przerwy prowadziły {margin}:",
        "TRAIL-TRAIL": f"drużyny, które przegrywały po Q1 i po Q2 {margin}:",
    }
    return descriptions.get(path, "drużyny w takim stanie meczu:")


def _state_description_en(path: str, bucket: str) -> str:
    margin = _bucket_text(bucket, "en-US")
    descriptions = {
        "LEAD-TRAIL": f"teams that led after Q1 but trailed by {margin} at halftime:",
        "LEAD-LEAD": f"teams that led after Q1 and Q2 with a {margin} halftime lead:",
        "TRAIL-LEAD": f"teams that trailed after Q1 but led by {margin} at halftime:",
        "TRAIL-TRAIL": f"teams that trailed after Q1 and after Q2 by {margin}:",
    }
    return descriptions.get(path, "teams in this game state:")


def _bucket_text(bucket: str, locale: str) -> str:
    mapping = {
        "LEADING_1_TO_7": "1–7 punktów" if locale == "pl-PL" else "1–7 points",
        "TRAILING_1_TO_7": "1–7 punktów" if locale == "pl-PL" else "1–7 points",
        "LEADING_8_TO_14": "8–14 punktów" if locale == "pl-PL" else "8–14 points",
        "TRAILING_8_TO_14": "8–14 punktów" if locale == "pl-PL" else "8–14 points",
        "LEADING_15_PLUS": "co najmniej 15 punktów" if locale == "pl-PL" else "at least 15 points",
        "TRAILING_15_PLUS": "co najmniej 15 punktów" if locale == "pl-PL" else "at least 15 points",
    }
    return mapping.get(
        bucket, "takim przedziale punktowym" if locale == "pl-PL" else "this point range"
    )


def _points(value: int, locale: str) -> str:
    if locale == "pl-PL":
        word = "punkt" if value == 1 else "punkty" if 2 <= value <= 4 else "punktów"
        return f"{value} {word}"
    return f"{value} point" if value == 1 else f"{value} points"


def _display(value: str, locale: str) -> str:
    return value or _unavailable(locale)


def _disclaimer(locale: str) -> str:
    return (
        "Historyczne dane — nie są automatycznymi typami live."
        if locale == "pl-PL"
        else "Historical context only — not an automatic live decision."
    )


def _signed_spread(spread: float, locale: str) -> str:
    value = f"{abs(spread):g}"
    if locale == "pl-PL":
        value = value.replace(".", ",")
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
    if (
        selected_level in {"exact_spread_match", "spread_bucket_match", "role_only_match"}
        and (_int_or_none(selected.get("sample_size")) or 0) >= FORUM_SPREAD_MIN_SAMPLE
    ):
        return selected_level, selected
    return None


def _best_low_sample_spread_context(levels: dict, selected: dict) -> tuple[str, dict] | None:
    candidates: list[tuple[str, dict]] = []
    for label in ("exact_spread_match", "spread_bucket_match", "role_only_match"):
        node = _as_dict(levels.get(label))
        if (_int_or_none(node.get("sample_size")) or 0) > 0:
            candidates.append((label, node))
    if not candidates and (_int_or_none(selected.get("sample_size")) or 0) > 0:
        candidates.append(
            (_clean_text(selected.get("selected_level") or selected.get("name")), selected)
        )
    return (
        max(candidates, key=lambda item: _int_or_none(item[1].get("sample_size")) or 0)
        if candidates
        else None
    )


def _low_sample_spread_sentence(label: str, spread: float, node: dict, locale: str) -> str:
    sample = _sample(node) or 0
    if locale == "pl-PL":
        return (
            f"Dla {_signed_spread(spread, locale)} znaleziono tylko {sample} "
            "podobnych przypadków — traktuj ten fragment wyłącznie jako kontekst."
        )
    return (
        f"Only {sample} similar cases were found for "
        f"{_signed_spread(spread, locale)} — treat this as context only."
    )
