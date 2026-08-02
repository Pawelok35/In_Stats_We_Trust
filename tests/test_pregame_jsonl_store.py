from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest

from pregame.contracts import CandidateRecord, MarketSnapshot, PregameEvent
from pregame.events import (
    CandidateStatus,
    ExecutableStatus,
    MarketQualityStatus,
    MarketType,
    PregameEventType,
    SnapshotKind,
)
from pregame.jsonl_store import EventStoreCorruptionError, JsonlPregameEventStore
from pregame.projector import project_game
from pregame.store import AppendStatus

GAME_ID = "2026_w01_BUF_at_HOU"


def utc_at(hour: int, minute: int = 0) -> datetime:
    return datetime(2026, 9, 8, hour, minute, tzinfo=timezone.utc)


def make_event(
    event_id: str,
    *,
    game_id: str = GAME_ID,
    event_type: PregameEventType = PregameEventType.GAME_CREATED,
    payload: dict | None = None,
    effective_at_utc: datetime | None = None,
    created_at_utc: datetime | None = None,
    supersedes_event_id: str | None = None,
) -> PregameEvent:
    return PregameEvent(
        event_id=event_id,
        game_id=game_id,
        event_type=event_type,
        created_at_utc=created_at_utc or utc_at(18),
        effective_at_utc=effective_at_utc or utc_at(18),
        source="test",
        schema_version="pregame_event.v1",
        idempotency_key=f"key_{event_id}",
        supersedes_event_id=supersedes_event_id,
        correction_reason="test correction" if supersedes_event_id else None,
        payload=payload
        or {
            "season": 2026,
            "week": 1,
            "away_team": "BUF",
            "home_team": "HOU",
        },
    )


def market_payload(snapshot_id: str) -> dict:
    return MarketSnapshot(
        snapshot_id=snapshot_id,
        game_id=GAME_ID,
        snapshot_kind=SnapshotKind.INITIAL,
        captured_at_utc=utc_at(18),
        book="TEST_BOOK",
        source="test",
        market_type=MarketType.SPREAD,
        quality_status=MarketQualityStatus.DISPLAYED_UNVERIFIED,
        executable_status=ExecutableStatus.UNVERIFIED,
        selected_side="BUF",
        spread=-1.5,
        spread_price=-110,
    ).to_json_dict()


def candidate_payload() -> dict:
    return CandidateRecord(
        candidate_id="candidate_1",
        game_id=GAME_ID,
        season=2026,
        week=1,
        away="BUF",
        home="HOU",
        status=CandidateStatus.MODEL_CANDIDATE,
        created_at_utc=utc_at(18),
        model_variant="variant_m",
        selected_team="BUF",
        model_tag="VALUE PLAY",
        production_eligible=True,
    ).to_json_dict()


def test_append_persists_one_utf8_json_line_and_reads_it_back(tmp_path):
    path = tmp_path / "events" / "pregame.jsonl"
    store = JsonlPregameEventStore(path)
    event = make_event("game")

    result = store.append(event)

    assert result.status == AppendStatus.APPENDED
    assert path.exists()
    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0])["created_at_utc"] == "2026-09-08T18:00:00Z"
    assert store.get_event("game") == event
    assert store.contains("game") is True
    assert store.list_events(GAME_ID) == [event]


def test_restart_rebuilds_index_and_preserves_idempotency(tmp_path):
    path = tmp_path / "events.jsonl"
    event = make_event("game")
    JsonlPregameEventStore(path).append(event)

    restarted = JsonlPregameEventStore(path)

    assert restarted.contains("game") is True
    assert restarted.get_event("game") == event
    assert restarted.append(event).status == AppendStatus.ALREADY_EXISTS
    assert len(path.read_text(encoding="utf-8").splitlines()) == 1


def test_identical_event_is_not_appended_twice_and_conflict_leaves_file_unchanged(tmp_path):
    path = tmp_path / "events.jsonl"
    store = JsonlPregameEventStore(path)
    original = make_event(
        "game", payload={"season": 2026, "week": 1, "away_team": "BUF", "home_team": "HOU"}
    )
    conflicting = make_event(
        "game", payload={"season": 2026, "week": 1, "away_team": "BUF", "home_team": "MIA"}
    )

    assert store.append(original).status == AppendStatus.APPENDED
    before = path.read_bytes()
    assert store.append(original).status == AppendStatus.ALREADY_EXISTS
    assert store.append(conflicting).status == AppendStatus.CONFLICT
    assert path.read_bytes() == before


def test_events_are_sorted_logically_and_games_do_not_mix(tmp_path):
    store = JsonlPregameEventStore(tmp_path / "events.jsonl")
    later = make_event("later", effective_at_utc=utc_at(20))
    earliest = make_event("earliest", effective_at_utc=utc_at(18))
    middle = make_event(
        "middle",
        effective_at_utc=utc_at(19),
        created_at_utc=utc_at(19) + timedelta(minutes=1),
    )
    other_game = make_event("other", game_id="2026_w01_MIA_at_LV")

    for item in (later, other_game, middle, earliest):
        store.append(item)

    assert [item.event_id for item in store.list_events(GAME_ID)] == [
        "earliest",
        "middle",
        "later",
    ]
    assert store.list_events("2026_w01_MIA_at_LV") == [other_game]


def test_empty_existing_file_and_missing_directory_are_supported(tmp_path):
    path = tmp_path / "nested" / "events.jsonl"
    path.parent.mkdir()
    path.touch()

    store = JsonlPregameEventStore(path)
    assert store.list_events(GAME_ID) == []
    assert store.append(make_event("game")).status == AppendStatus.APPENDED

    missing_path = tmp_path / "missing" / "deeper" / "events.jsonl"
    assert (
        JsonlPregameEventStore(missing_path).append(make_event("other")).status
        == AppendStatus.APPENDED
    )
    assert missing_path.exists()


def test_malformed_json_and_invalid_event_schema_raise_corruption_errors(tmp_path):
    malformed = tmp_path / "malformed.jsonl"
    malformed.write_text("not-json\n", encoding="utf-8")
    with pytest.raises(EventStoreCorruptionError, match="line 1: invalid JSON"):
        JsonlPregameEventStore(malformed)

    invalid = tmp_path / "invalid.jsonl"
    invalid.write_text(json.dumps({"event_id": "missing_everything"}) + "\n", encoding="utf-8")
    with pytest.raises(EventStoreCorruptionError, match="line 1: invalid PregameEvent schema"):
        JsonlPregameEventStore(invalid)


def test_identical_duplicate_line_is_diagnostic_but_conflicting_duplicate_is_corruption(tmp_path):
    event = make_event("game")
    identical = tmp_path / "identical.jsonl"
    line = json.dumps(event.to_json_dict(), sort_keys=True)
    identical.write_text(f"{line}\n{line}\n", encoding="utf-8")

    store = JsonlPregameEventStore(identical)
    assert store.duplicate_event_ids == ("game",)
    assert store.list_events(GAME_ID) == [event]

    conflict = tmp_path / "conflict.jsonl"
    changed = event.to_json_dict()
    changed["source"] = "different"
    conflict.write_text(
        f"{line}\n{json.dumps(changed, sort_keys=True)}\n",
        encoding="utf-8",
    )
    with pytest.raises(EventStoreCorruptionError, match="line 2: duplicate event_id"):
        JsonlPregameEventStore(conflict)


def test_round_trip_keeps_correction_metadata_and_mutation_is_defensive(tmp_path):
    path = tmp_path / "events.jsonl"
    source_payload = {"nested": {"spread": -1.5}}
    event = make_event(
        "correction",
        event_type=PregameEventType.CORRECTION_EVENT,
        payload=source_payload,
        supersedes_event_id="market_1",
    )
    store = JsonlPregameEventStore(path)
    store.append(event)
    source_payload["nested"]["spread"] = -9.5

    restarted = JsonlPregameEventStore(path)
    returned = restarted.get_event("correction")
    returned.payload["nested"]["spread"] = -8.5

    stored = restarted.get_event("correction")
    assert stored.payload == {"nested": {"spread": -1.5}}
    assert stored.idempotency_key == "key_correction"
    assert stored.supersedes_event_id == "market_1"
    assert stored.correction_reason == "test correction"
    assert stored.schema_version == "pregame_event.v1"
    assert stored.event_type == PregameEventType.CORRECTION_EVENT
    assert stored.created_at_utc.tzinfo == timezone.utc


def test_store_projects_current_record_after_restart(tmp_path):
    path = tmp_path / "events.jsonl"
    first = JsonlPregameEventStore(path)
    first.append(make_event("game"))
    first.append(
        make_event(
            "market",
            event_type=PregameEventType.INITIAL_MARKET_SNAPSHOT,
            payload=market_payload("market_1"),
            effective_at_utc=utc_at(19),
        )
    )
    first.append(
        make_event(
            "candidate",
            event_type=PregameEventType.MODEL_CANDIDATE_CREATED,
            payload=candidate_payload(),
            effective_at_utc=utc_at(20),
        )
    )

    record = project_game(JsonlPregameEventStore(path), GAME_ID)

    assert record.away_team == "BUF"
    assert record.initial_market_snapshot.snapshot_id == "market_1"
    assert record.candidate.selected_team == "BUF"
    assert record.event_count == 3
