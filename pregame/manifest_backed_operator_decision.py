"""Append-only human decision registration linked to an explicit gate evaluation."""

# ruff: noqa: E501

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from pregame.candidate_registry import CandidateRegistryService
from pregame.contracts import ManifestBackedOperatorDecisionRecord, PregameEvent
from pregame.events import FinalQuoteGateStatus, OperatorVerdict, PregameEventType, SnapshotKind
from pregame.market_history import MarketSnapshotHistoryService
from pregame.projector import project_game
from pregame.store import AppendStatus, PregameEventStore


@dataclass(frozen=True)
class OperatorDecisionRegistrationResult:
    decision_id: str
    event_id: str | None
    appended: bool
    candidate_id: str
    game_id: str | None
    gate_evaluation_id: str
    verdict: OperatorVerdict
    active: bool
    supersedes_decision_id: str | None
    projected_game: object | None
    readiness_failure_codes: tuple[str, ...] = ()


class ManifestBackedOperatorDecisionService:
    def __init__(
        self,
        *,
        store: PregameEventStore,
        candidates: CandidateRegistryService,
        market_history: MarketSnapshotHistoryService,
    ) -> None:
        self._store, self._candidates, self._market_history = store, candidates, market_history

    def record(
        self,
        *,
        decision_id: str,
        candidate_id: str,
        gate_evaluation_id: str,
        verdict: OperatorVerdict,
        stake_units: float | None,
        operator_id: str,
        reason_codes: tuple[str, ...],
        decision_at_utc: datetime,
        recorded_at_utc: datetime,
        supersedes_decision_id: str | None = None,
        operator_display_name: str | None = None,
        notes: str | None = None,
    ) -> OperatorDecisionRegistrationResult:
        candidate = self._candidates.get_candidate(candidate_id)
        if candidate is None:
            return self._failed(
                decision_id,
                candidate_id,
                None,
                gate_evaluation_id,
                verdict,
                supersedes_decision_id,
                "CANDIDATE_NOT_FOUND",
            )
        state = project_game(self._store, candidate.game_id)
        gate = (
            next(
                (
                    item
                    for item in state.final_quote_gate_results
                    if item.evaluation_id == gate_evaluation_id
                ),
                None,
            )
            if state
            else None
        )
        if gate is None:
            return self._failed(
                decision_id,
                candidate_id,
                candidate.game_id,
                gate_evaluation_id,
                verdict,
                supersedes_decision_id,
                "GATE_EVALUATION_NOT_FOUND",
                state,
            )
        if gate.research_lineage is None:
            return self._failed(
                decision_id,
                candidate_id,
                candidate.game_id,
                gate_evaluation_id,
                verdict,
                supersedes_decision_id,
                "GATE_RESEARCH_LINEAGE_MISSING",
                state,
            )
        approval = verdict in {OperatorVerdict.APPROVED, OperatorVerdict.APPROVED_REDUCED_STAKE}
        if approval and gate.primary_status != FinalQuoteGateStatus.FINAL_QUOTE_VALID:
            return self._failed(
                decision_id,
                candidate_id,
                candidate.game_id,
                gate_evaluation_id,
                verdict,
                supersedes_decision_id,
                "GATE_STATUS_INCOMPATIBLE_WITH_VERDICT",
                state,
            )
        if gate.candidate_id != candidate_id or gate.game_id != candidate.game_id:
            return self._failed(
                decision_id,
                candidate_id,
                candidate.game_id,
                gate_evaluation_id,
                verdict,
                supersedes_decision_id,
                "GATE_CANDIDATE_MISMATCH",
                state,
            )
        if not operator_id.strip() or not reason_codes:
            return self._failed(
                decision_id,
                candidate_id,
                candidate.game_id,
                gate_evaluation_id,
                verdict,
                supersedes_decision_id,
                "OPERATOR_ID_MISSING" if not operator_id.strip() else "REASON_CODES_MISSING",
                state,
            )
        snapshot = self._market_history.get_snapshot(gate.final_snapshot_id)
        if snapshot is None:
            return self._failed(
                decision_id,
                candidate_id,
                candidate.game_id,
                gate_evaluation_id,
                verdict,
                supersedes_decision_id,
                "FINAL_SNAPSHOT_NOT_FOUND",
                state,
            )
        latest = self._market_history.list_snapshots(
            candidate.game_id,
            market_type=snapshot.market_type,
            book=snapshot.book,
            snapshot_kind=SnapshotKind.FINAL,
        )
        relevant = [item for item in latest if item.selected_side == snapshot.selected_side]
        if relevant and relevant[-1].snapshot_id != snapshot.snapshot_id:
            return self._failed(
                decision_id,
                candidate_id,
                candidate.game_id,
                gate_evaluation_id,
                verdict,
                supersedes_decision_id,
                "NEWER_FINAL_SNAPSHOT_EXISTS",
                state,
            )
        latest_audit = state.latest_successful_structured_variant_b_audit
        if latest_audit is None or latest_audit.build_id != gate.research_lineage.audit_build_id:
            return self._failed(
                decision_id,
                candidate_id,
                candidate.game_id,
                gate_evaluation_id,
                verdict,
                supersedes_decision_id,
                "GATE_AUDIT_NOT_LATEST_SUCCESSFUL",
                state,
            )
        active = state.active_structured_operator_decision
        if active is None and supersedes_decision_id is not None:
            return self._failed(
                decision_id,
                candidate_id,
                candidate.game_id,
                gate_evaluation_id,
                verdict,
                supersedes_decision_id,
                "INVALID_DECISION_SUPERSESSION",
                state,
            )
        if active is not None and supersedes_decision_id != active.decision_id:
            return self._failed(
                decision_id,
                candidate_id,
                candidate.game_id,
                gate_evaluation_id,
                verdict,
                supersedes_decision_id,
                "ACTIVE_DECISION_REQUIRES_SUPERSESSION",
                state,
            )
        try:
            record = ManifestBackedOperatorDecisionRecord(
                decision_id=decision_id,
                candidate_id=candidate_id,
                game_id=candidate.game_id,
                gate_evaluation_id=gate_evaluation_id,
                verdict=verdict,
                operator_id=operator_id,
                reason_codes=reason_codes,
                decision_at_utc=decision_at_utc,
                recorded_at_utc=recorded_at_utc,
                final_snapshot_id=gate.final_snapshot_id,
                spread=gate.final_spread,
                price=gate.final_price,
                book=gate.book,
                audit_build_id=gate.research_lineage.audit_build_id,
                audit_evidence_id=gate.research_lineage.audit_evidence_id,
                manifest_id=gate.research_lineage.manifest_id,
                model_generation_snapshot_id=gate.research_lineage.model_generation_snapshot_id,
                policy_id=gate.policy_id,
                policy_digest=gate.policy_digest,
                gate_status=gate.primary_status,
                stake_units=stake_units,
                supersedes_decision_id=supersedes_decision_id,
                operator_display_name=operator_display_name,
                notes=notes,
            )
        except ValueError:
            return self._failed(
                decision_id,
                candidate_id,
                candidate.game_id,
                gate_evaluation_id,
                verdict,
                supersedes_decision_id,
                "INVALID_STAKE",
                state,
            )
        if gate.evaluated_at_utc > decision_at_utc or decision_at_utc > recorded_at_utc:
            return self._failed(
                decision_id,
                candidate_id,
                candidate.game_id,
                gate_evaluation_id,
                verdict,
                supersedes_decision_id,
                "INVALID_TIMESTAMP_ORDER",
                state,
            )
        event_id = f"operator-decision:{decision_id}"
        event = PregameEvent(
            event_id=event_id,
            game_id=candidate.game_id,
            event_type=PregameEventType.OPERATOR_DECISION_RECORDED,
            created_at_utc=recorded_at_utc,
            effective_at_utc=decision_at_utc,
            source="manifest_backed_operator_decision",
            idempotency_key=event_id,
            payload=record.to_json_dict(),
        )
        append = self._store.append(event)
        if append.status == AppendStatus.CONFLICT:
            return self._failed(
                decision_id,
                candidate_id,
                candidate.game_id,
                gate_evaluation_id,
                verdict,
                supersedes_decision_id,
                "DECISION_EVENT_CONFLICT",
                state,
            )
        projected = project_game(self._store, candidate.game_id)
        return OperatorDecisionRegistrationResult(
            decision_id,
            event_id,
            append.status == AppendStatus.APPENDED,
            candidate_id,
            candidate.game_id,
            gate_evaluation_id,
            verdict,
            projected.active_structured_operator_decision.decision_id == decision_id,
            supersedes_decision_id,
            projected,
        )

    @staticmethod
    def _failed(
        decision_id,
        candidate_id,
        game_id,
        gate_evaluation_id,
        verdict,
        supersedes,
        code,
        state=None,
    ):
        return OperatorDecisionRegistrationResult(
            decision_id,
            None,
            False,
            candidate_id,
            game_id,
            gate_evaluation_id,
            verdict,
            False,
            supersedes,
            state,
            (code,),
        )
