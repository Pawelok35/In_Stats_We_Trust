from __future__ import annotations

from datetime import timedelta

from pregame.candidate_registry import CandidateRegistryService
from pregame.contracts import PregameEvent
from pregame.events import MarketType, OperatorVerdict, PregameEventType
from pregame.jsonl_store import JsonlPregameEventStore
from pregame.manifest_backed_operator_decision import ManifestBackedOperatorDecisionService
from pregame.market_history import MarketSnapshotHistoryService
from pregame.projector import project_game
from pregame.store import AppendStatus
from pregame.wager_execution import ManifestBackedWagerExecutionService
from tests.test_pregame_manifest_backed_final_quote_gate import (
    NOW,
    evaluate,
    ready_service,
)


def _add_game(store, value) -> None:
    assert (
        store.append(
            PregameEvent(
                event_id=f"game-created:{value.game_id}",
                game_id=value.game_id,
                event_type=PregameEventType.GAME_CREATED,
                created_at_utc=NOW - timedelta(minutes=1),
                effective_at_utc=NOW - timedelta(minutes=1),
                source="test_schedule",
                payload={
                    "season": value.season,
                    "week": value.week,
                    "away_team": value.away,
                    "home_team": value.home,
                    "kickoff_utc": (NOW + timedelta(hours=2)).isoformat(),
                },
            )
        ).status
        == AppendStatus.APPENDED
    )


def _decision_service(store):
    return ManifestBackedOperatorDecisionService(
        store=store,
        candidates=CandidateRegistryService(store),
        market_history=MarketSnapshotHistoryService(store),
    )


def _approved(tmp_path, *, verdict=OperatorVerdict.APPROVED, stake_units=1.0):
    store, candidate, manifest, quote, build, _gate, wrapper = ready_service(tmp_path)
    _add_game(store, candidate)
    gate = evaluate(wrapper, candidate, manifest, quote, build).gate_result
    assert gate is not None
    result = _decision_service(store).record(
        decision_id="decision-1",
        candidate_id=candidate.candidate_id,
        gate_evaluation_id=gate.evaluation_id,
        verdict=verdict,
        stake_units=stake_units,
        operator_id="operator:daniel",
        reason_codes=(verdict.value,),
        decision_at_utc=NOW + timedelta(minutes=5),
        recorded_at_utc=NOW + timedelta(minutes=6),
    )
    assert result.appended
    return store, candidate, gate


def _execution_values(candidate, gate, **overrides):
    values = {
        "execution_id": "execution-1",
        "decision_id": "decision-1",
        "market_type": MarketType.SPREAD,
        "selected_side": candidate.selected_team,
        "spread": gate.final_spread,
        "price": gate.final_price,
        "book": gate.book,
        "stake_units": 1.0,
        "executed_at_utc": NOW + timedelta(minutes=7),
        "recorded_at_utc": NOW + timedelta(minutes=8),
    }
    values.update(overrides)
    return values


def test_approved_execution_is_recorded_idempotently_and_projected(tmp_path):
    store, candidate, gate = _approved(tmp_path)
    service = ManifestBackedWagerExecutionService(store=store)
    values = _execution_values(candidate, gate, external_ticket_id="ticket-42")

    first = service.record(**values)
    rerun = service.record(**values)

    assert first.appended and not rerun.appended
    assert first.projected_game.wager_execution_history[0].external_ticket_id == "ticket-42"
    assert first.projected_game.successful_execution_by_decision_id == (
        ("decision-1", "execution-1"),
    )
    conflict = service.record(**_execution_values(candidate, gate, price=gate.final_price + 1))
    assert conflict.readiness_failure_codes == ("EXECUTION_EVENT_CONFLICT",)


def test_reduced_stake_requires_the_exact_approved_stake(tmp_path):
    store, candidate, gate = _approved(
        tmp_path,
        verdict=OperatorVerdict.APPROVED_REDUCED_STAKE,
        stake_units=0.5,
    )
    service = ManifestBackedWagerExecutionService(store=store)

    mismatch = service.record(**_execution_values(candidate, gate, stake_units=1.0))
    exact = service.record(
        **_execution_values(candidate, gate, execution_id="execution-reduced", stake_units=0.5)
    )

    assert mismatch.readiness_failure_codes == ("EXECUTION_STAKE_MISMATCH",)
    assert exact.appended
    assert exact.projected_game.latest_wager_execution.stake_units == 0.5


def test_nonapproval_and_changed_terms_fail_closed(tmp_path):
    store, candidate, gate = _approved(tmp_path, verdict=OperatorVerdict.WAIT, stake_units=None)
    service = ManifestBackedWagerExecutionService(store=store)
    rejected = service.record(**_execution_values(candidate, gate, stake_units=1.0))
    assert rejected.readiness_failure_codes == ("DECISION_VERDICT_NOT_APPROVED",)

    store, candidate, gate = _approved(tmp_path)
    changed = ManifestBackedWagerExecutionService(store=store).record(
        **_execution_values(candidate, gate, price=gate.final_price + 1)
    )
    assert changed.readiness_failure_codes == ("EXECUTION_PRICE_MISMATCH",)
    assert not any(
        event.event_type == PregameEventType.WAGER_EXECUTION_RECORDED
        for event in store.list_events(candidate.game_id)
    )


def test_supersession_is_temporal_not_current_active_status(tmp_path):
    store, candidate, gate = _approved(tmp_path)
    decisions = _decision_service(store)
    superseding = decisions.record(
        decision_id="decision-2",
        candidate_id=candidate.candidate_id,
        gate_evaluation_id=gate.evaluation_id,
        verdict=OperatorVerdict.PASS,
        stake_units=None,
        operator_id="operator:daniel",
        reason_codes=("PASS",),
        decision_at_utc=NOW + timedelta(minutes=10),
        recorded_at_utc=NOW + timedelta(minutes=11),
        supersedes_decision_id="decision-1",
    )
    assert superseding.appended

    too_late = ManifestBackedWagerExecutionService(store=store).record(
        **_execution_values(
            candidate,
            gate,
            execution_id="execution-late",
            executed_at_utc=NOW + timedelta(minutes=10),
            recorded_at_utc=NOW + timedelta(minutes=12),
        )
    )
    historical = ManifestBackedWagerExecutionService(store=store).record(
        **_execution_values(candidate, gate)
    )

    assert too_late.readiness_failure_codes == ("DECISION_SUPERSEDED_AT_EXECUTION",)
    assert historical.appended
    state = project_game(store, candidate.game_id)
    assert state.wager_execution_history[0].decision_id == "decision-1"


def test_second_execution_and_jsonl_restart_preserve_one_execution_policy(tmp_path):
    path = tmp_path / "events.jsonl"
    source_store, candidate, gate = _approved(tmp_path)
    store = JsonlPregameEventStore(path)
    for event in source_store.list_all_events():
        assert store.append(event).status == AppendStatus.APPENDED
    service = ManifestBackedWagerExecutionService(store=store)
    assert service.record(**_execution_values(candidate, gate)).appended
    second = service.record(**_execution_values(candidate, gate, execution_id="execution-2"))
    assert second.readiness_failure_codes == ("DECISION_ALREADY_EXECUTED",)

    restarted = JsonlPregameEventStore(path)
    state = project_game(restarted, candidate.game_id)
    assert len(state.wager_execution_history) == 1
    assert state.wager_executions_by_id == (("execution-1", "execution-1"),)
