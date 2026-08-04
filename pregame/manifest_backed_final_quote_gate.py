"""Manifest-backed readiness wrapper for one explicit Final Quote Gate evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from pregame.candidate_registry import CandidateRegistryService
from pregame.contracts import FinalQuoteGateResearchLineage, FinalQuoteGateResult, FinalQuotePolicy
from pregame.final_quote_gate import FinalQuoteGateError, FinalQuoteGateService
from pregame.market_history import MarketSnapshotHistoryService
from pregame.projector import project_game
from pregame.store import PregameEventStore


@dataclass(frozen=True)
class ManifestBackedFinalQuoteGateRunResult:
    """Result of explicit audit/manifest readiness followed by the existing gate."""

    candidate_id: str
    game_id: str | None
    audit_build_id: str
    audit_evidence_id: str | None
    manifest_id: str
    model_generation_snapshot_id: str | None
    final_snapshot_id: str
    lineage_ready: bool
    gate_result: FinalQuoteGateResult | None
    projected_game: object | None
    readiness_failure_codes: tuple[str, ...] = ()


class ManifestBackedFinalQuoteGateService:
    """Require explicit successful audit lineage before invoking FinalQuoteGateService once."""

    def __init__(
        self,
        *,
        store: PregameEventStore,
        candidates: CandidateRegistryService,
        market_history: MarketSnapshotHistoryService,
        final_quote_gate: FinalQuoteGateService,
    ) -> None:
        self._store = store
        self._candidates = candidates
        self._market_history = market_history
        self._final_quote_gate = final_quote_gate

    def evaluate(
        self,
        *,
        candidate_id: str,
        audit_build_id: str,
        manifest_id: str,
        final_snapshot_id: str,
        policy: FinalQuotePolicy,
        evaluated_at_utc: datetime,
        recorded_at_utc: datetime,
    ) -> ManifestBackedFinalQuoteGateRunResult:
        """Validate explicit immutable lineage, then call the existing gate exactly once."""

        _require_utc(evaluated_at_utc, "evaluated_at_utc")
        _require_utc(recorded_at_utc, "recorded_at_utc")
        candidate = self._candidates.get_candidate(candidate_id)
        if candidate is None:
            return self._failed(
                candidate_id,
                None,
                audit_build_id,
                manifest_id,
                final_snapshot_id,
                "CANDIDATE_NOT_FOUND",
            )
        state = project_game(self._store, candidate.game_id)
        if state is None:
            return self._failed(
                candidate_id,
                candidate.game_id,
                audit_build_id,
                manifest_id,
                final_snapshot_id,
                "AUDIT_BUILD_NOT_FOUND",
            )

        audit = next(
            (
                item
                for item in state.structured_variant_b_successful_audits
                if item.build_id == audit_build_id
            ),
            None,
        )
        if audit is None:
            return self._failed(
                candidate_id,
                candidate.game_id,
                audit_build_id,
                manifest_id,
                final_snapshot_id,
                "AUDIT_BUILD_NOT_FOUND",
                state,
            )
        if audit.pure_core_status != "BUILT":
            return self._failed(
                candidate_id,
                candidate.game_id,
                audit_build_id,
                manifest_id,
                final_snapshot_id,
                "AUDIT_NOT_SUCCESSFUL",
                state,
            )
        latest_success = state.latest_successful_structured_variant_b_audit
        if latest_success is None or latest_success.build_id != audit_build_id:
            return self._failed(
                candidate_id,
                candidate.game_id,
                audit_build_id,
                manifest_id,
                final_snapshot_id,
                "AUDIT_NOT_LATEST_SUCCESSFUL",
                state,
            )
        latest_attempt = state.latest_structured_variant_b_audit_attempt
        if (
            latest_attempt is not None
            and latest_attempt.event_id != audit.event_id
            and latest_attempt.pure_core_status == "BLOCKED_PRECONDITION"
        ):
            return self._failed(
                candidate_id,
                candidate.game_id,
                audit_build_id,
                manifest_id,
                final_snapshot_id,
                "LATER_BLOCKED_AUDIT_ATTEMPT",
                state,
            )
        if audit.candidate_id != candidate_id:
            return self._failed(
                candidate_id,
                candidate.game_id,
                audit_build_id,
                manifest_id,
                final_snapshot_id,
                "AUDIT_CANDIDATE_MISMATCH",
                state,
            )
        if audit.game_id != candidate.game_id:
            return self._failed(
                candidate_id,
                candidate.game_id,
                audit_build_id,
                manifest_id,
                final_snapshot_id,
                "AUDIT_GAME_MISMATCH",
                state,
            )
        if not audit.evidence_id:
            return self._failed(
                candidate_id,
                candidate.game_id,
                audit_build_id,
                manifest_id,
                final_snapshot_id,
                "AUDIT_EVIDENCE_MISSING",
                state,
            )

        manifest = next(
            (
                item
                for item in state.variant_b_evidence_lineage_manifests
                if item.manifest_id == manifest_id
            ),
            None,
        )
        if manifest is None:
            return self._failed(
                candidate_id,
                candidate.game_id,
                audit_build_id,
                manifest_id,
                final_snapshot_id,
                "MANIFEST_NOT_FOUND",
                state,
            )
        if manifest.evidence_id != audit.evidence_id:
            return self._failed(
                candidate_id,
                candidate.game_id,
                audit_build_id,
                manifest_id,
                final_snapshot_id,
                "MANIFEST_EVIDENCE_MISMATCH",
                state,
            )
        if manifest.candidate_id != candidate_id:
            return self._failed(
                candidate_id,
                candidate.game_id,
                audit_build_id,
                manifest_id,
                final_snapshot_id,
                "MANIFEST_CANDIDATE_MISMATCH",
                state,
            )
        if manifest.game_id != candidate.game_id:
            return self._failed(
                candidate_id,
                candidate.game_id,
                audit_build_id,
                manifest_id,
                final_snapshot_id,
                "MANIFEST_GAME_MISMATCH",
                state,
            )
        if manifest.audit_stage != "PREKICK":
            return self._failed(
                candidate_id,
                candidate.game_id,
                audit_build_id,
                manifest_id,
                final_snapshot_id,
                "MANIFEST_STAGE_MISMATCH",
                state,
            )
        indexed = {
            item.evidence_id: item.manifest_id
            for item in state.variant_b_evidence_lineage_by_evidence_id
        }
        if indexed.get(audit.evidence_id) != manifest_id:
            return self._failed(
                candidate_id,
                candidate.game_id,
                audit_build_id,
                manifest_id,
                final_snapshot_id,
                "MANIFEST_EVIDENCE_MISMATCH",
                state,
            )

        model_pick = candidate.source_metadata.get("model_pick")
        candidate_snapshot_id = (
            model_pick.get("model_generation_quote_id") if isinstance(model_pick, dict) else None
        )
        if audit.model_generation_quote_id != candidate_snapshot_id:
            return self._failed(
                candidate_id,
                candidate.game_id,
                audit_build_id,
                manifest_id,
                final_snapshot_id,
                "MODEL_GENERATION_SNAPSHOT_MISMATCH",
                state,
            )
        if audit.model_generation_snapshot_id != candidate_snapshot_id:
            return self._failed(
                candidate_id,
                candidate.game_id,
                audit_build_id,
                manifest_id,
                final_snapshot_id,
                "MODEL_GENERATION_SNAPSHOT_MISMATCH",
                state,
            )

        audit_event = self._store.get_event(audit.event_id)
        snapshot = self._market_history.get_snapshot(final_snapshot_id)
        if not _valid_timeline(
            manifest_prepared_at_utc=manifest.prepared_at_utc,
            manifest_recorded_at_utc=manifest.recorded_at_utc,
            audit_built_at_utc=audit.build_timestamp_utc,
            audit_recorded_at_utc=audit_event.created_at_utc if audit_event else None,
            final_quote_at_utc=(
                snapshot.captured_at_utc
                if snapshot and snapshot.game_id == candidate.game_id
                else None
            ),
            evaluated_at_utc=evaluated_at_utc,
            recorded_at_utc=recorded_at_utc,
        ):
            return self._failed(
                candidate_id,
                candidate.game_id,
                audit_build_id,
                manifest_id,
                final_snapshot_id,
                "INVALID_TIMESTAMP_ORDER",
                state,
            )

        lineage = FinalQuoteGateResearchLineage(
            audit_build_id=audit_build_id,
            audit_evidence_id=audit.evidence_id,
            manifest_id=manifest_id,
            model_generation_snapshot_id=audit.model_generation_snapshot_id,
        )
        try:
            result, _append = self._final_quote_gate.evaluate_and_record(
                candidate_id=candidate_id,
                final_snapshot_id=final_snapshot_id,
                policy=policy,
                evaluated_at_utc=evaluated_at_utc,
                recorded_at_utc=recorded_at_utc,
                research_lineage=lineage,
            )
        except FinalQuoteGateError:
            return ManifestBackedFinalQuoteGateRunResult(
                candidate_id=candidate_id,
                game_id=candidate.game_id,
                audit_build_id=audit_build_id,
                audit_evidence_id=audit.evidence_id,
                manifest_id=manifest_id,
                model_generation_snapshot_id=audit.model_generation_snapshot_id,
                final_snapshot_id=final_snapshot_id,
                lineage_ready=True,
                gate_result=None,
                projected_game=project_game(self._store, candidate.game_id),
                readiness_failure_codes=(),
            )
        return ManifestBackedFinalQuoteGateRunResult(
            candidate_id=candidate_id,
            game_id=candidate.game_id,
            audit_build_id=audit_build_id,
            audit_evidence_id=audit.evidence_id,
            manifest_id=manifest_id,
            model_generation_snapshot_id=audit.model_generation_snapshot_id,
            final_snapshot_id=final_snapshot_id,
            lineage_ready=True,
            gate_result=result,
            projected_game=project_game(self._store, candidate.game_id),
        )

    @staticmethod
    def _failed(
        candidate_id, game_id, audit_build_id, manifest_id, final_snapshot_id, code, state=None
    ):
        return ManifestBackedFinalQuoteGateRunResult(
            candidate_id=candidate_id,
            game_id=game_id,
            audit_build_id=audit_build_id,
            audit_evidence_id=None,
            manifest_id=manifest_id,
            model_generation_snapshot_id=None,
            final_snapshot_id=final_snapshot_id,
            lineage_ready=False,
            gate_result=None,
            projected_game=state,
            readiness_failure_codes=(code,),
        )


def _valid_timeline(**values: datetime | None) -> bool:
    try:
        for name, value in values.items():
            if value is None:
                if name == "final_quote_at_utc":
                    continue
                return False
            _require_utc(value, name)
        ordered = [
            values["manifest_prepared_at_utc"],
            values["manifest_recorded_at_utc"],
            values["audit_built_at_utc"],
            values["audit_recorded_at_utc"],
        ]
        if values["final_quote_at_utc"] is not None:
            ordered.append(values["final_quote_at_utc"])
        ordered.extend([values["evaluated_at_utc"], values["recorded_at_utc"]])
        return all(left <= right for left, right in zip(ordered, ordered[1:]))
    except ValueError:
        return False


def _require_utc(value: datetime, field_name: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    if value.utcoffset() != timedelta(0):
        raise ValueError(f"{field_name} must be in UTC")
