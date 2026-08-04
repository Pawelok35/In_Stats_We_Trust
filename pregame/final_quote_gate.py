"""Deterministic technical gate for an explicit candidate and final quote."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta

from pregame.candidate_registry import CandidateRegistryService
from pregame.contracts import (
    CandidateRecord,
    FinalQuoteGateResearchLineage,
    FinalQuoteGateResult,
    FinalQuotePolicy,
    MarketSnapshot,
    PregameEvent,
)
from pregame.events import (
    CandidateStatus,
    FinalQuoteGateReason,
    FinalQuoteGateStatus,
    MarketType,
    PregameEventType,
    SnapshotKind,
)
from pregame.market_history import MarketSnapshotHistoryService
from pregame.store import AppendResult, AppendStatus, PregameEventStore


class FinalQuoteGateError(ValueError):
    """Raised when trusted event history is structurally inconsistent."""


_REASON_PRIORITY = (
    FinalQuoteGateReason.GAME_ID_MISMATCH,
    FinalQuoteGateReason.POLICY_SELECTED_TEAM_MISMATCH,
    FinalQuoteGateReason.POLICY_MARKET_MISMATCH,
    FinalQuoteGateReason.POLICY_INCOMPLETE,
    FinalQuoteGateReason.CANDIDATE_BLOCKED,
    FinalQuoteGateReason.CANDIDATE_NOT_PRODUCTION_ELIGIBLE,
    FinalQuoteGateReason.CANDIDATE_NOT_LATEST,
    FinalQuoteGateReason.SNAPSHOT_NOT_FINAL,
    FinalQuoteGateReason.WRONG_MARKET_TYPE,
    FinalQuoteGateReason.SELECTED_SIDE_MISSING,
    FinalQuoteGateReason.SELECTED_SIDE_MISMATCH,
    FinalQuoteGateReason.SPREAD_MISSING,
    FinalQuoteGateReason.PRICE_MISSING,
    FinalQuoteGateReason.QUOTE_TIMESTAMP_IN_FUTURE,
    FinalQuoteGateReason.FINAL_QUOTE_STALE,
    FinalQuoteGateReason.MARKET_QUALITY_REJECTED,
    FinalQuoteGateReason.EXECUTABLE_STATUS_REJECTED,
    FinalQuoteGateReason.BOOK_REJECTED,
    FinalQuoteGateReason.FINAL_SNAPSHOT_NOT_LATEST_FOR_BOOK,
    FinalQuoteGateReason.NO_CHASE_BLOCK,
    FinalQuoteGateReason.FINAL_QUOTE_OUTSIDE_FRONTIER,
    FinalQuoteGateReason.FINAL_PRICE_REJECTED,
    FinalQuoteGateReason.KEY_NUMBER_LOST,
)


def final_quote_evaluation_id(
    candidate_id: str,
    final_snapshot_id: str,
    policy: FinalQuotePolicy,
    evaluated_at_utc: datetime,
    research_lineage: FinalQuoteGateResearchLineage | None = None,
) -> str:
    """Return a content-addressed ID for one deterministic evaluation."""

    _require_utc(evaluated_at_utc, "evaluated_at_utc")
    payload = {
        "candidate_id": candidate_id,
        "final_snapshot_id": final_snapshot_id,
        "policy": policy.to_json_dict(),
        "evaluated_at_utc": evaluated_at_utc.isoformat(),
    }
    if research_lineage is not None:
        payload["research_lineage"] = research_lineage.to_json_dict()
    digest = hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()
    return f"final-quote-gate:{digest}"


def final_quote_gate_event_id(evaluation_id: str) -> str:
    if not evaluation_id.strip():
        raise ValueError("evaluation_id must not be empty")
    return f"final-quote-gate-event:{evaluation_id}"


def evaluate_final_quote(
    candidate: CandidateRecord,
    snapshot: MarketSnapshot,
    policy: FinalQuotePolicy,
    *,
    evaluated_at_utc: datetime,
    latest_candidate_id: str | None = None,
    latest_final_snapshot_id_for_book: str | None = None,
    research_lineage: FinalQuoteGateResearchLineage | None = None,
) -> FinalQuoteGateResult:
    """Evaluate supplied records only; no quote selection or mutation occurs."""

    _require_utc(evaluated_at_utc, "evaluated_at_utc")
    _ensure_candidate_preflight_consistency(candidate)
    reasons: set[FinalQuoteGateReason] = set()
    warnings: list[str] = []

    if candidate.game_id != snapshot.game_id:
        reasons.add(FinalQuoteGateReason.GAME_ID_MISMATCH)
    if policy.selected_team != candidate.selected_team:
        reasons.add(FinalQuoteGateReason.POLICY_SELECTED_TEAM_MISMATCH)
    if policy.market_type != MarketType.SPREAD:
        reasons.add(FinalQuoteGateReason.POLICY_MARKET_MISMATCH)
    if policy.minimum_acceptable_spread is None or policy.minimum_acceptable_price is None:
        reasons.add(FinalQuoteGateReason.POLICY_INCOMPLETE)
    if candidate.status == CandidateStatus.BLOCKED:
        reasons.add(FinalQuoteGateReason.CANDIDATE_BLOCKED)
    if candidate.status != CandidateStatus.MODEL_CANDIDATE or not candidate.production_eligible:
        reasons.add(FinalQuoteGateReason.CANDIDATE_NOT_PRODUCTION_ELIGIBLE)
    if latest_candidate_id is not None and latest_candidate_id != candidate.candidate_id:
        reasons.add(FinalQuoteGateReason.CANDIDATE_NOT_LATEST)

    if snapshot.snapshot_kind != SnapshotKind.FINAL:
        reasons.add(FinalQuoteGateReason.SNAPSHOT_NOT_FINAL)
    if snapshot.market_type != policy.market_type:
        reasons.add(FinalQuoteGateReason.WRONG_MARKET_TYPE)
    if snapshot.selected_side is None:
        reasons.add(FinalQuoteGateReason.SELECTED_SIDE_MISSING)
    elif snapshot.selected_side != candidate.selected_team:
        reasons.add(FinalQuoteGateReason.SELECTED_SIDE_MISMATCH)
    if snapshot.spread is None:
        reasons.add(FinalQuoteGateReason.SPREAD_MISSING)
    if snapshot.spread_price is None or snapshot.spread_price == 0:
        reasons.add(FinalQuoteGateReason.PRICE_MISSING)
    if snapshot.captured_at_utc > evaluated_at_utc:
        reasons.add(FinalQuoteGateReason.QUOTE_TIMESTAMP_IN_FUTURE)
        quote_age_seconds: int | None = None
    else:
        quote_age = (evaluated_at_utc - snapshot.captured_at_utc).total_seconds()
        quote_age_seconds = int(quote_age)
        if quote_age > policy.max_quote_age_seconds:
            reasons.add(FinalQuoteGateReason.FINAL_QUOTE_STALE)
    if snapshot.quality_status not in policy.allowed_quality_statuses:
        reasons.add(FinalQuoteGateReason.MARKET_QUALITY_REJECTED)
    if snapshot.executable_status not in policy.allowed_executable_statuses:
        reasons.add(FinalQuoteGateReason.EXECUTABLE_STATUS_REJECTED)
    if policy.allowed_books is not None and snapshot.book not in policy.allowed_books:
        reasons.add(FinalQuoteGateReason.BOOK_REJECTED)
    if (
        latest_final_snapshot_id_for_book is not None
        and latest_final_snapshot_id_for_book != snapshot.snapshot_id
    ):
        reasons.add(FinalQuoteGateReason.FINAL_SNAPSHOT_NOT_LATEST_FOR_BOOK)

    if snapshot.spread is not None and policy.minimum_acceptable_spread is not None:
        if snapshot.spread < policy.minimum_acceptable_spread:
            reasons.add(FinalQuoteGateReason.FINAL_QUOTE_OUTSIDE_FRONTIER)
    if snapshot.spread_price is not None and policy.minimum_acceptable_price is not None:
        if snapshot.spread_price == 0 or snapshot.spread_price < policy.minimum_acceptable_price:
            reasons.add(FinalQuoteGateReason.FINAL_PRICE_REJECTED)
    if snapshot.spread is not None and policy.no_chase_minimum_spread is not None:
        if snapshot.spread < policy.no_chase_minimum_spread:
            reasons.add(FinalQuoteGateReason.NO_CHASE_BLOCK)
    if snapshot.spread_price is not None and policy.no_chase_minimum_price is not None:
        if snapshot.spread_price == 0 or snapshot.spread_price < policy.no_chase_minimum_price:
            reasons.add(FinalQuoteGateReason.NO_CHASE_BLOCK)

    lost_keys = _lost_key_numbers(candidate.spread_at_scan, snapshot.spread, policy.key_numbers)
    if lost_keys:
        if policy.reject_key_number_loss:
            reasons.add(FinalQuoteGateReason.KEY_NUMBER_LOST)
        else:
            warnings.append(
                "key_number_loss_allowed_by_policy:"
                + ",".join(_format_key(key) for key in lost_keys)
            )

    ordered_reasons = tuple(reason for reason in _REASON_PRIORITY if reason in reasons)
    passed = not ordered_reasons
    evaluation_id = final_quote_evaluation_id(
        candidate.candidate_id,
        snapshot.snapshot_id,
        policy,
        evaluated_at_utc,
        research_lineage,
    )
    policy_snapshot = policy.to_json_dict()
    return FinalQuoteGateResult(
        evaluation_id=evaluation_id,
        game_id=candidate.game_id,
        candidate_id=candidate.candidate_id,
        final_snapshot_id=snapshot.snapshot_id,
        policy_id=policy.policy_id,
        evaluated_at_utc=evaluated_at_utc,
        passed=passed,
        primary_status=(
            FinalQuoteGateStatus.FINAL_QUOTE_VALID
            if passed
            else FinalQuoteGateStatus.FINAL_QUOTE_BLOCKED
        ),
        primary_reason=ordered_reasons[0] if ordered_reasons else None,
        reason_codes=ordered_reasons,
        warnings=tuple(warnings),
        selected_team=candidate.selected_team,
        model_variant=candidate.model_variant,
        candidate_spread=candidate.spread_at_scan,
        final_spread=snapshot.spread,
        candidate_price=candidate.price_at_scan,
        final_price=snapshot.spread_price,
        quote_age_seconds=quote_age_seconds,
        book=snapshot.book,
        quality_status=snapshot.quality_status,
        executable_status=snapshot.executable_status,
        crossed_or_lost_key_numbers=lost_keys,
        policy_snapshot=policy_snapshot,
        policy_digest=hashlib.sha256(_canonical_json(policy_snapshot).encode("utf-8")).hexdigest(),
        research_lineage=research_lineage,
    )


class FinalQuoteGateService:
    """Evaluate explicit persisted records and append the auditable result."""

    def __init__(
        self,
        candidate_registry: CandidateRegistryService,
        market_history: MarketSnapshotHistoryService,
        store: PregameEventStore,
    ) -> None:
        self._candidate_registry = candidate_registry
        self._market_history = market_history
        self._store = store

    def evaluate(
        self,
        *,
        candidate_id: str,
        final_snapshot_id: str,
        policy: FinalQuotePolicy,
        evaluated_at_utc: datetime,
        research_lineage: FinalQuoteGateResearchLineage | None = None,
    ) -> FinalQuoteGateResult:
        candidate = self._candidate_registry.get_candidate(candidate_id)
        snapshot = self._market_history.get_snapshot(final_snapshot_id)
        if candidate is None:
            raise FinalQuoteGateError(f"Candidate not found: {candidate_id}")
        if snapshot is None:
            raise FinalQuoteGateError(f"Final snapshot not found: {final_snapshot_id}")
        latest_candidate = self._candidate_registry.get_latest_candidate(
            candidate.game_id, model_variant=candidate.model_variant
        )
        latest_snapshot = self._latest_final_for_book_and_side(snapshot)
        return evaluate_final_quote(
            candidate,
            snapshot,
            policy,
            evaluated_at_utc=evaluated_at_utc,
            latest_candidate_id=latest_candidate.candidate_id if latest_candidate else None,
            latest_final_snapshot_id_for_book=(
                latest_snapshot.snapshot_id if latest_snapshot else None
            ),
            research_lineage=research_lineage,
        )

    def evaluate_and_record(
        self,
        *,
        candidate_id: str,
        final_snapshot_id: str,
        policy: FinalQuotePolicy,
        evaluated_at_utc: datetime,
        recorded_at_utc: datetime,
        research_lineage: FinalQuoteGateResearchLineage | None = None,
    ) -> tuple[FinalQuoteGateResult, AppendResult]:
        _require_utc(recorded_at_utc, "recorded_at_utc")
        result = self.evaluate(
            candidate_id=candidate_id,
            final_snapshot_id=final_snapshot_id,
            policy=policy,
            evaluated_at_utc=evaluated_at_utc,
            research_lineage=research_lineage,
        )
        event_id = final_quote_gate_event_id(result.evaluation_id)
        event = PregameEvent(
            event_id=event_id,
            game_id=result.game_id,
            event_type=PregameEventType.FINAL_QUOTE_GATE_EVALUATED,
            created_at_utc=recorded_at_utc,
            effective_at_utc=result.evaluated_at_utc,
            source="final_quote_gate",
            idempotency_key=event_id,
            payload=result.to_json_dict(),
        )
        append_result = self._store.append(event)
        if append_result.status == AppendStatus.CONFLICT:
            raise FinalQuoteGateError("Final quote gate event conflicts with existing event ID")
        return result, append_result

    def _latest_final_for_book_and_side(self, snapshot: MarketSnapshot) -> MarketSnapshot | None:
        snapshots = self._market_history.list_snapshots(
            snapshot.game_id,
            market_type=snapshot.market_type,
            book=snapshot.book,
            snapshot_kind=SnapshotKind.FINAL,
        )
        matching = [item for item in snapshots if item.selected_side == snapshot.selected_side]
        return matching[-1] if matching else None


def _lost_key_numbers(
    candidate_spread: float | None, final_spread: float | None, key_numbers: tuple[float, ...]
) -> tuple[float, ...]:
    if candidate_spread is None or final_spread is None or final_spread >= candidate_spread:
        return ()
    lost = {
        key
        for key in key_numbers
        for threshold in (key, -key)
        if candidate_spread > threshold >= final_spread
    }
    return tuple(sorted(lost))


def _ensure_candidate_preflight_consistency(candidate: CandidateRecord) -> None:
    preflight = candidate.source_metadata.get("preflight")
    if preflight is None:
        return
    if not isinstance(preflight, dict):
        raise FinalQuoteGateError("candidate preflight metadata must be a mapping")
    preserved_eligibility = preflight.get("production_eligible")
    if isinstance(preserved_eligibility, bool) and (
        preserved_eligibility != candidate.production_eligible
    ):
        raise FinalQuoteGateError(
            "candidate production_eligible conflicts with preserved preflight metadata"
        )


def _format_key(value: float) -> str:
    return str(int(value)) if value.is_integer() else str(value)


def _canonical_json(payload: object) -> str:
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def _require_utc(value: datetime, field_name: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    if value.utcoffset() != timedelta(0):
        raise ValueError(f"{field_name} must be in UTC")
