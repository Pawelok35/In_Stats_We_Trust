"""Append-only registry and read model for weekly model candidates."""

from __future__ import annotations

from datetime import datetime, timedelta

from pydantic import ValidationError

from pregame.contracts import CandidateRecord, PregameEvent
from pregame.events import CandidateStatus, PregameEventType
from pregame.store import AppendResult, AppendStatus, PregameEventStore

_STATUS_TO_EVENT_TYPE = {
    CandidateStatus.MODEL_CANDIDATE: PregameEventType.MODEL_CANDIDATE_CREATED,
    CandidateStatus.BLOCKED: PregameEventType.MODEL_CANDIDATE_BLOCKED,
    CandidateStatus.MISSING_DATA: PregameEventType.MODEL_CANDIDATE_BLOCKED,
}
_CANDIDATE_EVENT_TYPES = frozenset(_STATUS_TO_EVENT_TYPE.values())


class CandidateRegistryError(ValueError):
    """Raised for domain-inconsistent candidate events or registry records."""

    def __init__(
        self, reason: str, *, game_id: str | None = None, candidate_id: str | None = None
    ) -> None:
        self.reason = reason
        self.game_id = game_id
        self.candidate_id = candidate_id
        scope = f"game_id={game_id}, candidate_id={candidate_id}"
        super().__init__(f"Candidate registry error ({scope}): {reason}")


def candidate_record_event_id(candidate_id: str) -> str:
    """Return the deterministic event ID for a candidate record."""

    if not candidate_id or not candidate_id.strip():
        raise ValueError("candidate_id must not be empty")
    return f"candidate-record:{candidate_id}"


class CandidateRegistryService:
    """Store and query raw model candidate history without operator semantics."""

    def __init__(self, store: PregameEventStore) -> None:
        self._store = store

    def preflight_candidate(self, candidate: CandidateRecord) -> AppendResult:
        """Classify a candidate append without modifying the event store."""

        event_id = candidate_record_event_id(candidate.candidate_id)
        existing = self._store.get_event(event_id)
        if existing is None:
            return AppendResult(status=AppendStatus.APPENDED, event_id=event_id)
        existing_candidate = self._candidate_from_event(existing)
        if _semantic_candidate(existing_candidate) == _semantic_candidate(candidate):
            return AppendResult(
                status=AppendStatus.ALREADY_EXISTS,
                event_id=event_id,
                message="Identical candidate already exists.",
            )
        return AppendResult(
            status=AppendStatus.CONFLICT,
            event_id=event_id,
            message="candidate_id already exists with different content.",
        )

    def record_candidate(
        self,
        candidate: CandidateRecord,
        *,
        recorded_at_utc: datetime,
    ) -> AppendResult:
        """Append a model candidate event, idempotently by candidate_id."""

        _require_utc(recorded_at_utc)
        preflight = self.preflight_candidate(candidate)
        if preflight.status != AppendStatus.APPENDED:
            return preflight
        event = PregameEvent(
            event_id=preflight.event_id,
            game_id=candidate.game_id,
            event_type=_event_type_for_status(candidate.status),
            created_at_utc=recorded_at_utc,
            effective_at_utc=candidate.model_generated_at_utc or recorded_at_utc,
            source="matchup_batch",
            idempotency_key=f"candidate-record:{candidate.candidate_id}",
            payload=candidate.to_json_dict(),
        )
        return self._store.append(event)

    def get_candidate(self, candidate_id: str) -> CandidateRecord | None:
        event = self._store.get_event(candidate_record_event_id(candidate_id))
        if event is None:
            return None
        return self._candidate_from_event(event)

    def list_candidates(
        self,
        season: int,
        week: int,
        *,
        model_variant: str | None = None,
        status: CandidateStatus | None = None,
        game_id: str | None = None,
    ) -> list[CandidateRecord]:
        """Return complete raw candidate history matching the supplied filters."""

        candidates: list[CandidateRecord] = []
        for event in self._store.list_all_events():
            if event.event_type not in _CANDIDATE_EVENT_TYPES:
                continue
            candidate = self._candidate_from_event(event)
            if candidate.season != season or candidate.week != week:
                continue
            if model_variant is not None and candidate.model_variant != model_variant:
                continue
            if status is not None and candidate.status != status:
                continue
            if game_id is not None and candidate.game_id != game_id:
                continue
            candidates.append(candidate)
        candidates.sort(
            key=lambda candidate: (
                candidate.model_generated_at_utc or candidate.created_at_utc,
                candidate.created_at_utc,
                candidate.candidate_id,
            )
        )
        return [candidate.model_copy(deep=True) for candidate in candidates]

    def get_latest_candidate(self, game_id: str, *, model_variant: str) -> CandidateRecord | None:
        """Return the latest candidate version for one game and model variant."""

        candidates = self.list_candidates_for_game(game_id, model_variant=model_variant)
        return candidates[-1] if candidates else None

    def list_candidates_for_game(
        self, game_id: str, *, model_variant: str
    ) -> list[CandidateRecord]:
        candidates = []
        for event in self._store.list_all_events():
            if event.game_id != game_id or event.event_type not in _CANDIDATE_EVENT_TYPES:
                continue
            candidate = self._candidate_from_event(event)
            if candidate.model_variant == model_variant:
                candidates.append(candidate)
        candidates.sort(
            key=lambda candidate: (
                candidate.model_generated_at_utc or candidate.created_at_utc,
                candidate.created_at_utc,
                candidate.candidate_id,
            )
        )
        return candidates

    @staticmethod
    def _candidate_from_event(event: PregameEvent) -> CandidateRecord:
        if event.event_type not in _CANDIDATE_EVENT_TYPES:
            raise CandidateRegistryError(
                "event_type is not a candidate event",
                game_id=event.game_id,
            )
        try:
            candidate = CandidateRecord.model_validate(event.payload)
        except ValidationError as exc:
            raise CandidateRegistryError(
                f"invalid CandidateRecord payload: {exc.errors()[0]['msg']}",
                game_id=event.game_id,
            ) from exc
        if candidate.game_id != event.game_id:
            raise CandidateRegistryError(
                "payload game_id does not match event game_id",
                game_id=event.game_id,
                candidate_id=candidate.candidate_id,
            )
        if event.event_id != candidate_record_event_id(candidate.candidate_id):
            raise CandidateRegistryError(
                "event_id does not match candidate_id",
                game_id=event.game_id,
                candidate_id=candidate.candidate_id,
            )
        if event.event_type != _event_type_for_status(candidate.status):
            raise CandidateRegistryError(
                "event_type does not match candidate status",
                game_id=event.game_id,
                candidate_id=candidate.candidate_id,
            )
        expected_effective_at = candidate.model_generated_at_utc or event.created_at_utc
        if event.effective_at_utc != expected_effective_at:
            raise CandidateRegistryError(
                "effective_at_utc does not match candidate model timestamp",
                game_id=event.game_id,
                candidate_id=candidate.candidate_id,
            )
        return candidate.model_copy(deep=True)


def _event_type_for_status(status: CandidateStatus) -> PregameEventType:
    try:
        return _STATUS_TO_EVENT_TYPE[status]
    except KeyError as exc:
        raise CandidateRegistryError(f"unsupported candidate status {status.value}") from exc


def _semantic_candidate(candidate: CandidateRecord) -> dict:
    payload = candidate.to_json_dict()
    payload.pop("created_at_utc")
    payload.pop("source_ref")
    payload.pop("source_record_number")
    return payload


def _require_utc(value: datetime) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("recorded_at_utc must be timezone-aware")
    if value.utcoffset() != timedelta(0):
        raise ValueError("recorded_at_utc must be in UTC")
