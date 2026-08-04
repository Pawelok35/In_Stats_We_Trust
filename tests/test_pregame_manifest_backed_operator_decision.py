from __future__ import annotations

# ruff: noqa: E501
from datetime import timedelta

from pregame.candidate_registry import CandidateRegistryService
from pregame.events import OperatorVerdict
from pregame.manifest_backed_operator_decision import ManifestBackedOperatorDecisionService
from pregame.market_history import MarketSnapshotHistoryService
from tests.test_pregame_manifest_backed_final_quote_gate import evaluate, ready_service


def service(store):
    return ManifestBackedOperatorDecisionService(
        store=store,
        candidates=CandidateRegistryService(store),
        market_history=MarketSnapshotHistoryService(store),
    )


def test_approval_is_gate_linked_idempotent_and_supersedable(tmp_path):
    store, candidate, manifest, quote, build, _gate, wrapper = ready_service(tmp_path)
    gate = evaluate(wrapper, candidate, manifest, quote, build).gate_result
    assert gate is not None
    decisions = service(store)
    values = dict(
        decision_id="decision-1",
        candidate_id=candidate.candidate_id,
        gate_evaluation_id=gate.evaluation_id,
        verdict=OperatorVerdict.APPROVED,
        stake_units=1.0,
        operator_id="operator:daniel",
        reason_codes=("APPROVED_AFTER_REVIEW",),
        decision_at_utc=gate.evaluated_at_utc + timedelta(minutes=1),
        recorded_at_utc=gate.evaluated_at_utc + timedelta(minutes=2),
    )
    first = decisions.record(**values)
    rerun = decisions.record(**values)
    assert first.appended and not rerun.appended
    assert first.projected_game.active_structured_operator_decision.stake_units == 1.0
    second = decisions.record(
        **{
            **values,
            "decision_id": "decision-2",
            "verdict": OperatorVerdict.PASS,
            "stake_units": None,
            "supersedes_decision_id": "decision-1",
            "reason_codes": ("PASS",),
            "decision_at_utc": values["decision_at_utc"] + timedelta(minutes=2),
            "recorded_at_utc": values["recorded_at_utc"] + timedelta(minutes=2),
        }
    )
    assert (
        second.appended
        and second.projected_game.active_structured_operator_decision.decision_id == "decision-2"
    )


def test_non_approval_stake_and_blocked_gate_approval_fail_closed(tmp_path):
    store, candidate, manifest, quote, build, _gate, wrapper = ready_service(tmp_path)
    gate = evaluate(wrapper, candidate, manifest, quote, build).gate_result
    result = service(store).record(
        decision_id="bad",
        candidate_id=candidate.candidate_id,
        gate_evaluation_id=gate.evaluation_id,
        verdict=OperatorVerdict.PASS,
        stake_units=1.0,
        operator_id="operator:daniel",
        reason_codes=("PASS",),
        decision_at_utc=gate.evaluated_at_utc + timedelta(minutes=1),
        recorded_at_utc=gate.evaluated_at_utc + timedelta(minutes=2),
    )
    assert result.readiness_failure_codes == ("INVALID_STAKE",)
