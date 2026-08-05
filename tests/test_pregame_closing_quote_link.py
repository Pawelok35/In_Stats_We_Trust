from __future__ import annotations

from datetime import timedelta

from pregame.closing_quote_link import ClosingQuoteLinkService
from pregame.contracts import MarketSnapshot
from pregame.events import MarketType, OperatorVerdict, SnapshotKind
from pregame.jsonl_store import JsonlPregameEventStore
from pregame.market_history import MarketSnapshotHistoryService
from pregame.store import AppendStatus
from pregame.wager_execution import ManifestBackedWagerExecutionService
from tests.test_pregame_manifest_backed_final_quote_gate import NOW
from tests.test_pregame_wager_execution import _approved, _decision_service, _execution_values


def _execution(tmp_path):
    store, candidate, gate = _approved(tmp_path)
    execution = ManifestBackedWagerExecutionService(store=store).record(
        **_execution_values(candidate, gate)
    )
    assert execution.appended
    return store, candidate, gate, execution


def _closing(candidate, gate, *, snapshot_id="closing-1", captured_at_utc=None, **overrides):
    values = {
        "snapshot_id": snapshot_id,
        "game_id": candidate.game_id,
        "snapshot_kind": SnapshotKind.CLOSING,
        "captured_at_utc": captured_at_utc or NOW + timedelta(minutes=30),
        "book": gate.book,
        "source": "DIRECT_SPORTSBOOK",
        "market_type": MarketType.SPREAD,
        "quality_status": gate.quality_status,
        "executable_status": gate.executable_status,
        "selected_side": candidate.selected_team,
        "spread": gate.final_spread,
        "spread_price": gate.final_price,
    }
    values.update(overrides)
    return MarketSnapshot(**values)


def _record_snapshot(store, snapshot, *, recorded_at_utc=None):
    return MarketSnapshotHistoryService(store).record_snapshot(
        snapshot,
        recorded_at_utc=recorded_at_utc or snapshot.captured_at_utc,
    )


def test_explicit_same_book_closing_link_is_projected_without_side_effects(tmp_path):
    store, candidate, gate, execution = _execution(tmp_path)
    closing = _closing(candidate, gate)
    assert _record_snapshot(store, closing).status == AppendStatus.APPENDED

    result = ClosingQuoteLinkService(store=store).record(
        execution_id="execution-1",
        closing_snapshot_id=closing.snapshot_id,
        linked_at_utc=NOW + timedelta(minutes=31),
    )

    assert result.appended
    state = result.projected_game
    assert state.has_closing_quote_link("execution-1")
    assert state.closing_snapshot_id_for_execution("execution-1") == "closing-1"
    assert state.wager_execution_history == execution.projected_game.wager_execution_history
    assert not state.settled
    assert not any(
        "clv" in event.event_id.lower() for event in store.list_events(candidate.game_id)
    )


def test_nonclosing_and_mismatched_snapshots_fail_closed(tmp_path):
    store, candidate, gate, _execution_result = _execution(tmp_path)
    cases = [
        ("final", {"snapshot_kind": SnapshotKind.FINAL}, "SNAPSHOT_KIND_NOT_CLOSING"),
        ("other-game", {"game_id": "2026_w01_NE_at_SEA"}, "CLOSING_SNAPSHOT_GAME_MISMATCH"),
        (
            "total",
            {
                "market_type": MarketType.TOTAL,
                "spread": None,
                "spread_price": None,
                "total": 44.5,
                "total_price": -110,
            },
            "CLOSING_SNAPSHOT_MARKET_MISMATCH",
        ),
        ("opposite", {"selected_side": candidate.home}, "CLOSING_SNAPSHOT_SIDE_MISMATCH"),
        ("book", {"book": "OTHER_BOOK"}, "CLOSING_SNAPSHOT_BOOK_MISMATCH"),
    ]
    service = ClosingQuoteLinkService(store=store)
    for snapshot_id, changes, expected in cases:
        snapshot = _closing(candidate, gate, snapshot_id=snapshot_id, **changes)
        assert _record_snapshot(store, snapshot).status == AppendStatus.APPENDED
        result = service.record(
            execution_id="execution-1",
            closing_snapshot_id=snapshot_id,
            linked_at_utc=NOW + timedelta(minutes=31),
        )
        assert result.readiness_failure_codes == (expected,)


def test_timestamp_policy_allows_kickoff_and_late_link_but_blocks_postkick_quote(tmp_path):
    store, candidate, gate, _execution_result = _execution(tmp_path)
    kickoff = NOW + timedelta(hours=2)
    at_kickoff = _closing(candidate, gate, captured_at_utc=kickoff)
    assert _record_snapshot(store, at_kickoff).status == AppendStatus.APPENDED
    accepted = ClosingQuoteLinkService(store=store).record(
        execution_id="execution-1",
        closing_snapshot_id=at_kickoff.snapshot_id,
        linked_at_utc=kickoff + timedelta(minutes=1),
    )
    assert accepted.appended

    store, candidate, gate, _execution_result = _execution(tmp_path)
    after_kickoff = _closing(candidate, gate, captured_at_utc=kickoff + timedelta(seconds=1))
    assert _record_snapshot(store, after_kickoff).status == AppendStatus.APPENDED
    rejected = ClosingQuoteLinkService(store=store).record(
        execution_id="execution-1",
        closing_snapshot_id=after_kickoff.snapshot_id,
        linked_at_utc=kickoff + timedelta(minutes=1),
    )
    assert rejected.readiness_failure_codes == ("CLOSING_SNAPSHOT_AFTER_KICKOFF",)


def test_one_link_idempotency_and_conflict_do_not_select_alternative_snapshot(tmp_path):
    store, candidate, gate, _execution_result = _execution(tmp_path)
    first = _closing(candidate, gate, snapshot_id="closing-a")
    second = _closing(
        candidate, gate, snapshot_id="closing-b", captured_at_utc=NOW + timedelta(minutes=31)
    )
    assert _record_snapshot(store, first).status == AppendStatus.APPENDED
    assert _record_snapshot(store, second).status == AppendStatus.APPENDED
    service = ClosingQuoteLinkService(store=store)
    values = dict(
        execution_id="execution-1",
        closing_snapshot_id="closing-a",
        linked_at_utc=NOW + timedelta(minutes=32),
    )
    assert service.record(**values).appended
    assert not service.record(**values).appended
    changed = service.record(**{**values, "closing_snapshot_id": "closing-b"})
    assert changed.readiness_failure_codes == ("CLOSING_LINK_EVENT_CONFLICT",)
    changed_time = service.record(**{**values, "linked_at_utc": NOW + timedelta(minutes=33)})
    assert changed_time.readiness_failure_codes == ("CLOSING_LINK_EVENT_CONFLICT",)


def test_jsonl_restart_and_later_decision_supersession_preserve_link(tmp_path):
    source, candidate, gate, _execution_result = _execution(tmp_path)
    closing = _closing(candidate, gate)
    assert _record_snapshot(source, closing).status == AppendStatus.APPENDED
    decisions = _decision_service(source)
    superseding = decisions.record(
        decision_id="decision-2",
        candidate_id=candidate.candidate_id,
        gate_evaluation_id=gate.evaluation_id,
        verdict=OperatorVerdict.PASS,
        stake_units=None,
        operator_id="operator:daniel",
        reason_codes=("PASS",),
        decision_at_utc=NOW + timedelta(minutes=40),
        recorded_at_utc=NOW + timedelta(minutes=41),
        supersedes_decision_id="decision-1",
    )
    assert superseding.appended
    link = ClosingQuoteLinkService(store=source).record(
        execution_id="execution-1",
        closing_snapshot_id="closing-1",
        linked_at_utc=NOW + timedelta(minutes=42),
    )
    assert link.appended

    path = tmp_path / "events.jsonl"
    durable = JsonlPregameEventStore(path)
    for event in source.list_all_events():
        assert durable.append(event).status == AppendStatus.APPENDED
    restarted = JsonlPregameEventStore(path)
    rerun = ClosingQuoteLinkService(store=restarted).record(
        execution_id="execution-1",
        closing_snapshot_id="closing-1",
        linked_at_utc=NOW + timedelta(minutes=42),
    )
    assert not rerun.appended
    assert rerun.projected_game.closing_snapshot_id_for_execution("execution-1") == "closing-1"
