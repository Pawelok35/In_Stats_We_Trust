"""State and path helpers for Live Scenario.

Functions with the `_legacy` suffix intentionally mirror the current behavior
from `scripts.live_quarter_scenario_matrix`. They are used to compare the new
core package against the legacy implementation before V2 changes are enabled.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from live_scenario.config import QUARTERS, RESULTS, STATE_RESULTS


@dataclass(frozen=True)
class QuarterScore:
    team_a: int
    opponent: int


@dataclass(frozen=True)
class LiveCurrentState:
    team_a: str
    opponent: str
    completed_quarters: int
    quarter_scores: tuple[QuarterScore, ...]
    team_a_quarter_result_path: str
    opponent_quarter_result_path: str
    team_a_cumulative_state_path: str
    opponent_cumulative_state_path: str
    team_a_path: str
    opponent_path: str
    team_a_score: int
    opponent_score: int
    margin: int
    margin_bucket: str


def result_from_margin(margin: float) -> str:
    if margin > 0:
        return "WIN"
    if margin < 0:
        return "LOSS"
    return "TIE"


def state_after_margin(margin: float) -> str:
    return result_from_margin(margin)


def cumulative_state_from_margin(margin: float) -> str:
    if margin > 0:
        return "LEAD"
    if margin < 0:
        return "TRAIL"
    return "TIE"


def margin_bucket_legacy(margin: float) -> str:
    if margin == 0:
        return "TIE"
    prefix = "LEAD" if margin > 0 else "TRAIL"
    value = abs(margin)
    if value <= 3:
        return f"{prefix}_1_3"
    if value <= 7:
        return f"{prefix}_4_7"
    if value <= 14:
        return f"{prefix}_8_14"
    return f"{prefix}_15_PLUS"


def margin_bucket_v2(margin: int | float) -> str:
    if margin <= -15:
        return "TRAILING_15_PLUS"
    if margin <= -8:
        return "TRAILING_8_TO_14"
    if margin <= -1:
        return "TRAILING_1_TO_7"
    if margin == 0:
        return "TIED"
    if margin <= 7:
        return "LEADING_1_TO_7"
    if margin <= 14:
        return "LEADING_8_TO_14"
    return "LEADING_15_PLUS"


def spread_bucket(abs_spread: float | None) -> str:
    if abs_spread is None or math.isnan(abs_spread):
        return "UNKNOWN"
    if abs_spread <= 1.5:
        return "0.5-1.5"
    if abs_spread <= 3:
        return "2-3"
    if abs_spread <= 4.5:
        return "3.5-4.5"
    if abs_spread <= 6:
        return "5-6"
    if abs_spread <= 7:
        return "6.5-7"
    if abs_spread <= 9.5:
        return "7.5-9.5"
    if abs_spread <= 13.5:
        return "10-13.5"
    return "14+"


def season_phase_legacy(week: int) -> str:
    if week <= 5:
        return "EARLY"
    if week <= 11:
        return "MIDDLE"
    return "LATE"


def season_phase_v2(week: int, *, is_playoff: bool = False) -> str:
    if is_playoff:
        return "PLAYOFFS"
    if week < 1:
        raise ValueError("Regular-season week must be >= 1.")
    if week <= 4:
        return "EARLY"
    if week <= 12:
        return "MID"
    if week <= 18:
        return "LATE"
    raise ValueError("Week > 18 requires is_playoff=True.")


def path_key(path: tuple[str, ...]) -> str:
    return "START" if not path else "-".join(path)


def parse_path(raw: str | None) -> tuple[str, ...]:
    if not raw or raw.upper() == "START":
        return ()
    parts = tuple(part.strip().upper() for part in raw.replace(">", "-").split("-") if part.strip())
    invalid = [part for part in parts if part not in RESULTS]
    if invalid:
        raise ValueError(f"Invalid path result(s): {invalid}.")
    if len(parts) > 4:
        raise ValueError("Path can contain at most four quarter results.")
    return parts


def parse_cumulative_state_path(raw: str | None) -> tuple[str, ...]:
    if not raw or raw.upper() == "START":
        return ()
    parts = tuple(part.strip().upper() for part in raw.replace(">", "-").split("-") if part.strip())
    invalid = [part for part in parts if part not in STATE_RESULTS]
    if invalid:
        raise ValueError(f"Invalid cumulative state path result(s): {invalid}.")
    if len(parts) > 4:
        raise ValueError("Cumulative state path can contain at most four quarter states.")
    return parts


def mirror_path(path: str | tuple[str, ...]) -> str:
    swap = {"WIN": "LOSS", "LOSS": "WIN", "TIE": "TIE"}
    parts = parse_path(path) if isinstance(path, str) else tuple(path)
    invalid = [part for part in parts if part not in RESULTS]
    if invalid:
        raise ValueError(f"Invalid path result(s): {invalid}.")
    return path_key(tuple(swap[part] for part in parts))


def mirror_cumulative_state_path(path: str | tuple[str, ...]) -> str:
    swap = {"LEAD": "TRAIL", "TRAIL": "LEAD", "TIE": "TIE"}
    parts = parse_cumulative_state_path(path) if isinstance(path, str) else tuple(path)
    invalid = [part for part in parts if part not in STATE_RESULTS]
    if invalid:
        raise ValueError(f"Invalid cumulative state path result(s): {invalid}.")
    return path_key(tuple(swap[part] for part in parts))


def build_current_state_from_quarters(
    *,
    team_a: str,
    opponent: str,
    quarter_scores: list[tuple[int, int]] | tuple[tuple[int, int], ...],
) -> LiveCurrentState:
    if not team_a or not opponent:
        raise ValueError("team_a and opponent are required.")
    if not quarter_scores:
        raise ValueError("At least one completed quarter is required.")
    if len(quarter_scores) > len(QUARTERS):
        raise ValueError("At most four completed quarters are supported.")

    scores = tuple(QuarterScore(int(team), int(opp)) for team, opp in quarter_scores)
    for score in scores:
        if score.team_a < 0 or score.opponent < 0:
            raise ValueError("Quarter points cannot be negative.")

    path_parts = tuple(result_from_margin(score.team_a - score.opponent) for score in scores)
    cumulative_parts = []
    running_team = 0
    running_opponent = 0
    for score in scores:
        running_team += score.team_a
        running_opponent += score.opponent
        cumulative_parts.append(cumulative_state_from_margin(running_team - running_opponent))
    team_a_score = sum(score.team_a for score in scores)
    opponent_score = sum(score.opponent for score in scores)
    margin = team_a_score - opponent_score
    team_a_quarter_result_path = path_key(path_parts)
    opponent_quarter_result_path = mirror_path(path_parts)
    team_a_cumulative_state_path = path_key(tuple(cumulative_parts))
    opponent_cumulative_state_path = mirror_cumulative_state_path(tuple(cumulative_parts))

    return LiveCurrentState(
        team_a=team_a.strip().upper(),
        opponent=opponent.strip().upper(),
        completed_quarters=len(scores),
        quarter_scores=scores,
        team_a_quarter_result_path=team_a_quarter_result_path,
        opponent_quarter_result_path=opponent_quarter_result_path,
        team_a_cumulative_state_path=team_a_cumulative_state_path,
        opponent_cumulative_state_path=opponent_cumulative_state_path,
        team_a_path=team_a_quarter_result_path,
        opponent_path=opponent_quarter_result_path,
        team_a_score=team_a_score,
        opponent_score=opponent_score,
        margin=margin,
        margin_bucket=margin_bucket_v2(margin),
    )
