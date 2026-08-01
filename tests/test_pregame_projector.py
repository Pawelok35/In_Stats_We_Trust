from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from pregame.contracts import CandidateRecord, MarketSnapshot, OperatorDecision, PregameEvent
from pregame.events import (
    CandidateStatus,
    DecisionLevel,
    ExecutableStatus,
    MarketQualityStatus,
    MarketType,
    OperatorVerdict,
    PregameEventType,
    SnapshotKind,
)
from pregame.projector import ProjectionError, project_events, project_game
from pregame.store import InMemoryPregameEventStore

GAME_ID = "2026_w01_BUF_at_HOU"


def utc_at(hour: int, minute: int = 0) -> datetime:
    return datetime(2026, 9, 8, hour, minute, tzinfo=timezone.utc)


def event(
    event_id: str,
    event_type: PregameEventType,
    payload: dict | None = None,
    *,
    game_id: str = GAME_ID,
    hour: int = 18,
    created_minute: int = 0,
    supersedes_event_id: str | None = None,
) -> PregameEvent:
    return PregameEvent(
        event_id=event_id,
        game_id=game_id,
        event_type=event_type,
        created_at_utc=utc_at(hour, created_minute),
        effective_at_utc=utc_at(hour),
        source="test",
        payload=payload or {},
        supersedes_event_id=supersedes_event_id,
        correction_reason="test correction" if supersedes_event_id else None,
    )


def game_created(event_id: str = "game", *, hour: int = 18) -> PregameEvent:
    return event(
        event_id,
        PregameEventType.GAME_CREATED,
        {
            "season": 2026,
            "week": 1,
            "away_team": "BUF",
            "home_team": "HOU",
            "kickoff_utc": "2026-09-13T17:00:00Z",
            "venue": "NRG Stadium",
            "neutral_site": False,
        },
        hour=hour,
    )


def market_payload(snapshot_id: str, *, spread: float = -1.5) -> dict:
    return MarketSnapshot(
        snapshot_id=snapshot_id,
        game_id=GAME_ID,
        snapshot_kind=SnapshotKind.CURRENT,
        captured_at_utc=utc_at(18),
        book="TEST_BOOK",
        source="test",
        market_type=MarketType.SPREAD,
        quality_status=MarketQualityStatus.DISPLAYED_UNVERIFIED,
        executable_status=ExecutableStatus.UNVERIFIED,
        selected_side="BUF",
        spread=spread,
        spread_price=-110,
    ).to_json_dict()


def candidate_payload(*, status: CandidateStatus = CandidateStatus.MODEL_CANDIDATE) -> dict:
    return CandidateRecord(
        candidate_id="candidate_1",
        game_id=GAME_ID,
        season=2026,
        week=1,
        status=status,
        created_at_utc=utc_at(18),
        model_variant="variant_m",
        selected_team="BUF",
        model_tag="VALUE PLAY",
        production_eligible=True,
    ).to_json_dict()


def decision_payload(verdict: OperatorVerdict) -> dict:
    return OperatorDecision(
        decision_id="decision_1",
        game_id=GAME_ID,
        verdict=verdict,
        decided_at_utc=utc_at(20),
        operator="Daniel",
        reason_codes=["TEST"],
        selected_team="BUF",
    ).to_json_dict()


def test_unknown_game_returns_none_and_empty_projection_fails():
    store = InMemoryPregameEventStore()

    assert project_game(store, GAME_ID) is None
    with pytest.raises(ProjectionError, match="empty"):
        project_events([])


def test_game_created_projects_complete_identity():
    record = project_events([game_created()])

    assert record.game_id == GAME_ID
    assert (record.season, record.week, record.away_team, record.home_team) == (
        2026,
        1,
        "BUF",
        "HOU",
    )
    assert record.kickoff_utc == datetime(2026, 9, 13, 17, tzinfo=timezone.utc)
    assert record.venue == "NRG Stadium"
    assert record.neutral_site is False
    assert record.event_count == 1


def test_market_lifecycle_keeps_initial_and_projects_current_final_closing():
    record = project_events(
        [
            game_created(),
            event(
                "initial",
                PregameEventType.INITIAL_MARKET_SNAPSHOT,
                market_payload("initial", spread=-1.5),
                hour=19,
            ),
            event(
                "current",
                PregameEventType.MARKET_QUOTE_UPDATED,
                market_payload("current", spread=-2.0),
                hour=20,
            ),
            event(
                "final",
                PregameEventType.FINAL_QUOTE_CAPTURED,
                market_payload("final", spread=-2.5),
                hour=21,
            ),
            event(
                "closing",
                PregameEventType.CLOSING_QUOTE_CAPTURED,
                market_payload("closing", spread=-3.0),
                hour=22,
            ),
        ]
    )

    assert record.initial_market_snapshot.snapshot_id == "initial"
    assert record.final_market_snapshot.snapshot_id == "final"
    assert record.closing_market_snapshot.snapshot_id == "closing"
    assert record.current_market_snapshot.snapshot_id == "closing"
    assert record.market_snapshot_count == 4


def test_market_update_without_initial_is_retained_with_warning():
    record = project_events(
        [event("current", PregameEventType.MARKET_QUOTE_UPDATED, market_payload("current"))]
    )

    assert record.current_market_snapshot.snapshot_id == "current"
    assert "market_update_without_initial:current" in record.warnings


def test_candidate_blocked_preserves_candidate_without_final_pick():
    record = project_events(
        [
            event("candidate", PregameEventType.MODEL_CANDIDATE_CREATED, candidate_payload()),
            event("blocked", PregameEventType.MODEL_CANDIDATE_BLOCKED, hour=19),
        ]
    )

    assert record.candidate.candidate_id == "candidate_1"
    assert record.candidate_status == CandidateStatus.BLOCKED
    assert record.current_decision_level == DecisionLevel.MODEL_CANDIDATE


def test_research_lifecycle_does_not_create_final_operator_level():
    record = project_events(
        [
            event("started", PregameEventType.RESEARCH_STARTED),
            event("completed", PregameEventType.RESEARCH_COMPLETED, hour=19),
            event("updated", PregameEventType.RESEARCH_UPDATED, hour=20),
            event("approved", PregameEventType.RESEARCH_APPROVED, hour=21),
        ]
    )

    assert record.research_started is True
    assert record.research_completed is True
    assert record.research_approved is True
    assert record.latest_research_event_id == "approved"
    assert record.current_decision_level == DecisionLevel.RESEARCH_APPROVED


def test_operator_approved_and_rejected_follow_positive_level_semantics():
    approved = project_events(
        [
            event("candidate", PregameEventType.MODEL_CANDIDATE_CREATED, candidate_payload()),
            event(
                "approved",
                PregameEventType.OPERATOR_PICK_APPROVED,
                decision_payload(OperatorVerdict.APPROVED),
                hour=20,
            ),
        ]
    )
    rejected = project_events(
        [
            event("candidate", PregameEventType.MODEL_CANDIDATE_CREATED, candidate_payload()),
            event(
                "rejected",
                PregameEventType.OPERATOR_PICK_REJECTED,
                decision_payload(OperatorVerdict.REJECTED_OPERATOR),
                hour=20,
            ),
        ]
    )

    assert approved.current_verdict == OperatorVerdict.APPROVED
    assert approved.current_decision_level == DecisionLevel.FINAL_OPERATOR_PICK
    assert rejected.current_verdict == OperatorVerdict.REJECTED_OPERATOR
    assert rejected.current_decision_level == DecisionLevel.MODEL_CANDIDATE


def test_operator_approval_without_candidate_warns_but_projects():
    record = project_events(
        [
            event(
                "approved",
                PregameEventType.OPERATOR_PICK_APPROVED,
                decision_payload(OperatorVerdict.APPROVED),
            )
        ]
    )

    assert record.current_decision_level == DecisionLevel.FINAL_OPERATOR_PICK
    assert "operator_decision_without_candidate:approved" in record.warnings


def test_out_of_order_input_and_tie_breaking_are_deterministic():
    initial = event(
        "initial",
        PregameEventType.INITIAL_MARKET_SNAPSHOT,
        market_payload("initial", spread=-1.5),
        hour=19,
    )
    first = event(
        "a",
        PregameEventType.MARKET_QUOTE_UPDATED,
        market_payload("a", spread=-2.0),
        hour=20,
        created_minute=1,
    )
    second = event(
        "b",
        PregameEventType.MARKET_QUOTE_UPDATED,
        market_payload("b", spread=-2.5),
        hour=20,
        created_minute=1,
    )

    chronological = project_events([initial, first, second])
    unordered = project_events([second, initial, first])

    assert chronological.to_json_dict() == unordered.to_json_dict()
    assert chronological.current_market_snapshot.snapshot_id == "b"


def test_correction_replaces_market_effect_but_original_stays_in_store():
    store = InMemoryPregameEventStore()
    original = event(
        "market",
        PregameEventType.MARKET_QUOTE_UPDATED,
        market_payload("market", spread=-1.5),
        hour=19,
    )
    correction = event(
        "correction",
        PregameEventType.CORRECTION_EVENT,
        market_payload("corrected", spread=-2.5),
        hour=20,
        supersedes_event_id="market",
    )
    store.append(original)
    store.append(correction)

    record = project_game(store, GAME_ID)
    assert len(store.list_events(GAME_ID)) == 2
    assert store.get_event("market").payload["spread"] == -1.5
    assert record.current_market_snapshot.snapshot_id == "corrected"
    assert record.current_market_snapshot.spread == -2.5


def test_correction_chain_uses_terminal_payload():
    original = event(
        "market",
        PregameEventType.MARKET_QUOTE_UPDATED,
        market_payload("original", spread=-1.5),
        hour=18,
    )
    correction_one = event(
        "correction_one",
        PregameEventType.CORRECTION_EVENT,
        market_payload("one", spread=-2.0),
        hour=19,
        supersedes_event_id="market",
    )
    correction_two = event(
        "correction_two",
        PregameEventType.CORRECTION_EVENT,
        market_payload("two", spread=-2.5),
        hour=20,
        supersedes_event_id="correction_one",
    )

    record = project_events([original, correction_one, correction_two])
    assert record.current_market_snapshot.snapshot_id == "two"


def test_correction_missing_target_warns_and_self_or_cycle_fail():
    missing = event(
        "missing", PregameEventType.CORRECTION_EVENT, {}, supersedes_event_id="no_such_event"
    )
    record = project_events([game_created(), missing])
    assert "correction_target_missing:missing:no_such_event" in record.warnings

    self_reference = event(
        "self", PregameEventType.CORRECTION_EVENT, {}, supersedes_event_id="self"
    )
    with pytest.raises(ProjectionError, match="itself"):
        project_events([self_reference])

    a = event("a", PregameEventType.CORRECTION_EVENT, {}, supersedes_event_id="b", hour=18)
    b = event("b", PregameEventType.CORRECTION_EVENT, {}, supersedes_event_id="a", hour=19)
    with pytest.raises(ProjectionError, match="cycle"):
        project_events([a, b])


def test_mixed_game_ids_and_embedded_record_game_ids_fail():
    with pytest.raises(ProjectionError, match="one game_id"):
        project_events(
            [
                game_created(),
                game_created("other", hour=19).model_copy(update={"game_id": "other_game"}),
            ]
        )

    wrong_candidate = candidate_payload()
    wrong_candidate["game_id"] = "other_game"
    with pytest.raises(ProjectionError, match="CandidateRecord.game_id"):
        project_events(
            [event("candidate", PregameEventType.MODEL_CANDIDATE_CREATED, wrong_candidate)]
        )


def test_invalid_payload_fails_explicitly():
    with pytest.raises(ProjectionError, match="Invalid market snapshot payload"):
        project_events([event("market", PregameEventType.MARKET_QUOTE_UPDATED, {"spread": -1.5})])


def test_settlement_and_unsupported_known_events_are_safe():
    record = project_events(
        [
            event("injury", PregameEventType.INJURY_UPDATED, {"status": "DNP"}),
            event("settled", PregameEventType.GAME_SETTLED, {"result": "W"}, hour=19),
        ]
    )

    assert record.settled is True
    assert record.latest_settlement_event_id == "settled"
    assert not record.warnings


def test_result_is_frozen_and_does_not_mutate_event_store_history():
    store = InMemoryPregameEventStore()
    source = event(
        "market", PregameEventType.MARKET_QUOTE_UPDATED, market_payload("market", spread=-1.5)
    )
    store.append(source)
    record = project_game(store, GAME_ID)

    with pytest.raises(ValidationError):
        record.game_id = "other_game"
    record.current_market_snapshot.spread = -9.5

    assert store.get_event("market").payload["spread"] == -1.5


def test_same_history_projects_identically_and_does_not_mutate_input():
    events = [
        game_created(),
        event("candidate", PregameEventType.MODEL_CANDIDATE_CREATED, candidate_payload(), hour=19),
    ]
    first = project_events(events)
    second = project_events(events)

    assert first.to_json_dict() == second.to_json_dict()
    assert events[1].payload["status"] == "MODEL_CANDIDATE"
