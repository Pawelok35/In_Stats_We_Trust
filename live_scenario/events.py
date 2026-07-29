"""Event helpers for Live Scenario legacy compatibility."""

from __future__ import annotations

from typing import Any


def event_probability_from_lookup(
    node: dict[str, Any],
    event: str,
    settlement: str,
) -> tuple[float | None, float | None, float | None]:
    event = event.upper()
    if event == "TEAM_A_WIN_NEXT_QUARTER":
        block = node["next_quarter_distribution"]
    elif event == "TEAM_A_LEAD_AFTER_NEXT_QUARTER":
        block = node["cumulative_after_next_quarter"]
    elif event == "TEAM_A_WIN_FINAL":
        block = node["final_including_overtime"]
    else:
        raise ValueError(
            "Unsupported event. Use TEAM_A_WIN_NEXT_QUARTER, "
            "TEAM_A_LEAD_AFTER_NEXT_QUARTER, or TEAM_A_WIN_FINAL."
        )
    win_p = block.get("win_probability")
    loss_p = block.get("loss_probability")
    tie_p = block.get("tie_probability")
    if settlement == "TIE_IS_LOSS" and tie_p is not None and loss_p is not None:
        loss_p = loss_p + tie_p
        tie_p = 0.0
    return win_p, loss_p, tie_p

