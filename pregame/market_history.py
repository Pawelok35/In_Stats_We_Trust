"""Read and append raw market-snapshot history through a pregame event store."""

from __future__ import annotations

from datetime import datetime, timedelta

from pydantic import ValidationError

from pregame.contracts import MarketSnapshot, PregameEvent
from pregame.events import MarketType, PregameEventType, SnapshotKind
from pregame.store import AppendResult, AppendStatus, PregameEventStore

SNAPSHOT_KIND_TO_EVENT_TYPE: dict[SnapshotKind, PregameEventType] = {
    SnapshotKind.INITIAL: PregameEventType.INITIAL_MARKET_SNAPSHOT,
    SnapshotKind.CURRENT: PregameEventType.MARKET_QUOTE_UPDATED,
    SnapshotKind.FINAL: PregameEventType.FINAL_QUOTE_CAPTURED,
    SnapshotKind.CLOSING: PregameEventType.CLOSING_QUOTE_CAPTURED,
}

_MARKET_EVENT_TYPES = frozenset(SNAPSHOT_KIND_TO_EVENT_TYPE.values())


class MarketSnapshotHistoryError(ValueError):
    """Raised when a structurally valid event is market-domain inconsistent."""

    def __init__(self, event_id: str, game_id: str, reason: str) -> None:
        self.event_id = event_id
        self.game_id = game_id
        self.reason = reason
        super().__init__(f"Market snapshot history error for {game_id}/{event_id}: {reason}")


def market_snapshot_event_id(snapshot_id: str) -> str:
    """Return the deterministic event identifier for one market snapshot."""

    if not snapshot_id or not snapshot_id.strip():
        raise ValueError("snapshot_id must not be empty")
    return f"market-snapshot:{snapshot_id}"


class MarketSnapshotHistoryService:
    """Small raw-history service independent of any concrete event-store backend."""

    def __init__(self, store: PregameEventStore) -> None:
        self._store = store

    def record_snapshot(
        self,
        snapshot: MarketSnapshot,
        *,
        recorded_at_utc: datetime,
    ) -> AppendResult:
        """Append a snapshot event, idempotently by snapshot_id.

        recorded_at_utc records ingestion time only. A later retry with the same
        snapshot data returns ALREADY_EXISTS instead of creating a conflict.
        """

        _require_utc(recorded_at_utc)
        event_id = market_snapshot_event_id(snapshot.snapshot_id)
        existing = self._store.get_event(event_id)
        if existing is not None:
            existing_snapshot = self._snapshot_from_event(existing)
            if existing_snapshot.to_json_dict() == snapshot.to_json_dict():
                return AppendResult(
                    status=AppendStatus.ALREADY_EXISTS,
                    event_id=event_id,
                    message="Identical market snapshot already exists.",
                )
            return AppendResult(
                status=AppendStatus.CONFLICT,
                event_id=event_id,
                message="snapshot_id already exists with different content.",
            )

        event = PregameEvent(
            event_id=event_id,
            game_id=snapshot.game_id,
            event_type=SNAPSHOT_KIND_TO_EVENT_TYPE[snapshot.snapshot_kind],
            created_at_utc=recorded_at_utc,
            effective_at_utc=snapshot.captured_at_utc,
            source=snapshot.source,
            idempotency_key=f"market-snapshot:{snapshot.snapshot_id}",
            payload=snapshot.to_json_dict(),
        )
        result = self._store.append(event)
        if result.status != AppendStatus.CONFLICT:
            return result

        concurrent = self._store.get_event(event_id)
        if concurrent is None:
            return result
        existing_snapshot = self._snapshot_from_event(concurrent)
        if existing_snapshot.to_json_dict() == snapshot.to_json_dict():
            return AppendResult(
                status=AppendStatus.ALREADY_EXISTS,
                event_id=event_id,
                message="Identical market snapshot already exists.",
            )
        return result

    def get_snapshot(self, snapshot_id: str) -> MarketSnapshot | None:
        """Return the snapshot identified by its deterministic event ID."""

        event = self._store.get_event(market_snapshot_event_id(snapshot_id))
        if event is None:
            return None
        return self._snapshot_from_event(event)

    def list_snapshots(
        self,
        game_id: str,
        *,
        market_type: MarketType | None = None,
        book: str | None = None,
        snapshot_kind: SnapshotKind | None = None,
    ) -> list[MarketSnapshot]:
        """Return raw, validated snapshots ordered by market capture time.

        Book comparison is exact and case-sensitive to preserve source values.
        """

        entries: list[tuple[MarketSnapshot, PregameEvent]] = []
        for event in self._store.list_events(game_id):
            if event.event_type not in _MARKET_EVENT_TYPES:
                continue
            snapshot = self._snapshot_from_event(event)
            if market_type is not None and snapshot.market_type != market_type:
                continue
            if book is not None and snapshot.book != book:
                continue
            if snapshot_kind is not None and snapshot.snapshot_kind != snapshot_kind:
                continue
            entries.append((snapshot, event))

        entries.sort(
            key=lambda entry: (
                entry[0].captured_at_utc,
                entry[1].created_at_utc,
                entry[1].event_id,
            )
        )
        return [snapshot.model_copy(deep=True) for snapshot, _ in entries]

    def get_latest_snapshot(
        self,
        game_id: str,
        *,
        market_type: MarketType,
        book: str | None = None,
        snapshot_kind: SnapshotKind | None = None,
    ) -> MarketSnapshot | None:
        """Return the newest stored snapshot for one explicit market type."""

        snapshots = self.list_snapshots(
            game_id,
            market_type=market_type,
            book=book,
            snapshot_kind=snapshot_kind,
        )
        return snapshots[-1] if snapshots else None

    @staticmethod
    def _snapshot_from_event(event: PregameEvent) -> MarketSnapshot:
        if event.event_type not in _MARKET_EVENT_TYPES:
            raise MarketSnapshotHistoryError(
                event.event_id,
                event.game_id,
                f"event_type {event.event_type.value} is not a market snapshot event",
            )
        try:
            snapshot = MarketSnapshot.model_validate(event.payload)
        except ValidationError as exc:
            raise MarketSnapshotHistoryError(
                event.event_id,
                event.game_id,
                f"invalid MarketSnapshot payload: {exc.errors()[0]['msg']}",
            ) from exc
        if snapshot.game_id != event.game_id:
            raise MarketSnapshotHistoryError(
                event.event_id,
                event.game_id,
                "payload game_id does not match event game_id",
            )
        expected_event_type = SNAPSHOT_KIND_TO_EVENT_TYPE[snapshot.snapshot_kind]
        if event.event_type != expected_event_type:
            raise MarketSnapshotHistoryError(
                event.event_id,
                event.game_id,
                "event_type does not match payload snapshot_kind",
            )
        if snapshot.captured_at_utc != event.effective_at_utc:
            raise MarketSnapshotHistoryError(
                event.event_id,
                event.game_id,
                "payload captured_at_utc does not match event effective_at_utc",
            )
        return snapshot.model_copy(deep=True)


def _require_utc(value: datetime) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("recorded_at_utc must be timezone-aware")
    if value.utcoffset() != timedelta(0):
        raise ValueError("recorded_at_utc must be in UTC")
