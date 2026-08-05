"""Explicit immutable closing-quote benchmark links for successful executions."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timedelta

from pydantic import ValidationError

from pregame.contracts import (
    ClosingQuoteLink,
    ManifestBackedOperatorDecisionRecord,
    MarketSnapshot,
    PregameEvent,
    WagerExecution,
)
from pregame.events import MarketType, PregameEventType, SnapshotKind
from pregame.market_history import (
    MarketSnapshotHistoryError,
    MarketSnapshotHistoryService,
    market_snapshot_event_id,
)
from pregame.projector import project_game
from pregame.store import AppendStatus, PregameEventStore
from pregame.wager_execution import wager_execution_event_id


def closing_quote_link_event_id(execution_id: str) -> str:
    """Return the deterministic closing-link event ID for one execution."""

    if not isinstance(execution_id, str) or not execution_id.strip():
        raise ValueError("execution_id must be a non-empty string")
    return f"closing-quote-link:{execution_id}"


@dataclass(frozen=True)
class ClosingQuoteLinkRegistrationResult:
    """Structured outcome of an immutable closing-quote link registration."""

    execution_id: str
    closing_snapshot_id: str
    event_id: str | None
    appended: bool
    projected_game: object | None
    readiness_failure_codes: tuple[str, ...] = ()


class ClosingQuoteLinkService:
    """Link one explicit execution to one explicit same-book closing snapshot."""

    def __init__(self, *, store: PregameEventStore) -> None:
        self._store = store

    def record(
        self,
        *,
        execution_id: str,
        closing_snapshot_id: str,
        linked_at_utc: datetime,
    ) -> ClosingQuoteLinkRegistrationResult:
        """Record a closing benchmark link without selecting or discovering any quote."""

        if not self._is_utc(linked_at_utc):
            return self._failed(execution_id, closing_snapshot_id, "LINKED_TIMESTAMP_INVALID")
        try:
            event_id = closing_quote_link_event_id(execution_id)
            market_snapshot_event_id(closing_snapshot_id)
        except ValueError:
            return self._failed(execution_id, closing_snapshot_id, "LINK_ID_INPUT_INVALID")

        execution_event = self._store.get_event(wager_execution_event_id(execution_id))
        if execution_event is None:
            return self._failed(execution_id, closing_snapshot_id, "EXECUTION_NOT_FOUND")
        if execution_event.event_type != PregameEventType.WAGER_EXECUTION_RECORDED:
            return self._failed(execution_id, closing_snapshot_id, "EXECUTION_NOT_STRUCTURED")
        try:
            execution = WagerExecution.model_validate(execution_event.payload)
        except ValidationError:
            return self._failed(execution_id, closing_snapshot_id, "EXECUTION_PAYLOAD_INVALID")
        if execution.execution_id != execution_id:
            return self._failed(execution_id, closing_snapshot_id, "EXECUTION_ID_MISMATCH")
        if (
            execution_event.effective_at_utc != execution.executed_at_utc
            or execution_event.created_at_utc != execution.recorded_at_utc
        ):
            return self._failed(
                execution_id, closing_snapshot_id, "EXECUTION_EVENT_TIMESTAMPS_INVALID"
            )

        state = project_game(self._store, execution.game_id)
        if state is None or not any(
            item.execution_id == execution_id for item in state.wager_execution_history
        ):
            return self._failed(
                execution_id, closing_snapshot_id, "EXECUTION_PROJECTOR_STATE_MISSING", state
            )
        try:
            snapshot = MarketSnapshotHistoryService(self._store).get_snapshot(closing_snapshot_id)
        except MarketSnapshotHistoryError:
            return self._failed(
                execution_id, closing_snapshot_id, "CLOSING_SNAPSHOT_INVALID", state
            )
        if snapshot is None:
            return self._failed(
                execution_id, closing_snapshot_id, "CLOSING_SNAPSHOT_NOT_FOUND", state
            )

        decision_event = self._store.get_event(f"operator-decision:{execution.decision_id}")
        if (
            decision_event is None
            or decision_event.event_type != PregameEventType.OPERATOR_DECISION_RECORDED
        ):
            return self._failed(
                execution_id, closing_snapshot_id, "EXECUTION_LINEAGE_DECISION_MISSING", state
            )
        try:
            decision = ManifestBackedOperatorDecisionRecord.model_validate(decision_event.payload)
        except ValidationError:
            return self._failed(
                execution_id, closing_snapshot_id, "EXECUTION_LINEAGE_DECISION_INVALID", state
            )
        if (
            decision_event.effective_at_utc != decision.decision_at_utc
            or decision_event.created_at_utc != decision.recorded_at_utc
        ):
            return self._failed(
                execution_id, closing_snapshot_id, "EXECUTION_LINEAGE_TIMESTAMPS_INVALID", state
            )

        failure = self._validate(
            execution=execution,
            snapshot=snapshot,
            decision=decision,
            state=state,
            linked_at_utc=linked_at_utc,
        )
        if failure is not None:
            return self._failed(execution_id, closing_snapshot_id, failure, state)
        try:
            link = ClosingQuoteLink(
                execution_id=execution.execution_id,
                closing_snapshot_id=snapshot.snapshot_id,
                linked_at_utc=linked_at_utc,
                game_id=execution.game_id,
                candidate_id=execution.candidate_id,
                decision_id=execution.decision_id,
                gate_evaluation_id=execution.gate_evaluation_id,
                audit_build_id=decision.audit_build_id,
                audit_evidence_id=decision.audit_evidence_id,
                manifest_id=decision.manifest_id,
                model_generation_snapshot_id=decision.model_generation_snapshot_id,
            )
        except ValidationError:
            return self._failed(
                execution_id, closing_snapshot_id, "CLOSING_LINK_PAYLOAD_INVALID", state
            )

        append = self._store.append(
            PregameEvent(
                event_id=event_id,
                game_id=link.game_id,
                event_type=PregameEventType.CLOSING_QUOTE_LINKED,
                created_at_utc=linked_at_utc,
                effective_at_utc=linked_at_utc,
                source="closing_quote_link",
                idempotency_key=event_id,
                payload=link.to_json_dict(),
            )
        )
        if append.status == AppendStatus.CONFLICT:
            return self._failed(
                execution_id, closing_snapshot_id, "CLOSING_LINK_EVENT_CONFLICT", state, event_id
            )
        return ClosingQuoteLinkRegistrationResult(
            execution_id=execution_id,
            closing_snapshot_id=closing_snapshot_id,
            event_id=event_id,
            appended=append.status == AppendStatus.APPENDED,
            projected_game=project_game(self._store, execution.game_id),
        )

    @staticmethod
    def _validate(
        *,
        execution: WagerExecution,
        snapshot: MarketSnapshot,
        decision: ManifestBackedOperatorDecisionRecord,
        state: object,
        linked_at_utc: datetime,
    ) -> str | None:
        if (
            decision.decision_id != execution.decision_id
            or decision.candidate_id != execution.candidate_id
            or decision.game_id != execution.game_id
            or decision.gate_evaluation_id != execution.gate_evaluation_id
        ):
            return "EXECUTION_LINEAGE_MISMATCH"
        if state.kickoff_utc is None:
            return "AUTHORITATIVE_KICKOFF_MISSING"
        if snapshot.snapshot_kind != SnapshotKind.CLOSING:
            return "SNAPSHOT_KIND_NOT_CLOSING"
        if snapshot.game_id != execution.game_id:
            return "CLOSING_SNAPSHOT_GAME_MISMATCH"
        if snapshot.market_type != MarketType.SPREAD or execution.market_type != MarketType.SPREAD:
            return "CLOSING_SNAPSHOT_MARKET_MISMATCH"
        if snapshot.selected_side != execution.selected_side:
            return "CLOSING_SNAPSHOT_SIDE_MISMATCH"
        if snapshot.book != execution.book:
            return "CLOSING_SNAPSHOT_BOOK_MISMATCH"
        if snapshot.spread is None or not math.isfinite(snapshot.spread):
            return "CLOSING_SNAPSHOT_SPREAD_MISSING"
        if snapshot.spread_price is None or snapshot.spread_price == 0:
            return "CLOSING_SNAPSHOT_PRICE_MISSING"
        if not snapshot.source.strip():
            return "CLOSING_SNAPSHOT_SOURCE_MISSING"
        if snapshot.captured_at_utc > state.kickoff_utc:
            return "CLOSING_SNAPSHOT_AFTER_KICKOFF"
        if linked_at_utc < execution.executed_at_utc:
            return "LINKED_BEFORE_EXECUTION"
        if linked_at_utc < snapshot.captured_at_utc:
            return "LINKED_BEFORE_CLOSING_SNAPSHOT"
        return None

    @staticmethod
    def _is_utc(value: object) -> bool:
        return (
            isinstance(value, datetime)
            and value.tzinfo is not None
            and value.utcoffset() == timedelta(0)
        )

    @staticmethod
    def _failed(
        execution_id: str,
        closing_snapshot_id: str,
        code: str,
        state: object | None = None,
        event_id: str | None = None,
    ) -> ClosingQuoteLinkRegistrationResult:
        return ClosingQuoteLinkRegistrationResult(
            execution_id=execution_id,
            closing_snapshot_id=closing_snapshot_id,
            event_id=event_id,
            appended=False,
            projected_game=state,
            readiness_failure_codes=(code,),
        )
