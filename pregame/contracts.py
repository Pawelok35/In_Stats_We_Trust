"""Pydantic contracts for the NFL 2026 pregame operator layer.

These models intentionally contain no persistence, projection, model-adapter,
or GUI logic. They define the shape and validation rules for later layers.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from pregame.events import (
    CandidateStatus,
    DecisionLevel,
    ExecutableStatus,
    FinalQuoteGateReason,
    FinalQuoteGateStatus,
    MarketQualityStatus,
    MarketType,
    OperatorVerdict,
    PregameEventType,
    SnapshotKind,
    VariantBResearchKind,
    VariantBResearchStatus,
)

DEFAULT_EVENT_SCHEMA_VERSION = "pregame_event.v1"
DEFAULT_MARKET_SNAPSHOT_SCHEMA_VERSION = "market_snapshot.v1"
DEFAULT_CANDIDATE_SCHEMA_VERSION = "candidate_record.v1"
DEFAULT_OPERATOR_DECISION_SCHEMA_VERSION = "operator_decision.v1"
DEFAULT_GAME_RECORD_SCHEMA_VERSION = "pregame_game_record.v1"
DEFAULT_FINAL_QUOTE_POLICY_SCHEMA_VERSION = "final_quote_policy.v1"
DEFAULT_FINAL_QUOTE_GATE_RESULT_SCHEMA_VERSION = "final_quote_gate_result.v1"
DEFAULT_VARIANT_B_POINT_RESULT_SCHEMA_VERSION = "variant_b_point_result.v1"
DEFAULT_VARIANT_B_RESEARCH_RECORD_SCHEMA_VERSION = "variant_b_research_record.v1"


def _require_non_empty(value: str, field_name: str) -> str:
    if not value.strip():
        raise ValueError(f"{field_name} must not be empty")
    return value


def _ensure_utc(value: datetime, field_name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(timezone.utc)


def _json_compatible(value: Any) -> bool:
    if value is None or isinstance(value, (bool, int, float, str)):
        return True
    if isinstance(value, list):
        return all(_json_compatible(item) for item in value)
    if isinstance(value, dict):
        return all(isinstance(key, str) and _json_compatible(item) for key, item in value.items())
    return False


class PregameContract(BaseModel):
    """Base class with strict fields and JSON-compatible serialization."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    def to_json_dict(self) -> dict[str, Any]:
        """Return a stable JSON-compatible dict for event-log payloads."""

        return self.model_dump(mode="json", exclude_none=False)


class PregameEvent(PregameContract):
    """Append-only event envelope for the pregame decision process."""

    event_id: str
    game_id: str
    event_type: PregameEventType
    created_at_utc: datetime
    effective_at_utc: datetime
    source: str
    schema_version: str = DEFAULT_EVENT_SCHEMA_VERSION
    idempotency_key: str | None = None
    supersedes_event_id: str | None = None
    correction_reason: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)

    @field_validator("event_id", "game_id", "source", "schema_version")
    @classmethod
    def _non_empty_text(cls, value: str, info: Any) -> str:
        return _require_non_empty(value, info.field_name)

    @field_validator("idempotency_key", "supersedes_event_id", "correction_reason")
    @classmethod
    def _optional_non_empty_text(cls, value: str | None, info: Any) -> str | None:
        if value is None:
            return None
        return _require_non_empty(value, info.field_name)

    @field_validator("created_at_utc", "effective_at_utc")
    @classmethod
    def _aware_utc_datetime(cls, value: datetime, info: Any) -> datetime:
        return _ensure_utc(value, info.field_name)

    @field_validator("payload", mode="before")
    @classmethod
    def _payload_mapping(cls, value: Any) -> dict[str, Any]:
        if not isinstance(value, Mapping):
            raise ValueError("payload must be a mapping")
        payload = dict(value)
        if not _json_compatible(payload):
            raise ValueError("payload must be JSON-compatible")
        return payload


class MarketSnapshot(PregameContract):
    """One market observation; not a historical store by itself."""

    snapshot_id: str
    game_id: str
    snapshot_kind: SnapshotKind
    captured_at_utc: datetime
    book: str
    source: str
    market_type: MarketType
    quality_status: MarketQualityStatus
    executable_status: ExecutableStatus
    selected_side: str | None = None
    spread: float | None = None
    spread_price: int | None = None
    total: float | None = None
    total_price: int | None = None
    moneyline: int | None = None
    notes: str | None = None
    schema_version: str = DEFAULT_MARKET_SNAPSHOT_SCHEMA_VERSION

    @field_validator("snapshot_id", "game_id", "book", "source", "schema_version")
    @classmethod
    def _non_empty_text(cls, value: str, info: Any) -> str:
        return _require_non_empty(value, info.field_name)

    @field_validator("selected_side", "notes")
    @classmethod
    def _optional_non_empty_text(cls, value: str | None, info: Any) -> str | None:
        if value is None:
            return None
        return _require_non_empty(value, info.field_name)

    @field_validator("captured_at_utc")
    @classmethod
    def _aware_utc_datetime(cls, value: datetime, info: Any) -> datetime:
        return _ensure_utc(value, info.field_name)


class CandidateRecord(PregameContract):
    """Normalized model candidate state. This is not an operator decision."""

    candidate_id: str
    game_id: str
    season: int
    week: int
    status: CandidateStatus
    created_at_utc: datetime
    model_variant: str
    selected_team: str
    model_tag: str
    production_eligible: bool
    confidence: float | None = None
    edge_vs_line: float | None = None
    model_margin: float | None = None
    market_margin_at_scan: float | None = None
    spread_at_scan: float | None = None
    price_at_scan: int | None = None
    preflight_status: str | None = None
    warnings: list[str] = Field(default_factory=list)
    reason_codes: list[str] = Field(default_factory=list)
    model_generated_at_utc: datetime | None = None
    scan_id: str | None = None
    source_ref: str | None = None
    source_sha256: str | None = None
    source_record_number: int | None = None
    source_metadata: dict[str, Any] = Field(default_factory=dict)
    schema_version: str = DEFAULT_CANDIDATE_SCHEMA_VERSION

    @field_validator(
        "candidate_id",
        "game_id",
        "model_variant",
        "selected_team",
        "model_tag",
        "scan_id",
        "source_ref",
        "source_sha256",
        "schema_version",
    )
    @classmethod
    def _non_empty_text(cls, value: str | None, info: Any) -> str | None:
        if value is None:
            return None
        return _require_non_empty(value, info.field_name)

    @field_validator("preflight_status")
    @classmethod
    def _optional_non_empty_text(cls, value: str | None, info: Any) -> str | None:
        if value is None:
            return None
        return _require_non_empty(value, info.field_name)

    @field_validator("season", "week", "source_record_number")
    @classmethod
    def _positive_int(cls, value: int | None, info: Any) -> int | None:
        if value is None:
            return None
        if value <= 0:
            raise ValueError(f"{info.field_name} must be positive")
        return value

    @field_validator("created_at_utc", "model_generated_at_utc")
    @classmethod
    def _aware_utc_datetime(cls, value: datetime | None, info: Any) -> datetime | None:
        if value is None:
            return None
        return _ensure_utc(value, info.field_name)

    @field_validator("warnings", "reason_codes")
    @classmethod
    def _list_items_not_empty(cls, value: list[str], info: Any) -> list[str]:
        for item in value:
            _require_non_empty(item, info.field_name)
        return value

    @field_validator("source_metadata", mode="before")
    @classmethod
    def _source_metadata_mapping(cls, value: Any) -> dict[str, Any]:
        if not isinstance(value, Mapping):
            raise ValueError("source_metadata must be a mapping")
        metadata = dict(value)
        if not _json_compatible(metadata):
            raise ValueError("source_metadata must be JSON-compatible")
        return metadata


class VariantBPointResult(PregameContract):
    """Compact structured representation of one Variant B audit point."""

    point_id: int
    point_name: str
    status: str
    blocking: bool
    risk_codes: tuple[str, ...] = ()
    warning_codes: tuple[str, ...] = ()
    evidence_present: bool
    evidence_source_refs: tuple[str, ...] = ()
    summary: str | None = None
    schema_version: str = DEFAULT_VARIANT_B_POINT_RESULT_SCHEMA_VERSION

    @field_validator("point_id")
    @classmethod
    def _positive_point_id(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("point_id must be positive")
        return value

    @field_validator("point_name", "status", "schema_version")
    @classmethod
    def _non_empty_text(cls, value: str, info: Any) -> str:
        return _require_non_empty(value, info.field_name)

    @field_validator("summary")
    @classmethod
    def _optional_non_empty_text(cls, value: str | None) -> str | None:
        return None if value is None else _require_non_empty(value, "summary")

    @field_validator("risk_codes", "warning_codes", "evidence_source_refs")
    @classmethod
    def _non_empty_items(cls, value: tuple[str, ...], info: Any) -> tuple[str, ...]:
        return tuple(_require_non_empty(item, info.field_name) for item in value)


class VariantBResearchRecord(PregameContract):
    """Auditable import of one official materialized Variant B JSON audit."""

    research_id: str
    candidate_id: str
    game_id: str
    model_variant: str
    selected_team: str
    research_kind: VariantBResearchKind
    research_status: VariantBResearchStatus
    framework_version: str
    audit_schema_version: str
    source_ref: str
    source_sha256: str
    generated_at_utc: datetime
    recorded_at_utc: datetime
    expected_point_count: int
    present_point_count: int
    sections_complete: bool
    point_results: tuple[VariantBPointResult, ...]
    blocking_risk_codes: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    p_cover: float | None = None
    p_push: float | None = None
    p_loss: float | None = None
    research_approved: bool = False
    legacy_audit_recommendation: dict[str, Any] | None = None
    acceptable_quote_frontier_raw: dict[str, Any] | None = None
    no_chase_raw: dict[str, Any] | None = None
    key_number_check_raw: dict[str, Any] | None = None
    schema_version: str = DEFAULT_VARIANT_B_RESEARCH_RECORD_SCHEMA_VERSION

    @field_validator(
        "research_id",
        "candidate_id",
        "game_id",
        "model_variant",
        "selected_team",
        "framework_version",
        "audit_schema_version",
        "source_ref",
        "source_sha256",
        "schema_version",
    )
    @classmethod
    def _non_empty_text(cls, value: str, info: Any) -> str:
        return _require_non_empty(value, info.field_name)

    @field_validator("generated_at_utc", "recorded_at_utc")
    @classmethod
    def _aware_utc_datetime(cls, value: datetime, info: Any) -> datetime:
        return _ensure_utc(value, info.field_name)

    @field_validator("expected_point_count", "present_point_count")
    @classmethod
    def _non_negative_count(cls, value: int, info: Any) -> int:
        if value < 0:
            raise ValueError(f"{info.field_name} must be non-negative")
        return value

    @field_validator("warnings", "blocking_risk_codes")
    @classmethod
    def _non_empty_items(cls, value: tuple[str, ...], info: Any) -> tuple[str, ...]:
        return tuple(_require_non_empty(item, info.field_name) for item in value)

    @field_validator(
        "legacy_audit_recommendation",
        "acceptable_quote_frontier_raw",
        "no_chase_raw",
        "key_number_check_raw",
        mode="before",
    )
    @classmethod
    def _optional_json_mapping(cls, value: Any) -> dict[str, Any] | None:
        if value is None:
            return None
        if not isinstance(value, Mapping):
            raise ValueError("raw research fragment must be a mapping")
        payload = dict(value)
        if not _json_compatible(payload):
            raise ValueError("raw research fragment must be JSON-compatible")
        return payload


class FinalQuotePolicy(PregameContract):
    """Explicit operator-supplied limits for one final quote evaluation."""

    policy_id: str
    source: str
    selected_team: str
    market_type: MarketType
    minimum_acceptable_spread: float | None
    minimum_acceptable_price: int | None
    max_quote_age_seconds: int
    allowed_quality_statuses: tuple[MarketQualityStatus, ...]
    allowed_executable_statuses: tuple[ExecutableStatus, ...]
    allowed_books: tuple[str, ...] | None = None
    key_numbers: tuple[float, ...] = ()
    reject_key_number_loss: bool = False
    no_chase_minimum_spread: float | None = None
    no_chase_minimum_price: int | None = None
    created_at_utc: datetime
    notes: str | None = None
    schema_version: str = DEFAULT_FINAL_QUOTE_POLICY_SCHEMA_VERSION

    @field_validator("policy_id", "source", "selected_team", "schema_version")
    @classmethod
    def _non_empty_text(cls, value: str, info: Any) -> str:
        return _require_non_empty(value, info.field_name)

    @field_validator("notes")
    @classmethod
    def _optional_non_empty_text(cls, value: str | None, info: Any) -> str | None:
        if value is None:
            return None
        return _require_non_empty(value, info.field_name)

    @field_validator("created_at_utc")
    @classmethod
    def _aware_utc_datetime(cls, value: datetime) -> datetime:
        return _ensure_utc(value, "created_at_utc")

    @field_validator("max_quote_age_seconds")
    @classmethod
    def _positive_quote_age(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("max_quote_age_seconds must be positive")
        return value

    @field_validator("allowed_quality_statuses", "allowed_executable_statuses")
    @classmethod
    def _non_empty_statuses(cls, value: tuple[Any, ...], info: Any) -> tuple[Any, ...]:
        if not value:
            raise ValueError(f"{info.field_name} must not be empty")
        return value

    @field_validator("allowed_books")
    @classmethod
    def _valid_allowed_books(cls, value: tuple[str, ...] | None) -> tuple[str, ...] | None:
        if value is None:
            return None
        if not value:
            raise ValueError("allowed_books must be null or non-empty")
        return tuple(_require_non_empty(book, "allowed_books") for book in value)

    @field_validator("key_numbers")
    @classmethod
    def _positive_key_numbers(cls, value: tuple[float, ...]) -> tuple[float, ...]:
        if any(number <= 0 for number in value):
            raise ValueError("key_numbers must be positive")
        return tuple(sorted(set(value)))

    @field_validator("minimum_acceptable_price", "no_chase_minimum_price")
    @classmethod
    def _valid_american_price(cls, value: int | None, info: Any) -> int | None:
        if value == 0:
            raise ValueError(f"{info.field_name} must not be zero")
        return value


class FinalQuoteGateResult(PregameContract):
    """Auditable result of evaluating one candidate against one final snapshot."""

    evaluation_id: str
    game_id: str
    candidate_id: str
    final_snapshot_id: str
    policy_id: str
    evaluated_at_utc: datetime
    passed: bool
    primary_status: FinalQuoteGateStatus
    primary_reason: FinalQuoteGateReason | None = None
    reason_codes: tuple[FinalQuoteGateReason, ...] = ()
    warnings: tuple[str, ...] = ()
    selected_team: str
    model_variant: str
    candidate_spread: float | None = None
    final_spread: float | None = None
    candidate_price: int | None = None
    final_price: int | None = None
    quote_age_seconds: int | None = None
    book: str | None = None
    quality_status: MarketQualityStatus | None = None
    executable_status: ExecutableStatus | None = None
    crossed_or_lost_key_numbers: tuple[float, ...] = ()
    policy_snapshot: dict[str, Any]
    policy_digest: str
    schema_version: str = DEFAULT_FINAL_QUOTE_GATE_RESULT_SCHEMA_VERSION

    @field_validator(
        "evaluation_id",
        "game_id",
        "candidate_id",
        "final_snapshot_id",
        "policy_id",
        "selected_team",
        "model_variant",
        "policy_digest",
        "schema_version",
    )
    @classmethod
    def _non_empty_text(cls, value: str, info: Any) -> str:
        return _require_non_empty(value, info.field_name)

    @field_validator("book")
    @classmethod
    def _optional_non_empty_text(cls, value: str | None, info: Any) -> str | None:
        if value is None:
            return None
        return _require_non_empty(value, "book")

    @field_validator("evaluated_at_utc")
    @classmethod
    def _aware_utc_datetime(cls, value: datetime) -> datetime:
        return _ensure_utc(value, "evaluated_at_utc")

    @field_validator("warnings")
    @classmethod
    def _warning_text(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(_require_non_empty(item, "warnings") for item in value)

    @field_validator("policy_snapshot", mode="before")
    @classmethod
    def _policy_snapshot_mapping(cls, value: Any) -> dict[str, Any]:
        if not isinstance(value, Mapping):
            raise ValueError("policy_snapshot must be a mapping")
        payload = dict(value)
        if not _json_compatible(payload):
            raise ValueError("policy_snapshot must be JSON-compatible")
        return payload


class OperatorDecision(PregameContract):
    """Final operator verdict contract. Approval rules are implemented later."""

    decision_id: str
    game_id: str
    verdict: OperatorVerdict
    decided_at_utc: datetime
    operator: str
    reason_codes: list[str]
    schema_version: str = DEFAULT_OPERATOR_DECISION_SCHEMA_VERSION
    candidate_id: str | None = None
    final_snapshot_id: str | None = None
    selected_team: str | None = None
    spread: float | None = None
    price: int | None = None
    stake_units: float | None = None
    comment: str | None = None
    model_version: str | None = None
    variant_b_version: str | None = None

    @field_validator("decision_id", "game_id", "operator", "schema_version")
    @classmethod
    def _non_empty_text(cls, value: str, info: Any) -> str:
        return _require_non_empty(value, info.field_name)

    @field_validator(
        "candidate_id",
        "final_snapshot_id",
        "selected_team",
        "comment",
        "model_version",
        "variant_b_version",
    )
    @classmethod
    def _optional_non_empty_text(cls, value: str | None, info: Any) -> str | None:
        if value is None:
            return None
        return _require_non_empty(value, info.field_name)

    @field_validator("decided_at_utc")
    @classmethod
    def _aware_utc_datetime(cls, value: datetime, info: Any) -> datetime:
        return _ensure_utc(value, info.field_name)

    @field_validator("reason_codes")
    @classmethod
    def _reason_codes_required(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("reason_codes must not be empty")
        for item in value:
            _require_non_empty(item, "reason_codes")
        return value


class PregameGameRecord(PregameContract):
    """Immutable current-state view projected from one game's event history."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    game_id: str
    schema_version: str = DEFAULT_GAME_RECORD_SCHEMA_VERSION
    last_projected_at_utc: datetime
    event_count: int
    current_decision_level: DecisionLevel | None = None

    season: int | None = None
    week: int | None = None
    away_team: str | None = None
    home_team: str | None = None
    kickoff_utc: datetime | None = None
    venue: str | None = None
    neutral_site: bool | None = None

    candidate: CandidateRecord | None = None
    candidate_status: CandidateStatus | None = None
    selected_team: str | None = None
    model_tag: str | None = None
    production_eligible: bool | None = None

    initial_market_snapshot: MarketSnapshot | None = None
    current_market_snapshot: MarketSnapshot | None = None
    final_market_snapshot: MarketSnapshot | None = None
    closing_market_snapshot: MarketSnapshot | None = None
    market_snapshot_count: int = 0

    final_quote_gate_result: FinalQuoteGateResult | None = None
    final_quote_gate_passed: bool | None = None
    final_quote_gate_status: FinalQuoteGateStatus | None = None
    latest_final_quote_gate_event_id: str | None = None

    latest_variant_b_research: VariantBResearchRecord | None = None
    latest_variant_b_research_id: str | None = None
    variant_b_research_status: VariantBResearchStatus | None = None
    variant_b_research_approved: bool | None = None
    variant_b_blocking_risk_codes: tuple[str, ...] = ()
    variant_b_framework_version: str | None = None
    variant_b_generated_at_utc: datetime | None = None

    research_started: bool = False
    research_completed: bool = False
    research_approved: bool = False
    latest_research_event_id: str | None = None

    operator_decision: OperatorDecision | None = None
    current_verdict: OperatorVerdict | None = None

    settled: bool = False
    latest_settlement_event_id: str | None = None

    last_event_id: str | None = None
    last_effective_at_utc: datetime | None = None
    warnings: tuple[str, ...] = ()
    projection_errors: tuple[str, ...] = ()

    @field_validator("game_id", "schema_version")
    @classmethod
    def _non_empty_text(cls, value: str, info: Any) -> str:
        return _require_non_empty(value, info.field_name)

    @field_validator(
        "last_projected_at_utc",
        "kickoff_utc",
        "last_effective_at_utc",
        "variant_b_generated_at_utc",
    )
    @classmethod
    def _aware_utc_datetime(cls, value: datetime | None, info: Any) -> datetime | None:
        if value is None:
            return None
        return _ensure_utc(value, info.field_name)
