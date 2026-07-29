"""Pregame spread context helpers for Live Scenario V2."""

from __future__ import annotations

import math
from dataclasses import dataclass

from live_scenario.state import spread_bucket


@dataclass(frozen=True)
class PregameSpreadContext:
    team_a_closing_spread: float | None
    opponent_closing_spread: float | None
    team_a_role: str
    exact_spread: float | None
    spread_bucket: str
    spread_source: str | None
    spread_captured_at_utc: str | None
    spread_quality: str

    def to_dict(self) -> dict[str, float | str | None]:
        return {
            "team_a_closing_spread": self.team_a_closing_spread,
            "opponent_closing_spread": self.opponent_closing_spread,
            "team_a_role": self.team_a_role,
            "exact_spread": self.exact_spread,
            "spread_bucket": self.spread_bucket,
            "spread_source": self.spread_source,
            "spread_captured_at_utc": self.spread_captured_at_utc,
            "spread_quality": self.spread_quality,
        }


def role_from_team_a_spread(team_a_closing_spread: float | None) -> str:
    if team_a_closing_spread is None or math.isnan(team_a_closing_spread):
        return "UNKNOWN"
    if team_a_closing_spread < 0:
        return "FAVORITE"
    if team_a_closing_spread > 0:
        return "UNDERDOG"
    return "PICKEM"


def build_pregame_spread_context(
    *,
    team_a_closing_spread: float | None = None,
    team_a_role: str | None = None,
    spread_source: str | None = None,
    spread_captured_at_utc: str | None = None,
    spread_quality: str | None = None,
) -> PregameSpreadContext:
    inferred_role = role_from_team_a_spread(team_a_closing_spread)
    normalized_role = team_a_role.strip().upper() if team_a_role else inferred_role
    if normalized_role and normalized_role != inferred_role and inferred_role != "UNKNOWN":
        raise ValueError(
            "team_a_role conflicts with team_a_closing_spread: "
            f"{normalized_role} vs inferred {inferred_role}."
        )

    exact_spread = abs(team_a_closing_spread) if team_a_closing_spread is not None else None
    bucket = "UNKNOWN"
    if exact_spread is not None:
        bucket = spread_bucket(exact_spread)
        prefix = {
            "FAVORITE": "FAV",
            "UNDERDOG": "DOG",
            "PICKEM": "PK",
        }.get(inferred_role, "UNKNOWN")
        bucket = f"{prefix}_{bucket}" if prefix != "UNKNOWN" else "UNKNOWN"

    return PregameSpreadContext(
        team_a_closing_spread=team_a_closing_spread,
        opponent_closing_spread=-team_a_closing_spread
        if team_a_closing_spread is not None
        else None,
        team_a_role=inferred_role if normalized_role == "UNKNOWN" else normalized_role,
        exact_spread=exact_spread,
        spread_bucket=bucket,
        spread_source=spread_source,
        spread_captured_at_utc=spread_captured_at_utc,
        spread_quality=(spread_quality or "UNKNOWN").strip().upper(),
    )
