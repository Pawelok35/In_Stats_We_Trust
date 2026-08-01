"""Append-only event store contracts for the NFL 2026 pregame layer."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from pregame.contracts import PregameEvent


class _StrEnum(str, Enum):
    """Python 3.10 compatible string enum base."""


class AppendStatus(_StrEnum):
    """Result status for an append attempt."""

    APPENDED = "APPENDED"
    ALREADY_EXISTS = "ALREADY_EXISTS"
    CONFLICT = "CONFLICT"


@dataclass(frozen=True)
class AppendResult:
    """Explicit result of an append-only write attempt."""

    status: AppendStatus
    event_id: str
    message: str | None = None


class PregameEventStore(Protocol):
    """Minimal storage interface for append-only pregame events."""

    def append(self, event: PregameEvent) -> AppendResult:
        """Append an event or return an idempotency/conflict result."""

    def get_event(self, event_id: str) -> PregameEvent | None:
        """Return an event by ID, if present."""

    def list_events(self, game_id: str) -> list[PregameEvent]:
        """Return deterministic event history for one game."""

    def list_all_events(self) -> list[PregameEvent]:
        """Return all events in deterministic logical order."""

    def contains(self, event_id: str) -> bool:
        """Return whether event_id exists."""


class InMemoryPregameEventStore:
    """In-memory append-only store for tests and early orchestration work."""

    def __init__(self) -> None:
        self._events_by_id: dict[str, PregameEvent] = {}

    def append(self, event: PregameEvent) -> AppendResult:
        stored = self._events_by_id.get(event.event_id)
        if stored is not None:
            if self._canonical_event(stored) == self._canonical_event(event):
                return AppendResult(
                    status=AppendStatus.ALREADY_EXISTS,
                    event_id=event.event_id,
                    message="Identical event already exists.",
                )
            return AppendResult(
                status=AppendStatus.CONFLICT,
                event_id=event.event_id,
                message="event_id already exists with different content.",
            )

        self._events_by_id[event.event_id] = self._clone_event(event)
        return AppendResult(status=AppendStatus.APPENDED, event_id=event.event_id)

    def get_event(self, event_id: str) -> PregameEvent | None:
        event = self._events_by_id.get(event_id)
        if event is None:
            return None
        return self._clone_event(event)

    def list_events(self, game_id: str) -> list[PregameEvent]:
        return [event for event in self.list_all_events() if event.game_id == game_id]

    def list_all_events(self) -> list[PregameEvent]:
        ordered = sorted(
            self._events_by_id.values(),
            key=lambda event: (event.effective_at_utc, event.created_at_utc, event.event_id),
        )
        return [self._clone_event(event) for event in ordered]

    def contains(self, event_id: str) -> bool:
        return event_id in self._events_by_id

    @staticmethod
    def _clone_event(event: PregameEvent) -> PregameEvent:
        return event.model_copy(deep=True)

    @staticmethod
    def _canonical_event(event: PregameEvent) -> dict:
        return event.to_json_dict()
