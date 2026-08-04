"""Central one-game orchestration for the accepted Stage 11.2 audit boundary."""

from __future__ import annotations

import hashlib
import json
import tempfile
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from pregame.candidate_registry import CandidateRegistryService
from pregame.contracts import (
    CandidateRecord,
    PregameEvent,
    PregameGameRecord,
    StructuredVariantBAuditResultRecord,
)
from pregame.events import MarketType, PregameEventType
from pregame.market_history import MarketSnapshotHistoryService
from pregame.projector import project_game
from pregame.store import AppendResult, AppendStatus, PregameEventStore
from pregame.variant_b_audit_orchestrator import (
    StructuredVariantBAuditOrchestrationResult,
    StructuredVariantBAuditOrchestrationStatus,
    StructuredVariantBAuditOrchestrator,
)
from pregame.variant_b_evidence import VariantBGptEvidenceSidecar, load_variant_b_evidence
from scripts.variant_b_audit import load_rules_config


class CentralVariantBAuditError(ValueError):
    """Raised for explicit transport, linkage, or event-store failures."""


@dataclass(frozen=True)
class CentralVariantBAuditRunResult:
    """One explicit central audit attempt and its projected one-game state."""

    orchestration_result: StructuredVariantBAuditOrchestrationResult
    central_event_id: str | None
    central_append_result: AppendResult | None
    candidate_id: str
    game_id: str
    evidence_id: str
    model_generation_snapshot_id: str
    projected_game: PregameGameRecord | None


class CentralSingleGameVariantBAuditService:
    """Link one registry candidate to Stage 11.2 and one central audit event."""

    def __init__(
        self,
        *,
        candidates: CandidateRegistryService,
        market_history: MarketSnapshotHistoryService,
        store: PregameEventStore,
        orchestrator: StructuredVariantBAuditOrchestrator | None = None,
    ) -> None:
        self._candidates = candidates
        self._market_history = market_history
        self._store = store
        self._orchestrator = orchestrator or StructuredVariantBAuditOrchestrator()

    def run(
        self,
        *,
        candidate_id: str,
        model_generation_snapshot_id: str,
        evidence_path: Path,
        rules_path: Path,
        build_timestamp_utc: datetime,
        output_path: Path,
        recorded_at_utc: datetime,
    ) -> CentralVariantBAuditRunResult:
        _require_utc(build_timestamp_utc, "build_timestamp_utc")
        _require_utc(recorded_at_utc, "recorded_at_utc")
        candidate = self._require_candidate(candidate_id)
        snapshot = self._require_model_generation_snapshot(candidate, model_generation_snapshot_id)
        evidence = _load_evidence(Path(evidence_path))
        rules_config = _load_rules(Path(rules_path))

        with _temporary_candidate_transport(candidate, output_path) as candidate_path:
            orchestration = self._orchestrator.run(
                candidate_path=candidate_path,
                evidence_path=Path(evidence_path),
                rules_config=rules_config,
                build_timestamp=build_timestamp_utc,
                output_path=Path(output_path),
            )

        if orchestration.status not in {
            StructuredVariantBAuditOrchestrationStatus.WRITTEN,
            StructuredVariantBAuditOrchestrationStatus.ALREADY_EXISTS_IDENTICAL,
            StructuredVariantBAuditOrchestrationStatus.BLOCKED,
        }:
            return _result_without_event(
                orchestration, candidate, evidence, model_generation_snapshot_id, self._store
            )

        record = _central_record(
            candidate=candidate,
            evidence=evidence,
            model_generation_snapshot_id=model_generation_snapshot_id,
            orchestration=orchestration,
            build_timestamp_utc=build_timestamp_utc,
            output_path=Path(output_path),
        )
        event = PregameEvent(
            event_id=record.event_id,
            game_id=candidate.game_id,
            event_type=PregameEventType.STRUCTURED_VARIANT_B_AUDIT_RESULT_RECORDED,
            created_at_utc=recorded_at_utc,
            effective_at_utc=build_timestamp_utc,
            source="central_single_game_variant_b_audit",
            idempotency_key=record.event_id,
            payload=record.to_json_dict(),
        )
        append = self._append_central_event(event)
        if append.status == AppendStatus.CONFLICT:
            raise CentralVariantBAuditError("central audit-result event conflicts with existing ID")
        return CentralVariantBAuditRunResult(
            orchestration_result=orchestration,
            central_event_id=event.event_id,
            central_append_result=append,
            candidate_id=candidate.candidate_id,
            game_id=candidate.game_id,
            evidence_id=evidence.evidence_id,
            model_generation_snapshot_id=snapshot.snapshot_id,
            projected_game=project_game(self._store, candidate.game_id),
        )

    def _append_central_event(self, event: PregameEvent) -> AppendResult:
        existing = self._store.get_event(event.event_id)
        if existing is None:
            return self._store.append(event)
        if existing.event_type != event.event_type or existing.game_id != event.game_id:
            return AppendResult(AppendStatus.CONFLICT, event.event_id, "central event ID conflict")
        existing_record = StructuredVariantBAuditResultRecord.model_validate(existing.payload)
        requested_record = StructuredVariantBAuditResultRecord.model_validate(event.payload)
        if _event_identity(existing_record) != _event_identity(requested_record):
            return AppendResult(
                AppendStatus.CONFLICT, event.event_id, "central event payload conflict"
            )
        return AppendResult(
            AppendStatus.ALREADY_EXISTS, event.event_id, "Equivalent audit event exists."
        )

    def _require_candidate(self, candidate_id: str) -> CandidateRecord:
        candidate = self._candidates.get_candidate(candidate_id)
        if candidate is None:
            raise CentralVariantBAuditError(f"candidate not found: {candidate_id}")
        return candidate

    def _require_model_generation_snapshot(self, candidate: CandidateRecord, snapshot_id: str):
        model_pick = candidate.source_metadata.get("model_pick")
        if not isinstance(model_pick, dict):
            raise CentralVariantBAuditError("candidate model provenance is missing")
        expected_id = model_pick.get("model_generation_quote_id")
        if snapshot_id != expected_id:
            raise CentralVariantBAuditError("snapshot ID does not match candidate quote provenance")
        snapshot = self._market_history.get_snapshot(snapshot_id)
        if snapshot is None:
            raise CentralVariantBAuditError(f"model-generation snapshot not found: {snapshot_id}")
        if snapshot.game_id != candidate.game_id:
            raise CentralVariantBAuditError("model-generation snapshot game mismatch")
        if snapshot.market_type != MarketType.SPREAD:
            raise CentralVariantBAuditError("model-generation snapshot market mismatch")
        expected = {
            "selected_side": candidate.selected_team,
            "spread": model_pick.get("model_generation_spread_selected_team"),
            "spread_price": model_pick.get("model_generation_price"),
            "book": model_pick.get("model_generation_book"),
            "source": model_pick.get("odds_source"),
        }
        actual = {
            "selected_side": snapshot.selected_side,
            "spread": snapshot.spread,
            "spread_price": snapshot.spread_price,
            "book": snapshot.book,
            "source": snapshot.source,
        }
        if actual != expected:
            raise CentralVariantBAuditError(
                "model-generation snapshot values or provenance mismatch"
            )
        expected_timestamp = model_pick.get("model_generation_quote_timestamp_utc")
        if not isinstance(expected_timestamp, str):
            raise CentralVariantBAuditError("candidate model quote timestamp is missing")
        if snapshot.captured_at_utc.isoformat().replace("+00:00", "Z") != expected_timestamp:
            raise CentralVariantBAuditError("model-generation snapshot timestamp mismatch")
        if model_pick.get("market_scope") in (None, ""):
            # This remains a Stage 11.2 precondition, not a fallback or repair.
            return snapshot
        if model_pick.get("market") != "SPREAD":
            raise CentralVariantBAuditError("candidate market provenance mismatch")
        return snapshot


def central_variant_b_audit_event_id(record_payload: dict[str, Any]) -> str:
    """Return a deterministic event ID from semantic central-result metadata."""

    identity = {
        key: value
        for key, value in record_payload.items()
        if key not in {"orchestration_status", "persistence_written"}
    }
    digest = hashlib.sha256(_canonical_json(identity).encode("utf-8")).hexdigest()
    return f"structured-variant-b-audit-result:{digest}"


def _central_record(
    *,
    candidate: CandidateRecord,
    evidence: VariantBGptEvidenceSidecar,
    model_generation_snapshot_id: str,
    orchestration: StructuredVariantBAuditOrchestrationResult,
    build_timestamp_utc: datetime,
    output_path: Path,
) -> StructuredVariantBAuditResultRecord:
    if orchestration.status in {
        StructuredVariantBAuditOrchestrationStatus.WRITTEN,
        StructuredVariantBAuditOrchestrationStatus.ALREADY_EXISTS_IDENTICAL,
    }:
        pure_status = "BUILT"
        blocking_reasons: tuple[str, ...] = ()
        artifact_ref: str | None = str(output_path)
    else:
        pure_status = "BLOCKED_PRECONDITION"
        blocking_reasons = orchestration.blocking_reasons
        artifact_ref = None
    identity = {
        "candidate_id": candidate.candidate_id,
        "game_id": candidate.game_id,
        "evidence_id": evidence.evidence_id,
        "model_generation_snapshot_id": model_generation_snapshot_id,
        "model_generation_quote_id": _model_generation_quote_id(candidate),
        "audit_stage": "PREKICK",
        "build_timestamp_utc": build_timestamp_utc.isoformat(),
        "pure_core_status": pure_status,
        "orchestration_status": orchestration.status.value,
        "persistence_written": orchestration.written,
        "blocking_reasons": list(blocking_reasons),
        "build_id": orchestration.build_id,
        "canonical_digest": orchestration.canonical_digest,
        "artifact_ref": artifact_ref,
    }
    event_id = central_variant_b_audit_event_id(identity)
    return StructuredVariantBAuditResultRecord(event_id=event_id, **identity)


def _result_without_event(
    orchestration: StructuredVariantBAuditOrchestrationResult,
    candidate: CandidateRecord,
    evidence: VariantBGptEvidenceSidecar,
    snapshot_id: str,
    store: PregameEventStore,
) -> CentralVariantBAuditRunResult:
    return CentralVariantBAuditRunResult(
        orchestration_result=orchestration,
        central_event_id=None,
        central_append_result=None,
        candidate_id=candidate.candidate_id,
        game_id=candidate.game_id,
        evidence_id=evidence.evidence_id,
        model_generation_snapshot_id=snapshot_id,
        projected_game=project_game(store, candidate.game_id),
    )


def _load_evidence(path: Path) -> VariantBGptEvidenceSidecar:
    try:
        return load_variant_b_evidence(path)
    except (OSError, ValueError) as exc:
        raise CentralVariantBAuditError(f"evidence load failed: {exc}") from exc


def _load_rules(path: Path) -> dict[str, Any]:
    try:
        return load_rules_config(path)
    except (OSError, ValueError, TypeError) as exc:
        raise CentralVariantBAuditError(f"rules load failed: {exc}") from exc


def _model_generation_quote_id(candidate: CandidateRecord) -> str:
    model_pick = candidate.source_metadata.get("model_pick")
    if not isinstance(model_pick, dict):
        raise CentralVariantBAuditError("candidate model provenance is missing")
    quote_id = model_pick.get("model_generation_quote_id")
    if not isinstance(quote_id, str) or not quote_id.strip():
        raise CentralVariantBAuditError("candidate model-generation quote ID is missing")
    return quote_id


class _temporary_candidate_transport:
    def __init__(self, candidate: CandidateRecord, output_path: Path) -> None:
        self._candidate = candidate
        self._directory = Path(output_path).parent
        self.path: Path | None = None

    def __enter__(self) -> Path:
        if not self._directory.exists():
            raise CentralVariantBAuditError("output parent missing")
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".candidate.json",
            prefix="stage_11_3b_",
            dir=self._directory,
            encoding="utf-8",
            delete=False,
        ) as handle:
            json.dump(self._candidate.to_json_dict(), handle, sort_keys=True, separators=(",", ":"))
            self.path = Path(handle.name)
        loaded = CandidateRecord.model_validate(json.loads(self.path.read_text(encoding="utf-8")))
        if loaded.to_json_dict() != self._candidate.to_json_dict():
            raise CentralVariantBAuditError("temporary candidate transport is not equivalent")
        return self.path

    def __exit__(self, exc_type, exc, traceback) -> bool:
        if self.path is not None:
            self.path.unlink(missing_ok=True)
        return False


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False
    )


def _event_identity(record: StructuredVariantBAuditResultRecord) -> dict[str, Any]:
    payload = record.to_json_dict()
    payload.pop("orchestration_status")
    payload.pop("persistence_written")
    payload.pop("event_id")
    return payload


def _require_utc(value: datetime, field_name: str) -> None:
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise CentralVariantBAuditError(f"{field_name} must be UTC")
