"""Deterministic same-book spread CLV for one immutable wager execution."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation, localcontext

from pydantic import ValidationError

from pregame.closing_quote_link import closing_quote_link_event_id
from pregame.contracts import (
    OPERATOR_DESIGNATED_SAME_BOOK_SPREAD_CLV_V1,
    ClosingQuoteLink,
    ManifestBackedOperatorDecisionRecord,
    PregameEvent,
    WagerExecution,
    WagerExecutionClv,
)
from pregame.events import MarketType, PregameEventType, SnapshotKind
from pregame.market_history import MarketSnapshotHistoryError, MarketSnapshotHistoryService
from pregame.projector import ProjectionError, project_game
from pregame.store import AppendStatus, PregameEventStore
from pregame.wager_execution import wager_execution_event_id

DECIMAL_PRECISION = 28
ROUNDING_SCALE = Decimal("0.000001")
ROUNDING_MODE = "ROUND_HALF_UP"


def wager_execution_clv_event_id(execution_id: str) -> str:
    """Return the deterministic CLV event ID for one execution."""

    if not isinstance(execution_id, str) or not execution_id.strip():
        raise ValueError("execution_id must be a non-empty string")
    return f"wager-execution-clv:{execution_id}"


@dataclass(frozen=True)
class WagerExecutionClvCalculationResult:
    """Explicit result of calculating one immutable execution CLV record."""

    execution_id: str
    event_id: str | None
    appended: bool
    projected_game: object | None
    readiness_failure_codes: tuple[str, ...] = ()


class WagerExecutionClvService:
    """Calculate CLV only from the explicit same-book closing link authority."""

    def __init__(self, *, store: PregameEventStore) -> None:
        self._store = store

    def record(
        self, *, execution_id: str, calculated_at_utc: datetime
    ) -> WagerExecutionClvCalculationResult:
        try:
            event_id = wager_execution_clv_event_id(execution_id)
            link_event_id = closing_quote_link_event_id(execution_id)
        except ValueError:
            return self._failed(execution_id, None, "EXECUTION_ID_INVALID")
        if not _is_literal_utc(calculated_at_utc):
            return self._failed(execution_id, event_id, "CLV_TIMESTAMP_INVALID")

        execution = self._execution(execution_id)
        if execution is None:
            return self._failed(execution_id, event_id, "EXECUTION_NOT_FOUND")
        try:
            state = project_game(self._store, execution.game_id)
        except ProjectionError:
            return self._failed(execution_id, event_id, "PROJECTOR_STATE_INVALID")
        if state is None or not any(
            item.execution_id == execution_id for item in state.wager_execution_history
        ):
            return self._failed(execution_id, event_id, "EXECUTION_PROJECTOR_STATE_MISSING", state)

        link_event = self._store.get_event(link_event_id)
        if link_event is None:
            return self._failed(execution_id, event_id, "CLOSING_LINK_MISSING", state)
        if link_event.event_type != PregameEventType.CLOSING_QUOTE_LINKED:
            return self._failed(execution_id, event_id, "CLOSING_LINK_INVALID", state)
        try:
            link = ClosingQuoteLink.model_validate(link_event.payload)
        except ValidationError:
            return self._failed(execution_id, event_id, "CLOSING_LINK_PAYLOAD_INVALID", state)
        if link.execution_id != execution_id or link_event.game_id != execution.game_id:
            return self._failed(execution_id, event_id, "CLOSING_LINK_IDENTITY_MISMATCH", state)
        if (
            link_event.created_at_utc != link.linked_at_utc
            or link_event.effective_at_utc != link.linked_at_utc
            or calculated_at_utc < link.linked_at_utc
        ):
            return self._failed(execution_id, event_id, "CLOSING_LINK_TIMESTAMPS_INVALID", state)

        try:
            closing = MarketSnapshotHistoryService(self._store).get_snapshot(
                link.closing_snapshot_id
            )
        except MarketSnapshotHistoryError:
            return self._failed(execution_id, event_id, "CLOSING_SNAPSHOT_INVALID", state)
        if closing is None:
            return self._failed(execution_id, event_id, "CLOSING_SNAPSHOT_NOT_FOUND", state)
        decision = self._decision(execution)
        if decision is None:
            return self._failed(execution_id, event_id, "EXECUTION_DECISION_LINEAGE_MISSING", state)
        failure = _validate_authorities(execution, link, closing, decision)
        if failure is not None:
            return self._failed(execution_id, event_id, failure, state)
        try:
            clv = _build_clv(
                event_id=event_id,
                closing_link_event_id=link_event_id,
                execution=execution,
                closing=closing,
                decision=decision,
                calculated_at_utc=calculated_at_utc,
            )
        except (InvalidOperation, ValueError, ValidationError):
            return self._failed(execution_id, event_id, "CLV_FINANCIAL_TERMS_INVALID", state)
        append = self._store.append(
            PregameEvent(
                event_id=event_id,
                game_id=execution.game_id,
                event_type=PregameEventType.WAGER_EXECUTION_CLV_CALCULATED,
                created_at_utc=calculated_at_utc,
                effective_at_utc=calculated_at_utc,
                source="wager_execution_clv",
                idempotency_key=event_id,
                payload=clv.to_json_dict(),
            )
        )
        if append.status == AppendStatus.CONFLICT:
            return self._failed(execution_id, event_id, "CLV_EVENT_CONFLICT", state)
        return WagerExecutionClvCalculationResult(
            execution_id=execution_id,
            event_id=event_id,
            appended=append.status == AppendStatus.APPENDED,
            projected_game=project_game(self._store, execution.game_id),
        )

    def _execution(self, execution_id: str) -> WagerExecution | None:
        event = self._store.get_event(wager_execution_event_id(execution_id))
        if event is None or event.event_type != PregameEventType.WAGER_EXECUTION_RECORDED:
            return None
        try:
            execution = WagerExecution.model_validate(event.payload)
        except ValidationError:
            return None
        return execution if execution.execution_id == execution_id else None

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
        execution_id: object,
        event_id: str | None,
        code: str,
        state: object | None = None,
    ) -> WagerExecutionClvCalculationResult:
        return WagerExecutionClvCalculationResult(
            execution_id=execution_id if isinstance(execution_id, str) else "",
            event_id=event_id,
            appended=False,
            projected_game=state,
            readiness_failure_codes=(code,),
        )


def _validate_authorities(execution, link, closing, decision) -> str | None:
    if execution.market_type != MarketType.SPREAD:
        return "EXECUTION_MARKET_UNSUPPORTED"
    if (
        link.game_id != execution.game_id
        or link.candidate_id != execution.candidate_id
        or link.decision_id != execution.decision_id
        or link.gate_evaluation_id != execution.gate_evaluation_id
    ):
        return "CLOSING_LINK_LINEAGE_MISMATCH"
    if (
        decision.game_id != execution.game_id
        or decision.candidate_id != execution.candidate_id
        or decision.gate_evaluation_id != execution.gate_evaluation_id
    ):
        return "EXECUTION_DECISION_LINEAGE_MISMATCH"
    if (
        closing.snapshot_kind != SnapshotKind.CLOSING
        or closing.game_id != execution.game_id
        or closing.market_type != MarketType.SPREAD
        or closing.selected_side != execution.selected_side
        or closing.book != execution.book
    ):
        return "CLOSING_SNAPSHOT_NOT_SAME_BOOK_SPREAD"
    try:
        _decimal(execution.spread)
        _decimal(closing.spread)
    except (InvalidOperation, ValueError):
        return "CLV_SPREAD_INVALID"
    if not (_valid_american_price(execution.price) and _valid_american_price(closing.spread_price)):
        return "CLV_PRICE_INVALID"
    return None


def _build_clv(
    *, event_id, closing_link_event_id, execution, closing, decision, calculated_at_utc
) -> WagerExecutionClv:
    execution_spread = _decimal(execution.spread)
    closing_spread = _decimal(closing.spread)
    execution_price = Decimal(execution.price)
    closing_price = Decimal(closing.spread_price)
    with localcontext() as context:
        context.prec = DECIMAL_PRECISION
        line_clv = execution_spread - closing_spread
        execution_implied = _implied_probability(execution_price)
        closing_implied = _implied_probability(closing_price)
        if execution_spread == closing_spread:
            price_clv = closing_implied - execution_implied
            price_status = "COMPARABLE"
            classification = _price_classification(price_clv)
        else:
            price_clv = None
            price_status = "NOT_COMPARABLE_LINE_CHANGED"
            classification = "BEAT_CLOSE" if line_clv > 0 else "LOST_TO_CLOSE"
    return WagerExecutionClv(
        clv_event_id=event_id,
        execution_id=execution.execution_id,
        game_id=execution.game_id,
        closing_link_event_id=closing_link_event_id,
        closing_snapshot_id=closing.snapshot_id,
        candidate_id=execution.candidate_id,
        decision_id=execution.decision_id,
        gate_evaluation_id=execution.gate_evaluation_id,
        audit_build_id=decision.audit_build_id,
        audit_evidence_id=decision.audit_evidence_id,
        manifest_id=decision.manifest_id,
        model_generation_snapshot_id=decision.model_generation_snapshot_id,
        methodology_version=OPERATOR_DESIGNATED_SAME_BOOK_SPREAD_CLV_V1,
        selected_side=execution.selected_side,
        execution_spread=_canonical_decimal(execution_spread),
        closing_spread=_canonical_decimal(closing_spread),
        line_clv_points=_canonical_decimal(line_clv),
        execution_price=execution.price,
        closing_price=closing.spread_price,
        execution_implied_probability=_canonical_decimal(execution_implied),
        closing_implied_probability=_canonical_decimal(closing_implied),
        price_clv_probability=None if price_clv is None else _canonical_decimal(price_clv),
        price_clv_status=price_status,
        close_classification=classification,
        decimal_precision=DECIMAL_PRECISION,
        rounding_scale=_canonical_decimal(ROUNDING_SCALE),
        rounding_mode=ROUNDING_MODE,
        calculated_at_utc=calculated_at_utc,
    )


def _implied_probability(price: Decimal) -> Decimal:
    return (
        abs(price) / (abs(price) + Decimal("100"))
        if price < 0
        else Decimal("100") / (price + Decimal("100"))
    )


def _price_classification(value: Decimal) -> str:
    if value > 0:
        return "BEAT_CLOSE_ON_PRICE"
    if value < 0:
        return "LOST_TO_CLOSE_ON_PRICE"
    return "MATCHED_CLOSE"


def _valid_american_price(value: object) -> bool:
    return (
        isinstance(value, int) and not isinstance(value, bool) and (value <= -100 or value >= 100)
    )


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
