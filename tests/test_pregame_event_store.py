from __future__ import annotations

from datetime import datetime, timedelta, timezone

from pregame.contracts import PregameEvent
from pregame.events import PregameEventType
from pregame.store import AppendStatus, InMemoryPregameEventStore


def utc_at(hour: int, minute: int = 0) -> datetime:
    return datetime(2026, 9, 8, hour, minute, tzinfo=timezone.utc)


def make_event(
    event_id: str,
    *,
    game_id: str = "2026_w01_BUF_at_HOU",
    event_type: PregameEventType = PregameEventType.MODEL_CANDIDATE_CREATED,
    created_at_utc: datetime | None = None,
    effective_at_utc: datetime | None = None,
    payload: dict | None = None,
    supersedes_event_id: str | None = None,
    correction_reason: str | None = None,
) -> PregameEvent:
    timestamp = utc_at(18)
    return PregameEvent(
        event_id=event_id,
        game_id=game_id,
        event_type=event_type,
        created_at_utc=created_at_utc or timestamp,
        effective_at_utc=effective_at_utc or timestamp,
        source="unit_test",
        idempotency_key=f"idempotency_{event_id}",
        supersedes_event_id=supersedes_event_id,
        correction_reason=correction_reason,
        payload=payload or {"edge": 4.88},
    )


def test_append_one_event_and_read_by_event_id_game_id_and_contains():
    store = InMemoryPregameEventStore()
    event = make_event("evt_001")

    result = store.append(event)

    assert result.status == AppendStatus.APPENDED
    assert result.event_id == "evt_001"
    assert store.contains("evt_001") is True
    assert store.get_event("evt_001") == event
    assert store.list_events("2026_w01_BUF_at_HOU") == [event]


def test_append_only_keeps_two_events_for_one_game_without_changing_first():
    store = InMemoryPregameEventStore()
    first = make_event("evt_001", payload={"edge": 4.88})
    second = make_event(
        "evt_002",
        event_type=PregameEventType.RESEARCH_COMPLETED,
        created_at_utc=utc_at(19),
        effective_at_utc=utc_at(19),
        payload={"research_status": "COMPLETE"},
    )

    store.append(first)
    store.append(second)

    events = store.list_events("2026_w01_BUF_at_HOU")
    assert events == [first, second]
    assert events[0].payload == {"edge": 4.88}


def test_append_identical_event_is_idempotent_and_does_not_duplicate():
    store = InMemoryPregameEventStore()
    event = make_event("evt_001")

    first_result = store.append(event)
    second_result = store.append(event)

    assert first_result.status == AppendStatus.APPENDED
    assert second_result.status == AppendStatus.ALREADY_EXISTS
    assert len(store.list_events("2026_w01_BUF_at_HOU")) == 1


def test_append_same_event_id_with_different_payload_returns_conflict():
    store = InMemoryPregameEventStore()
    original = make_event("evt_001", payload={"edge": 4.88})
    conflicting = make_event("evt_001", payload={"edge": 5.25})

    store.append(original)
    result = store.append(conflicting)

    assert result.status == AppendStatus.CONFLICT
    assert store.get_event("evt_001") == original
    assert store.get_event("evt_001").payload == {"edge": 4.88}
    assert len(store.list_events("2026_w01_BUF_at_HOU")) == 1


def test_append_same_event_id_with_different_timestamp_returns_conflict():
    store = InMemoryPregameEventStore()
    original = make_event("evt_001", created_at_utc=utc_at(18))
    conflicting = make_event("evt_001", created_at_utc=utc_at(18, 1))

    store.append(original)
    result = store.append(conflicting)

    assert result.status == AppendStatus.CONFLICT
    assert store.get_event("evt_001") == original


def test_events_for_different_games_do_not_mix():
    store = InMemoryPregameEventStore()
    buf_hou = make_event("evt_buf_hou", game_id="2026_w01_BUF_at_HOU")
    mia_lv = make_event("evt_mia_lv", game_id="2026_w01_MIA_at_LV")

    store.append(buf_hou)
    store.append(mia_lv)

    assert store.list_events("2026_w01_BUF_at_HOU") == [buf_hou]
    assert store.list_events("2026_w01_MIA_at_LV") == [mia_lv]


def test_list_events_uses_deterministic_logical_order_not_physical_write_order():
    store = InMemoryPregameEventStore()
    base = utc_at(18)
    later = make_event("evt_c", created_at_utc=base, effective_at_utc=base + timedelta(hours=2))
    earliest = make_event("evt_a", created_at_utc=base, effective_at_utc=base)
    tie_breaker_first = make_event(
        "evt_b1",
        created_at_utc=base + timedelta(minutes=1),
        effective_at_utc=base + timedelta(hours=1),
    )
    tie_breaker_second = make_event(
        "evt_b2",
        created_at_utc=base + timedelta(minutes=1),
        effective_at_utc=base + timedelta(hours=1),
    )

    for event in [later, tie_breaker_second, earliest, tie_breaker_first]:
        store.append(event)

    assert [event.event_id for event in store.list_events("2026_w01_BUF_at_HOU")] == [
        "evt_a",
        "evt_b1",
        "evt_b2",
        "evt_c",
    ]


def test_correction_event_preserves_original_and_supersedes_relationship():
    store = InMemoryPregameEventStore()
    original = make_event("evt_001", payload={"spread": -1.5})
    correction = make_event(
        "evt_002",
        event_type=PregameEventType.CORRECTION_EVENT,
        created_at_utc=utc_at(19),
        effective_at_utc=utc_at(18),
        payload={"spread": -2.0},
        supersedes_event_id="evt_001",
        correction_reason="corrected parsed spread",
    )

    store.append(original)
    store.append(correction)

    events = store.list_events("2026_w01_BUF_at_HOU")
    assert len(events) == 2
    assert events[0].event_id == "evt_001"
    assert events[1].event_id == "evt_002"
    assert events[1].supersedes_event_id == "evt_001"
    assert events[1].correction_reason == "corrected parsed spread"


def test_payload_mutation_after_append_does_not_change_stored_event():
    store = InMemoryPregameEventStore()
    source_payload = {"nested": {"edge": 4.88}, "tags": ["VALUE_PLAY"]}
    event = make_event("evt_001", payload=source_payload)

    store.append(event)
    source_payload["nested"]["edge"] = 9.99
    source_payload["tags"].append("MUTATED")
    event.payload["nested"]["edge"] = 7.77

    stored = store.get_event("evt_001")
    assert stored.payload == {"nested": {"edge": 4.88}, "tags": ["VALUE_PLAY"]}


def test_mutating_returned_event_does_not_change_store():
    store = InMemoryPregameEventStore()
    event = make_event("evt_001", payload={"edge": 4.88})
    store.append(event)

    returned = store.get_event("evt_001")
    returned.payload["edge"] = 9.99

    assert store.get_event("evt_001").payload == {"edge": 4.88}


def test_empty_results_for_unknown_ids():
    store = InMemoryPregameEventStore()

    assert store.get_event("missing") is None
    assert store.contains("missing") is False
    assert store.list_events("missing_game") == []


def test_retrieved_event_keeps_json_compatible_contract_serialization():
    store = InMemoryPregameEventStore()
    event = make_event(
        "evt_001",
        event_type=PregameEventType.INITIAL_MARKET_SNAPSHOT,
        payload={"book": "PREGAME_COM", "spread": -1.5, "price": -102},
    )

    store.append(event)
    stored = store.get_event("evt_001")
    payload = stored.to_json_dict()

    assert stored.event_type == PregameEventType.INITIAL_MARKET_SNAPSHOT
    assert payload["event_type"] == "INITIAL_MARKET_SNAPSHOT"
    assert payload["created_at_utc"] == "2026-09-08T18:00:00Z"
    assert payload["payload"] == {"book": "PREGAME_COM", "spread": -1.5, "price": -102}
