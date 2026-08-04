"""Registration of immutable external lineage for one Variant B evidence sidecar."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from pregame.candidate_registry import CandidateRegistryService
from pregame.contracts import (
    PregameEvent,
    PregameGameRecord,
    StructuredManualEvidenceAssessmentRecord,
    StructuredManualEvidenceRecord,
    VariantBEvidenceLineageManifestRecord,
)
from pregame.events import (
    PregameEventType,
    StructuredManualEvidenceAssessmentStatus,
)
from pregame.projector import project_game
from pregame.store import AppendResult, AppendStatus, PregameEventStore
from pregame.variant_b_audit_integration import _sha256
from pregame.variant_b_evidence import evidence_id_for_payload, load_variant_b_evidence

_EVENT_TYPE = PregameEventType.VARIANT_B_EVIDENCE_LINEAGE_RECORDED
_OBSERVATION_EVENT_TYPE = PregameEventType.STRUCTURED_MANUAL_EVIDENCE_RECORDED
_ASSESSMENT_EVENT_TYPE = PregameEventType.STRUCTURED_MANUAL_EVIDENCE_ASSESSMENT_RECORDED


class VariantBEvidenceLineageError(ValueError):
    """Raised when one immutable evidence-lineage manifest is invalid."""


@dataclass(frozen=True)
class VariantBEvidenceLineageRegistrationResult:
    manifest_id: str
    evidence_id: str
    event_id: str
    candidate_id: str
    game_id: str
    evidence_sidecar_digest: str
    append_result: AppendResult
    projected_game: PregameGameRecord


def variant_b_evidence_lineage_manifest_id(
    *,
    evidence_id: str,
    candidate_id: str,
    game_id: str,
    audit_stage: str,
    observation_ids: tuple[str, ...],
    assessment_ids: tuple[str, ...],
    evidence_sidecar_digest: str,
    schema_version: str,
) -> str:
    """Build the deterministic manifest identity from canonical lineage fields."""

    identity = {
        "evidence_id": evidence_id,
        "candidate_id": candidate_id,
        "game_id": game_id,
        "audit_stage": audit_stage,
        "observation_ids": list(observation_ids),
        "assessment_ids": list(assessment_ids),
        "evidence_sidecar_digest": evidence_sidecar_digest,
        "schema_version": schema_version,
    }
    return f"variant-b-evidence-lineage:{_sha256(identity)}"


def variant_b_evidence_lineage_event_id(evidence_id: str) -> str:
    """Return the one central event ID reserved for an evidence identity."""

    if not evidence_id or not evidence_id.strip():
        raise ValueError("evidence_id must not be empty")
    return f"variant-b-evidence-lineage:{evidence_id}"


class VariantBEvidenceLineageRegistryService:
    """Record one manifest using official sidecar loading and explicit IDs only."""

    def __init__(self, *, store: PregameEventStore, candidates: CandidateRegistryService) -> None:
        self._store = store
        self._candidates = candidates

    def record(
        self, *, manifest: VariantBEvidenceLineageManifestRecord, evidence_path: Path
    ) -> VariantBEvidenceLineageRegistrationResult:
        sidecar = self._load_sidecar(evidence_path)
        self._validate_sidecar(manifest, sidecar)

        event_id = variant_b_evidence_lineage_event_id(manifest.evidence_id)
        existing = self._store.get_event(event_id)
        if existing is not None:
            existing_manifest = self._manifest_from_event(existing)
            status = (
                AppendStatus.ALREADY_EXISTS
                if existing_manifest.to_json_dict() == manifest.to_json_dict()
                else AppendStatus.CONFLICT
            )
            message = (
                "Identical evidence lineage exists."
                if status == AppendStatus.ALREADY_EXISTS
                else "evidence_id already exists with different lineage."
            )
            return self._result(manifest, AppendResult(status, event_id, message))

        self._validate_candidate_and_sidecar(manifest, sidecar)
        observations = self._validate_observations(manifest)
        assessments = self._validate_assessments(manifest)
        self._validate_assessment_observation_consistency(manifest, observations, assessments)
        self._validate_as_of(manifest, observations, assessments)
        self._validate_manifest_id(manifest)

        event = PregameEvent(
            event_id=event_id,
            game_id=manifest.game_id,
            event_type=_EVENT_TYPE,
            created_at_utc=manifest.recorded_at_utc,
            effective_at_utc=manifest.prepared_at_utc,
            source=manifest.preparer_id or "variant_b_evidence_lineage",
            idempotency_key=f"variant-b-evidence-lineage:{manifest.evidence_id}",
            payload=manifest.to_json_dict(),
        )
        return self._result(manifest, self._store.append(event))

    def _result(
        self, manifest: VariantBEvidenceLineageManifestRecord, append_result: AppendResult
    ) -> VariantBEvidenceLineageRegistrationResult:
        projected = project_game(self._store, manifest.game_id)
        if projected is None:
            raise VariantBEvidenceLineageError("lineage manifest event was not projectable")
        return VariantBEvidenceLineageRegistrationResult(
            manifest_id=manifest.manifest_id,
            evidence_id=manifest.evidence_id,
            event_id=append_result.event_id,
            candidate_id=manifest.candidate_id,
            game_id=manifest.game_id,
            evidence_sidecar_digest=manifest.evidence_sidecar_digest,
            append_result=append_result,
            projected_game=projected,
        )

    @staticmethod
    def _load_sidecar(evidence_path: Path):
        try:
            return load_variant_b_evidence(Path(evidence_path))
        except (OSError, ValueError) as exc:
            raise VariantBEvidenceLineageError(f"sidecar load failed: {exc}") from exc

    @staticmethod
    def _validate_sidecar(manifest: VariantBEvidenceLineageManifestRecord, sidecar: Any) -> None:
        evidence_id = evidence_id_for_payload(sidecar)
        digest = _sha256(sidecar.to_json_dict())
        if manifest.evidence_id != sidecar.evidence_id or sidecar.evidence_id != evidence_id:
            raise VariantBEvidenceLineageError(
                "manifest evidence_id does not match official sidecar"
            )
        if manifest.evidence_sidecar_digest != digest:
            raise VariantBEvidenceLineageError("manifest sidecar digest does not match Stage 11.2")

    def _validate_candidate_and_sidecar(self, manifest, sidecar) -> None:
        candidate = self._candidates.get_candidate(manifest.candidate_id)
        if candidate is None:
            raise VariantBEvidenceLineageError("candidate_id was not found")
        if candidate.game_id != manifest.game_id:
            raise VariantBEvidenceLineageError("candidate_id belongs to another game")
        expected = {
            "candidate_id": candidate.candidate_id,
            "game_id": candidate.game_id,
            "season": candidate.season,
            "week": candidate.week,
            "away_team": candidate.away,
            "home_team": candidate.home,
            "selected_team": candidate.selected_team,
            "model_variant": candidate.model_variant,
        }
        actual = {key: getattr(sidecar, key) for key in expected}
        if actual != expected:
            raise VariantBEvidenceLineageError("sidecar identity does not match candidate")

    def _validate_observations(
        self, manifest: VariantBEvidenceLineageManifestRecord
    ) -> list[StructuredManualEvidenceRecord]:
        records: list[StructuredManualEvidenceRecord] = []
        for observation_id in manifest.observation_ids:
            event = self._store.get_event(f"structured-manual-evidence:{observation_id}")
            if event is None:
                raise VariantBEvidenceLineageError("observation_id was not found")
            observation = self._observation_from_event(event)
            if observation.game_id != manifest.game_id:
                raise VariantBEvidenceLineageError("observation belongs to another game")
            if observation.candidate_id not in {None, manifest.candidate_id}:
                raise VariantBEvidenceLineageError("observation candidate_id mismatch")
            records.append(observation)
        return records

    def _validate_assessments(
        self, manifest: VariantBEvidenceLineageManifestRecord
    ) -> list[StructuredManualEvidenceAssessmentRecord]:
        records: list[StructuredManualEvidenceAssessmentRecord] = []
        for assessment_id in manifest.assessment_ids:
            event = self._store.get_event(f"structured-manual-evidence-assessment:{assessment_id}")
            if event is None:
                raise VariantBEvidenceLineageError("assessment_id was not found")
            assessment = self._assessment_from_event(event)
            if assessment.game_id != manifest.game_id:
                raise VariantBEvidenceLineageError("assessment belongs to another game")
            if assessment.candidate_id not in {None, manifest.candidate_id}:
                raise VariantBEvidenceLineageError("assessment candidate_id mismatch")
            records.append(assessment)
        if not manifest.observation_ids and any(
            item.status
            not in {
                StructuredManualEvidenceAssessmentStatus.NO_DATA,
                StructuredManualEvidenceAssessmentStatus.NOT_DUE,
            }
            for item in records
        ):
            raise VariantBEvidenceLineageError(
                "non-empty evidence assessment requires observations"
            )
        return records

    @staticmethod
    def _validate_assessment_observation_consistency(
        manifest: VariantBEvidenceLineageManifestRecord,
        observations: list[StructuredManualEvidenceRecord],
        assessments: list[StructuredManualEvidenceAssessmentRecord],
    ) -> None:
        known = set(manifest.observation_ids)
        by_id = {observation.observation_id: observation for observation in observations}
        for assessment in assessments:
            if not set(assessment.observation_ids).issubset(known):
                raise VariantBEvidenceLineageError(
                    "assessment references observation outside manifest"
                )
            if any(
                by_id[observation_id].category != assessment.category
                for observation_id in assessment.observation_ids
            ):
                raise VariantBEvidenceLineageError("assessment observation category mismatch")

    def _validate_as_of(self, manifest, observations, assessments) -> None:
        all_observations = self._list_observations(manifest.game_id)
        for observation in observations:
            effective = observation.effective_at_utc or observation.observed_at_utc
            if effective > manifest.prepared_at_utc:
                raise VariantBEvidenceLineageError(
                    "observation is effective after manifest preparation"
                )
            if observation.recorded_at_utc > manifest.recorded_at_utc:
                raise VariantBEvidenceLineageError("observation was recorded after manifest")
            self._require_observation_active_as_of(manifest, observation, all_observations)
        all_assessments = self._list_assessments(manifest.game_id)
        for assessment in assessments:
            if assessment.as_of_utc > manifest.prepared_at_utc:
                raise VariantBEvidenceLineageError("assessment as_of is after manifest preparation")
            if assessment.assessed_at_utc > manifest.prepared_at_utc:
                raise VariantBEvidenceLineageError("assessment is after manifest preparation")
            if assessment.recorded_at_utc > manifest.recorded_at_utc:
                raise VariantBEvidenceLineageError("assessment was recorded after manifest")
            self._require_assessment_active_as_of(manifest, assessment, all_assessments)

    @staticmethod
    def _require_observation_active_as_of(manifest, observation, observations) -> None:
        for replacement in observations:
            effective = replacement.effective_at_utc or replacement.observed_at_utc
            if (
                replacement.supersedes_observation_id == observation.observation_id
                and effective <= manifest.prepared_at_utc
                and replacement.recorded_at_utc <= manifest.recorded_at_utc
            ):
                raise VariantBEvidenceLineageError(
                    "observation was superseded at manifest preparation"
                )

    @staticmethod
    def _require_assessment_active_as_of(manifest, assessment, assessments) -> None:
        for replacement in assessments:
            if (
                replacement.supersedes_assessment_id == assessment.assessment_id
                and replacement.as_of_utc <= manifest.prepared_at_utc
                and replacement.recorded_at_utc <= manifest.recorded_at_utc
            ):
                raise VariantBEvidenceLineageError(
                    "assessment was superseded at manifest preparation"
                )

    @staticmethod
    def _validate_manifest_id(manifest: VariantBEvidenceLineageManifestRecord) -> None:
        expected = variant_b_evidence_lineage_manifest_id(
            evidence_id=manifest.evidence_id,
            candidate_id=manifest.candidate_id,
            game_id=manifest.game_id,
            audit_stage=manifest.audit_stage,
            observation_ids=manifest.observation_ids,
            assessment_ids=manifest.assessment_ids,
            evidence_sidecar_digest=manifest.evidence_sidecar_digest,
            schema_version=manifest.schema_version,
        )
        if manifest.manifest_id != expected:
            raise VariantBEvidenceLineageError(
                "manifest_id does not match canonical lineage identity"
            )

    def _list_observations(self, game_id: str) -> list[StructuredManualEvidenceRecord]:
        return [
            self._observation_from_event(event)
            for event in self._store.list_events(game_id)
            if event.event_type == _OBSERVATION_EVENT_TYPE
        ]

    def _list_assessments(self, game_id: str) -> list[StructuredManualEvidenceAssessmentRecord]:
        return [
            self._assessment_from_event(event)
            for event in self._store.list_events(game_id)
            if event.event_type == _ASSESSMENT_EVENT_TYPE
        ]

    @staticmethod
    def _observation_from_event(event: PregameEvent) -> StructuredManualEvidenceRecord:
        try:
            return StructuredManualEvidenceRecord.model_validate(event.payload).model_copy(
                deep=True
            )
        except ValidationError as exc:
            raise VariantBEvidenceLineageError("invalid manual evidence payload") from exc

    @staticmethod
    def _assessment_from_event(event: PregameEvent) -> StructuredManualEvidenceAssessmentRecord:
        try:
            return StructuredManualEvidenceAssessmentRecord.model_validate(
                event.payload
            ).model_copy(deep=True)
        except ValidationError as exc:
            raise VariantBEvidenceLineageError("invalid evidence assessment payload") from exc

    @staticmethod
    def _manifest_from_event(event: PregameEvent) -> VariantBEvidenceLineageManifestRecord:
        if event.event_type != _EVENT_TYPE:
            raise VariantBEvidenceLineageError("event is not Variant B evidence lineage")
        try:
            manifest = VariantBEvidenceLineageManifestRecord.model_validate(event.payload)
        except ValidationError as exc:
            raise VariantBEvidenceLineageError("invalid evidence lineage payload") from exc
        if event.game_id != manifest.game_id:
            raise VariantBEvidenceLineageError("manifest payload game mismatch")
        if event.event_id != variant_b_evidence_lineage_event_id(manifest.evidence_id):
            raise VariantBEvidenceLineageError("manifest event_id mismatch")
        if event.created_at_utc != manifest.recorded_at_utc:
            raise VariantBEvidenceLineageError("manifest recorded timestamp mismatch")
        if event.effective_at_utc != manifest.prepared_at_utc:
            raise VariantBEvidenceLineageError("manifest prepared timestamp mismatch")
        return manifest.model_copy(deep=True)
