"""Read-only projection of one pregame game's append-only event history."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from pydantic import ValidationError

from pregame.contracts import (
    CandidateRecord,
    MarketSnapshot,
    OperatorDecision,
    PregameEvent,
    PregameGameRecord,
)
from pregame.events import CandidateStatus, DecisionLevel, PregameEventType
from pregame.store import PregameEventStore


class ProjectionError(ValueError):
    """Raised when a trustworthy current-state view cannot be constructed."""


@dataclass(frozen=True)
class _EffectiveEvent:
    event: PregameEvent
    interpreted_type: PregameEventType


_PASS_THROUGH_EVENT_TYPES = {
    PregameEventType.MODEL_SCAN_COMPLETED,
    PregameEventType.INJURY_UPDATED,
    PregameEventType.ROSTER_UPDATED,
    PregameEventType.WEATHER_UPDATED,
    PregameEventType.PUBLIC_BETTING_UPDATED,
}

_LEVEL_RANK = {
    DecisionLevel.MODEL_CANDIDATE: 1,
    DecisionLevel.RESEARCH_APPROVED: 2,
    DecisionLevel.FINAL_OPERATOR_PICK: 3,
}


def project_events(events: Sequence[PregameEvent]) -> PregameGameRecord:
    """Project a deterministic, immutable read model from one game's events."""

    if not events:
        raise ProjectionError("Cannot project an empty event history.")

    ordered = sorted(events, key=_event_sort_key)
    game_ids = {event.game_id for event in ordered}
    if len(game_ids) != 1:
        raise ProjectionError("All projected events must belong to one game_id.")

    effective_events, correction_warnings = _effective_events(ordered)
    state = _ProjectionState(game_id=ordered[0].game_id)
    state.warnings.extend(correction_warnings)

    for effective_event in effective_events:
        _apply_event(state, effective_event)

    last_event = ordered[-1]
    return PregameGameRecord(
        game_id=state.game_id,
        last_projected_at_utc=last_event.effective_at_utc,
        event_count=len(ordered),
        current_decision_level=state.decision_level,
        season=state.season,
        week=state.week,
        away_team=state.away_team,
        home_team=state.home_team,
        kickoff_utc=state.kickoff_utc,
        venue=state.venue,
        neutral_site=state.neutral_site,
        candidate=state.candidate,
        candidate_status=state.candidate_status,
        selected_team=state.selected_team,
        model_tag=state.model_tag,
        production_eligible=state.production_eligible,
        initial_market_snapshot=state.initial_market_snapshot,
        current_market_snapshot=state.current_market_snapshot,
        final_market_snapshot=state.final_market_snapshot,
        closing_market_snapshot=state.closing_market_snapshot,
        market_snapshot_count=state.market_snapshot_count,
        research_started=state.research_started,
        research_completed=state.research_completed,
        research_approved=state.research_approved,
        latest_research_event_id=state.latest_research_event_id,
        operator_decision=state.operator_decision,
        current_verdict=state.current_verdict,
        settled=state.settled,
        latest_settlement_event_id=state.latest_settlement_event_id,
        last_event_id=last_event.event_id,
        last_effective_at_utc=last_event.effective_at_utc,
        warnings=tuple(state.warnings),
        projection_errors=tuple(state.projection_errors),
    )


def project_game(store: PregameEventStore, game_id: str) -> PregameGameRecord | None:
    """Project one game's history from a store without modifying the store."""

    events = store.list_events(game_id)
    if not events:
        return None
    return project_events(events)


class PregameGameProjector:
    """Small object wrapper for callers that prefer a projector instance."""

    def project_events(self, events: Sequence[PregameEvent]) -> PregameGameRecord:
        return project_events(events)

    def project_game(self, store: PregameEventStore, game_id: str) -> PregameGameRecord | None:
        return project_game(store, game_id)


@dataclass
class _ProjectionState:
    game_id: str
    decision_level: DecisionLevel | None = None
    season: int | None = None
    week: int | None = None
    away_team: str | None = None
    home_team: str | None = None
    kickoff_utc: datetime | None = None
    venue: str | None = None
    neutral_site: bool | None = None
    candidate: CandidateRecord | None = None
    candidate_status: CandidateStatus | None = None
    selected_team: str | None = None
    model_tag: str | None = None
    production_eligible: bool | None = None
    initial_market_snapshot: MarketSnapshot | None = None
    current_market_snapshot: MarketSnapshot | None = None
    final_market_snapshot: MarketSnapshot | None = None
    closing_market_snapshot: MarketSnapshot | None = None
    market_snapshot_count: int = 0
    research_started: bool = False
    research_completed: bool = False
    research_approved: bool = False
    latest_research_event_id: str | None = None
    operator_decision: OperatorDecision | None = None
    current_verdict: Any = None
    settled: bool = False
    latest_settlement_event_id: str | None = None
    warnings: list[str] = None  # type: ignore[assignment]
    projection_errors: list[str] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        self.warnings = []
        self.projection_errors = []


def _event_sort_key(event: PregameEvent) -> tuple[datetime, datetime, str]:
    return event.effective_at_utc, event.created_at_utc, event.event_id


def _effective_events(events: list[PregameEvent]) -> tuple[list[_EffectiveEvent], list[str]]:
    by_id = {event.event_id: event for event in events}
    warnings: list[str] = []
    replacements: dict[str, PregameEvent] = {}

    for correction in (
        event for event in events if event.event_type == PregameEventType.CORRECTION_EVENT
    ):
        target_id = correction.supersedes_event_id
        if target_id is None:
            warnings.append(f"correction_missing_supersedes:{correction.event_id}")
            continue
        if target_id == correction.event_id:
            raise ProjectionError(
                f"Correction event {correction.event_id} cannot supersede itself."
            )
        if target_id not in by_id:
            warnings.append(f"correction_target_missing:{correction.event_id}:{target_id}")
            continue
        previous = replacements.get(target_id)
        if previous is None or _event_sort_key(previous) < _event_sort_key(correction):
            replacements[target_id] = correction

    for correction in replacements.values():
        _validate_correction_chain(correction, replacements)

    effective: list[_EffectiveEvent] = []
    for event in events:
        if event.event_type == PregameEventType.CORRECTION_EVENT:
            continue
        terminal = _terminal_correction(event, replacements)
        effective.append(_EffectiveEvent(event=terminal, interpreted_type=event.event_type))

    return sorted(effective, key=lambda item: _event_sort_key(item.event)), warnings


def _validate_correction_chain(start: PregameEvent, replacements: dict[str, PregameEvent]) -> None:
    seen: set[str] = set()
    current = start
    while current.event_id in replacements:
        if current.event_id in seen:
            raise ProjectionError(f"Correction cycle detected at {current.event_id}.")
        seen.add(current.event_id)
        current = replacements[current.event_id]
    if current.event_id in seen:
        raise ProjectionError(f"Correction cycle detected at {current.event_id}.")


def _terminal_correction(
    event: PregameEvent, replacements: dict[str, PregameEvent]
) -> PregameEvent:
    current = event
    while current.event_id in replacements:
        current = replacements[current.event_id]
    return current


def _apply_event(state: _ProjectionState, effective_event: _EffectiveEvent) -> None:
    event = effective_event.event
    event_type = effective_event.interpreted_type

    if event_type == PregameEventType.GAME_CREATED:
        _apply_game_created(state, event)
    elif event_type in {
        PregameEventType.INITIAL_MARKET_SNAPSHOT,
        PregameEventType.MARKET_QUOTE_UPDATED,
        PregameEventType.FINAL_QUOTE_CAPTURED,
        PregameEventType.CLOSING_QUOTE_CAPTURED,
    }:
        _apply_market_event(state, event, event_type)
    elif event_type == PregameEventType.MODEL_CANDIDATE_CREATED:
        candidate = _parse_payload(event, CandidateRecord, "candidate")
        _ensure_record_game_id(event, candidate.game_id, "CandidateRecord")
        state.candidate = candidate.model_copy(deep=True)
        state.candidate_status = candidate.status
        state.selected_team = candidate.selected_team
        state.model_tag = candidate.model_tag
        state.production_eligible = candidate.production_eligible
        _advance_level(state, DecisionLevel.MODEL_CANDIDATE)
    elif event_type == PregameEventType.MODEL_CANDIDATE_BLOCKED:
        if state.candidate is None:
            state.warnings.append(f"candidate_blocked_without_candidate:{event.event_id}")
        else:
            state.candidate = state.candidate.model_copy(
                update={"status": CandidateStatus.BLOCKED}, deep=True
            )
            state.candidate_status = CandidateStatus.BLOCKED
    elif event_type == PregameEventType.RESEARCH_STARTED:
        state.research_started = True
    elif event_type == PregameEventType.RESEARCH_COMPLETED:
        state.research_completed = True
        state.latest_research_event_id = event.event_id
    elif event_type == PregameEventType.RESEARCH_UPDATED:
        state.latest_research_event_id = event.event_id
    elif event_type == PregameEventType.RESEARCH_APPROVED:
        state.research_approved = True
        state.latest_research_event_id = event.event_id
        _advance_level(state, DecisionLevel.RESEARCH_APPROVED)
    elif event_type in {
        PregameEventType.OPERATOR_PICK_APPROVED,
        PregameEventType.OPERATOR_PICK_REJECTED,
    }:
        _apply_operator_event(state, event, event_type)
    elif event_type == PregameEventType.GAME_SETTLED:
        state.settled = True
        state.latest_settlement_event_id = event.event_id
    elif event_type in _PASS_THROUGH_EVENT_TYPES:
        return
    else:
        state.warnings.append(f"unhandled_event_type:{event_type.value}:{event.event_id}")


def _apply_game_created(state: _ProjectionState, event: PregameEvent) -> None:
    payload = event.payload
    required = ("season", "week", "away_team", "home_team")
    missing = [field for field in required if field not in payload]
    if missing:
        raise ProjectionError(
            f"GAME_CREATED {event.event_id} missing required fields: {', '.join(missing)}."
        )
    if not isinstance(payload["season"], int) or not isinstance(payload["week"], int):
        raise ProjectionError(f"GAME_CREATED {event.event_id} season and week must be integers.")
    for field in ("away_team", "home_team"):
        if not isinstance(payload[field], str) or not payload[field].strip():
            raise ProjectionError(
                f"GAME_CREATED {event.event_id} {field} must be a non-empty string."
            )

    state.season = payload["season"]
    state.week = payload["week"]
    state.away_team = payload["away_team"]
    state.home_team = payload["home_team"]
    state.kickoff_utc = _parse_optional_datetime(payload.get("kickoff_utc"), event.event_id)
    state.venue = _optional_text(payload.get("venue"), "venue", event.event_id)
    state.neutral_site = _optional_bool(payload.get("neutral_site"), "neutral_site", event.event_id)


def _apply_market_event(
    state: _ProjectionState, event: PregameEvent, event_type: PregameEventType
) -> None:
    snapshot = _parse_payload(event, MarketSnapshot, "market snapshot")
    _ensure_record_game_id(event, snapshot.game_id, "MarketSnapshot")
    snapshot = snapshot.model_copy(deep=True)
    state.market_snapshot_count += 1

    if event_type == PregameEventType.INITIAL_MARKET_SNAPSHOT:
        if state.initial_market_snapshot is None:
            state.initial_market_snapshot = snapshot
        else:
            state.warnings.append(f"duplicate_initial_market_snapshot:{event.event_id}")
        if state.current_market_snapshot is None:
            state.current_market_snapshot = snapshot
    elif event_type == PregameEventType.MARKET_QUOTE_UPDATED:
        if state.initial_market_snapshot is None:
            state.warnings.append(f"market_update_without_initial:{event.event_id}")
        state.current_market_snapshot = snapshot
    elif event_type == PregameEventType.FINAL_QUOTE_CAPTURED:
        state.final_market_snapshot = snapshot
        if state.closing_market_snapshot is None:
            state.current_market_snapshot = snapshot
    elif event_type == PregameEventType.CLOSING_QUOTE_CAPTURED:
        state.closing_market_snapshot = snapshot
        state.current_market_snapshot = snapshot


def _apply_operator_event(
    state: _ProjectionState, event: PregameEvent, event_type: PregameEventType
) -> None:
    decision = _parse_payload(event, OperatorDecision, "operator decision")
    _ensure_record_game_id(event, decision.game_id, "OperatorDecision")
    state.operator_decision = decision.model_copy(deep=True)
    state.current_verdict = decision.verdict
    if state.candidate is None:
        state.warnings.append(f"operator_decision_without_candidate:{event.event_id}")
    if event_type == PregameEventType.OPERATOR_PICK_APPROVED:
        _advance_level(state, DecisionLevel.FINAL_OPERATOR_PICK)


def _parse_payload(event: PregameEvent, model_type: type[Any], label: str) -> Any:
    try:
        return model_type.model_validate(event.payload)
    except ValidationError as exc:
        raise ProjectionError(f"Invalid {label} payload for {event.event_id}: {exc}") from exc


def _ensure_record_game_id(event: PregameEvent, record_game_id: str, label: str) -> None:
    if event.game_id != record_game_id:
        raise ProjectionError(
            f"{label}.game_id {record_game_id!r} does not match event game_id {event.game_id!r}."
        )


def _parse_optional_datetime(value: Any, event_id: str) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ProjectionError(f"GAME_CREATED {event_id} kickoff_utc must be timezone-aware.")
        return value.astimezone(timezone.utc)
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ProjectionError(f"GAME_CREATED {event_id} kickoff_utc is invalid.") from exc
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise ProjectionError(f"GAME_CREATED {event_id} kickoff_utc must be timezone-aware.")
        return parsed.astimezone(timezone.utc)
    raise ProjectionError(f"GAME_CREATED {event_id} kickoff_utc must be an ISO datetime.")


def _optional_text(value: Any, field: str, event_id: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ProjectionError(f"GAME_CREATED {event_id} {field} must be a non-empty string.")
    return value


def _optional_bool(value: Any, field: str, event_id: str) -> bool | None:
    if value is None:
        return None
    if not isinstance(value, bool):
        raise ProjectionError(f"GAME_CREATED {event_id} {field} must be boolean.")
    return value


def _advance_level(state: _ProjectionState, level: DecisionLevel) -> None:
    if state.decision_level is None or _LEVEL_RANK[level] > _LEVEL_RANK[state.decision_level]:
        state.decision_level = level
