"""Durable append-only JSONL implementation of the pregame event store."""

from __future__ import annotations

import json
import os
from pathlib import Path
from threading import RLock
from typing import Any

from pydantic import ValidationError

from pregame.contracts import PregameEvent
from pregame.store import AppendResult, AppendStatus


class EventStoreCorruptionError(ValueError):
    """Raised when an existing JSONL event log cannot be trusted."""

    def __init__(self, path: Path, line_number: int, reason: str) -> None:
        self.path = path
        self.line_number = line_number
        self.reason = reason
        super().__init__(f"Corrupt event log {path} at line {line_number}: {reason}")


class JsonlPregameEventStore:
    """Single-process JSONL event store with append-only write semantics.

    Existing events are indexed during initialization. New appends serialize one
    complete UTF-8 JSON line, flush it, and request an OS-level fsync before the
    in-memory index is updated.
    """

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self._lock = RLock()
        self._events_by_id: dict[str, PregameEvent] = {}
        self._duplicate_event_ids: set[str] = set()
        self._load_existing()

    @property
    def duplicate_event_ids(self) -> tuple[str, ...]:
        """Return redundant identical IDs observed in the existing physical log."""

        return tuple(sorted(self._duplicate_event_ids))

    def append(self, event: PregameEvent) -> AppendResult:
        """Append one new event or return the existing idempotency result."""

        with self._lock:
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

            line = self._serialize_event(event)
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8", newline="\n") as handle:
                handle.write(line)
                handle.flush()
                os.fsync(handle.fileno())

            self._events_by_id[event.event_id] = self._clone_event(event)
            return AppendResult(status=AppendStatus.APPENDED, event_id=event.event_id)

    def get_event(self, event_id: str) -> PregameEvent | None:
        """Return a defensive copy of the event identified by event_id."""

        with self._lock:
            event = self._events_by_id.get(event_id)
            return None if event is None else self._clone_event(event)

    def list_events(self, game_id: str) -> list[PregameEvent]:
        """Return one game's events in deterministic logical rather than file order."""

        return [event for event in self.list_all_events() if event.game_id == game_id]

    def list_all_events(self) -> list[PregameEvent]:
        """Return all events in deterministic logical rather than file order."""

        with self._lock:
            ordered = sorted(
                self._events_by_id.values(),
                key=lambda event: (
                    event.effective_at_utc,
                    event.created_at_utc,
                    event.event_id,
                ),
            )
            return [self._clone_event(event) for event in ordered]

    def contains(self, event_id: str) -> bool:
        """Return whether an event exists in the indexed event history."""

        with self._lock:
            return event_id in self._events_by_id

    def _load_existing(self) -> None:
        if not self.path.exists():
            return

        with self.path.open("r", encoding="utf-8") as handle:
            for line_number, raw_line in enumerate(handle, start=1):
                event = self._deserialize_line(raw_line, line_number)
                stored = self._events_by_id.get(event.event_id)
                if stored is None:
                    self._events_by_id[event.event_id] = event
                    continue
                if self._canonical_event(stored) == self._canonical_event(event):
                    self._duplicate_event_ids.add(event.event_id)
                    continue
                raise EventStoreCorruptionError(
                    self.path,
                    line_number,
                    f"duplicate event_id {event.event_id!r} has conflicting content",
                )

    def _deserialize_line(self, raw_line: str, line_number: int) -> PregameEvent:
        try:
            payload: Any = json.loads(raw_line)
        except json.JSONDecodeError as exc:
            raise EventStoreCorruptionError(self.path, line_number, "invalid JSON") from exc
        if not isinstance(payload, dict):
            raise EventStoreCorruptionError(
                self.path, line_number, "event line must be a JSON object"
            )
        try:
            return PregameEvent.model_validate(payload)
        except ValidationError as exc:
            raise EventStoreCorruptionError(
                self.path,
                line_number,
                f"invalid PregameEvent schema: {exc.errors()[0]['msg']}",
            ) from exc

    @staticmethod
    def _serialize_event(event: PregameEvent) -> str:
        return (
            json.dumps(
                event.to_json_dict(),
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            )
            + "\n"
        )

    @staticmethod
    def _clone_event(event: PregameEvent) -> PregameEvent:
        return event.model_copy(deep=True)

    @staticmethod
    def _canonical_event(event: PregameEvent) -> dict[str, Any]:
        return event.to_json_dict()
