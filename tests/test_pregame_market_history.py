from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from pregame.contracts import MarketSnapshot, PregameEvent
from pregame.events import (
    ExecutableStatus,
    MarketQualityStatus,
    MarketType,
    PregameEventType,
    SnapshotKind,
)
from pregame.jsonl_store import JsonlPregameEventStore
from pregame.market_history import (
    SNAPSHOT_KIND_TO_EVENT_TYPE,
    MarketSnapshotHistoryError,
    MarketSnapshotHistoryService,
    market_snapshot_event_id,
)
from pregame.projector import project_game
from pregame.store import AppendStatus, InMemoryPregameEventStore

GAME_ID = "2026_w01_BUF_at_HOU"


def utc_at(hour: int, minute: int = 0) -> datetime:
    return datetime(2026, 9, 8, hour, minute, tzinfo=timezone.utc)


def snapshot(
    snapshot_id: str,
    *,
    game_id: str = GAME_ID,
    kind: SnapshotKind = SnapshotKind.CURRENT,
    market_type: MarketType = MarketType.SPREAD,
    book: str = "Book A",
    captured_at_utc: datetime | None = None,
    spread: float | None = -1.5,
    spread_price: int | None = -110,
    quality_status: MarketQualityStatus = MarketQualityStatus.DISPLAYED_UNVERIFIED,
) -> MarketSnapshot:
    return MarketSnapshot(
        snapshot_id=snapshot_id,
        game_id=game_id,
        snapshot_kind=kind,
        captured_at_utc=captured_at_utc or utc_at(18),
        book=book,
        source="PREGAME_COM",
        market_type=market_type,
        quality_status=quality_status,
        executable_status=ExecutableStatus.UNVERIFIED,
        selected_side="BUF",
        spread=spread if market_type == MarketType.SPREAD else None,
        spread_price=spread_price if market_type == MarketType.SPREAD else None,
        total=44.5 if market_type == MarketType.TOTAL else None,
        total_price=-110 if market_type == MarketType.TOTAL else None,
        moneyline=120 if market_type == MarketType.MONEYLINE else None,
    )


def game_created() -> PregameEvent:
    return PregameEvent(
        event_id="game-created",
        game_id=GAME_ID,
        event_type=PregameEventType.GAME_CREATED,
        created_at_utc=utc_at(17),
        effective_at_utc=utc_at(17),
        source="test",
        payload={"season": 2026, "week": 1, "away_team": "BUF", "home_team": "HOU"},
    )


@pytest.mark.parametrize(
    ("kind", "event_type"),
    [
        (SnapshotKind.INITIAL, PregameEventType.INITIAL_MARKET_SNAPSHOT),
        (SnapshotKind.CURRENT, PregameEventType.MARKET_QUOTE_UPDATED),
        (SnapshotKind.FINAL, PregameEventType.FINAL_QUOTE_CAPTURED),
        (SnapshotKind.CLOSING, PregameEventType.CLOSING_QUOTE_CAPTURED),
    ],
)
def test_snapshot_kind_mapping_is_canonical(kind, event_type):
    assert SNAPSHOT_KIND_TO_EVENT_TYPE[kind] == event_type


@pytest.mark.parametrize("backend", ["memory", "jsonl"])
def test_record_snapshot_creates_expected_event_for_both_backends(backend, tmp_path):
    store = (
        InMemoryPregameEventStore()
        if backend == "memory"
        else JsonlPregameEventStore(tmp_path / "events.jsonl")
    )
    service = MarketSnapshotHistoryService(store)
    item = snapshot("initial", kind=SnapshotKind.INITIAL)

    result = service.record_snapshot(item, recorded_at_utc=utc_at(19))
    event = store.get_event(market_snapshot_event_id("initial"))

    assert result.status == AppendStatus.APPENDED
    assert event.game_id == GAME_ID
    assert event.event_type == PregameEventType.INITIAL_MARKET_SNAPSHOT
    assert event.effective_at_utc == item.captured_at_utc
    assert event.created_at_utc == utc_at(19)
    assert event.source == "PREGAME_COM"
    assert event.payload == item.to_json_dict()


def test_event_id_is_deterministic_and_distinct():
    assert market_snapshot_event_id("abc") == "market-snapshot:abc"
    assert market_snapshot_event_id("abc") == market_snapshot_event_id("abc")
    assert market_snapshot_event_id("abc") != market_snapshot_event_id("def")


def test_snapshot_retry_ignores_different_recorded_time_and_conflict_preserves_original():
    store = InMemoryPregameEventStore()
    service = MarketSnapshotHistoryService(store)
    original = snapshot("current", spread=-1.5)

    assert (
        service.record_snapshot(original, recorded_at_utc=utc_at(19)).status
        == AppendStatus.APPENDED
    )
    assert (
        service.record_snapshot(original, recorded_at_utc=utc_at(20)).status
        == AppendStatus.ALREADY_EXISTS
    )
    conflict = snapshot("current", spread=-2.5)
    assert (
        service.record_snapshot(conflict, recorded_at_utc=utc_at(21)).status
        == AppendStatus.CONFLICT
    )
    assert service.get_snapshot("current").spread == -1.5
    assert len(store.list_events(GAME_ID)) == 1


def test_raw_history_keeps_lifecycle_snapshots_and_sorts_by_capture_time():
    service = MarketSnapshotHistoryService(InMemoryPregameEventStore())
    snapshots = [
        snapshot("closing", kind=SnapshotKind.CLOSING, captured_at_utc=utc_at(22)),
        snapshot("initial", kind=SnapshotKind.INITIAL, captured_at_utc=utc_at(18)),
        snapshot("current_1", captured_at_utc=utc_at(19)),
        snapshot("current_2", captured_at_utc=utc_at(20)),
        snapshot("final", kind=SnapshotKind.FINAL, captured_at_utc=utc_at(21)),
    ]
    for item in snapshots:
        service.record_snapshot(item, recorded_at_utc=utc_at(23))

    assert [item.snapshot_id for item in service.list_snapshots(GAME_ID)] == [
        "initial",
        "current_1",
        "current_2",
        "final",
        "closing",
    ]


def test_filters_latest_multiple_books_and_market_types():
    service = MarketSnapshotHistoryService(InMemoryPregameEventStore())
    records = [
        snapshot("spread_a", book="Book A", captured_at_utc=utc_at(18)),
        snapshot("spread_b", book="Book B", captured_at_utc=utc_at(19)),
        snapshot("spread_a_later", book="Book A", captured_at_utc=utc_at(20)),
        snapshot(
            "total_a",
            market_type=MarketType.TOTAL,
            book="Book B",
            captured_at_utc=utc_at(21),
        ),
        snapshot(
            "ml_c", market_type=MarketType.MONEYLINE, book="Book C", captured_at_utc=utc_at(22)
        ),
    ]
    for item in records:
        service.record_snapshot(item, recorded_at_utc=utc_at(23))

    assert [item.snapshot_id for item in service.list_snapshots(GAME_ID, book="Book A")] == [
        "spread_a",
        "spread_a_later",
    ]
    assert [
        item.snapshot_id for item in service.list_snapshots(GAME_ID, market_type=MarketType.SPREAD)
    ] == ["spread_a", "spread_b", "spread_a_later"]
    assert (
        service.get_latest_snapshot(GAME_ID, market_type=MarketType.SPREAD).snapshot_id
        == "spread_a_later"
    )
    assert (
        service.get_latest_snapshot(GAME_ID, market_type=MarketType.TOTAL).snapshot_id == "total_a"
    )
    assert (
        service.get_latest_snapshot(
            GAME_ID, market_type=MarketType.SPREAD, book="Book B"
        ).snapshot_id
        == "spread_b"
    )


def test_games_are_separated_unknown_snapshot_is_none_and_non_market_events_are_ignored():
    store = InMemoryPregameEventStore()
    service = MarketSnapshotHistoryService(store)
    service.record_snapshot(snapshot("home"), recorded_at_utc=utc_at(19))
    service.record_snapshot(
        snapshot("away", game_id="2026_w01_MIA_at_LV"), recorded_at_utc=utc_at(19)
    )
    store.append(game_created())

    assert [item.snapshot_id for item in service.list_snapshots(GAME_ID)] == ["home"]
    assert service.get_snapshot("missing") is None


def test_invalid_direct_market_event_payload_and_domain_mismatches_raise_errors():
    store = InMemoryPregameEventStore()
    service = MarketSnapshotHistoryService(store)
    invalid = PregameEvent(
        event_id="invalid",
        game_id=GAME_ID,
        event_type=PregameEventType.MARKET_QUOTE_UPDATED,
        created_at_utc=utc_at(18),
        effective_at_utc=utc_at(18),
        source="test",
        payload={"spread": -1.5},
    )
    store.append(invalid)
    with pytest.raises(MarketSnapshotHistoryError, match="invalid MarketSnapshot payload"):
        service.list_snapshots(GAME_ID)

    payload = snapshot("wrong_game").to_json_dict()
    payload["game_id"] = "other_game"
    wrong_game = invalid.model_copy(update={"event_id": "wrong-game", "payload": payload})
    store = InMemoryPregameEventStore()
    store.append(wrong_game)
    with pytest.raises(MarketSnapshotHistoryError, match="payload game_id"):
        MarketSnapshotHistoryService(store).list_snapshots(GAME_ID)


def test_event_type_and_effective_time_mismatches_raise_errors():
    item = snapshot("final", kind=SnapshotKind.FINAL, captured_at_utc=utc_at(18))
    wrong_type = PregameEvent(
        event_id="wrong-type",
        game_id=GAME_ID,
        event_type=PregameEventType.MARKET_QUOTE_UPDATED,
        created_at_utc=utc_at(19),
        effective_at_utc=utc_at(18),
        source="test",
        payload=item.to_json_dict(),
    )
    store = InMemoryPregameEventStore()
    store.append(wrong_type)
    with pytest.raises(MarketSnapshotHistoryError, match="event_type does not match"):
        MarketSnapshotHistoryService(store).list_snapshots(GAME_ID)

    wrong_time = wrong_type.model_copy(
        update={
            "event_id": "wrong-time",
            "event_type": PregameEventType.FINAL_QUOTE_CAPTURED,
            "effective_at_utc": utc_at(19),
        }
    )
    store = InMemoryPregameEventStore()
    store.append(wrong_time)
    with pytest.raises(MarketSnapshotHistoryError, match="captured_at_utc"):
        MarketSnapshotHistoryService(store).list_snapshots(GAME_ID)


@pytest.mark.parametrize(
    "quality",
    [
        MarketQualityStatus.DISPLAYED_UNVERIFIED,
        MarketQualityStatus.MISSING_PRICE,
        MarketQualityStatus.STALE,
    ],
)
def test_quality_status_is_preserved_without_business_evaluation(quality):
    service = MarketSnapshotHistoryService(InMemoryPregameEventStore())
    item = snapshot(f"quality-{quality.value}", quality_status=quality, spread_price=None)

    service.record_snapshot(item, recorded_at_utc=utc_at(19))

    assert service.get_snapshot(item.snapshot_id).quality_status == quality
    assert service.get_snapshot(item.snapshot_id).spread_price is None


def test_jsonl_restart_and_projector_integration(tmp_path):
    store = JsonlPregameEventStore(tmp_path / "events.jsonl")
    store.append(game_created())
    service = MarketSnapshotHistoryService(store)
    service.record_snapshot(
        snapshot("initial", kind=SnapshotKind.INITIAL, captured_at_utc=utc_at(18)),
        recorded_at_utc=utc_at(19),
    )
    service.record_snapshot(
        snapshot("current", captured_at_utc=utc_at(20)), recorded_at_utc=utc_at(21)
    )

    restarted_store = JsonlPregameEventStore(store.path)
    restarted_service = MarketSnapshotHistoryService(restarted_store)
    history = restarted_service.list_snapshots(GAME_ID)
    record = project_game(restarted_store, GAME_ID)

    assert [item.snapshot_id for item in history] == ["initial", "current"]
    assert record.initial_market_snapshot.snapshot_id == "initial"
    assert record.current_market_snapshot.snapshot_id == "current"


def test_recorded_at_requires_aware_utc():
    service = MarketSnapshotHistoryService(InMemoryPregameEventStore())
    with pytest.raises(ValueError, match="timezone-aware"):
        service.record_snapshot(snapshot("naive"), recorded_at_utc=datetime(2026, 9, 8, 19))
    with pytest.raises(ValueError, match="in UTC"):
        service.record_snapshot(
            snapshot("offset"),
            recorded_at_utc=datetime(2026, 9, 8, 20, tzinfo=timezone(timedelta(hours=1))),
        )
