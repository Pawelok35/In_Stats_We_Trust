"""Append-only successful placement records authorized by explicit decisions."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from pydantic import ValidationError

from pregame.contracts import (
    ManifestBackedOperatorDecisionRecord,
    PregameEvent,
    WagerExecution,
)
from pregame.events import MarketType, OperatorVerdict, PregameEventType
from pregame.projector import project_game
from pregame.store import AppendStatus, PregameEventStore


def wager_execution_event_id(execution_id: str) -> str:
    """Return the stable append-only event identity for one execution."""

    return f"wager-execution:{execution_id}"


@dataclass(frozen=True)
class WagerExecutionRegistrationResult:
    """Outcome of an execution registration attempt without placement side effects."""

    execution_id: str
    event_id: str | None
    appended: bool
    decision_id: str
    successful_execution_exists: bool
    projected_game: object | None
    readiness_failure_codes: tuple[str, ...] = ()


class ManifestBackedWagerExecutionService:
    """Register one immutable successful placement from one explicit decision ID."""

    def __init__(self, *, store: PregameEventStore) -> None:
        self._store = store

    def record(
        self,
        *,
        execution_id: str,
        decision_id: str,
        market_type: MarketType,
        selected_side: str,
        spread: float,
        price: int,
        book: str,
        stake_units: float,
        executed_at_utc: datetime,
        recorded_at_utc: datetime,
        external_ticket_id: str | None = None,
    ) -> WagerExecutionRegistrationResult:
        """Record a fact of placement; this never invokes a sportsbook or a gate."""

        event_id = wager_execution_event_id(execution_id)
        decision_event = self._store.get_event(f"operator-decision:{decision_id}")
        if decision_event is None:
            return self._failed(execution_id, decision_id, "DECISION_NOT_FOUND")
        if decision_event.event_type != PregameEventType.OPERATOR_DECISION_RECORDED:
            return self._failed(execution_id, decision_id, "DECISION_NOT_STRUCTURED")
        try:
            decision = ManifestBackedOperatorDecisionRecord.model_validate(decision_event.payload)
        except ValidationError:
            return self._failed(execution_id, decision_id, "DECISION_PAYLOAD_INVALID")
        if decision.decision_id != decision_id:
            return self._failed(execution_id, decision_id, "DECISION_ID_MISMATCH")

        state = project_game(self._store, decision.game_id)
        if state is None:
            return self._failed(execution_id, decision_id, "PROJECTED_DECISION_STATE_MISSING")
        if not any(item.decision_id == decision_id for item in state.structured_operator_decisions):
            return self._failed(
                execution_id, decision_id, "DECISION_NOT_IN_STRUCTURED_HISTORY", state
            )
        existing = next(
            (item for item in state.wager_execution_history if item.decision_id == decision_id),
            None,
        )
        if existing is not None and existing.execution_id != execution_id:
            return self._failed(execution_id, decision_id, "DECISION_ALREADY_EXECUTED", state)

        try:
            execution = WagerExecution(
                execution_id=execution_id,
                decision_id=decision_id,
                candidate_id=decision.candidate_id,
                game_id=decision.game_id,
                gate_evaluation_id=decision.gate_evaluation_id,
                market_type=market_type,
                selected_side=selected_side,
                spread=spread,
                price=price,
                book=book,
                stake_units=stake_units,
                executed_at_utc=executed_at_utc,
                recorded_at_utc=recorded_at_utc,
                external_ticket_id=external_ticket_id,
            )
        except ValidationError:
            return self._failed(execution_id, decision_id, "INVALID_EXECUTION")
        if existing is not None:
            append = self._store.append(self._event_for(execution))
            if append.status == AppendStatus.CONFLICT:
                return self._failed(
                    execution_id, decision_id, "EXECUTION_EVENT_CONFLICT", state, event_id
                )
            return WagerExecutionRegistrationResult(
                execution_id=execution_id,
                event_id=event_id,
                appended=False,
                decision_id=decision_id,
                successful_execution_exists=True,
                projected_game=state,
            )

        failure = self._validate_authorization(
            decision=decision,
            state=state,
            market_type=market_type,
            selected_side=selected_side,
            spread=spread,
            price=price,
            book=book,
            stake_units=stake_units,
            executed_at_utc=executed_at_utc,
            recorded_at_utc=recorded_at_utc,
        )
        if failure is not None:
            return self._failed(execution_id, decision_id, failure, state)

        append = self._store.append(self._event_for(execution))
        if append.status == AppendStatus.CONFLICT:
            return self._failed(
                execution_id, decision_id, "EXECUTION_EVENT_CONFLICT", state, event_id
            )
        projected = project_game(self._store, execution.game_id)
        return WagerExecutionRegistrationResult(
            execution_id=execution_id,
            event_id=event_id,
            appended=append.status == AppendStatus.APPENDED,
            decision_id=decision_id,
            successful_execution_exists=True,
            projected_game=projected,
        )

    @staticmethod
    def _event_for(execution: WagerExecution) -> PregameEvent:
        event_id = wager_execution_event_id(execution.execution_id)
        return PregameEvent(
            event_id=event_id,
            game_id=execution.game_id,
            event_type=PregameEventType.WAGER_EXECUTION_RECORDED,
            created_at_utc=execution.recorded_at_utc,
            effective_at_utc=execution.executed_at_utc,
            source="manifest_backed_wager_execution",
            idempotency_key=event_id,
            payload=execution.to_json_dict(),
        )

    def _validate_authorization(
        self,
        *,
        decision: ManifestBackedOperatorDecisionRecord,
        state: object,
        market_type: MarketType,
        selected_side: str,
        spread: float,
        price: int,
        book: str,
        stake_units: float,
        executed_at_utc: datetime,
        recorded_at_utc: datetime,
    ) -> str | None:
        if decision.verdict not in {
            OperatorVerdict.APPROVED,
            OperatorVerdict.APPROVED_REDUCED_STAKE,
        }:
            return "DECISION_VERDICT_NOT_APPROVED"
        if decision.stake_units is None:
            return "DECISION_STAKE_MISSING"
        gate = next(
            (
                item
                for item in state.final_quote_gate_results
                if item.evaluation_id == decision.gate_evaluation_id
            ),
            None,
        )
        if gate is None or gate.research_lineage is None:
            return "GATE_LINEAGE_MISSING"
        if (
            gate.candidate_id != decision.candidate_id
            or gate.game_id != decision.game_id
            or gate.final_snapshot_id != decision.final_snapshot_id
            or gate.policy_id != decision.policy_id
            or gate.policy_digest != decision.policy_digest
            or gate.research_lineage.audit_build_id != decision.audit_build_id
            or gate.research_lineage.audit_evidence_id != decision.audit_evidence_id
            or gate.research_lineage.manifest_id != decision.manifest_id
            or gate.research_lineage.model_generation_snapshot_id
            != decision.model_generation_snapshot_id
        ):
            return "DECISION_GATE_LINEAGE_MISMATCH"
        if state.kickoff_utc is None:
            return "AUTHORITATIVE_KICKOFF_MISSING"
        if decision.decision_at_utc > executed_at_utc:
            return "EXECUTION_BEFORE_DECISION"
        if executed_at_utc > state.kickoff_utc:
            return "EXECUTION_AFTER_KICKOFF"
        if executed_at_utc > recorded_at_utc:
            return "EXECUTION_RECORDED_BEFORE_EXECUTION"
        superseder = next(
            (
                item
                for item in state.structured_operator_decisions
                if item.supersedes_decision_id == decision.decision_id
            ),
            None,
        )
        if superseder is not None:
            supersession_event = self._store.get_event(
                f"operator-decision:{superseder.decision_id}"
            )
            if supersession_event is None:
                return "SUPERSESSION_CHRONOLOGY_UNRESOLVED"
            if supersession_event.effective_at_utc <= executed_at_utc:
                return "DECISION_SUPERSEDED_AT_EXECUTION"
        if market_type != MarketType.SPREAD:
            return "EXECUTION_MARKET_MISMATCH"
        if selected_side != gate.selected_team:
            return "EXECUTION_SIDE_MISMATCH"
        if spread != decision.spread or spread != gate.final_spread:
            return "EXECUTION_SPREAD_MISMATCH"
        if price != decision.price or price != gate.final_price:
            return "EXECUTION_PRICE_MISMATCH"
        if book != decision.book or book != gate.book:
            return "EXECUTION_BOOK_MISMATCH"
        if stake_units != decision.stake_units:
            return "EXECUTION_STAKE_MISMATCH"
        return None

    @staticmethod
    def _failed(
        execution_id: str,
        decision_id: str,
        code: str,
        state: object | None = None,
        event_id: str | None = None,
    ) -> WagerExecutionRegistrationResult:
        return WagerExecutionRegistrationResult(
            execution_id=execution_id,
            event_id=event_id,
            appended=False,
            decision_id=decision_id,
            successful_execution_exists=False,
            projected_game=state,
            readiness_failure_codes=(code,),
        )
