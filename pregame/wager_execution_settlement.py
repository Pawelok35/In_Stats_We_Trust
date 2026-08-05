"""Deterministic V1 settlement for immutable spread WagerExecution records."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation, localcontext

from pydantic import ValidationError

from pregame.contracts import (
    FINANCIAL_TERMS_VERSION_AMERICAN_ODDS_RISK_BASED_V1,
    AuthoritativeGameResult,
    ManifestBackedOperatorDecisionRecord,
    PregameEvent,
    WagerExecution,
    WagerExecutionSettlement,
)
from pregame.events import MarketType, PregameEventType
from pregame.projector import ProjectionError, project_game
from pregame.store import AppendStatus, PregameEventStore
from pregame.wager_execution import wager_execution_event_id

PAYOUT_METHODOLOGY = FINANCIAL_TERMS_VERSION_AMERICAN_ODDS_RISK_BASED_V1
DECIMAL_PRECISION = 28
ROUNDING_SCALE = Decimal("0.000001")
ROUNDING_MODE = "ROUND_HALF_UP"


def wager_execution_settlement_event_id(execution_id: str) -> str:
    if not isinstance(execution_id, str) or not execution_id.strip():
        raise ValueError("execution_id must be a non-empty string")
    return f"wager-execution-settlement:{execution_id}"


@dataclass(frozen=True)
class WagerExecutionSettlementResult:
    execution_id: str
    event_id: str | None
    appended: bool
    projected_game: object | None
    readiness_failure_codes: tuple[str, ...] = ()


class WagerExecutionSettlementService:
    """Settle one V1 spread execution from immutable authorities only."""

    def __init__(self, *, store: PregameEventStore) -> None:
        self._store = store

    def record(
        self, *, execution_id: str, settled_at_utc: datetime
    ) -> WagerExecutionSettlementResult:
        try:
            event_id = wager_execution_settlement_event_id(execution_id)
        except ValueError:
            return self._failed(execution_id, None, "EXECUTION_ID_INVALID")
        if not _is_literal_utc(settled_at_utc):
            return self._failed(execution_id, event_id, "SETTLEMENT_TIMESTAMP_INVALID")

        execution_event = self._store.get_event(wager_execution_event_id(execution_id))
        if execution_event is None:
            return self._failed(execution_id, event_id, "EXECUTION_NOT_FOUND")
        if execution_event.event_type != PregameEventType.WAGER_EXECUTION_RECORDED:
            return self._failed(execution_id, event_id, "EXECUTION_NOT_STRUCTURED")
        try:
            execution = WagerExecution.model_validate(execution_event.payload)
        except ValidationError:
            return self._failed(execution_id, event_id, "EXECUTION_PAYLOAD_INVALID")
        if execution.execution_id != execution_id:
            return self._failed(execution_id, event_id, "EXECUTION_ID_MISMATCH")
        if execution.financial_terms_version != FINANCIAL_TERMS_VERSION_AMERICAN_ODDS_RISK_BASED_V1:
            return self._failed(execution_id, event_id, "EXECUTION_FINANCIAL_TERMS_UNVERSIONED")

        try:
            state = project_game(self._store, execution.game_id)
        except ProjectionError:
            return self._failed(execution_id, event_id, "PROJECTOR_STATE_INVALID")
        if state is None or not any(
            item.execution_id == execution_id for item in state.wager_execution_history
        ):
            return self._failed(execution_id, event_id, "EXECUTION_PROJECTOR_STATE_MISSING", state)
        if state.authoritative_game_result is None:
            return self._failed(execution_id, event_id, "AUTHORITATIVE_RESULT_MISSING", state)
        result = state.authoritative_game_result
        if settled_at_utc < result.source_finalized_at_utc:
            return self._failed(execution_id, event_id, "SETTLEMENT_BEFORE_RESULT_FINALIZED", state)
        decision = self._decision(execution)
        if decision is None:
            return self._failed(execution_id, event_id, "EXECUTION_DECISION_LINEAGE_MISSING", state)
        failure = _validate_authorities(execution, result, state, decision)
        if failure is not None:
            return self._failed(execution_id, event_id, failure, state)
        try:
            settlement = _build_settlement(event_id, execution, result, decision, settled_at_utc)
        except (InvalidOperation, ValueError, ValidationError):
            return self._failed(execution_id, event_id, "SETTLEMENT_FINANCIAL_TERMS_INVALID", state)
        append = self._store.append(
            PregameEvent(
                event_id=event_id,
                game_id=execution.game_id,
                event_type=PregameEventType.WAGER_EXECUTION_SETTLED,
                created_at_utc=settled_at_utc,
                effective_at_utc=settled_at_utc,
                source="wager_execution_settlement",
                idempotency_key=event_id,
                payload=settlement.to_json_dict(),
            )
        )
        if append.status == AppendStatus.CONFLICT:
            return self._failed(execution_id, event_id, "SETTLEMENT_EVENT_CONFLICT", state)
        return WagerExecutionSettlementResult(
            execution_id=execution_id,
            event_id=event_id,
            appended=append.status == AppendStatus.APPENDED,
            projected_game=project_game(self._store, execution.game_id),
        )

    def _decision(self, execution: WagerExecution) -> ManifestBackedOperatorDecisionRecord | None:
        event = self._store.get_event(f"operator-decision:{execution.decision_id}")
        if event is None or event.event_type != PregameEventType.OPERATOR_DECISION_RECORDED:
            return None
        try:
            decision = ManifestBackedOperatorDecisionRecord.model_validate(event.payload)
        except ValidationError:
            return None
        return decision if decision.decision_id == execution.decision_id else None

    @staticmethod
    def _failed(
        execution_id: object, event_id: str | None, code: str, state: object | None = None
    ) -> WagerExecutionSettlementResult:
        return WagerExecutionSettlementResult(
            execution_id=execution_id if isinstance(execution_id, str) else "",
            event_id=event_id,
            appended=False,
            projected_game=state,
            readiness_failure_codes=(code,),
        )


def _build_settlement(
    event_id: str,
    execution: WagerExecution,
    result: AuthoritativeGameResult,
    decision: ManifestBackedOperatorDecisionRecord,
    settled_at_utc: datetime,
) -> WagerExecutionSettlement:
    selected_score, opponent_score = _scores_for_execution(execution, result)
    risk = _decimal(execution.stake_units)
    spread = _decimal(execution.spread)
    price = Decimal(execution.price)
    with localcontext() as context:
        context.prec = DECIMAL_PRECISION
        adjusted_margin = Decimal(selected_score) - Decimal(opponent_score) + spread
        if adjusted_margin > 0:
            outcome = "WIN"
            unrounded_profit = (
                risk * Decimal("100") / abs(price) if price < 0 else risk * price / Decimal("100")
            )
        elif adjusted_margin < 0:
            outcome = "LOSS"
            unrounded_profit = -risk
        else:
            outcome = "PUSH"
            unrounded_profit = Decimal("0")
        net_profit = unrounded_profit.quantize(ROUNDING_SCALE, rounding=ROUND_HALF_UP)
    return WagerExecutionSettlement(
        settlement_event_id=event_id,
        execution_id=execution.execution_id,
        game_id=execution.game_id,
        authoritative_result_event_id=result.result_event_id,
        candidate_id=execution.candidate_id,
        decision_id=execution.decision_id,
        gate_evaluation_id=execution.gate_evaluation_id,
        audit_build_id=decision.audit_build_id,
        audit_evidence_id=decision.audit_evidence_id,
        manifest_id=decision.manifest_id,
        model_generation_snapshot_id=decision.model_generation_snapshot_id,
        selected_side=execution.selected_side,
        selected_score=selected_score,
        opponent_score=opponent_score,
        execution_spread=_canonical_decimal(spread),
        adjusted_margin=_canonical_decimal(adjusted_margin),
        outcome=outcome,
        execution_price=execution.price,
        risk_units=_canonical_decimal(risk),
        net_profit_units=_canonical_decimal(net_profit),
        financial_terms_version=FINANCIAL_TERMS_VERSION_AMERICAN_ODDS_RISK_BASED_V1,
        payout_methodology=PAYOUT_METHODOLOGY,
        decimal_precision=DECIMAL_PRECISION,
        rounding_scale=_canonical_decimal(ROUNDING_SCALE),
        rounding_mode=ROUNDING_MODE,
        settled_at_utc=settled_at_utc,
    )


def _validate_authorities(
    execution: WagerExecution,
    result: AuthoritativeGameResult,
    state: object,
    decision: ManifestBackedOperatorDecisionRecord,
) -> str | None:
    if execution.market_type != MarketType.SPREAD:
        return "EXECUTION_MARKET_UNSUPPORTED"
    if result.status != "FINAL" or result.game_id != execution.game_id:
        return "AUTHORITATIVE_RESULT_INVALID"
    if execution.selected_side not in {result.home_team, result.away_team}:
        return "EXECUTION_SELECTED_SIDE_NOT_IN_RESULT"
    if state.authoritative_game_result_event_id != result.result_event_id:
        return "AUTHORITATIVE_RESULT_AMBIGUOUS"
    if (
        decision.game_id != execution.game_id
        or decision.candidate_id != execution.candidate_id
        or decision.gate_evaluation_id != execution.gate_evaluation_id
    ):
        return "EXECUTION_DECISION_LINEAGE_MISMATCH"
    try:
        risk = _decimal(execution.stake_units)
        price = execution.price
        _decimal(execution.spread)
    except (InvalidOperation, ValueError):
        return "EXECUTION_FINANCIAL_TERMS_INVALID"
    if risk <= 0:
        return "EXECUTION_STAKE_INVALID"
    if isinstance(price, bool) or not isinstance(price, int) or -99 <= price <= 99:
        return "EXECUTION_PRICE_INVALID"
    return None


def _scores_for_execution(
    execution: WagerExecution, result: AuthoritativeGameResult
) -> tuple[int, int]:
    if execution.selected_side == result.home_team:
        return result.home_score, result.away_score
    if execution.selected_side == result.away_team:
        return result.away_score, result.home_score
    raise ValueError("execution selected_side is not in authoritative result")


def _decimal(value: object) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("value must be numeric and non-bool")
    decimal = Decimal(str(value))
    if not decimal.is_finite():
        raise ValueError("value must be finite")
    return Decimal("0") if decimal == 0 else decimal


def _canonical_decimal(value: Decimal) -> str:
    canonical = value.quantize(ROUNDING_SCALE, rounding=ROUND_HALF_UP)
    if canonical == 0:
        canonical = Decimal("0").quantize(ROUNDING_SCALE)
    return format(canonical, "f")


def _is_literal_utc(value: object) -> bool:
    return (
        isinstance(value, datetime)
        and value.tzinfo is not None
        and value.utcoffset() == timedelta(0)
    )
