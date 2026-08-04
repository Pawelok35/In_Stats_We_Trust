"""Pydantic contracts for the NFL 2026 pregame operator layer.

These models intentionally contain no persistence, projection, model-adapter,
or GUI logic. They define the shape and validation rules for later layers.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

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
    StructuredManualEvidenceAssessmentStatus,
    StructuredManualEvidenceAssessorType,
    StructuredManualEvidenceCategory,
    VariantBPolicyBuildReason,
    VariantBPolicyBuildStatus,
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
DEFAULT_FINAL_QUOTE_RUNTIME_POLICY_SCHEMA_VERSION = "final_quote_runtime_policy.v1"
DEFAULT_VARIANT_B_POLICY_BUILD_RESULT_SCHEMA_VERSION = "variant_b_policy_build_result.v1"
DEFAULT_STRUCTURED_MANUAL_EVIDENCE_SCHEMA_VERSION = "structured_manual_evidence.v1"
DEFAULT_STRUCTURED_MANUAL_EVIDENCE_ASSESSMENT_SCHEMA_VERSION = (
    "structured_manual_evidence_assessment.v1"
)
DEFAULT_VARIANT_B_EVIDENCE_LINEAGE_MANIFEST_SCHEMA_VERSION = (
    "variant_b_evidence_lineage_manifest.v1"
)


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


def _require_literal_utc(value: datetime, field_name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    if value.utcoffset() != timezone.utc.utcoffset(value):
        raise ValueError(f"{field_name} must be in UTC")
    return value.astimezone(timezone.utc)


def _require_finite(value: float | None, field_name: str) -> float | None:
    if value is not None and not math.isfinite(value):
        raise ValueError(f"{field_name} must be finite")
    return value


class InjuryObservationPayload(PregameContract):
    """Source facts from one injury/practice report."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    team: str
    player_name: str
    report_status: str | None = None
    practice_participation: str | None = None
    game_designation: str | None = None
    position: str | None = None
    injury_description: str | None = None

    @field_validator(
        "team",
        "player_name",
        "report_status",
        "practice_participation",
        "game_designation",
        "position",
        "injury_description",
    )
    @classmethod
    def _text(cls, value: str | None, info: Any) -> str | None:
        if value is None:
            return None
        return _require_non_empty(value, info.field_name)

    @model_validator(mode="after")
    def _status_present(self) -> "InjuryObservationPayload":
        if not any((self.report_status, self.practice_participation, self.game_designation)):
            raise ValueError("injury payload requires a report, practice, or game status")
        return self


class RosterObservationPayload(PregameContract):
    """Source facts from one roster transaction."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    team: str
    player_name: str
    transaction_type: str
    previous_status: str | None = None
    new_status: str | None = None
    previous_team: str | None = None
    new_team: str | None = None

    @field_validator(
        "team",
        "player_name",
        "transaction_type",
        "previous_status",
        "new_status",
        "previous_team",
        "new_team",
    )
    @classmethod
    def _text(cls, value: str | None, info: Any) -> str | None:
        if value is None:
            return None
        return _require_non_empty(value, info.field_name)


class WeatherObservationPayload(PregameContract):
    """Source facts for one venue forecast valid at an explicit time."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    venue: str
    forecast_valid_for_utc: datetime
    indoor: bool | None = None
    roof_status: str | None = None
    temperature: float | None = None
    wind_speed: float | None = None
    wind_direction: str | None = None
    wind_gusts: float | None = None
    precipitation: str | None = None
    field_conditions: str | None = None

    @field_validator("venue", "roof_status", "wind_direction", "precipitation", "field_conditions")
    @classmethod
    def _text(cls, value: str | None, info: Any) -> str | None:
        if value is None:
            return None
        return _require_non_empty(value, info.field_name)

    @field_validator("forecast_valid_for_utc")
    @classmethod
    def _utc(cls, value: datetime, info: Any) -> datetime:
        return _require_literal_utc(value, info.field_name)

    @field_validator("temperature", "wind_speed", "wind_gusts")
    @classmethod
    def _finite(cls, value: float | None, info: Any) -> float | None:
        return _require_finite(value, info.field_name)

    @model_validator(mode="after")
    def _condition_present(self) -> "WeatherObservationPayload":
        values = (
            self.indoor,
            self.roof_status,
            self.temperature,
            self.wind_speed,
            self.wind_direction,
            self.wind_gusts,
            self.precipitation,
            self.field_conditions,
        )
        if not any(value is not None for value in values):
            raise ValueError("weather payload requires at least one factual condition")
        return self


class PublicBettingObservationPayload(PregameContract):
    """Source facts for one public-betting market observation."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    provider_scope: str
    market_type: MarketType
    market_scope: str
    selected_side: str
    tickets_percentage: float | None = None
    money_percentage: float | None = None
    market_snapshot_id: str | None = None
    provider_market_id: str | None = None

    @field_validator(
        "provider_scope",
        "market_scope",
        "selected_side",
        "market_snapshot_id",
        "provider_market_id",
    )
    @classmethod
    def _text(cls, value: str | None, info: Any) -> str | None:
        if value is None:
            return None
        return _require_non_empty(value, info.field_name)

    @field_validator("tickets_percentage", "money_percentage")
    @classmethod
    def _percentage(cls, value: float | None, info: Any) -> float | None:
        value = _require_finite(value, info.field_name)
        if value is not None and not 0 <= value <= 100:
            raise ValueError(f"{info.field_name} must be in 0..100")
        return value

    @model_validator(mode="after")
    def _percentage_present(self) -> "PublicBettingObservationPayload":
        if self.tickets_percentage is None and self.money_percentage is None:
            raise ValueError("public betting payload requires tickets or money percentage")
        return self


ManualEvidencePayload = (
    InjuryObservationPayload
    | RosterObservationPayload
    | WeatherObservationPayload
    | PublicBettingObservationPayload
)


class StructuredManualEvidenceRecord(PregameContract):
    """Immutable, source-factual observation for exactly one pregame game."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    observation_id: str
    game_id: str
    category: StructuredManualEvidenceCategory
    source_name: str
    source_type: str
    source_reference: str
    observed_at_utc: datetime
    recorded_at_utc: datetime
    payload: ManualEvidencePayload
    schema_version: str = DEFAULT_STRUCTURED_MANUAL_EVIDENCE_SCHEMA_VERSION
    candidate_id: str | None = None
    provider_record_id: str | None = None
    effective_at_utc: datetime | None = None
    supersedes_observation_id: str | None = None

    @field_validator(
        "observation_id",
        "game_id",
        "source_name",
        "source_type",
        "source_reference",
        "schema_version",
        "candidate_id",
        "provider_record_id",
        "supersedes_observation_id",
    )
    @classmethod
    def _text(cls, value: str | None, info: Any) -> str | None:
        if value is None:
            return None
        return _require_non_empty(value, info.field_name)

    @field_validator("observed_at_utc", "recorded_at_utc", "effective_at_utc")
    @classmethod
    def _utc(cls, value: datetime | None, info: Any) -> datetime | None:
        if value is None:
            return None
        return _require_literal_utc(value, info.field_name)

    @field_validator("payload", mode="before")
    @classmethod
    def _payload_mapping(cls, value: Any) -> Any:
        if isinstance(
            value,
            (
                InjuryObservationPayload,
                RosterObservationPayload,
                WeatherObservationPayload,
                PublicBettingObservationPayload,
            ),
        ):
            return value
        if not isinstance(value, Mapping):
            raise ValueError("payload must be a mapping")
        return dict(value)

    @model_validator(mode="after")
    def _category_payload_alignment(self) -> "StructuredManualEvidenceRecord":
        expected = {
            StructuredManualEvidenceCategory.INJURY: InjuryObservationPayload,
            StructuredManualEvidenceCategory.ROSTER: RosterObservationPayload,
            StructuredManualEvidenceCategory.WEATHER: WeatherObservationPayload,
            StructuredManualEvidenceCategory.PUBLIC_BETTING: PublicBettingObservationPayload,
        }[self.category]
        if not isinstance(self.payload, expected):
            raise ValueError("category does not match payload type")
        if (
            self.category == StructuredManualEvidenceCategory.ROSTER
            and self.effective_at_utc is None
        ):
            raise ValueError("roster observation requires effective_at_utc")
        if self.supersedes_observation_id == self.observation_id:
            raise ValueError("observation cannot supersede itself")
        return self

    @property
    def subject_key(self) -> str:
        payload = self.payload
        if isinstance(payload, (InjuryObservationPayload, RosterObservationPayload)):
            return f"{self.category.value}|{payload.team}|{payload.player_name}"
        if isinstance(payload, WeatherObservationPayload):
            return f"WEATHER|{payload.venue}|{payload.forecast_valid_for_utc.isoformat()}"
        return (
            "PUBLIC_BETTING|"
            f"{payload.market_type.value}|{payload.market_scope}|{payload.selected_side}|{payload.provider_scope}"
        )


class StructuredManualEvidenceLatestIndex(PregameContract):
    """Immutable lookup entry for the newest active observation per source/subject."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    category: StructuredManualEvidenceCategory
    subject_key: str
    source_name: str
    observation_id: str

    @field_validator("subject_key", "source_name", "observation_id")
    @classmethod
    def _text(cls, value: str, info: Any) -> str:
        return _require_non_empty(value, info.field_name)


class OperatorAssessorMetadata(PregameContract):
    model_config = ConfigDict(extra="forbid", frozen=True)

    assessor_type: Literal[StructuredManualEvidenceAssessorType.OPERATOR]
    assessor_id: str
    display_name: str | None = None

    @field_validator("assessor_id", "display_name")
    @classmethod
    def _text(cls, value: str | None, info: Any) -> str | None:
        if value is None:
            return None
        return _require_non_empty(value, info.field_name)


class GptLlmAssessorMetadata(PregameContract):
    model_config = ConfigDict(extra="forbid", frozen=True)

    assessor_type: Literal[StructuredManualEvidenceAssessorType.GPT_LLM]
    assessor_id: str
    provider: str
    model_name: str
    model_version: str | None = None
    model_revision: str | None = None
    prompt_template_version: str | None = None
    prompt_digest: str | None = None
    run_artifact_reference: str | None = None

    @field_validator(
        "assessor_id",
        "provider",
        "model_name",
        "model_version",
        "model_revision",
        "prompt_template_version",
        "prompt_digest",
        "run_artifact_reference",
    )
    @classmethod
    def _text(cls, value: str | None, info: Any) -> str | None:
        if value is None:
            return None
        return _require_non_empty(value, info.field_name)

    @model_validator(mode="after")
    def _metadata_present(self) -> "GptLlmAssessorMetadata":
        if not (self.model_version or self.model_revision):
            raise ValueError("GPT_LLM requires model_version or model_revision")
        if not (self.prompt_template_version or self.prompt_digest or self.run_artifact_reference):
            raise ValueError("GPT_LLM requires prompt or run identity")
        return self


class DeterministicRuleAssessorMetadata(PregameContract):
    model_config = ConfigDict(extra="forbid", frozen=True)

    assessor_type: Literal[StructuredManualEvidenceAssessorType.DETERMINISTIC_RULE]
    assessor_id: str
    rule_profile_id: str
    rule_version: str | None = None
    rule_digest: str | None = None

    @field_validator("assessor_id", "rule_profile_id", "rule_version", "rule_digest")
    @classmethod
    def _text(cls, value: str | None, info: Any) -> str | None:
        if value is None:
            return None
        return _require_non_empty(value, info.field_name)

    @model_validator(mode="after")
    def _version_present(self) -> "DeterministicRuleAssessorMetadata":
        if not (self.rule_version or self.rule_digest):
            raise ValueError("DETERMINISTIC_RULE requires rule_version or rule_digest")
        return self


class ResearchProcessAssessorMetadata(PregameContract):
    model_config = ConfigDict(extra="forbid", frozen=True)

    assessor_type: Literal[StructuredManualEvidenceAssessorType.RESEARCH_PROCESS]
    assessor_id: str
    process_id: str
    process_version: str | None = None
    process_digest: str | None = None
    researcher_id: str | None = None

    @field_validator(
        "assessor_id", "process_id", "process_version", "process_digest", "researcher_id"
    )
    @classmethod
    def _text(cls, value: str | None, info: Any) -> str | None:
        if value is None:
            return None
        return _require_non_empty(value, info.field_name)

    @model_validator(mode="after")
    def _version_present(self) -> "ResearchProcessAssessorMetadata":
        if not (self.process_version or self.process_digest):
            raise ValueError("RESEARCH_PROCESS requires process_version or process_digest")
        return self


ManualEvidenceAssessorMetadata = (
    OperatorAssessorMetadata
    | GptLlmAssessorMetadata
    | DeterministicRuleAssessorMetadata
    | ResearchProcessAssessorMetadata
)


class StructuredManualEvidenceAssessmentRecord(PregameContract):
    """Immutable interpretation of explicitly referenced source observations."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    assessment_id: str
    game_id: str
    category: StructuredManualEvidenceCategory
    assessment_scope: str
    observation_ids: tuple[str, ...]
    assessor: ManualEvidenceAssessorMetadata
    as_of_utc: datetime
    assessed_at_utc: datetime
    recorded_at_utc: datetime
    status: StructuredManualEvidenceAssessmentStatus
    reason_codes: tuple[str, ...]
    schema_version: str = DEFAULT_STRUCTURED_MANUAL_EVIDENCE_ASSESSMENT_SCHEMA_VERSION
    candidate_id: str | None = None
    notes: str | None = None
    supersedes_assessment_id: str | None = None

    @field_validator(
        "assessment_id",
        "game_id",
        "assessment_scope",
        "schema_version",
        "candidate_id",
        "notes",
        "supersedes_assessment_id",
    )
    @classmethod
    def _text(cls, value: str | None, info: Any) -> str | None:
        if value is None:
            return None
        return _require_non_empty(value, info.field_name)

    @field_validator("observation_ids", "reason_codes")
    @classmethod
    def _text_values(cls, value: tuple[str, ...], info: Any) -> tuple[str, ...]:
        cleaned = tuple(_require_non_empty(item, info.field_name) for item in value)
        if len(cleaned) != len(set(cleaned)):
            raise ValueError(f"{info.field_name} must not contain duplicates")
        return cleaned

    @field_validator("as_of_utc", "assessed_at_utc", "recorded_at_utc")
    @classmethod
    def _utc(cls, value: datetime, info: Any) -> datetime:
        return _require_literal_utc(value, info.field_name)

    @model_validator(mode="after")
    def _semantics(self) -> "StructuredManualEvidenceAssessmentRecord":
        if self.as_of_utc > self.assessed_at_utc or self.assessed_at_utc > self.recorded_at_utc:
            raise ValueError("assessment timestamps must satisfy as_of <= assessed <= recorded")
        with_observations = {
            StructuredManualEvidenceAssessmentStatus.PASS,
            StructuredManualEvidenceAssessmentStatus.WARNING,
            StructuredManualEvidenceAssessmentStatus.BLOCKING,
            StructuredManualEvidenceAssessmentStatus.PENDING,
        }
        with_reasons = {
            StructuredManualEvidenceAssessmentStatus.WARNING,
            StructuredManualEvidenceAssessmentStatus.BLOCKING,
            StructuredManualEvidenceAssessmentStatus.PENDING,
            StructuredManualEvidenceAssessmentStatus.NO_DATA,
            StructuredManualEvidenceAssessmentStatus.NOT_DUE,
        }
        if self.status in with_observations and not self.observation_ids:
            raise ValueError(f"{self.status.value} assessment requires observation_ids")
        if self.status in with_reasons and not self.reason_codes:
            raise ValueError(f"{self.status.value} assessment requires reason_codes")
        if self.supersedes_assessment_id == self.assessment_id:
            raise ValueError("assessment cannot supersede itself")
        return self

    @property
    def assessor_type(self) -> StructuredManualEvidenceAssessorType:
        return self.assessor.assessor_type

    @property
    def latest_key(self) -> str:
        candidate = self.candidate_id or "__GAME_LEVEL__"
        return "|".join(
            (
                candidate,
                self.category.value,
                self.assessment_scope,
                self.assessor_type.value,
                self.assessor.assessor_id,
            )
        )


class StructuredManualEvidenceAssessmentLatestIndex(PregameContract):
    model_config = ConfigDict(extra="forbid", frozen=True)

    latest_key: str
    assessment_id: str

    @field_validator("latest_key", "assessment_id")
    @classmethod
    def _text(cls, value: str, info: Any) -> str:
        return _require_non_empty(value, info.field_name)


class VariantBEvidenceLineageManifestRecord(PregameContract):
    """Immutable external references used to prepare one Variant B sidecar."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    manifest_id: str
    evidence_id: str
    candidate_id: str
    game_id: str
    audit_stage: str
    observation_ids: tuple[str, ...]
    assessment_ids: tuple[str, ...]
    evidence_sidecar_digest: str
    evidence_sidecar_reference: str
    prepared_at_utc: datetime
    recorded_at_utc: datetime
    schema_version: str = DEFAULT_VARIANT_B_EVIDENCE_LINEAGE_MANIFEST_SCHEMA_VERSION
    preparer_id: str | None = None
    notes: str | None = None

    @field_validator(
        "manifest_id",
        "evidence_id",
        "candidate_id",
        "game_id",
        "audit_stage",
        "evidence_sidecar_digest",
        "evidence_sidecar_reference",
        "schema_version",
        "preparer_id",
        "notes",
    )
    @classmethod
    def _text(cls, value: str | None, info: Any) -> str | None:
        if value is None:
            return None
        return _require_non_empty(value, info.field_name)

    @field_validator("observation_ids", "assessment_ids")
    @classmethod
    def _identifiers(cls, value: tuple[str, ...], info: Any) -> tuple[str, ...]:
        cleaned = tuple(_require_non_empty(item, info.field_name) for item in value)
        if len(cleaned) != len(set(cleaned)):
            raise ValueError(f"{info.field_name} must not contain duplicates")
        if cleaned != tuple(sorted(cleaned)):
            raise ValueError(f"{info.field_name} must be canonical ordered")
        return cleaned

    @field_validator("prepared_at_utc", "recorded_at_utc")
    @classmethod
    def _utc(cls, value: datetime, info: Any) -> datetime:
        return _require_literal_utc(value, info.field_name)

    @model_validator(mode="after")
    def _semantics(self) -> "VariantBEvidenceLineageManifestRecord":
        if self.audit_stage != "PREKICK":
            raise ValueError("only PREKICK evidence lineage is supported")
        if not self.assessment_ids:
            raise ValueError("assessment_ids must not be empty")
        if self.prepared_at_utc > self.recorded_at_utc:
            raise ValueError("prepared_at_utc must not be after recorded_at_utc")
        return self


class VariantBEvidenceLineageManifestIndex(PregameContract):
    model_config = ConfigDict(extra="forbid", frozen=True)

    evidence_id: str
    manifest_id: str

    @field_validator("evidence_id", "manifest_id")
    @classmethod
    def _text(cls, value: str, info: Any) -> str:
        return _require_non_empty(value, info.field_name)


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
    away: str
    home: str
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
        "away",
        "home",
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

    @model_validator(mode="after")
    def _distinct_matchup_teams(self) -> "CandidateRecord":
        if self.home == self.away:
            raise ValueError("home and away must be different")
        if "model_pick" in self.source_metadata:
            model_pick = self.source_metadata["model_pick"]
            if not isinstance(model_pick, Mapping):
                raise ValueError("source_metadata.model_pick must be a mapping")
            quote_id = model_pick.get("model_generation_quote_id")
            if not isinstance(quote_id, str) or not quote_id.strip():
                raise ValueError(
                    "source_metadata.model_pick.model_generation_quote_id "
                    "must be a non-empty string"
                )
        return self


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


class FinalQuoteRuntimePolicy(PregameContract):
    """Explicit execution constraints, separate from Variant B frontier evidence."""

    runtime_policy_id: str
    source: str
    created_at_utc: datetime
    max_quote_age_seconds: int
    allowed_quality_statuses: tuple[MarketQualityStatus, ...]
    allowed_executable_statuses: tuple[ExecutableStatus, ...]
    allowed_books: tuple[str, ...] | None = None
    key_numbers: tuple[float, ...] | None = None
    reject_key_number_loss: bool | None = None
    require_latest_candidate: bool = True
    require_latest_final_snapshot_for_book: bool = True
    notes: str | None = None
    schema_version: str = DEFAULT_FINAL_QUOTE_RUNTIME_POLICY_SCHEMA_VERSION

    @field_validator("runtime_policy_id", "source", "schema_version")
    @classmethod
    def _non_empty_text(cls, value: str, info: Any) -> str:
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
    def _positive_key_numbers(cls, value: tuple[float, ...] | None) -> tuple[float, ...] | None:
        if value is None:
            return None
        if any(number <= 0 for number in value):
            raise ValueError("key_numbers must be positive")
        return tuple(sorted(set(value)))


class VariantBFinalQuotePolicyBuildResult(PregameContract):
    """Pure adapter result; failed construction is structured, not exceptional."""

    build_id: str
    candidate_id: str
    research_id: str | None
    runtime_policy_id: str
    built_at_utc: datetime
    status: VariantBPolicyBuildStatus
    policy: FinalQuotePolicy | None
    reason_codes: tuple[VariantBPolicyBuildReason, ...] = ()
    warnings: tuple[str, ...] = ()
    source_frontier_digest: str | None = None
    source_no_chase_digest: str | None = None
    source_key_number_digest: str | None = None
    research_status: VariantBResearchStatus | None = None
    research_approved: bool | None = None
    schema_version: str = DEFAULT_VARIANT_B_POLICY_BUILD_RESULT_SCHEMA_VERSION

    @field_validator("build_id", "candidate_id", "runtime_policy_id", "schema_version")
    @classmethod
    def _non_empty_text(cls, value: str, info: Any) -> str:
        return _require_non_empty(value, info.field_name)

    @field_validator("research_id")
    @classmethod
    def _optional_non_empty_text(cls, value: str | None) -> str | None:
        return None if value is None else _require_non_empty(value, "research_id")

    @field_validator("built_at_utc")
    @classmethod
    def _aware_utc_datetime(cls, value: datetime) -> datetime:
        return _ensure_utc(value, "built_at_utc")

    @field_validator("warnings")
    @classmethod
    def _warning_text(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(_require_non_empty(item, "warnings") for item in value)


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


class StructuredVariantBAuditResultRecord(PregameContract):
    """Compact central record of one Stage 11.2 audit attempt."""

    event_id: str
    candidate_id: str
    game_id: str
    evidence_id: str
    model_generation_snapshot_id: str
    model_generation_quote_id: str
    audit_stage: str
    build_timestamp_utc: datetime
    pure_core_status: str
    orchestration_status: str
    persistence_written: bool
    blocking_reasons: tuple[str, ...] = ()
    build_id: str | None = None
    canonical_digest: str | None = None
    artifact_ref: str | None = None
    schema_version: str = "structured_variant_b_audit_result_record.v1"

    @field_validator(
        "event_id",
        "candidate_id",
        "game_id",
        "evidence_id",
        "model_generation_snapshot_id",
        "model_generation_quote_id",
        "audit_stage",
        "pure_core_status",
        "orchestration_status",
        "schema_version",
    )
    @classmethod
    def _non_empty_text(cls, value: str, info: Any) -> str:
        return _require_non_empty(value, info.field_name)

    @field_validator("build_id", "canonical_digest", "artifact_ref")
    @classmethod
    def _optional_non_empty_text(cls, value: str | None, info: Any) -> str | None:
        return None if value is None else _require_non_empty(value, info.field_name)

    @field_validator("build_timestamp_utc")
    @classmethod
    def _aware_utc_datetime(cls, value: datetime, info: Any) -> datetime:
        return _ensure_utc(value, info.field_name)

    @field_validator("blocking_reasons")
    @classmethod
    def _non_empty_reasons(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(_require_non_empty(item, "blocking_reasons") for item in value)

    @model_validator(mode="after")
    def _result_semantics(self) -> "StructuredVariantBAuditResultRecord":
        successful = self.pure_core_status == "BUILT"
        if successful:
            if self.orchestration_status not in {"WRITTEN", "ALREADY_EXISTS_IDENTICAL"}:
                raise ValueError("successful audit requires a successful orchestration status")
            if not self.build_id or not self.canonical_digest or not self.artifact_ref:
                raise ValueError("successful audit requires build_id, digest, and artifact_ref")
            if self.blocking_reasons:
                raise ValueError("successful audit must not contain blocking reasons")
        elif self.pure_core_status == "BLOCKED_PRECONDITION":
            if self.orchestration_status != "BLOCKED" or self.persistence_written:
                raise ValueError("blocked audit must be an unwritten BLOCKED orchestration result")
            if not self.blocking_reasons:
                raise ValueError("blocked audit requires blocking reasons")
            if self.artifact_ref is not None:
                raise ValueError("blocked audit must not expose an artifact_ref")
        else:
            raise ValueError("unsupported pure_core_status for central audit result")
        return self


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

    latest_structured_variant_b_audit_attempt: StructuredVariantBAuditResultRecord | None = None
    latest_successful_structured_variant_b_audit: StructuredVariantBAuditResultRecord | None = None

    structured_manual_evidence: tuple[StructuredManualEvidenceRecord, ...] = ()
    active_structured_manual_evidence: tuple[StructuredManualEvidenceRecord, ...] = ()
    superseded_structured_manual_evidence_ids: tuple[str, ...] = ()
    latest_structured_manual_evidence_by_source_subject: tuple[
        StructuredManualEvidenceLatestIndex, ...
    ] = ()
    structured_manual_evidence_assessments: tuple[
        StructuredManualEvidenceAssessmentRecord, ...
    ] = ()
    active_structured_manual_evidence_assessments: tuple[
        StructuredManualEvidenceAssessmentRecord, ...
    ] = ()
    superseded_structured_manual_evidence_assessment_ids: tuple[str, ...] = ()
    latest_structured_manual_evidence_assessment_by_scope_assessor: tuple[
        StructuredManualEvidenceAssessmentLatestIndex, ...
    ] = ()
    variant_b_evidence_lineage_manifests: tuple[VariantBEvidenceLineageManifestRecord, ...] = ()
    variant_b_evidence_lineage_by_evidence_id: tuple[VariantBEvidenceLineageManifestIndex, ...] = ()

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
