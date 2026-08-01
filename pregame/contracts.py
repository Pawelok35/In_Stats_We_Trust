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
    ExecutableStatus,
    MarketQualityStatus,
    MarketType,
    OperatorVerdict,
    PregameEventType,
    SnapshotKind,
)

DEFAULT_EVENT_SCHEMA_VERSION = "pregame_event.v1"
DEFAULT_MARKET_SNAPSHOT_SCHEMA_VERSION = "market_snapshot.v1"
DEFAULT_CANDIDATE_SCHEMA_VERSION = "candidate_record.v1"
DEFAULT_OPERATOR_DECISION_SCHEMA_VERSION = "operator_decision.v1"


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
    schema_version: str = DEFAULT_CANDIDATE_SCHEMA_VERSION

    @field_validator(
        "candidate_id",
        "game_id",
        "model_variant",
        "selected_team",
        "model_tag",
        "schema_version",
    )
    @classmethod
    def _non_empty_text(cls, value: str, info: Any) -> str:
        return _require_non_empty(value, info.field_name)

    @field_validator("preflight_status")
    @classmethod
    def _optional_non_empty_text(cls, value: str | None, info: Any) -> str | None:
        if value is None:
            return None
        return _require_non_empty(value, info.field_name)

    @field_validator("season", "week")
    @classmethod
    def _positive_int(cls, value: int, info: Any) -> int:
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
