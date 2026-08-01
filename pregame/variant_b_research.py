"""Adapter and append-only registry for official Variant B JSON audit outputs."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Mapping

from pydantic import ValidationError

from pregame.candidate_registry import CandidateRegistryService
from pregame.contracts import (
    CandidateRecord,
    PregameEvent,
    VariantBPointResult,
    VariantBResearchRecord,
)
from pregame.events import (
    CandidateStatus,
    PregameEventType,
    VariantBResearchKind,
    VariantBResearchStatus,
)
from pregame.store import AppendResult, AppendStatus, PregameEventStore

_AUDIT_SCHEMA_VERSION = "variant_b_audit_output.v1"
_EXPECTED_POINT_COUNT = 19
_RESEARCH_EVENT_TYPE = PregameEventType.VARIANT_B_RESEARCH_RECORDED


class VariantBResearchError(ValueError):
    """Raised for malformed or domain-inconsistent Variant B research data."""


class VariantBResearchImportResult:
    """Outcome of adapting and recording one audit artifact."""

    def __init__(self, record: VariantBResearchRecord, append_result: AppendResult) -> None:
        self.record = record
        self.append_result = append_result


def variant_b_research_id(
    payload: Mapping[str, Any], *, candidate_id: str, research_kind: VariantBResearchKind
) -> str:
    """Return a deterministic identity independent of source path and ingestion time."""

    audit_digest = _sha256_payload(payload)
    identity = {
        "candidate_id": candidate_id,
        "research_kind": research_kind.value,
        "source_sha256": audit_digest,
        "framework_version": payload.get("framework_version"),
        "audit_schema_version": payload.get("schema_version"),
        "generated_at_utc": _parse_timestamp(
            payload.get("generated_at_utc"), "generated_at_utc"
        ).isoformat(),
    }
    digest = hashlib.sha256(_canonical_json(identity).encode("utf-8")).hexdigest()
    return f"variant-b-research:{digest}"


def variant_b_research_event_id(research_id: str) -> str:
    if not research_id.strip():
        raise ValueError("research_id must not be empty")
    return f"variant-b-research-event:{research_id}"


def adapt_variant_b_output(
    payload: Mapping[str, Any],
    *,
    candidate: CandidateRecord,
    research_kind: VariantBResearchKind,
    recorded_at_utc: datetime,
    source_ref: str,
    source_sha256: str | None = None,
) -> VariantBResearchRecord:
    """Map the official Variant B audit JSON without parsing prose or Markdown."""

    _require_utc(recorded_at_utc, "recorded_at_utc")
    audit = _validate_audit_payload(payload)
    _validate_candidate_link(audit, candidate)
    raw_points = audit["audit_points"]
    points = tuple(_adapt_point(point, audit) for point in raw_points)
    point_ids = [point.point_id for point in points]
    if len(point_ids) != len(set(point_ids)):
        raise VariantBResearchError("audit_points contain duplicate point_number values")
    blocking_codes = tuple(
        sorted({code for point in points if point.blocking for code in point.risk_codes})
    )
    source_pick = audit["source_pick"]
    point_by_id = {point["point_number"]: point for point in raw_points}
    process_values = _point_values(point_by_id.get(18))
    legacy_recommendation = _point_values(point_by_id.get(19))
    expected_points = _EXPECTED_POINT_COUNT
    sections_complete = len(points) == expected_points and set(point_ids) == set(range(1, 20))
    warnings: list[str] = []
    if not sections_complete:
        warnings.append("RESEARCH_SECTIONS_NOT_FULLY_MATERIALIZED")
    if audit.get("research_evidence", {}).get("gpt_full_19_status") == "STRUCTURALLY_COMPLETE":
        warnings.append("GPT_19_POINT_EVIDENCE_IS_MARKDOWN_NOT_IMPORTED")

    probabilities = tuple(source_pick.get(field) for field in ("p_cover", "p_push", "p_loss"))
    frontier = _frontier_fragment(source_pick)
    status, approved, approval_warning = _derive_status(
        candidate=candidate,
        sections_complete=sections_complete,
        blocking_codes=blocking_codes,
        process_values=process_values,
        legacy_recommendation=legacy_recommendation,
        probabilities=probabilities,
        frontier=frontier,
    )
    if approval_warning:
        warnings.append(approval_warning)
    research_id = variant_b_research_id(
        audit, candidate_id=candidate.candidate_id, research_kind=research_kind
    )
    return VariantBResearchRecord(
        research_id=research_id,
        candidate_id=candidate.candidate_id,
        game_id=candidate.game_id,
        model_variant=candidate.model_variant,
        selected_team=candidate.selected_team,
        research_kind=research_kind,
        research_status=status,
        framework_version=audit["framework_version"],
        audit_schema_version=audit["schema_version"],
        source_ref=source_ref,
        source_sha256=_sha256_payload(audit),
        generated_at_utc=_parse_timestamp(audit["generated_at_utc"], "generated_at_utc"),
        recorded_at_utc=recorded_at_utc,
        expected_point_count=expected_points,
        present_point_count=len(points),
        sections_complete=sections_complete,
        point_results=points,
        blocking_risk_codes=blocking_codes,
        warnings=tuple(sorted(set(warnings))),
        p_cover=_optional_float(source_pick.get("p_cover")),
        p_push=_optional_float(source_pick.get("p_push")),
        p_loss=_optional_float(source_pick.get("p_loss")),
        research_approved=approved,
        legacy_audit_recommendation=legacy_recommendation or None,
        acceptable_quote_frontier_raw=frontier,
        no_chase_raw=_raw_point_fragment(point_by_id.get(7)),
        key_number_check_raw=_raw_point_fragment(point_by_id.get(6)),
    )


class VariantBResearchRegistryService:
    """Persist and query raw Variant B research history without operator actions."""

    def __init__(self, store: PregameEventStore, candidates: CandidateRegistryService) -> None:
        self._store = store
        self._candidates = candidates

    def record_research(self, record: VariantBResearchRecord) -> AppendResult:
        """Append one research record idempotently by its content-addressed ID."""

        self._validate_record_link(record)
        event_id = variant_b_research_event_id(record.research_id)
        existing = self._store.get_event(event_id)
        if existing is not None:
            existing_record = self._record_from_event(existing)
            if _semantic_record(existing_record) == _semantic_record(record):
                return AppendResult(
                    AppendStatus.ALREADY_EXISTS, event_id, "Identical research exists."
                )
            return AppendResult(
                AppendStatus.CONFLICT, event_id, "research_id conflicts with content."
            )
        event = PregameEvent(
            event_id=event_id,
            game_id=record.game_id,
            event_type=_RESEARCH_EVENT_TYPE,
            created_at_utc=record.recorded_at_utc,
            effective_at_utc=record.generated_at_utc,
            source="variant_b_audit",
            idempotency_key=event_id,
            payload=record.to_json_dict(),
        )
        return self._store.append(event)

    def import_file(
        self,
        path: Path,
        *,
        candidate_id: str,
        research_kind: VariantBResearchKind,
        recorded_at_utc: datetime,
        source_ref: str | None = None,
    ) -> VariantBResearchImportResult:
        candidate = self._candidates.get_candidate(candidate_id)
        if candidate is None:
            raise VariantBResearchError(f"candidate not found: {candidate_id}")
        try:
            raw = Path(path).read_bytes()
            payload = json.loads(raw.decode("utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise VariantBResearchError(f"unable to read Variant B JSON: {exc}") from exc
        if not isinstance(payload, dict):
            raise VariantBResearchError("Variant B audit must be a JSON object")
        record = adapt_variant_b_output(
            payload,
            candidate=candidate,
            research_kind=research_kind,
            recorded_at_utc=recorded_at_utc,
            source_ref=source_ref or Path(path).name,
            source_sha256=_sha256_payload(payload),
        )
        return VariantBResearchImportResult(record, self.record_research(record))

    def get_research(self, research_id: str) -> VariantBResearchRecord | None:
        event = self._store.get_event(variant_b_research_event_id(research_id))
        return None if event is None else self._record_from_event(event)

    def list_research(
        self,
        game_id: str,
        *,
        candidate_id: str | None = None,
        research_kind: VariantBResearchKind | None = None,
        research_status: VariantBResearchStatus | None = None,
    ) -> list[VariantBResearchRecord]:
        records = []
        for event in self._store.list_events(game_id):
            if event.event_type != _RESEARCH_EVENT_TYPE:
                continue
            record = self._record_from_event(event)
            if candidate_id is not None and record.candidate_id != candidate_id:
                continue
            if research_kind is not None and record.research_kind != research_kind:
                continue
            if research_status is not None and record.research_status != research_status:
                continue
            records.append(record)
        return sorted(
            records,
            key=lambda item: (item.generated_at_utc, item.recorded_at_utc, item.research_id),
        )

    def get_latest_research(self, candidate_id: str) -> VariantBResearchRecord | None:
        candidate = self._candidates.get_candidate(candidate_id)
        if candidate is None:
            raise VariantBResearchError(f"candidate not found: {candidate_id}")
        records = self.list_research(candidate.game_id, candidate_id=candidate_id)
        return records[-1] if records else None

    def get_latest_approved_research(self, candidate_id: str) -> VariantBResearchRecord | None:
        latest = self.get_latest_research(candidate_id)
        if latest is None or not latest.research_approved:
            return None
        return latest

    def _validate_record_link(self, record: VariantBResearchRecord) -> None:
        candidate = self._candidates.get_candidate(record.candidate_id)
        if candidate is None:
            raise VariantBResearchError(f"candidate not found: {record.candidate_id}")
        _validate_record_candidate(record, candidate)
        expected_id = variant_b_research_id_from_record(record)
        if record.research_id != expected_id:
            raise VariantBResearchError("research_id does not match canonical record content")

    def _record_from_event(self, event: PregameEvent) -> VariantBResearchRecord:
        if event.event_type != _RESEARCH_EVENT_TYPE:
            raise VariantBResearchError("event type is not VARIANT_B_RESEARCH_RECORDED")
        try:
            record = VariantBResearchRecord.model_validate(event.payload)
        except ValidationError as exc:
            raise VariantBResearchError(
                f"invalid VariantBResearchRecord: {exc.errors()[0]['msg']}"
            ) from exc
        if record.game_id != event.game_id:
            raise VariantBResearchError("payload game_id does not match event game_id")
        if record.generated_at_utc != event.effective_at_utc:
            raise VariantBResearchError("generated_at_utc does not match event effective_at_utc")
        if event.event_id != variant_b_research_event_id(record.research_id):
            raise VariantBResearchError("event_id does not match research_id")
        self._validate_record_link(record)
        return record.model_copy(deep=True)


def _validate_audit_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    audit = dict(payload)
    required = {
        "schema_version",
        "framework_version",
        "generated_at_utc",
        "event",
        "source_pick",
        "audit_points",
    }
    missing = sorted(required - audit.keys())
    if missing:
        raise VariantBResearchError("missing required audit fields: " + ", ".join(missing))
    if audit["schema_version"] != _AUDIT_SCHEMA_VERSION:
        raise VariantBResearchError(f"unsupported audit schema: {audit['schema_version']}")
    if not isinstance(audit["event"], Mapping) or not isinstance(audit["source_pick"], Mapping):
        raise VariantBResearchError("event and source_pick must be mappings")
    if not isinstance(audit["audit_points"], list):
        raise VariantBResearchError("audit_points must be a list")
    _parse_timestamp(audit["generated_at_utc"], "generated_at_utc")
    return audit


def _validate_candidate_link(audit: Mapping[str, Any], candidate: CandidateRecord) -> None:
    event = audit["event"]
    source_pick = audit["source_pick"]
    expected_game_id = (
        f"{event.get('season')}_w{int(event.get('week', 0)):02d}_"
        f"{event.get('away')}_at_{event.get('home')}"
    )
    if expected_game_id != candidate.game_id:
        raise VariantBResearchError("Variant B event game_id does not match candidate")
    if event.get("selected_team") != candidate.selected_team:
        raise VariantBResearchError("Variant B selected_team does not match candidate")
    model_variant = source_pick.get("model_version")
    if model_variant is not None and model_variant != candidate.model_variant:
        raise VariantBResearchError("Variant B model_version does not match candidate")
    if event.get("season") != candidate.season or event.get("week") != candidate.week:
        raise VariantBResearchError("Variant B season/week does not match candidate")
    if candidate.status != CandidateStatus.MODEL_CANDIDATE or not candidate.production_eligible:
        raise VariantBResearchError("candidate is not production eligible MODEL_CANDIDATE")


def _validate_record_candidate(record: VariantBResearchRecord, candidate: CandidateRecord) -> None:
    if record.game_id != candidate.game_id:
        raise VariantBResearchError("research game_id does not match candidate")
    if record.selected_team != candidate.selected_team:
        raise VariantBResearchError("research selected_team does not match candidate")
    if record.model_variant != candidate.model_variant:
        raise VariantBResearchError("research model_variant does not match candidate")
    if candidate.status != CandidateStatus.MODEL_CANDIDATE or not candidate.production_eligible:
        raise VariantBResearchError("research candidate is not production eligible MODEL_CANDIDATE")


def _adapt_point(point: Any, audit: Mapping[str, Any]) -> VariantBPointResult:
    if not isinstance(point, Mapping):
        raise VariantBResearchError("audit point must be a mapping")
    required = {"point_number", "point_name", "status", "triggered_rules"}
    missing = sorted(required - point.keys())
    if missing:
        raise VariantBResearchError("audit point missing: " + ", ".join(missing))
    rules = point["triggered_rules"]
    if not isinstance(rules, list):
        raise VariantBResearchError("triggered_rules must be a list")
    blocking = []
    warnings = []
    for rule in rules:
        if not isinstance(rule, Mapping) or not isinstance(rule.get("rule_id"), str):
            raise VariantBResearchError("triggered rule lacks rule_id")
        (blocking if bool(rule.get("blocking")) else warnings).append(rule["rule_id"])
    evidence = bool(point.get("confirmed_facts"))
    refs = []
    research_evidence = audit.get("research_evidence")
    if isinstance(research_evidence, Mapping) and research_evidence.get(
        "gpt_full_19_snapshot_path"
    ):
        refs.append(str(research_evidence["gpt_full_19_snapshot_path"]))
    return VariantBPointResult(
        point_id=point["point_number"],
        point_name=point["point_name"],
        status=point["status"],
        blocking=bool(blocking),
        risk_codes=tuple(sorted(blocking)),
        warning_codes=tuple(sorted(warnings)),
        evidence_present=evidence,
        evidence_source_refs=tuple(refs),
        summary=point.get("narrative"),
    )


def _derive_status(
    *,
    candidate: CandidateRecord,
    sections_complete: bool,
    blocking_codes: tuple[str, ...],
    process_values: dict[str, Any],
    legacy_recommendation: dict[str, Any],
    probabilities: tuple[Any, ...],
    frontier: dict[str, Any] | None,
) -> tuple[VariantBResearchStatus, bool, str | None]:
    if blocking_codes:
        return VariantBResearchStatus.BLOCKED, False, None
    if not sections_complete or any(value is None for value in probabilities) or frontier is None:
        return (
            VariantBResearchStatus.INCOMPLETE,
            False,
            "RESEARCH_APPROVAL_NOT_STRUCTURALLY_DETERMINABLE",
        )
    gate_state = legacy_recommendation.get("gate_state")
    action = legacy_recommendation.get("operator_action")
    readiness = process_values.get("readiness", {})
    if gate_state in {"HOLD", "INVALID"} or action in {"PASS", "WAIT", "REJECT", "BLOCK"}:
        return VariantBResearchStatus.BLOCKED, False, None
    if readiness.get("final_prekick_readiness") != "PREKICK_READY":
        return (
            VariantBResearchStatus.COMPLETE,
            False,
            "RESEARCH_APPROVAL_NOT_STRUCTURALLY_DETERMINABLE",
        )
    return VariantBResearchStatus.APPROVED, True, None


def _point_values(point: Any) -> dict[str, Any]:
    if not isinstance(point, Mapping):
        return {}
    calculations = point.get("calculations")
    if not isinstance(calculations, Mapping) or not isinstance(calculations.get("values"), Mapping):
        return {}
    return dict(calculations["values"])


def _raw_point_fragment(point: Any) -> dict[str, Any] | None:
    values = _point_values(point)
    return values or None


def _frontier_fragment(source_pick: Mapping[str, Any]) -> dict[str, Any] | None:
    keys = ("acceptable_quote_frontier_id", "acceptable_quote_frontier_path")
    fragment = {key: source_pick[key] for key in keys if source_pick.get(key) not in (None, "")}
    return fragment or None


def _parse_timestamp(value: Any, field: str) -> datetime:
    if not isinstance(value, str):
        raise VariantBResearchError(f"{field} must be an ISO UTC string")
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise VariantBResearchError(f"{field} is invalid") from exc
    _require_utc(result, field)
    return result


def _optional_float(value: Any) -> float | None:
    return None if value is None else float(value)


def _sha256_payload(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def variant_b_research_id_from_record(record: VariantBResearchRecord) -> str:
    """Validate identity from the compact persisted record's stable metadata."""

    payload = {
        "candidate_id": record.candidate_id,
        "research_kind": record.research_kind.value,
        "source_sha256": record.source_sha256,
        "framework_version": record.framework_version,
        "audit_schema_version": record.audit_schema_version,
        "generated_at_utc": record.generated_at_utc.isoformat(),
    }
    digest = hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()
    return f"variant-b-research:{digest}"


def _semantic_record(record: VariantBResearchRecord) -> dict[str, Any]:
    payload = record.to_json_dict()
    payload.pop("recorded_at_utc")
    payload.pop("source_ref")
    return payload


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False
    )


def _require_utc(value: datetime, field: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise VariantBResearchError(f"{field} must be timezone-aware")
    if value.utcoffset() != timedelta(0):
        raise VariantBResearchError(f"{field} must be UTC")
