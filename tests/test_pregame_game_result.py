from __future__ import annotations

import inspect
from datetime import datetime, timedelta, timezone

import pytest

from pregame.events import PregameEventType
from pregame.game_result import AuthoritativeGameResultService, game_result_event_id
from pregame.jsonl_store import JsonlPregameEventStore
from pregame.projector import project_game
from pregame.store import AppendStatus, InMemoryPregameEventStore

NOW = datetime(2026, 9, 10, 12, tzinfo=timezone.utc)
GAME_ID = "2026_w01_BUF_at_HOU"
KICKOFF = NOW + timedelta(hours=1)


def _game_created(
    store,
    *,
    event_id: str = "game-created:2026_w01_BUF_at_HOU",
    game_id: str = GAME_ID,
    kickoff=KICKOFF,
    home_team: str = "HOU",
    away_team: str = "BUF",
    **overrides,
):
    payload = {
        "season": 2026,
        "week": 1,
        "home_team": home_team,
        "away_team": away_team,
        "kickoff_utc": kickoff.isoformat() if isinstance(kickoff, datetime) else kickoff,
        "neutral_site": False,
    }
    payload.update(overrides)
    from pregame.contracts import PregameEvent

    event = PregameEvent(
        event_id=event_id,
        game_id=game_id,
        event_type=PregameEventType.GAME_CREATED,
        created_at_utc=NOW,
        effective_at_utc=NOW,
        source="structured_game_creation",
        idempotency_key=event_id,
        payload=payload,
    )
    assert store.append(event).status == AppendStatus.APPENDED
    return event


def _result_values(**overrides):
    values = {
        "game_id": GAME_ID,
        "home_score": 17,
        "away_score": 20,
        "source": "NFL_OFFICIAL_GAMEBOOK",
        "source_reference": "gamebook:2026_w01_BUF_at_HOU",
        "source_finalized_at_utc": KICKOFF + timedelta(hours=3),
        "observed_at_utc": KICKOFF + timedelta(hours=3, minutes=5),
        "overtime": None,
    }
    values.update(overrides)
    return values


def test_final_result_is_home_away_immutable_and_does_not_touch_legacy_settlement():
    store = InMemoryPregameEventStore()
    creation = _game_created(store)

    registered = AuthoritativeGameResultService(store=store).record(**_result_values())

    assert registered.appended
    assert registered.event_id == game_result_event_id(GAME_ID)
    state = registered.projected_game
    assert state.authoritative_game_result is not None
    assert state.authoritative_game_result.status == "FINAL"
    assert state.authoritative_game_result.home_team == "HOU"
    assert state.authoritative_game_result.away_team == "BUF"
    assert state.authoritative_game_result.home_score == 17
    assert state.authoritative_game_result.away_score == 20
    assert state.authoritative_game_result.game_created_event_id == creation.event_id
    assert state.has_authoritative_game_result(GAME_ID)
    assert state.authoritative_result_event_id_for_game(GAME_ID) == game_result_event_id(GAME_ID)
    assert not state.settled
    assert state.latest_settlement_event_id is None
    assert not any(
        event.event_type == PregameEventType.GAME_SETTLED for event in store.list_events(GAME_ID)
    )


@pytest.mark.parametrize("home_score, away_score", [(1, 0), (0, 1), (17, 17), (0, 0)])
def test_final_result_accepts_integer_home_away_scores_including_ties_and_zeroes(
    home_score, away_score
):
    store = InMemoryPregameEventStore()
    _game_created(store)
    result = AuthoritativeGameResultService(store=store).record(
        **_result_values(home_score=home_score, away_score=away_score)
    )
    assert result.appended


@pytest.mark.parametrize("value", [-1, 1.0, "1", None, True])
def test_final_result_rejects_non_strict_or_negative_scores(value):
    store = InMemoryPregameEventStore()
    _game_created(store)
    result = AuthoritativeGameResultService(store=store).record(**_result_values(home_score=value))
    assert result.readiness_failure_codes == ("INVALID_AUTHORITATIVE_RESULT",)


@pytest.mark.parametrize("overtime", [True, False, None])
def test_final_result_accepts_boolean_or_none_overtime(overtime):
    store = InMemoryPregameEventStore()
    _game_created(store)
    assert (
        AuthoritativeGameResultService(store=store)
        .record(**_result_values(overtime=overtime))
        .appended
    )


def test_final_result_rejects_non_boolean_overtime_and_bad_provenance_or_timestamps():
    cases = [
        {"overtime": 1},
        {"source": " "},
        {"source_reference": ""},
        {"source_finalized_at_utc": KICKOFF},
        {"source_finalized_at_utc": KICKOFF - timedelta(seconds=1)},
        {"source_finalized_at_utc": datetime(2026, 9, 10, 20)},
        {"source_finalized_at_utc": datetime(2026, 9, 10, 22, tzinfo=timezone(timedelta(hours=2)))},
        {"observed_at_utc": datetime(2026, 9, 10, 20)},
    ]
    for changes in cases:
        store = InMemoryPregameEventStore()
        _game_created(store)
        result = AuthoritativeGameResultService(store=store).record(**_result_values(**changes))
        assert result.readiness_failure_codes == ("INVALID_AUTHORITATIVE_RESULT",)


def test_game_creation_is_required_complete_and_exactly_one_even_when_payloads_match():
    missing = InMemoryPregameEventStore()
    assert AuthoritativeGameResultService(store=missing).record(
        **_result_values()
    ).readiness_failure_codes == ("GAME_CREATED_NOT_FOUND",)

    invalid_cases = [
        {"kickoff_utc": None},
        {"home_team": ""},
        {"away_team": ""},
        {"home_team": "BUF", "away_team": "BUF"},
    ]
    for overrides in invalid_cases:
        store = InMemoryPregameEventStore()
        _game_created(store, **overrides)
        assert (
            AuthoritativeGameResultService(store=store)
            .record(**_result_values())
            .readiness_failure_codes[0]
            .startswith("GAME_CREATED_")
        )

    ambiguous = InMemoryPregameEventStore()
    _game_created(ambiguous)
    _game_created(ambiguous, event_id="game-created:duplicate")
    result = AuthoritativeGameResultService(store=ambiguous).record(**_result_values())
    assert result.readiness_failure_codes == ("GAME_CREATED_AMBIGUOUS",)
    assert project_game(ambiguous, GAME_ID).game_created_event_ids == (
        "game-created:2026_w01_BUF_at_HOU",
        "game-created:duplicate",
    )


def test_result_retry_is_idempotent_but_any_payload_change_conflicts():
    store = InMemoryPregameEventStore()
    _game_created(store)
    service = AuthoritativeGameResultService(store=store)
    values = _result_values(overtime=False)
    assert service.record(**values).appended
    assert not service.record(**values).appended
    for changes in (
        {"home_score": 18},
        {"away_score": 21},
        {"source": "OTHER"},
        {"source_reference": "other"},
        {"source_finalized_at_utc": KICKOFF + timedelta(hours=4)},
        {"observed_at_utc": KICKOFF + timedelta(hours=4, minutes=1)},
        {"overtime": True},
    ):
        result = service.record(**_result_values(**({"overtime": False} | changes)))
        assert result.readiness_failure_codes == ("AUTHORITATIVE_RESULT_EVENT_CONFLICT",)


def test_jsonl_restart_rebuilds_result_lineage_and_preserves_idempotency(tmp_path):
    path = tmp_path / "events.jsonl"
    store = JsonlPregameEventStore(path)
    creation = _game_created(store)
    service = AuthoritativeGameResultService(store=store)
    values = _result_values(overtime=True)
    assert service.record(**values).appended

    restarted = JsonlPregameEventStore(path)
    state = project_game(restarted, GAME_ID)
    assert state.authoritative_game_result is not None
    assert state.authoritative_game_result.game_created_event_id == creation.event_id
    assert not AuthoritativeGameResultService(store=restarted).record(**values).appended
    assert AuthoritativeGameResultService(store=restarted).record(
        **_result_values(home_score=21, overtime=True)
    ).readiness_failure_codes == ("AUTHORITATIVE_RESULT_EVENT_CONFLICT",)


def test_legacy_game_settled_is_independent_and_caller_api_has_only_authorized_inputs():
    store = InMemoryPregameEventStore()
    _game_created(store)
    from pregame.contracts import PregameEvent

    legacy = PregameEvent(
        event_id="legacy-settlement",
        game_id=GAME_ID,
        event_type=PregameEventType.GAME_SETTLED,
        created_at_utc=KICKOFF + timedelta(hours=4),
        effective_at_utc=KICKOFF + timedelta(hours=4),
        source="legacy",
        payload={},
    )
    assert store.append(legacy).status == AppendStatus.APPENDED
    assert project_game(store, GAME_ID).authoritative_game_result is None
    assert inspect.signature(AuthoritativeGameResultService.record).parameters.keys() == {
        "self",
        "game_id",
        "home_score",
        "away_score",
        "source",
        "source_reference",
        "source_finalized_at_utc",
        "observed_at_utc",
        "overtime",
    }
    with pytest.raises(TypeError):
        AuthoritativeGameResultService(store=store).record(
            **{key: value for key, value in _result_values().items() if key != "away_score"}
        )
