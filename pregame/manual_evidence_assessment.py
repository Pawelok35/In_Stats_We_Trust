"""Central registration for assessments of explicit manual-evidence observations."""

from __future__ import annotations

from dataclasses import dataclass

from pydantic import ValidationError

from pregame.candidate_registry import CandidateRegistryService
from pregame.contracts import (
    PregameEvent,
    PregameGameRecord,
    StructuredManualEvidenceAssessmentRecord,
    StructuredManualEvidenceRecord,
)
from pregame.events import PregameEventType
from pregame.projector import project_game
from pregame.store import AppendResult, AppendStatus, PregameEventStore

_EVENT_TYPE = PregameEventType.STRUCTURED_MANUAL_EVIDENCE_ASSESSMENT_RECORDED
_OBSERVATION_EVENT_TYPE = PregameEventType.STRUCTURED_MANUAL_EVIDENCE_RECORDED


class StructuredManualEvidenceAssessmentError(ValueError):
    """Raised when an assessment cannot be safely registered."""


@dataclass(frozen=True)
class StructuredManualEvidenceAssessmentRegistrationResult:
    assessment_id: str
    event_id: str
    game_id: str
    category: str
    candidate_id: str | None
    append_result: AppendResult
    projected_game: PregameGameRecord


def structured_manual_evidence_assessment_event_id(assessment_id: str) -> str:
    """Return the deterministic event ID for an explicit assessment identity."""

    if not assessment_id or not assessment_id.strip():
        raise ValueError("assessment_id must not be empty")
    return f"structured-manual-evidence-assessment:{assessment_id}"


class StructuredManualEvidenceAssessmentRegistryService:
    """Append one factual-evidence assessment without producing other workflows."""

    def __init__(self, *, store: PregameEventStore, candidates: CandidateRegistryService) -> None:
        self._store = store
        self._candidates = candidates

    def record(
        self, *, assessment: StructuredManualEvidenceAssessmentRecord
    ) -> StructuredManualEvidenceAssessmentRegistrationResult:
        event_id = structured_manual_evidence_assessment_event_id(assessment.assessment_id)
        existing = self._store.get_event(event_id)
        if existing is not None:
            existing_assessment = self._assessment_from_event(existing)
            if existing_assessment.to_json_dict() == assessment.to_json_dict():
                return self._result(
                    assessment,
                    AppendResult(
                        AppendStatus.ALREADY_EXISTS,
                        event_id,
                        "Identical evidence assessment exists.",
                    ),
                )
            return self._result(
                assessment,
                AppendResult(
                    AppendStatus.CONFLICT,
                    event_id,
                    "assessment_id already exists with different content.",
                ),
            )

        self._validate_candidate_link(assessment)
        observations = self._validate_observations(assessment)
        self._validate_active_as_of(assessment, observations)
        self._validate_supersession(assessment)

        event = PregameEvent(
            event_id=event_id,
            game_id=assessment.game_id,
            event_type=_EVENT_TYPE,
            created_at_utc=assessment.recorded_at_utc,
            effective_at_utc=assessment.as_of_utc,
            source=assessment.assessor.assessor_id,
            idempotency_key=f"structured-manual-evidence-assessment:{assessment.assessment_id}",
            payload=assessment.to_json_dict(),
        )
        return self._result(assessment, self._store.append(event))

    def _result(
        self, assessment: StructuredManualEvidenceAssessmentRecord, append_result: AppendResult
    ) -> StructuredManualEvidenceAssessmentRegistrationResult:
        projected = project_game(self._store, assessment.game_id)
        if projected is None:
            raise StructuredManualEvidenceAssessmentError("assessment event was not projectable")
        return StructuredManualEvidenceAssessmentRegistrationResult(
            assessment_id=assessment.assessment_id,
            event_id=append_result.event_id,
            game_id=assessment.game_id,
            category=assessment.category.value,
            candidate_id=assessment.candidate_id,
            append_result=append_result,
            projected_game=projected,
        )

    def _validate_candidate_link(
        self, assessment: StructuredManualEvidenceAssessmentRecord
    ) -> None:
        if assessment.candidate_id is None:
            return
        candidate = self._candidates.get_candidate(assessment.candidate_id)
        if candidate is None:
            raise StructuredManualEvidenceAssessmentError("candidate_id was not found")
        if candidate.game_id != assessment.game_id:
            raise StructuredManualEvidenceAssessmentError("candidate_id belongs to another game")

    def _validate_observations(
        self, assessment: StructuredManualEvidenceAssessmentRecord
    ) -> list[StructuredManualEvidenceRecord]:
        observations: list[StructuredManualEvidenceRecord] = []
        for observation_id in assessment.observation_ids:
            event = self._store.get_event(f"structured-manual-evidence:{observation_id}")
            if event is None:
                raise StructuredManualEvidenceAssessmentError("observation_id was not found")
            observation = self._observation_from_event(event)
            if observation.game_id != assessment.game_id:
                raise StructuredManualEvidenceAssessmentError("observation belongs to another game")
            if observation.category != assessment.category:
                raise StructuredManualEvidenceAssessmentError(
                    "observation belongs to another category"
                )
            observation_effective = observation.effective_at_utc or observation.observed_at_utc
            if observation_effective > assessment.as_of_utc:
                raise StructuredManualEvidenceAssessmentError(
                    "observation is effective after assessment as_of"
                )
            if observation.recorded_at_utc > assessment.recorded_at_utc:
                raise StructuredManualEvidenceAssessmentError(
                    "observation was recorded after assessment"
                )
            observations.append(observation)
        return observations

    def _validate_active_as_of(
        self,
        assessment: StructuredManualEvidenceAssessmentRecord,
        observations: list[StructuredManualEvidenceRecord],
    ) -> None:
        replacements = self._list_observations(assessment.game_id)
        for observation in observations:
            for replacement in replacements:
                replacement_effective = replacement.effective_at_utc or replacement.observed_at_utc
                if (
                    replacement.supersedes_observation_id == observation.observation_id
                    and replacement_effective <= assessment.as_of_utc
                    and replacement.recorded_at_utc <= assessment.recorded_at_utc
                ):
                    raise StructuredManualEvidenceAssessmentError(
                        "observation was superseded at assessment as_of"
                    )

    def _validate_supersession(self, assessment: StructuredManualEvidenceAssessmentRecord) -> None:
        prior_id = assessment.supersedes_assessment_id
        if prior_id is None:
            return
        prior = self._find_assessment(prior_id)
        if prior is None:
            raise StructuredManualEvidenceAssessmentError("supersedes_assessment_id was not found")
        if prior.game_id != assessment.game_id:
            raise StructuredManualEvidenceAssessmentError("assessment supersession crosses games")
        if prior.category != assessment.category:
            raise StructuredManualEvidenceAssessmentError(
                "assessment supersession crosses categories"
            )
        if prior.candidate_id != assessment.candidate_id:
            raise StructuredManualEvidenceAssessmentError(
                "assessment supersession crosses candidates"
            )
        if prior.assessment_scope != assessment.assessment_scope:
            raise StructuredManualEvidenceAssessmentError("assessment supersession crosses scopes")
        if prior.assessor_type != assessment.assessor_type:
            raise StructuredManualEvidenceAssessmentError(
                "assessment supersession crosses assessor types"
            )
        if prior.assessor.assessor_id != assessment.assessor.assessor_id:
            raise StructuredManualEvidenceAssessmentError(
                "assessment supersession crosses assessor IDs"
            )
        if (
            assessment.as_of_utc < prior.as_of_utc
            or assessment.assessed_at_utc < prior.assessed_at_utc
            or assessment.recorded_at_utc < prior.recorded_at_utc
        ):
            raise StructuredManualEvidenceAssessmentError(
                "assessment supersession regresses chronology"
            )
        for existing in self._list_assessments(assessment.game_id):
            if existing.supersedes_assessment_id == prior_id:
                raise StructuredManualEvidenceAssessmentError(
                    "superseded assessment is already superseded"
                )

    def _find_assessment(
        self, assessment_id: str
    ) -> StructuredManualEvidenceAssessmentRecord | None:
        event = self._store.get_event(structured_manual_evidence_assessment_event_id(assessment_id))
        return None if event is None else self._assessment_from_event(event)

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
            if event.event_type == _EVENT_TYPE
        ]

    @staticmethod
    def _observation_from_event(event: PregameEvent) -> StructuredManualEvidenceRecord:
        if event.event_type != _OBSERVATION_EVENT_TYPE:
            raise StructuredManualEvidenceAssessmentError("event is not structured manual evidence")
        try:
            observation = StructuredManualEvidenceRecord.model_validate(event.payload)
        except ValidationError as exc:
            raise StructuredManualEvidenceAssessmentError(
                "invalid manual evidence payload"
            ) from exc
        return observation.model_copy(deep=True)

    @staticmethod
    def _assessment_from_event(event: PregameEvent) -> StructuredManualEvidenceAssessmentRecord:
        if event.event_type != _EVENT_TYPE:
            raise StructuredManualEvidenceAssessmentError(
                "event is not structured evidence assessment"
            )
        try:
            assessment = StructuredManualEvidenceAssessmentRecord.model_validate(event.payload)
        except ValidationError as exc:
            raise StructuredManualEvidenceAssessmentError(
                "invalid evidence assessment payload"
            ) from exc
        if assessment.game_id != event.game_id:
            raise StructuredManualEvidenceAssessmentError("assessment payload game mismatch")
        if event.event_id != structured_manual_evidence_assessment_event_id(
            assessment.assessment_id
        ):
            raise StructuredManualEvidenceAssessmentError("assessment event_id mismatch")
        if event.created_at_utc != assessment.recorded_at_utc:
            raise StructuredManualEvidenceAssessmentError("assessment recorded timestamp mismatch")
        if event.effective_at_utc != assessment.as_of_utc:
            raise StructuredManualEvidenceAssessmentError("assessment as_of timestamp mismatch")
        return assessment.model_copy(deep=True)
