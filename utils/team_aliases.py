"""Canonical NFL team-code normalization."""

from __future__ import annotations

from typing import Any

TEAM_ALIASES = {
    "LAR": "LA",
    "STL": "LA",
    "OAK": "LV",
    "SD": "LAC",
}


def normalize_team_code(value: Any) -> str:
    """Return the project-canonical team code for historical/current aliases."""

    code = str(value or "").strip().upper()
    return TEAM_ALIASES.get(code, code)
