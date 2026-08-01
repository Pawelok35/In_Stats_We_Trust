"""Fail-closed adapter from structured Variant B research to quote policy."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta
from typing import Any, Mapping

from pregame.candidate_registry import CandidateRegistryService
from pregame.contracts import (
    CandidateRecord,
    FinalQuotePolicy,
    FinalQuoteRuntimePolicy,
    VariantBFinalQuotePolicyBuildResult,
    VariantBResearchRecord,
)
from pregame.events import (
    CandidateStatus,
    MarketType,
    VariantBPolicyBuildReason,
    VariantBPolicyBuildStatus,
    VariantBResearchStatus,
)
from pregame.variant_b_research import VariantBResearchRegistryService


class VariantBPolicyAdapterError(ValueError):
    """Raised only for broken registry/domain contracts, not normal blocks."""


def build_final_quote_policy(
    *,
    candidate: CandidateRecord,
    research: VariantBResearchRecord,
    runtime_policy: FinalQuoteRuntimePolicy,
    built_at_utc: datetime,
) -> VariantBFinalQuotePolicyBuildResult:
    """Build an explicit policy from machine-readable fields only."""

    _require_utc(built_at_utc, "built_at_utc")
    reasons: set[VariantBPolicyBuildReason] = set()
    warnings: list[str] = []
    _candidate_reasons(candidate, reasons)
    _research_reasons(candidate, research, reasons)
    if research.legacy_audit_recommendation is not None:
        warnings.append(VariantBPolicyBuildReason.LEGACY_RECOMMENDATION_IGNORED.value)

    frontier = research.acceptable_quote_frontier_raw
    no_chase = research.no_chase_raw
    key_check = research.key_number_check_raw
    spread, price, market = _frontier_values(frontier, candidate, reasons)
    no_chase_spread, no_chase_price = _no_chase_values(no_chase, spread, price, reasons)
    keys, reject = _key_number_values(key_check, runtime_policy, reasons)

    policy = None
    if not reasons:
        identity = {
            "candidate_id": candidate.candidate_id,
            "research_id": research.research_id,
            "runtime_policy": runtime_policy.to_json_dict(),
            "frontier": {"spread": spread, "price": price, "market": market.value},
            "no_chase": {"spread": no_chase_spread, "price": no_chase_price},
            "key_numbers": keys,
            "reject_key_number_loss": reject,
        }
        policy = FinalQuotePolicy(
            policy_id=f"variant-b-final-quote-policy:{_digest(identity)}",
            source="variant_b_research+runtime_execution_policy",
            selected_team=candidate.selected_team,
            market_type=MarketType.SPREAD,
            minimum_acceptable_spread=spread,
            minimum_acceptable_price=price,
            max_quote_age_seconds=runtime_policy.max_quote_age_seconds,
            allowed_quality_statuses=runtime_policy.allowed_quality_statuses,
            allowed_executable_statuses=runtime_policy.allowed_executable_statuses,
            allowed_books=runtime_policy.allowed_books,
            key_numbers=keys,
            reject_key_number_loss=reject,
            no_chase_minimum_spread=no_chase_spread,
            no_chase_minimum_price=no_chase_price,
            created_at_utc=built_at_utc,
            notes=(
                f"research_id={research.research_id}; "
                f"runtime_policy_id={runtime_policy.runtime_policy_id}"
            ),
        )
        reasons.add(VariantBPolicyBuildReason.POLICY_BUILT)

    status = _status_for(reasons, research)
    reason_codes = tuple(sorted(reasons, key=lambda item: item.value))
    build_identity = {
        "candidate_id": candidate.candidate_id,
        "research_id": research.research_id,
        "runtime_policy_id": runtime_policy.runtime_policy_id,
        "policy_id": None if policy is None else policy.policy_id,
        "status": status.value,
        "reasons": [reason.value for reason in reason_codes],
    }
    return VariantBFinalQuotePolicyBuildResult(
        build_id=f"variant-b-policy-build:{_digest(build_identity)}",
        candidate_id=candidate.candidate_id,
        research_id=research.research_id,
        runtime_policy_id=runtime_policy.runtime_policy_id,
        built_at_utc=built_at_utc,
        status=status,
        policy=policy,
        reason_codes=reason_codes,
        warnings=tuple(warnings),
        source_frontier_digest=_optional_digest(frontier),
        source_no_chase_digest=_optional_digest(no_chase),
        source_key_number_digest=_optional_digest(key_check),
        research_status=research.research_status,
        research_approved=research.research_approved,
    )


class VariantBFinalQuotePolicyAdapter:
    """Build policy from the latest research record for an explicit candidate."""

    def __init__(
        self,
        candidates: CandidateRegistryService,
        research: VariantBResearchRegistryService,
    ) -> None:
        self._candidates = candidates
        self._research = research

    def build_from_latest_research(
        self,
        *,
        candidate_id: str,
        runtime_policy: FinalQuoteRuntimePolicy,
        built_at_utc: datetime,
    ) -> VariantBFinalQuotePolicyBuildResult:
        _require_utc(built_at_utc, "built_at_utc")
        candidate = self._candidates.get_candidate(candidate_id)
        if candidate is None:
            return _not_found(candidate_id, runtime_policy, built_at_utc)
        research = self._research.get_latest_research(candidate_id)
        if research is None:
            return _missing_research(candidate, runtime_policy, built_at_utc)
        latest = self._candidates.get_latest_candidate(
            candidate.game_id, model_variant=candidate.model_variant
        )
        result = build_final_quote_policy(
            candidate=candidate,
            research=research,
            runtime_policy=runtime_policy,
            built_at_utc=built_at_utc,
        )
        if latest is not None and latest.candidate_id != candidate.candidate_id:
            return _with_reason(result, VariantBPolicyBuildReason.CANDIDATE_NOT_LATEST)
        return result


def _candidate_reasons(candidate: CandidateRecord, reasons: set[VariantBPolicyBuildReason]) -> None:
    if candidate.status == CandidateStatus.BLOCKED:
        reasons.add(VariantBPolicyBuildReason.CANDIDATE_BLOCKED)
    if candidate.status != CandidateStatus.MODEL_CANDIDATE or not candidate.production_eligible:
        reasons.add(VariantBPolicyBuildReason.CANDIDATE_NOT_PRODUCTION_ELIGIBLE)


def _research_reasons(
    candidate: CandidateRecord,
    research: VariantBResearchRecord,
    reasons: set[VariantBPolicyBuildReason],
) -> None:
    if research.candidate_id != candidate.candidate_id:
        reasons.add(VariantBPolicyBuildReason.CANDIDATE_ID_MISMATCH)
    if research.game_id != candidate.game_id:
        reasons.add(VariantBPolicyBuildReason.GAME_ID_MISMATCH)
    if research.selected_team != candidate.selected_team:
        reasons.add(VariantBPolicyBuildReason.SELECTED_TEAM_MISMATCH)
    if research.model_variant != candidate.model_variant:
        reasons.add(VariantBPolicyBuildReason.MODEL_VARIANT_MISMATCH)
    if research.research_status == VariantBResearchStatus.BLOCKED or research.blocking_risk_codes:
        reasons.add(VariantBPolicyBuildReason.RESEARCH_BLOCKED)
    elif research.research_status in {
        VariantBResearchStatus.PENDING,
        VariantBResearchStatus.INCOMPLETE,
    }:
        reasons.add(VariantBPolicyBuildReason.RESEARCH_INCOMPLETE)
    elif (
        research.research_status != VariantBResearchStatus.APPROVED
        or not research.research_approved
    ):
        reasons.add(VariantBPolicyBuildReason.RESEARCH_NOT_APPROVED)
    if (
        not research.sections_complete
        or research.expected_point_count != 19
        or research.present_point_count < 19
    ):
        reasons.add(VariantBPolicyBuildReason.RESEARCH_INCOMPLETE)


def _frontier_values(
    raw: Mapping[str, Any] | None,
    candidate: CandidateRecord,
    reasons: set[VariantBPolicyBuildReason],
) -> tuple[float | None, int | None, MarketType | None]:
    if raw is None:
        reasons.add(VariantBPolicyBuildReason.FRONTIER_MISSING)
        return None, None, None
    expected = {
        "selected_team",
        "market_type",
        "minimum_acceptable_spread",
        "minimum_acceptable_price",
    }
    if not expected.issubset(raw):
        reasons.add(VariantBPolicyBuildReason.FRONTIER_NOT_STRUCTURED)
        return None, None, None
    if raw["selected_team"] != candidate.selected_team:
        reasons.add(VariantBPolicyBuildReason.SELECTED_TEAM_MISMATCH)
    try:
        market = MarketType(raw["market_type"])
    except (TypeError, ValueError):
        reasons.add(VariantBPolicyBuildReason.MARKET_TYPE_MISSING)
        return None, None, None
    if market != MarketType.SPREAD:
        reasons.add(VariantBPolicyBuildReason.MARKET_TYPE_UNSUPPORTED)
    spread = raw["minimum_acceptable_spread"]
    price = raw["minimum_acceptable_price"]
    if isinstance(spread, bool) or not isinstance(spread, (int, float)):
        reasons.add(VariantBPolicyBuildReason.SPREAD_FRONTIER_NOT_NUMERIC)
    if isinstance(price, bool) or not isinstance(price, int) or price == 0:
        reasons.add(VariantBPolicyBuildReason.PRICE_FRONTIER_NOT_NUMERIC)
    return (
        (
            float(spread)
            if isinstance(spread, (int, float)) and not isinstance(spread, bool)
            else None
        ),
        price if isinstance(price, int) and not isinstance(price, bool) and price != 0 else None,
        market,
    )


def _no_chase_values(
    raw: Mapping[str, Any] | None,
    frontier_spread: float | None,
    frontier_price: int | None,
    reasons: set[VariantBPolicyBuildReason],
) -> tuple[float | None, int | None]:
    if raw is None:
        reasons.add(VariantBPolicyBuildReason.NO_CHASE_MISSING)
        return None, None
    if raw.get("represented_by_frontier") is True:
        return frontier_spread, frontier_price
    required = {"minimum_acceptable_spread", "minimum_acceptable_price"}
    if not required.issubset(raw):
        reasons.add(VariantBPolicyBuildReason.NO_CHASE_NOT_STRUCTURED)
        return None, None
    spread, price = raw["minimum_acceptable_spread"], raw["minimum_acceptable_price"]
    if isinstance(spread, bool) or not isinstance(spread, (int, float)):
        reasons.add(VariantBPolicyBuildReason.NO_CHASE_NOT_STRUCTURED)
        return None, None
    if isinstance(price, bool) or not isinstance(price, int) or price == 0:
        reasons.add(VariantBPolicyBuildReason.NO_CHASE_NOT_STRUCTURED)
        return None, None
    if frontier_spread is not None and float(spread) < frontier_spread:
        reasons.add(VariantBPolicyBuildReason.NO_CHASE_CONFLICT)
    if frontier_price is not None and price < frontier_price:
        reasons.add(VariantBPolicyBuildReason.NO_CHASE_CONFLICT)
    return float(spread), price


def _key_number_values(
    raw: Mapping[str, Any] | None,
    runtime: FinalQuoteRuntimePolicy,
    reasons: set[VariantBPolicyBuildReason],
) -> tuple[tuple[float, ...], bool]:
    raw_keys = None if raw is None else raw.get("key_numbers")
    raw_reject = None if raw is None else raw.get("reject_key_number_loss")
    if raw_keys is not None and (
        not isinstance(raw_keys, list)
        or any(not isinstance(x, (int, float)) or isinstance(x, bool) or x <= 0 for x in raw_keys)
    ):
        reasons.add(VariantBPolicyBuildReason.KEY_NUMBER_POLICY_NOT_STRUCTURED)
    if raw_reject is not None and not isinstance(raw_reject, bool):
        reasons.add(VariantBPolicyBuildReason.KEY_NUMBER_POLICY_NOT_STRUCTURED)
    keys = (
        tuple(sorted(set(float(x) for x in raw_keys)))
        if isinstance(raw_keys, list)
        else runtime.key_numbers
    )
    reject = raw_reject if isinstance(raw_reject, bool) else runtime.reject_key_number_loss
    if (
        raw_keys is not None
        and runtime.key_numbers is not None
        and tuple(sorted(set(float(x) for x in raw_keys))) != runtime.key_numbers
    ):
        reasons.add(VariantBPolicyBuildReason.RUNTIME_POLICY_CONFLICT)
    if (
        isinstance(raw_reject, bool)
        and runtime.reject_key_number_loss is not None
        and raw_reject != runtime.reject_key_number_loss
    ):
        reasons.add(VariantBPolicyBuildReason.RUNTIME_POLICY_CONFLICT)
    if keys is None or reject is None:
        reasons.add(VariantBPolicyBuildReason.KEY_NUMBER_POLICY_MISSING)
        return (), False
    return keys, reject


def _status_for(
    reasons: set[VariantBPolicyBuildReason], research: VariantBResearchRecord
) -> VariantBPolicyBuildStatus:
    if reasons == {VariantBPolicyBuildReason.POLICY_BUILT}:
        return VariantBPolicyBuildStatus.BUILT
    if VariantBPolicyBuildReason.RESEARCH_INCOMPLETE in reasons:
        return VariantBPolicyBuildStatus.INCOMPLETE
    if research.research_status == VariantBResearchStatus.PENDING:
        return VariantBPolicyBuildStatus.INCOMPLETE
    return VariantBPolicyBuildStatus.BLOCKED


def _not_found(
    candidate_id: str, runtime: FinalQuoteRuntimePolicy, built_at: datetime
) -> VariantBFinalQuotePolicyBuildResult:
    reason = VariantBPolicyBuildReason.CANDIDATE_NOT_FOUND
    identity = {
        "candidate_id": candidate_id,
        "reason": reason.value,
        "runtime_policy_id": runtime.runtime_policy_id,
    }
    return VariantBFinalQuotePolicyBuildResult(
        build_id=f"variant-b-policy-build:{_digest(identity)}",
        candidate_id=candidate_id,
        research_id=None,
        runtime_policy_id=runtime.runtime_policy_id,
        built_at_utc=built_at,
        status=VariantBPolicyBuildStatus.BLOCKED,
        policy=None,
        reason_codes=(reason,),
    )


def _missing_research(
    candidate: CandidateRecord, runtime: FinalQuoteRuntimePolicy, built_at: datetime
) -> VariantBFinalQuotePolicyBuildResult:
    reason = VariantBPolicyBuildReason.RESEARCH_NOT_FOUND
    identity = {
        "candidate_id": candidate.candidate_id,
        "reason": reason.value,
        "runtime_policy_id": runtime.runtime_policy_id,
    }
    return VariantBFinalQuotePolicyBuildResult(
        build_id=f"variant-b-policy-build:{_digest(identity)}",
        candidate_id=candidate.candidate_id,
        research_id=None,
        runtime_policy_id=runtime.runtime_policy_id,
        built_at_utc=built_at,
        status=VariantBPolicyBuildStatus.BLOCKED,
        policy=None,
        reason_codes=(reason,),
    )


def _with_reason(
    result: VariantBFinalQuotePolicyBuildResult, reason: VariantBPolicyBuildReason
) -> VariantBFinalQuotePolicyBuildResult:
    reasons = tuple(sorted(set(result.reason_codes) | {reason}, key=lambda item: item.value))
    identity = {
        "candidate_id": result.candidate_id,
        "research_id": result.research_id,
        "runtime_policy_id": result.runtime_policy_id,
        "status": VariantBPolicyBuildStatus.BLOCKED.value,
        "reasons": [item.value for item in reasons],
    }
    return result.model_copy(
        update={
            "build_id": f"variant-b-policy-build:{_digest(identity)}",
            "status": VariantBPolicyBuildStatus.BLOCKED,
            "policy": None,
            "reason_codes": reasons,
        }
    )


def _optional_digest(value: Mapping[str, Any] | None) -> str | None:
    return None if value is None else _digest(value)


def _digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest()


def _require_utc(value: datetime, name: str) -> None:
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise VariantBPolicyAdapterError(f"{name} must be timezone-aware UTC")
