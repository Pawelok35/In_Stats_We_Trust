"""Structured, immutable GPT evidence sidecar for the Variant B framework."""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import Field, ValidationInfo, field_validator, model_validator

from pregame.contracts import PregameContract
from pregame.events import MarketType, VariantBResearchKind

EVIDENCE_SCHEMA_VERSION = "variant_b_gpt_evidence.v1"
EVIDENCE_PROMPT_VERSION = "variant_b_structured_19_point_evidence.v1"

VARIANT_B_POINT_DEFINITIONS = (
    (1, "argument_against", "GPT_EVIDENCE"),
    (2, "market_move_notes", "HYBRID"),
    (3, "injury_role_notes", "GPT_EVIDENCE"),
    (4, "schedule_spot_notes", "GPT_EVIDENCE"),
    (5, "weather_notes", "GPT_EVIDENCE"),
    (6, "key_number_check", "HYBRID"),
    (7, "no_chase_limit", "HYBRID"),
    (8, "price_quality", "HYBRID"),
    (9, "market_snapshot", "DETERMINISTIC"),
    (10, "public_bias / tickets_handle", "GPT_EVIDENCE"),
    (11, "power_rankings_check", "HYBRID"),
    (12, "roster_change_check", "GPT_EVIDENCE"),
    (13, "matchup_specific_risk", "GPT_EVIDENCE"),
    (14, "game_script_risk", "GPT_EVIDENCE"),
    (15, "closing_line", "NOT_DUE_PREKICK"),
    (16, "closing_price", "NOT_DUE_PREKICK"),
    (17, "clv_points", "NOT_DUE_PREKICK"),
    (18, "process_quality", "DETERMINISTIC"),
    (19, "final_operator_decision", "NON_AUTHORITATIVE_EVIDENCE"),
)
POINT_NAMES = {point_id: name for point_id, name, _ in VARIANT_B_POINT_DEFINITIONS}


class EvidenceStatus(str, Enum):
    PASS = "PASS"
    WARNING = "WARNING"
    BLOCKING_RISK = "BLOCKING_RISK"
    PENDING = "PENDING"
    UNKNOWN = "UNKNOWN"
    NO_DATA = "NO_DATA"
    NOT_DUE = "NOT_DUE"


class SidecarWriteStatus(str, Enum):
    WRITTEN = "WRITTEN"
    ALREADY_EXISTS = "ALREADY_EXISTS"
    CONFLICT = "CONFLICT"


class VariantBEvidenceSource(PregameContract):
    evidence_source_id: str
    source_type: str
    source_name: str
    source_ref: str
    captured_at_utc: datetime
    reliability: str
    fact_summary: str
    supports_assessment: str
    data_fields: dict[str, Any] = Field(default_factory=dict)
    published_at_utc: datetime | None = None
    notes: str | None = None

    @field_validator(
        "evidence_source_id",
        "source_type",
        "source_name",
        "source_ref",
        "reliability",
        "fact_summary",
        "supports_assessment",
    )
    @classmethod
    def _text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("evidence source text must not be empty")
        return value

    @field_validator("captured_at_utc", "published_at_utc")
    @classmethod
    def _utc(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None or value.utcoffset() != timezone.utc.utcoffset(value):
            raise ValueError("timestamps must be UTC")
        return value


class VariantBGptPointEvidence(PregameContract):
    point_id: int
    point_name: str
    status: EvidenceStatus
    gpt_assessment: str
    blocking_assessment: str
    risk_codes: tuple[str, ...] = ()
    warning_codes: tuple[str, ...] = ()
    summary: str
    evidence_items: tuple[str, ...] = ()
    structured_data: dict[str, Any] = Field(default_factory=dict)
    data_complete: bool
    no_data_reason: str | None = None

    @model_validator(mode="after")
    def _point_contract(self):
        if self.point_id not in POINT_NAMES:
            raise ValueError("unknown point_id")
        if self.point_name != POINT_NAMES[self.point_id]:
            raise ValueError("point_name does not match point_id")
        if (
            self.status
            in {EvidenceStatus.PASS, EvidenceStatus.WARNING, EvidenceStatus.BLOCKING_RISK}
            and not self.evidence_items
        ):
            raise ValueError("evidence is required for assessed point")
        if (
            self.status
            in {
                EvidenceStatus.UNKNOWN,
                EvidenceStatus.NO_DATA,
                EvidenceStatus.PENDING,
                EvidenceStatus.NOT_DUE,
            }
            and not self.no_data_reason
        ):
            raise ValueError("no_data_reason is required for unresolved point")
        return self


class VariantBProbabilityAssessment(PregameContract):
    p_cover: float
    p_push: float
    p_loss: float
    method: str
    source_refs: tuple[str, ...]
    generated_at_utc: datetime
    confidence_note: str | None = None

    @model_validator(mode="after")
    def _probabilities(self):
        if any(value < 0 or value > 1 for value in (self.p_cover, self.p_push, self.p_loss)):
            raise ValueError("probabilities must be in 0..1")
        if abs(self.p_cover + self.p_push + self.p_loss - 1) > 0.000001:
            raise ValueError("probabilities must sum to 1")
        if not self.method.strip() or not self.source_refs:
            raise ValueError("probability method and source_refs are required")
        if (
            self.generated_at_utc.tzinfo is None
            or self.generated_at_utc.utcoffset() != timezone.utc.utcoffset(self.generated_at_utc)
        ):
            raise ValueError("generated_at_utc must be UTC")
        return self


class VariantBAcceptableQuoteFrontierEvidence(PregameContract):
    selected_team: str
    market_type: MarketType
    minimum_acceptable_spread: float
    minimum_acceptable_price: int
    frontier_basis: str
    source_refs: tuple[str, ...]
    effective_at_utc: datetime
    notes: str | None = None

    @model_validator(mode="after")
    def _frontier(self):
        if self.market_type != MarketType.SPREAD:
            raise ValueError("v1 supports spread frontier only")
        if self.minimum_acceptable_price == 0:
            raise ValueError("American price must not be zero")
        if (
            not self.selected_team.strip()
            or not self.frontier_basis.strip()
            or not self.source_refs
        ):
            raise ValueError("frontier fields are required")
        return self


class VariantBNoChaseEvidence(PregameContract):
    represented_by_frontier: bool
    source_refs: tuple[str, ...]
    rationale: str
    effective_at_utc: datetime
    minimum_acceptable_spread: float | None = None
    minimum_acceptable_price: int | None = None
    max_spread_deterioration: float | None = None

    @model_validator(mode="after")
    def _no_chase(self):
        if not self.source_refs or not self.rationale.strip():
            raise ValueError("no-chase source_refs and rationale required")
        if not self.represented_by_frontier and all(
            v is None
            for v in (
                self.minimum_acceptable_spread,
                self.minimum_acceptable_price,
                self.max_spread_deterioration,
            )
        ):
            raise ValueError("separate no-chase requires a numeric limit")
        if self.minimum_acceptable_price == 0:
            raise ValueError("American price must not be zero")
        return self


class VariantBKeyNumberEvidence(PregameContract):
    key_numbers: tuple[float, ...]
    reject_key_number_loss: bool
    source_refs: tuple[str, ...]
    methodology_note: str

    @model_validator(mode="after")
    def _keys(self):
        if (
            not self.key_numbers
            or any(x <= 0 for x in self.key_numbers)
            or len(set(self.key_numbers)) != len(self.key_numbers)
        ):
            raise ValueError("key_numbers must be positive and unique")
        if not self.source_refs or not self.methodology_note.strip():
            raise ValueError("key number source_refs and methodology required")
        return self


class VariantBInjuryEvidence(PregameContract):
    player: str
    team: str
    position: str
    role: str
    starter_status: str
    practice_status: str
    game_status: str
    injury_type: str
    reported_at_utc: datetime
    source_ref: str
    impact: str
    blocking_assessment: str
    notes: str | None = None


class VariantBPublicBettingEvidence(PregameContract):
    market_type: MarketType
    side: str
    bet_percentage: float | None = None
    money_percentage: float | None = None
    source: str
    source_scope: str
    captured_at_utc: datetime
    reliability: str
    notes: str | None = None

    @field_validator("bet_percentage", "money_percentage")
    @classmethod
    def _pct(cls, value: float | None) -> float | None:
        if value is not None and not 0 <= value <= 100:
            raise ValueError("percentages must be in 0..100")
        return value


class VariantBWeatherEvidence(PregameContract):
    venue: str
    roof_status: str
    forecast_for_utc: datetime
    captured_at_utc: datetime
    temperature: float | None = None
    wind_speed: float | None = None
    wind_gusts: float | None = None
    precipitation_probability: float | None = None
    precipitation_type: str | None = None
    source_ref: str
    reliability: str
    impact_assessment: str


class VariantBMarketEvidence(PregameContract):
    book: str
    spread: float | None
    price: int | None
    captured_at_utc: datetime
    source: str
    executable_status: str
    quality_status: str
    snapshot_id: str | None = None
    snapshot_ref: str | None = None
    movement_note: str | None = None
    key_number_note: str | None = None


class VariantBGptEvidenceSidecar(PregameContract):
    evidence_id: str
    schema_version: str = EVIDENCE_SCHEMA_VERSION
    prompt_version: str = EVIDENCE_PROMPT_VERSION
    candidate_id: str
    game_id: str
    season: int
    week: int
    away_team: str
    home_team: str
    selected_team: str
    model_variant: str
    research_kind: VariantBResearchKind
    generated_at_utc: datetime
    recorded_at_utc: datetime
    source_ref: str
    expected_point_count: int
    point_results: tuple[VariantBGptPointEvidence, ...]
    evidence_sources: tuple[VariantBEvidenceSource, ...]
    probability_assessment: VariantBProbabilityAssessment | None = None
    acceptable_quote_frontier: VariantBAcceptableQuoteFrontierEvidence | None = None
    no_chase: VariantBNoChaseEvidence | None = None
    key_number_policy: VariantBKeyNumberEvidence | None = None
    injury_evidence: tuple[VariantBInjuryEvidence, ...] = ()
    public_betting_evidence: tuple[VariantBPublicBettingEvidence, ...] = ()
    weather_evidence: tuple[VariantBWeatherEvidence, ...] = ()
    market_evidence: tuple[VariantBMarketEvidence, ...] = ()
    blocking_risk_codes_reported: tuple[str, ...] = ()
    warnings_reported: tuple[str, ...] = ()
    overall_summary: str
    source_count: int

    @model_validator(mode="after")
    def _sidecar(self, info: ValidationInfo):
        if self.expected_point_count != 19 or len(self.point_results) != 19:
            raise ValueError("sidecar requires exactly 19 points")
        ids = [point.point_id for point in self.point_results]
        if ids != list(POINT_NAMES):
            raise ValueError("point_results must contain the ordered official points")
        if self.selected_team not in {self.away_team, self.home_team}:
            raise ValueError("selected_team must be in matchup")
        if (
            self.acceptable_quote_frontier
            and self.acceptable_quote_frontier.selected_team != self.selected_team
        ):
            raise ValueError("frontier selected_team mismatch")
        if self.season <= 0 or self.week <= 0 or self.source_count < 0:
            raise ValueError("invalid season, week, or source_count")
        source_ids = [source.evidence_source_id for source in self.evidence_sources]
        if len(source_ids) != len(set(source_ids)):
            raise ValueError("evidence_source_id values must be unique")
        if self.source_count != len(source_ids):
            raise ValueError("source_count must match evidence_sources")
        referenced = {ref for point in self.point_results for ref in point.evidence_items}
        if not referenced.issubset(set(source_ids)):
            raise ValueError("point evidence_items must reference evidence_sources")
        for stamp in (self.generated_at_utc, self.recorded_at_utc):
            if stamp.tzinfo is None or stamp.utcoffset() != timezone.utc.utcoffset(stamp):
                raise ValueError("sidecar timestamps must be UTC")
        if (
            not info.context or not info.context.get("skip_evidence_id_check")
        ) and self.evidence_id != evidence_id_for_payload(self):
            raise ValueError("evidence_id does not match canonical content")
        return self

    def completeness_summary(self) -> dict[str, Any]:
        unresolved = {EvidenceStatus.UNKNOWN, EvidenceStatus.NO_DATA, EvidenceStatus.PENDING}
        incomplete = [
            p.point_id for p in self.point_results if not p.data_complete or p.status in unresolved
        ]
        no_evidence = [
            p.point_id
            for p in self.point_results
            if not p.evidence_items
            and p.status
            not in {
                EvidenceStatus.UNKNOWN,
                EvidenceStatus.NO_DATA,
                EvidenceStatus.PENDING,
                EvidenceStatus.NOT_DUE,
            }
        ]
        ready = (
            not incomplete
            and not no_evidence
            and bool(self.evidence_sources)
            and all(
                (
                    self.probability_assessment,
                    self.acceptable_quote_frontier,
                    self.no_chase,
                    self.key_number_policy,
                )
            )
        )
        return {
            "expected_points": 19,
            "present_points": len(self.point_results),
            "missing_point_ids": [],
            "duplicate_point_ids": [],
            "incomplete_point_ids": incomplete,
            "points_without_evidence": no_evidence,
            "probability_complete": self.probability_assessment is not None,
            "frontier_complete": self.acceptable_quote_frontier is not None,
            "no_chase_complete": self.no_chase is not None,
            "key_number_complete": self.key_number_policy is not None,
            "structurally_ready_for_variant_b_import": ready,
        }


class SidecarWriteResult(PregameContract):
    evidence_id: str
    path: str
    status: SidecarWriteStatus
    digest: str
    warnings: tuple[str, ...] = ()


def evidence_id_for_payload(evidence: VariantBGptEvidenceSidecar | dict[str, Any]) -> str:
    if isinstance(evidence, VariantBGptEvidenceSidecar):
        value = evidence.to_json_dict()
    else:
        temporary = dict(evidence)
        temporary["evidence_id"] = "temporary"
        value = VariantBGptEvidenceSidecar.model_validate(
            temporary, context={"skip_evidence_id_check": True}
        ).to_json_dict()
    for field in ("evidence_id", "recorded_at_utc", "source_ref"):
        value.pop(field, None)
    canonical = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return f"variant-b-gpt-evidence:{hashlib.sha256(canonical.encode()).hexdigest()}"


def validate_variant_b_evidence(payload: dict[str, Any]) -> VariantBGptEvidenceSidecar:
    return VariantBGptEvidenceSidecar.model_validate(payload)


def load_variant_b_evidence(path: Path) -> VariantBGptEvidenceSidecar:
    return validate_variant_b_evidence(json.loads(Path(path).read_text(encoding="utf-8")))


def write_variant_b_evidence_sidecar(
    evidence: VariantBGptEvidenceSidecar, *, output_root: Path
) -> SidecarWriteResult:
    root = Path(output_root).resolve()
    target = (
        root
        / str(evidence.season)
        / f"week_{evidence.week:02d}"
        / evidence.candidate_id
        / f"{evidence.evidence_id.replace(':', '_')}.json"
    ).resolve()
    if root not in target.parents:
        raise ValueError("sidecar path escapes output_root")
    data = json.dumps(evidence.to_json_dict(), indent=2, sort_keys=True, ensure_ascii=True) + "\n"
    digest = hashlib.sha256(data.encode()).hexdigest()
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        existing = target.read_text(encoding="utf-8")
        status = (
            SidecarWriteStatus.ALREADY_EXISTS if existing == data else SidecarWriteStatus.CONFLICT
        )
        return SidecarWriteResult(
            evidence_id=evidence.evidence_id, path=str(target), status=status, digest=digest
        )
    temp = target.with_suffix(".tmp")
    with temp.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temp, target)
    return SidecarWriteResult(
        evidence_id=evidence.evidence_id,
        path=str(target),
        status=SidecarWriteStatus.WRITTEN,
        digest=digest,
    )
