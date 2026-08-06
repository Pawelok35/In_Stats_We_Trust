"""Batch-after-halftime orchestration for Live Scenario.

The batch layer owns only operator state, validation, ordering, and composition.
Each READY game is still calculated by the existing V2 service and formatted by
the existing forum formatter.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

import pandas as pd

from live_scenario.forum_formatter import build_forum_post
from live_scenario.service import build_basic_after_q_report
from live_scenario.spread import build_pregame_spread_context
from live_scenario.state import build_current_state_from_quarters
from live_scenario.week_games import WeekGame

BATCH_STATUSES = (
    "NOT_AT_HALFTIME",
    "READY",
    "INCLUDED",
    "EXCLUDED",
    "ERROR",
)
ACCEPTED_EMPTY_STATUSES = {"NOT_AT_HALFTIME", "EXCLUDED"}


class BatchValidationError(ValueError):
    """Raised when strict batch generation cannot include every game safely."""

    def __init__(self, issues: dict[str, str]) -> None:
        self.issues = issues
        details = "\n".join(f"- {game_id}: {reason}" for game_id, reason in issues.items())
        super().__init__(f"Batch validation failed:\n{details}")


@dataclass
class BatchGameInput:
    """Operator-editable halftime state for one scheduled game."""

    game: WeekGame
    q1_away: str = ""
    q1_home: str = ""
    q2_away: str = ""
    q2_home: str = ""
    spread_away: str = ""
    status: str = "NOT_AT_HALFTIME"
    error: str = ""
    updated_at_utc: str = ""

    @property
    def game_id(self) -> str:
        return self.game.game_id

    @property
    def label(self) -> str:
        return self.game.label

    def to_dict(self) -> dict[str, Any]:
        return {
            "season": self.game.season,
            "week": self.game.week,
            "game_id": self.game.game_id,
            "away": self.game.away,
            "home": self.game.home,
            "game_date": self.game.game_date,
            "game_time": self.game.game_time,
            "q1_away": self.q1_away,
            "q1_home": self.q1_home,
            "q2_away": self.q2_away,
            "q2_home": self.q2_home,
            "spread_away": self.spread_away,
            "status": self.status,
            "error": self.error,
            "updated_at_utc": self.updated_at_utc,
        }


@dataclass(frozen=True)
class BatchValidation:
    game_id: str
    status: str
    error: str = ""
    q1: tuple[int, int] | None = None
    q2: tuple[int, int] | None = None
    spread: float | None = None


@dataclass(frozen=True)
class BatchGenerationResult:
    text: str
    included_game_ids: tuple[str, ...]
    omitted_game_ids: tuple[str, ...]
    validations: tuple[BatchValidation, ...]
    partial: bool


@dataclass(frozen=True)
class BatchCompleteness:
    total: int
    ready: int
    included: int
    not_at_halftime: int
    excluded: int
    errors: int
    unclassified: int

    def to_dict(self) -> dict[str, int]:
        return asdict(self)


def parse_score(raw: str) -> tuple[int, int]:
    """Parse an away-home score entered as ``7-3`` or ``7:3``."""
    text = str(raw or "").strip()
    separator = "-" if "-" in text else ":"
    parts = [part.strip() for part in text.split(separator)]
    if len(parts) != 2 or any(not part.isdigit() for part in parts):
        raise ValueError("wynik musi miec format AWAY-HOME, np. 7-3")
    values = tuple(int(part) for part in parts)
    if any(value < 0 for value in values):
        raise ValueError("wynik nie moze byc ujemny")
    return values  # type: ignore[return-value]


def parse_spread(raw: str, *, default: float | None = None) -> float | None:
    text = str(raw or "").strip().replace(",", ".")
    if not text:
        return default
    try:
        return float(text)
    except ValueError as exc:
        raise ValueError("spread musi byc liczba w perspektywie AWAY") from exc


def block_options(games: list[WeekGame]) -> list[str]:
    """Return deterministic kickoff-block labels, preserving repo time strings."""
    return sorted({f"{game.game_date} {game.game_time}".strip() for game in games})


def games_for_block(games: list[WeekGame], block: str) -> list[WeekGame]:
    return sorted(
        [game for game in games if f"{game.game_date} {game.game_time}".strip() == block],
        key=lambda game: (game.game_date, game.game_time, game.game_id),
    )


def build_entries(
    games: list[WeekGame],
    *,
    previous: dict[str, BatchGameInput] | None = None,
) -> list[BatchGameInput]:
    previous = previous or {}
    entries: list[BatchGameInput] = []
    for game in games:
        old = previous.get(game.game_id)
        if old is None:
            default_spread = "" if game.spread_line is None else str(game.spread_line)
            entries.append(BatchGameInput(game=game, spread_away=default_spread))
            continue
        entries.append(
            BatchGameInput(
                game=game,
                q1_away=old.q1_away,
                q1_home=old.q1_home,
                q2_away=old.q2_away,
                q2_home=old.q2_home,
                spread_away=old.spread_away,
                status=old.status,
                error=old.error,
                updated_at_utc=old.updated_at_utc,
            )
        )
    return entries


def validate_entry(entry: BatchGameInput) -> BatchValidation:
    status = str(entry.status or "").strip().upper()
    if status in ACCEPTED_EMPTY_STATUSES:
        return BatchValidation(entry.game_id, status)
    if status not in {"READY", "INCLUDED"}:
        return BatchValidation(
            entry.game_id,
            "UNCLASSIFIED",
            "Wybierz READY, NOT_AT_HALFTIME albo EXCLUDED.",
        )
    try:
        q1 = parse_score(f"{entry.q1_away}-{entry.q1_home}")
        q2 = parse_score(f"{entry.q2_away}-{entry.q2_home}")
        spread = parse_spread(entry.spread_away, default=entry.game.spread_line)
    except ValueError as exc:
        return BatchValidation(entry.game_id, "ERROR", str(exc))
    return BatchValidation(entry.game_id, status, q1=q1, q2=q2, spread=spread)


def completeness(entries: list[BatchGameInput]) -> BatchCompleteness:
    validations = [validate_entry(entry) for entry in entries]
    counts = {status: 0 for status in (*BATCH_STATUSES, "UNCLASSIFIED")}
    for validation in validations:
        status = "ERROR" if validation.status == "ERROR" else validation.status
        counts[status] = counts.get(status, 0) + 1
    return BatchCompleteness(
        total=len(entries),
        ready=counts.get("READY", 0),
        included=counts.get("INCLUDED", 0),
        not_at_halftime=counts.get("NOT_AT_HALFTIME", 0),
        excluded=counts.get("EXCLUDED", 0),
        errors=counts.get("ERROR", 0),
        unclassified=counts.get("UNCLASSIFIED", 0),
    )


def _apply_cutoff(rows: pd.DataFrame, cutoff_utc: str) -> pd.DataFrame:
    if "gameday" not in rows.columns:
        return rows
    cutoff = pd.to_datetime(cutoff_utc, utc=True, errors="coerce")
    if pd.isna(cutoff):
        return rows
    dates = pd.to_datetime(rows["gameday"], utc=True, errors="coerce")
    return rows[dates <= cutoff].copy()


def _report_for_entry(
    entry: BatchGameInput,
    validation: BatchValidation,
    historical_rows: pd.DataFrame,
    *,
    data_cutoff_utc: str,
    generated_at_utc: str,
    tie_policy: str,
) -> str:
    if validation.q1 is None or validation.q2 is None:
        raise ValueError("READY entry has no complete Q1/Q2")
    current_state = build_current_state_from_quarters(
        team_a=entry.game.away,
        opponent=entry.game.home,
        quarter_scores=[validation.q1, validation.q2],
    )
    report = build_basic_after_q_report(
        current_state=current_state,
        historical_rows=_apply_cutoff(historical_rows, data_cutoff_utc),
        data_cutoff_utc=data_cutoff_utc,
        generated_at_utc=generated_at_utc,
        tie_policy=tie_policy,
        pregame_spread_context=build_pregame_spread_context(
            team_a_closing_spread=validation.spread,
            team_a_role=entry.game.perspective(entry.game.away).role,
            spread_source=entry.game.spread_source,
            spread_captured_at_utc=entry.game.schedule_timestamp_utc,
            spread_quality=entry.game.spread_status,
        ),
    )
    return build_forum_post(report.to_dict(), language="pl")


def generate_batch_post(
    entries: list[BatchGameInput],
    historical_rows: pd.DataFrame,
    *,
    season: int,
    week: int,
    block: str,
    data_cutoff_utc: str,
    generated_at_utc: str | None = None,
    tie_policy: str = "TIE_AS_LOSS",
    allow_partial: bool = False,
) -> BatchGenerationResult:
    generated_at = generated_at_utc or (
        datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    )
    validations = tuple(validate_entry(entry) for entry in entries)
    for validation in validations:
        if validation.status == "ERROR":
            entry = next(item for item in entries if item.game_id == validation.game_id)
            entry.status = "ERROR"
            entry.error = validation.error
    accepted_statuses = ACCEPTED_EMPTY_STATUSES | {"READY", "INCLUDED"}
    issues = {
        validation.game_id: validation.error or validation.status
        for validation in validations
        if validation.status not in accepted_statuses
    }
    if issues and not allow_partial:
        raise BatchValidationError(issues)

    sections: list[str] = [f"🏈 NFL HALFTIME SCENARIOS — WEEK {week}", f"Block: {block}"]
    included: list[str] = []
    omitted: list[str] = []
    entry_by_id = {entry.game_id: entry for entry in entries}
    ordered_validations = sorted(
        validations,
        key=lambda item: (
            entry_by_id[item.game_id].game.game_date,
            entry_by_id[item.game_id].game.game_time,
            item.game_id,
        ),
    )
    for validation in ordered_validations:
        if validation.status not in {"READY", "INCLUDED"}:
            omitted.append(validation.game_id)
            continue
        entry = entry_by_id[validation.game_id]
        try:
            post = _report_for_entry(
                entry,
                validation,
                historical_rows,
                data_cutoff_utc=data_cutoff_utc,
                generated_at_utc=generated_at,
                tie_policy=tie_policy,
            )
        except Exception as exc:
            entry.status = "ERROR"
            entry.error = str(exc)
            if not allow_partial:
                raise BatchValidationError({entry.game_id: str(exc)}) from exc
            omitted.append(entry.game_id)
            continue
        sections.extend(["", "━" * 60, "", entry.game.label, "", post])
        included.append(entry.game_id)
    return BatchGenerationResult(
        text="\n".join(sections),
        included_game_ids=tuple(included),
        omitted_game_ids=tuple(omitted),
        validations=validations,
        partial=allow_partial,
    )
