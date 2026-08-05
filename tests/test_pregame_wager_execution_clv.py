from __future__ import annotations

from datetime import timedelta

from pregame.closing_quote_link import ClosingQuoteLinkService
from pregame.events import PregameEventType
from pregame.jsonl_store import JsonlPregameEventStore
from pregame.store import AppendStatus
from pregame.wager_execution_clv import WagerExecutionClvService
from tests.test_pregame_closing_quote_link import _closing, _execution, _record_snapshot
from tests.test_pregame_manifest_backed_final_quote_gate import NOW


def _linked_execution(tmp_path, **closing_overrides):
    store, candidate, gate, _execution_result = _execution(tmp_path)
    closing = _closing(candidate, gate, **closing_overrides)
    assert _record_snapshot(store, closing).status == AppendStatus.APPENDED
    linked_at = closing.captured_at_utc + timedelta(minutes=1)
    link = ClosingQuoteLinkService(store=store).record(
        execution_id="execution-1",
        closing_snapshot_id=closing.snapshot_id,
        linked_at_utc=linked_at,
    )
    assert link.appended
    return store, candidate, closing, linked_at


def test_clv_uses_only_designated_same_book_closing_link_without_result_or_settlement(tmp_path):
    store, candidate, closing, linked_at = _linked_execution(
        tmp_path, spread=-3.5, spread_price=-110
    )

    result = WagerExecutionClvService(store=store).record(
        execution_id="execution-1", calculated_at_utc=linked_at + timedelta(minutes=1)
    )

    assert result.appended
    state = result.projected_game
    assert state.authoritative_game_result is None
    assert not state.has_execution_settlement("execution-1")
    assert state.has_execution_clv("execution-1")
    clv = state.clv_for_execution("execution-1")
    assert clv is not None
    assert clv.closing_snapshot_id == closing.snapshot_id
    assert clv.methodology_version == "OPERATOR_DESIGNATED_SAME_BOOK_SPREAD_CLV_V1"
    assert clv.line_clv_points == "1.500000"
    assert clv.price_clv_probability is None
    assert clv.price_clv_status == "NOT_COMPARABLE_LINE_CHANGED"
    assert clv.close_classification == "BEAT_CLOSE"
    assert not any(
        event.event_type == PregameEventType.WAGER_EXECUTION_SETTLED
        for event in store.list_events(candidate.game_id)
    )


def test_price_clv_is_compared_only_at_the_same_spread(tmp_path):
    store, _candidate, _closing_snapshot, linked_at = _linked_execution(
        tmp_path, spread=-2.0, spread_price=-105
    )

    result = WagerExecutionClvService(store=store).record(
        execution_id="execution-1", calculated_at_utc=linked_at + timedelta(minutes=1)
    )

    assert result.appended
    clv = result.projected_game.clv_for_execution("execution-1")
    assert clv is not None
    assert clv.line_clv_points == "0.000000"
    assert clv.execution_implied_probability == "0.523810"
    assert clv.closing_implied_probability == "0.512195"
    assert clv.price_clv_probability == "-0.011614"
    assert clv.price_clv_status == "COMPARABLE"
    assert clv.close_classification == "LOST_TO_CLOSE_ON_PRICE"


def test_clv_requires_explicit_link_is_idempotent_and_conflicts_on_changed_timestamp(tmp_path):
    store, _candidate, _gate, _execution_result = _execution(tmp_path)
    service = WagerExecutionClvService(store=store)
    assert service.record(
        execution_id="execution-1", calculated_at_utc=NOW + timedelta(hours=1)
    ).readiness_failure_codes == ("CLOSING_LINK_MISSING",)

    store, _candidate, _closing_snapshot, linked_at = _linked_execution(tmp_path)
    service = WagerExecutionClvService(store=store)
    values = {
        "execution_id": "execution-1",
        "calculated_at_utc": linked_at + timedelta(minutes=1),
    }
    assert service.record(**values).appended
    assert not service.record(**values).appended
    assert service.record(
        execution_id="execution-1", calculated_at_utc=linked_at + timedelta(minutes=2)
    ).readiness_failure_codes == ("CLV_EVENT_CONFLICT",)


def test_clv_jsonl_restart_preserves_record(tmp_path):
    source, candidate, _closing_snapshot, linked_at = _linked_execution(tmp_path)
    path = tmp_path / "events.jsonl"
    store = JsonlPregameEventStore(path)
    for event in source.list_all_events():
        assert store.append(event).status == AppendStatus.APPENDED
    assert (
        WagerExecutionClvService(store=store)
        .record(execution_id="execution-1", calculated_at_utc=linked_at + timedelta(minutes=1))
        .appended
    )

    restarted = JsonlPregameEventStore(path)
    rerun = WagerExecutionClvService(store=restarted).record(
        execution_id="execution-1", calculated_at_utc=linked_at + timedelta(minutes=1)
    )
    assert not rerun.appended
    assert rerun.projected_game.clv_for_execution("execution-1").line_clv_points == "0.000000"
    assert rerun.projected_game.game_id == candidate.game_id
