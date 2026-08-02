"""Pure in-memory integration of a model candidate and Variant B evidence."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping

from pregame.contracts import CandidateRecord
from pregame.events import CandidateStatus
from pregame.variant_b_evidence import VariantBGptEvidenceSidecar
from scripts.variant_b_audit import build_audit_with_structured_evidence


class StructuredVariantBAuditBuildStatus(str, Enum):
    BUILT = "BUILT"
    BLOCKED_PRECONDITION = "BLOCKED_PRECONDITION"
    INVALID = "INVALID"


class StructuredVariantBAuditBuildReason(str, Enum):
    CANDIDATE_BLOCKED = "CANDIDATE_BLOCKED"
    CANDIDATE_NOT_PRODUCTION_ELIGIBLE = "CANDIDATE_NOT_PRODUCTION_ELIGIBLE"
    CANDIDATE_UNSAFE_BYPASS = "CANDIDATE_UNSAFE_BYPASS"
    CANDIDATE_GAME_ID_MISMATCH = "CANDIDATE_GAME_ID_MISMATCH"
    EVIDENCE_NOT_STRUCTURALLY_READY = "EVIDENCE_NOT_STRUCTURALLY_READY"
    EVIDENCE_CANDIDATE_MISMATCH = "EVIDENCE_CANDIDATE_MISMATCH"
    EVIDENCE_GAME_MISMATCH = "EVIDENCE_GAME_MISMATCH"
    EVIDENCE_TEAM_MISMATCH = "EVIDENCE_TEAM_MISMATCH"
    EVIDENCE_MODEL_VARIANT_MISMATCH = "EVIDENCE_MODEL_VARIANT_MISMATCH"
    EVIDENCE_SEASON_WEEK_MISMATCH = "EVIDENCE_SEASON_WEEK_MISMATCH"
    EVIDENCE_MATCHUP_MISMATCH = "EVIDENCE_MATCHUP_MISMATCH"
    EVIDENCE_MARKET_MISMATCH = "EVIDENCE_MARKET_MISMATCH"
    SOURCE_PICK_FIELD_MISSING = "SOURCE_PICK_FIELD_MISSING"
    AUDIT_STAGE_INVALID = "AUDIT_STAGE_INVALID"
    RULES_CONFIG_INVALID = "RULES_CONFIG_INVALID"
    STRUCTURED_AUDIT_BLOCKING_STATUS = "STRUCTURED_AUDIT_BLOCKING_STATUS"
    STRUCTURED_AUDIT_BUILT = "STRUCTURED_AUDIT_BUILT"


class StructuredVariantBAuditIntegrationError(ValueError):
    """Raised only for impossible internal integration-contract failures."""


@dataclass(frozen=True)
class StructuredVariantBAuditBuildResult:
    build_id: str
    build_status: StructuredVariantBAuditBuildStatus
    candidate_id: str
    evidence_id: str
    audit_stage: str
    generated_at_utc: str
    source_pick: dict[str, Any] | None
    source_pick_sha256: str | None
    evidence_sha256: str
    rules_config_sha256: str | None
    audit_output: dict[str, Any] | None
    audit_output_sha256: str | None
    reason_codes: tuple[StructuredVariantBAuditBuildReason, ...]
    warnings: tuple[str, ...]
    schema_version: str = "structured_variant_b_audit_build_result.v1"


def build_structured_variant_b_audit(
    *,
    candidate: CandidateRecord,
    evidence: VariantBGptEvidenceSidecar,
    rules_config: Mapping[str, Any],
    audit_stage: str,
    generated_at_utc: datetime,
) -> StructuredVariantBAuditBuildResult:
    """Build the canonical Variant B audit without persistence or external reads."""

    timestamp = _utc_timestamp(generated_at_utc)
    evidence_json = evidence.to_json_dict()
    evidence_sha = _sha256(evidence_json)
    rules_json = _json_mapping_or_none(rules_config)
    if rules_json is None:
        return _blocked(
            candidate,
            evidence,
            audit_stage,
            timestamp,
            evidence_sha,
            (),
            (StructuredVariantBAuditBuildReason.RULES_CONFIG_INVALID,),
        )
    rules_sha = _sha256(rules_json)
    reasons = _precondition_reasons(candidate, evidence, audit_stage, rules_json)
    if reasons:
        return _blocked(
            candidate, evidence, audit_stage, timestamp, evidence_sha, rules_sha, reasons
        )

    source_pick, missing = build_authoritative_source_pick(candidate=candidate)
    if missing:
        return _blocked(
            candidate,
            evidence,
            audit_stage,
            timestamp,
            evidence_sha,
            rules_sha,
            (StructuredVariantBAuditBuildReason.SOURCE_PICK_FIELD_MISSING,),
            warnings=tuple(f"SOURCE_PICK_FIELD_MISSING:{field}" for field in missing),
        )
    source_sha = _sha256(source_pick)
    try:
        audit = build_audit_with_structured_evidence(
            source_pick,
            rules_json,
            audit_stage,
            evidence_json,
            generated_at_utc=timestamp,
        )
    except ValueError as exc:
        raise StructuredVariantBAuditIntegrationError(
            "structured audit wrapper rejected validated inputs"
        ) from exc
    _validate_audit_output(audit, candidate, evidence, timestamp)
    audit_sha = _sha256(audit)
    if _audit_has_blocking_status(audit):
        return _blocked(
            candidate,
            evidence,
            audit_stage,
            timestamp,
            evidence_sha,
            rules_sha,
            (StructuredVariantBAuditBuildReason.STRUCTURED_AUDIT_BLOCKING_STATUS,),
            source_pick=source_pick,
            source_pick_sha256=source_sha,
            audit_output=audit,
            audit_output_sha256=audit_sha,
        )
    return StructuredVariantBAuditBuildResult(
        build_id=_build_id(
            candidate.candidate_id,
            evidence.evidence_id,
            audit_stage,
            timestamp,
            source_sha,
            rules_sha,
            audit_sha,
        ),
        build_status=StructuredVariantBAuditBuildStatus.BUILT,
        candidate_id=candidate.candidate_id,
        evidence_id=evidence.evidence_id,
        audit_stage=audit_stage,
        generated_at_utc=timestamp,
        source_pick=source_pick,
        source_pick_sha256=source_sha,
        evidence_sha256=evidence_sha,
        rules_config_sha256=rules_sha,
        audit_output=audit,
        audit_output_sha256=audit_sha,
        reason_codes=(StructuredVariantBAuditBuildReason.STRUCTURED_AUDIT_BUILT,),
        warnings=(),
    )


def build_authoritative_source_pick(
    *, candidate: CandidateRecord
) -> tuple[dict[str, Any], tuple[str, ...]]:
    """Construct the wrapper input solely from a candidate and its model provenance."""

    model_pick = candidate.source_metadata.get("model_pick")
    if not isinstance(model_pick, Mapping):
        return {}, ("source_metadata.model_pick",)
    canonical_game_id = (
        f"{candidate.season}_w{candidate.week:02d}_{candidate.away}_at_{candidate.home}"
    )
    required = {
        "market": model_pick.get("market"),
        "book": model_pick.get("model_generation_book"),
        "quote_timestamp_utc": model_pick.get("model_generation_quote_timestamp_utc"),
        "market_scope": model_pick.get("market_scope"),
        "model_generation_quote_id": model_pick.get("model_generation_quote_id"),
    }
    missing = tuple(
        name
        for name, value in required.items()
        if value in (None, "")
        or (name == "model_generation_quote_id" and not isinstance(value, str))
        or (name == "model_generation_quote_id" and isinstance(value, str) and not value.strip())
    )
    if missing:
        return {}, missing
    identity = {
        "season": candidate.season,
        "week": candidate.week,
        "away": candidate.away,
        "home": candidate.home,
        "selected_team": candidate.selected_team,
        "model_version": candidate.model_variant,
    }
    source = {
        **identity,
        "model_winner": candidate.selected_team,
        "tag": candidate.model_tag,
        "confidence": candidate.confidence,
        "edge_vs_line": candidate.edge_vs_line,
        "model_margin": candidate.model_margin,
        "market_margin": candidate.market_margin_at_scan,
        "handicap": candidate.spread_at_scan,
        "price": candidate.price_at_scan,
        "preflight": model_pick.get("preflight"),
        "preflight_status": candidate.preflight_status,
        "market": model_pick["market"],
        "market_scope": model_pick["market_scope"],
        "book": model_pick["model_generation_book"],
        "source_type": model_pick.get("odds_source"),
        "quote_timestamp_utc": model_pick["model_generation_quote_timestamp_utc"],
        "quote_id": model_pick["model_generation_quote_id"],
        "model_generation_quote_id": model_pick["model_generation_quote_id"],
        "executable_status": model_pick.get("executable_status"),
        "neutral_site": model_pick.get("neutral_site", False),
        "model_generation_spread_selected_team": model_pick.get(
            "model_generation_spread_selected_team"
        ),
        "model_generation_price": model_pick.get("model_generation_price"),
        "model_generation_quote_timestamp_utc": model_pick["model_generation_quote_timestamp_utc"],
        "model_generation_book": model_pick["model_generation_book"],
        "candidate_id": candidate.candidate_id,
        "canonical_game_id": canonical_game_id,
    }
    conflicting = tuple(
        field
        for field, expected in identity.items()
        if field in model_pick and model_pick[field] != expected
    )
    if candidate.game_id != canonical_game_id:
        conflicting += ("candidate.game_id",)
    if conflicting:
        return {}, conflicting
    return source, ()


def _precondition_reasons(
    candidate, evidence, audit_stage, rules
) -> tuple[StructuredVariantBAuditBuildReason, ...]:
    reasons: list[StructuredVariantBAuditBuildReason] = []
    if candidate.status != CandidateStatus.MODEL_CANDIDATE:
        reasons.append(StructuredVariantBAuditBuildReason.CANDIDATE_BLOCKED)
    if not candidate.production_eligible:
        reasons.append(StructuredVariantBAuditBuildReason.CANDIDATE_NOT_PRODUCTION_ELIGIBLE)
    if candidate.preflight_status == "BYPASSED_UNSAFE" or "BYPASSED_UNSAFE" in candidate.warnings:
        reasons.append(StructuredVariantBAuditBuildReason.CANDIDATE_UNSAFE_BYPASS)
    canonical_game_id = (
        f"{candidate.season}_w{candidate.week:02d}_{candidate.away}_at_{candidate.home}"
    )
    if candidate.game_id != canonical_game_id:
        reasons.append(StructuredVariantBAuditBuildReason.CANDIDATE_GAME_ID_MISMATCH)
    summary = evidence.completeness_summary()
    if (
        not summary["structurally_ready_for_variant_b_import"]
        or evidence.expected_point_count != 19
        or len(evidence.point_results) != 19
    ):
        reasons.append(StructuredVariantBAuditBuildReason.EVIDENCE_NOT_STRUCTURALLY_READY)
    if any(point.status.value == "BLOCKING_RISK" for point in evidence.point_results):
        reasons.append(StructuredVariantBAuditBuildReason.STRUCTURED_AUDIT_BLOCKING_STATUS)
    if evidence.candidate_id != candidate.candidate_id:
        reasons.append(StructuredVariantBAuditBuildReason.EVIDENCE_CANDIDATE_MISMATCH)
    if evidence.game_id != candidate.game_id:
        reasons.append(StructuredVariantBAuditBuildReason.EVIDENCE_GAME_MISMATCH)
    if evidence.selected_team != candidate.selected_team:
        reasons.append(StructuredVariantBAuditBuildReason.EVIDENCE_TEAM_MISMATCH)
    if evidence.model_variant != candidate.model_variant:
        reasons.append(StructuredVariantBAuditBuildReason.EVIDENCE_MODEL_VARIANT_MISMATCH)
    if evidence.season != candidate.season or evidence.week != candidate.week:
        reasons.append(StructuredVariantBAuditBuildReason.EVIDENCE_SEASON_WEEK_MISMATCH)
    if evidence.away_team != candidate.away or evidence.home_team != candidate.home:
        reasons.append(StructuredVariantBAuditBuildReason.EVIDENCE_MATCHUP_MISMATCH)
    model_pick = candidate.source_metadata.get("model_pick")
    if isinstance(model_pick, Mapping):
        market = model_pick.get("market")
        frontier = evidence.acceptable_quote_frontier
        if market != frontier.market_type.value:
            reasons.append(StructuredVariantBAuditBuildReason.EVIDENCE_MARKET_MISMATCH)
        for item in evidence.market_evidence:
            if (
                item.book != model_pick.get("model_generation_book")
                or item.spread != candidate.spread_at_scan
                or item.price != candidate.price_at_scan
                or item.captured_at_utc.isoformat().replace("+00:00", "Z")
                != model_pick.get("model_generation_quote_timestamp_utc")
            ):
                reasons.append(StructuredVariantBAuditBuildReason.EVIDENCE_MARKET_MISMATCH)
                break
    stages = rules.get("audit_stages")
    if not isinstance(stages, list) or audit_stage not in stages:
        reasons.append(StructuredVariantBAuditBuildReason.AUDIT_STAGE_INVALID)
    return tuple(dict.fromkeys(reasons))


def _blocked(
    candidate,
    evidence,
    stage,
    timestamp,
    evidence_sha,
    rules_sha,
    reasons,
    *,
    warnings=(),
    source_pick=None,
    source_pick_sha256=None,
    audit_output=None,
    audit_output_sha256=None,
):
    return StructuredVariantBAuditBuildResult(
        build_id=_build_id(
            candidate.candidate_id,
            evidence.evidence_id,
            stage,
            timestamp,
            source_pick_sha256,
            rules_sha,
            audit_output_sha256,
        ),
        build_status=StructuredVariantBAuditBuildStatus.BLOCKED_PRECONDITION,
        candidate_id=candidate.candidate_id,
        evidence_id=evidence.evidence_id,
        audit_stage=stage,
        generated_at_utc=timestamp,
        source_pick=source_pick,
        source_pick_sha256=source_pick_sha256,
        evidence_sha256=evidence_sha,
        rules_config_sha256=rules_sha,
        audit_output=audit_output,
        audit_output_sha256=audit_output_sha256,
        reason_codes=tuple(reasons),
        warnings=tuple(warnings),
    )


def _validate_audit_output(audit, candidate, evidence, timestamp):
    if not isinstance(audit, dict) or audit.get("schema_version") != "variant_b_audit_output.v1":
        raise StructuredVariantBAuditIntegrationError("invalid audit schema")
    if (
        audit.get("framework_version") != "variant_b_audit_v1"
        or audit.get("generated_at_utc") != timestamp
    ):
        raise StructuredVariantBAuditIntegrationError("invalid audit metadata")
    event = audit.get("event")
    metadata = audit.get("structured_evidence_metadata")
    if (
        not isinstance(event, dict)
        or event.get("away") != candidate.away
        or event.get("home") != candidate.home
    ):
        raise StructuredVariantBAuditIntegrationError("audit matchup mismatch")
    if not isinstance(metadata, dict) or metadata.get("evidence_id") != evidence.evidence_id:
        raise StructuredVariantBAuditIntegrationError("audit evidence mismatch")
    points = audit.get("audit_points")
    if not isinstance(points, list) or [point.get("point_number") for point in points] != list(
        range(1, 20)
    ):
        raise StructuredVariantBAuditIntegrationError("audit point mapping mismatch")
    _canonical_json(audit)


def _audit_has_blocking_status(audit: Mapping[str, Any]) -> bool:
    return any(bool(point.get("blocking")) for point in audit["audit_points"])


def _utc_timestamp(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() != timezone.utc.utcoffset(value):
        raise StructuredVariantBAuditIntegrationError("generated_at_utc must be UTC")
    return value.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _json_mapping_or_none(value: Mapping[str, Any]) -> dict[str, Any] | None:
    if not isinstance(value, Mapping):
        return None
    copied = dict(value)
    try:
        _canonical_json(copied)
    except (TypeError, ValueError):
        return None
    return copied


def _canonical_json(value: Any) -> str:
    _reject_non_finite(value)
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    )


def _reject_non_finite(value: Any) -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("non-finite JSON number")
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError("JSON object keys must be strings")
            _reject_non_finite(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _reject_non_finite(item)


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _build_id(candidate_id, evidence_id, stage, timestamp, source_sha, rules_sha, audit_sha) -> str:
    payload = {
        "candidate_id": candidate_id,
        "evidence_id": evidence_id,
        "audit_stage": stage,
        "generated_at_utc": timestamp,
        "source_pick_sha256": source_sha,
        "rules_config_sha256": rules_sha,
        "audit_output_sha256": audit_sha,
        "integration_core_version": "v1",
    }
    return "structured-variant-b-audit-build:" + _sha256(payload)
