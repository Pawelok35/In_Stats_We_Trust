from __future__ import annotations

from datetime import timedelta

import pytest
from pydantic import ValidationError

from pregame.contracts import PregameEvent, WagerExecution
from pregame.events import PregameEventType
from pregame.game_result import AuthoritativeGameResultService
from pregame.jsonl_store import JsonlPregameEventStore
from pregame.projector import project_game
from pregame.store import AppendStatus
from pregame.wager_execution import (
    ManifestBackedWagerExecutionService,
    wager_execution_event_id,
)
from pregame.wager_execution_settlement import WagerExecutionSettlementService
from tests.test_pregame_manifest_backed_final_quote_gate import NOW
from tests.test_pregame_wager_execution import _approved, _execution_values


def _record_final_result(store, candidate, *, selected_score: int, opponent_score: int):
    state = project_game(store, candidate.game_id)
    assert state.kickoff_utc is not None
    home_score, away_score = (
        (selected_score, opponent_score)
        if candidate.selected_team == state.home_team
        else (opponent_score, selected_score)
    )
    finalized = state.kickoff_utc + timedelta(hours=3)
    result = AuthoritativeGameResultService(store=store).record(
        game_id=candidate.game_id,
        home_score=home_score,
        away_score=away_score,
        source="NFL_OFFICIAL_GAMEBOOK",
        source_reference=f"gamebook:{candidate.game_id}",
        source_finalized_at_utc=finalized,
        observed_at_utc=finalized + timedelta(minutes=1),
    )
    assert result.appended
    return finalized


def _executed(tmp_path, *, stake_units: float = 1.0):
    store, candidate, gate = _approved(tmp_path, stake_units=stake_units)
    execution = ManifestBackedWagerExecutionService(store=store).record(
        **_execution_values(candidate, gate, stake_units=stake_units)
    )
    assert execution.appended
    return store, candidate, gate


@pytest.mark.parametrize(
    ("selected_score", "opponent_score", "expected_outcome", "expected_profit"),
    [
        (24, 20, "WIN", "0.909091"),
        (20, 24, "LOSS", "-1.000000"),
        (22, 20, "PUSH", "0.000000"),
    ],
)
def test_v1_settlement_uses_execution_side_spread_and_risk_based_american_odds(
    tmp_path, selected_score, opponent_score, expected_outcome, expected_profit
):
    store, candidate, _gate = _executed(tmp_path)
    finalized = _record_final_result(
        store,
        candidate,
        selected_score=selected_score,
        opponent_score=opponent_score,
    )

    settlement = WagerExecutionSettlementService(store=store).record(
        execution_id="execution-1", settled_at_utc=finalized + timedelta(minutes=2)
    )

    assert settlement.appended
    value = settlement.projected_game.latest_wager_execution_settlement
    assert value is not None
    assert value.outcome == expected_outcome
    assert value.execution_price == -110
    assert value.risk_units == "1.000000"
    assert value.net_profit_units == expected_profit
    assert (
        value.adjusted_margin
        == {
            "WIN": "2.000000",
            "LOSS": "-6.000000",
            "PUSH": "0.000000",
        }[expected_outcome]
    )
    assert not settlement.projected_game.settled
    assert settlement.projected_game.latest_settlement_event_id is None


def test_positive_american_odds_and_rounding_are_deterministic(tmp_path):
    store, candidate, gate = _approved(tmp_path, stake_units=3.0)
    values = _execution_values(candidate, gate, price=105, stake_units=3.0)
    values["financial_terms_version"] = "AMERICAN_ODDS_RISK_BASED_V1"
    execution = WagerExecution(
        candidate_id=candidate.candidate_id,
        game_id=candidate.game_id,
        gate_evaluation_id=gate.evaluation_id,
        **values,
    )
    assert (
        store.append(
            PregameEvent(
                event_id=wager_execution_event_id(execution.execution_id),
                game_id=candidate.game_id,
                event_type=PregameEventType.WAGER_EXECUTION_RECORDED,
                created_at_utc=execution.recorded_at_utc,
                effective_at_utc=execution.executed_at_utc,
                source="test_execution",
                payload=execution.to_json_dict(),
            )
        ).status
        == AppendStatus.APPENDED
    )
    finalized = _record_final_result(store, candidate, selected_score=24, opponent_score=20)

    settled = WagerExecutionSettlementService(store=store).record(
        execution_id="execution-1", settled_at_utc=finalized + timedelta(minutes=1)
    )

    assert settled.appended
    assert settled.projected_game.latest_wager_execution_settlement.net_profit_units == "3.150000"


def test_settlement_fails_closed_without_final_result_or_before_finalization(tmp_path):
    store, candidate, _gate = _executed(tmp_path)
    service = WagerExecutionSettlementService(store=store)
    assert service.record(
        execution_id="execution-1", settled_at_utc=NOW + timedelta(days=1)
    ).readiness_failure_codes == ("AUTHORITATIVE_RESULT_MISSING",)

    finalized = _record_final_result(store, candidate, selected_score=24, opponent_score=20)
    assert service.record(
        execution_id="execution-1", settled_at_utc=finalized - timedelta(seconds=1)
    ).readiness_failure_codes == ("SETTLEMENT_BEFORE_RESULT_FINALIZED",)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("stake_units", True),
        ("stake_units", 0),
        ("stake_units", float("nan")),
        ("spread", False),
        ("spread", float("inf")),
        ("price", True),
        ("price", -99),
        ("price", 99),
        ("price", -110.0),
        ("price", "-110"),
    ],
)
def test_v1_execution_contract_rejects_invalid_financial_inputs(tmp_path, field, value):
    _store, candidate, gate = _approved(tmp_path)
    values = _execution_values(candidate, gate)
    values[field] = value
    values["financial_terms_version"] = "AMERICAN_ODDS_RISK_BASED_V1"

    with pytest.raises(ValidationError):
        WagerExecution(
            candidate_id=candidate.candidate_id,
            game_id=candidate.game_id,
            gate_evaluation_id=gate.evaluation_id,
            **values,
        )


def test_unversioned_execution_is_replayable_but_cannot_be_centrally_settled(tmp_path):
    store, candidate, gate = _approved(tmp_path)
    values = _execution_values(candidate, gate)
    execution = WagerExecution(
        candidate_id=candidate.candidate_id,
        game_id=candidate.game_id,
        gate_evaluation_id=gate.evaluation_id,
        **values,
    )
    assert execution.financial_terms_version is None
    assert (
        store.append(
            PregameEvent(
                event_id=wager_execution_event_id(execution.execution_id),
                game_id=candidate.game_id,
                event_type=PregameEventType.WAGER_EXECUTION_RECORDED,
                created_at_utc=execution.recorded_at_utc,
                effective_at_utc=execution.executed_at_utc,
                source="legacy_execution",
                payload=execution.to_json_dict(),
            )
        ).status
        == AppendStatus.APPENDED
    )
    assert len(project_game(store, candidate.game_id).wager_execution_history) == 1

    result = WagerExecutionSettlementService(store=store).record(
        execution_id="execution-1", settled_at_utc=NOW + timedelta(days=1)
    )
    assert result.readiness_failure_codes == ("EXECUTION_FINANCIAL_TERMS_UNVERSIONED",)


def test_settlement_is_idempotent_and_jsonl_restart_preserves_immutable_record(tmp_path):
    source, candidate, _gate = _executed(tmp_path)
    path = tmp_path / "events.jsonl"
    store = JsonlPregameEventStore(path)
    for event in source.list_all_events():
        assert store.append(event).status == AppendStatus.APPENDED
    finalized = _record_final_result(store, candidate, selected_score=24, opponent_score=20)
    service = WagerExecutionSettlementService(store=store)
    first = service.record(
        execution_id="execution-1", settled_at_utc=finalized + timedelta(minutes=1)
    )
    second = service.record(
        execution_id="execution-1", settled_at_utc=finalized + timedelta(minutes=1)
    )

    assert first.appended and not second.appended
    restarted = JsonlPregameEventStore(path)
    state = project_game(restarted, candidate.game_id)
    assert state.has_execution_settlement("execution-1")
    assert state.settlement_for_execution("execution-1").net_profit_units == "0.909091"
