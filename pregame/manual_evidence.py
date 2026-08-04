"""Central registration for factual manual pregame evidence only."""

from __future__ import annotations

from dataclasses import dataclass

from pydantic import ValidationError

from pregame.candidate_registry import CandidateRegistryService
from pregame.contracts import (
    PregameEvent,
    PregameGameRecord,
    PublicBettingObservationPayload,
    StructuredManualEvidenceRecord,
)
from pregame.events import PregameEventType
from pregame.market_history import MarketSnapshotHistoryService
from pregame.projector import project_game
from pregame.store import AppendResult, AppendStatus, PregameEventStore

_EVENT_TYPE = PregameEventType.STRUCTURED_MANUAL_EVIDENCE_RECORDED


class StructuredManualEvidenceError(ValueError):
    """Raised when one factual observation cannot be safely registered."""


@dataclass(frozen=True)
class StructuredManualEvidenceRegistrationResult:
    observation_id: str
    event_id: str
    game_id: str
    category: str
    append_result: AppendResult
    projected_game: PregameGameRecord


def structured_manual_evidence_event_id(observation_id: str) -> str:
    """Return the deterministic event ID for an explicit observation identity."""

    if not observation_id or not observation_id.strip():
        raise ValueError("observation_id must not be empty")
    return f"structured-manual-evidence:{observation_id}"


class StructuredManualEvidenceRegistryService:
    """Append exactly one validated factual manual observation at a time."""

    def __init__(
        self,
        *,
        store: PregameEventStore,
        candidates: CandidateRegistryService,
        market_history: MarketSnapshotHistoryService,
    ) -> None:
        self._store = store
        self._candidates = candidates
        self._market_history = market_history

    def record(
        self, *, observation: StructuredManualEvidenceRecord
    ) -> StructuredManualEvidenceRegistrationResult:
        event_id = structured_manual_evidence_event_id(observation.observation_id)
        existing = self._store.get_event(event_id)
        if existing is not None:
            existing_observation = self._observation_from_event(existing)
            if existing_observation.to_json_dict() == observation.to_json_dict():
                append_result = AppendResult(
                    AppendStatus.ALREADY_EXISTS, event_id, "Identical manual evidence exists."
                )
            else:
                append_result = AppendResult(
                    AppendStatus.CONFLICT,
                    event_id,
                    "observation_id already exists with different content.",
                )
            return self._result(observation, append_result)

        self._validate_candidate_link(observation)
        self._validate_market_snapshot_link(observation)
        self._validate_supersession(observation)

        event = PregameEvent(
            event_id=event_id,
            game_id=observation.game_id,
            event_type=_EVENT_TYPE,
            created_at_utc=observation.recorded_at_utc,
            effective_at_utc=observation.effective_at_utc or observation.observed_at_utc,
            source=observation.source_name,
            idempotency_key=f"structured-manual-evidence:{observation.observation_id}",
            payload=observation.to_json_dict(),
        )
        append_result = self._store.append(event)
        return self._result(observation, append_result)

    def _result(
        self, observation: StructuredManualEvidenceRecord, append_result: AppendResult
    ) -> StructuredManualEvidenceRegistrationResult:
        projected = project_game(self._store, observation.game_id)
        if projected is None:
            raise StructuredManualEvidenceError("manual evidence event was not projectable")
        return StructuredManualEvidenceRegistrationResult(
            observation_id=observation.observation_id,
            event_id=append_result.event_id,
            game_id=observation.game_id,
            category=observation.category.value,
            append_result=append_result,
            projected_game=projected,
        )

    def _validate_candidate_link(self, observation: StructuredManualEvidenceRecord) -> None:
        if observation.candidate_id is None:
            return
        candidate = self._candidates.get_candidate(observation.candidate_id)
        if candidate is None:
            raise StructuredManualEvidenceError("candidate_id was not found")
        if candidate.game_id != observation.game_id:
            raise StructuredManualEvidenceError("candidate_id belongs to another game")

    def _validate_market_snapshot_link(self, observation: StructuredManualEvidenceRecord) -> None:
        payload = observation.payload
        if (
            not isinstance(payload, PublicBettingObservationPayload)
            or not payload.market_snapshot_id
        ):
            return
        snapshot = self._market_history.get_snapshot(payload.market_snapshot_id)
        if snapshot is None:
            raise StructuredManualEvidenceError("market_snapshot_id was not found")
        if snapshot.game_id != observation.game_id:
            raise StructuredManualEvidenceError("market_snapshot_id belongs to another game")
        if snapshot.market_type != payload.market_type:
            raise StructuredManualEvidenceError("market snapshot market_type mismatch")
        if snapshot.selected_side is not None and snapshot.selected_side != payload.selected_side:
            raise StructuredManualEvidenceError("market snapshot selected_side mismatch")

    def _validate_supersession(self, observation: StructuredManualEvidenceRecord) -> None:
        previous_id = observation.supersedes_observation_id
        if previous_id is None:
            return
        prior = self._find_observation(previous_id)
        if prior is None:
            raise StructuredManualEvidenceError("supersedes_observation_id was not found")
        if prior.game_id != observation.game_id:
            raise StructuredManualEvidenceError("supersession crosses games")
        if prior.category != observation.category:
            raise StructuredManualEvidenceError("supersession crosses categories")
        if prior.subject_key != observation.subject_key:
            raise StructuredManualEvidenceError("supersession crosses subjects")
        if prior.source_name != observation.source_name:
            raise StructuredManualEvidenceError("supersession crosses sources")
        for candidate in self._list_observations(observation.game_id):
            if candidate.supersedes_observation_id == previous_id:
                raise StructuredManualEvidenceError("superseded observation is already superseded")

    def _find_observation(self, observation_id: str) -> StructuredManualEvidenceRecord | None:
        event = self._store.get_event(structured_manual_evidence_event_id(observation_id))
        return None if event is None else self._observation_from_event(event)

    def _list_observations(self, game_id: str) -> list[StructuredManualEvidenceRecord]:
        return [
            self._observation_from_event(event)
            for event in self._store.list_events(game_id)
            if event.event_type == _EVENT_TYPE
        ]

    @staticmethod
    def _observation_from_event(event: PregameEvent) -> StructuredManualEvidenceRecord:
        if event.event_type != _EVENT_TYPE:
            raise StructuredManualEvidenceError("event is not structured manual evidence")
        try:
            observation = StructuredManualEvidenceRecord.model_validate(event.payload)
        except ValidationError as exc:
            raise StructuredManualEvidenceError("invalid manual evidence payload") from exc
        if observation.game_id != event.game_id:
            raise StructuredManualEvidenceError("manual evidence payload game mismatch")
        if event.event_id != structured_manual_evidence_event_id(observation.observation_id):
            raise StructuredManualEvidenceError("manual evidence event_id mismatch")
        if event.created_at_utc != observation.recorded_at_utc:
            raise StructuredManualEvidenceError("manual evidence recorded timestamp mismatch")
        expected_effective = observation.effective_at_utc or observation.observed_at_utc
        if event.effective_at_utc != expected_effective:
            raise StructuredManualEvidenceError("manual evidence effective timestamp mismatch")
        return observation.model_copy(deep=True)
