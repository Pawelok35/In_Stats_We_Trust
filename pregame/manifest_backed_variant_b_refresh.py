"""Manifest-backed handoff to the existing single-game Variant B audit service."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from pregame.candidate_registry import CandidateRegistryService
from pregame.central_variant_b_audit import (
    CentralSingleGameVariantBAuditService,
    CentralVariantBAuditError,
    CentralVariantBAuditRunResult,
    _require_utc,
)
from pregame.contracts import (
    DEFAULT_VARIANT_B_EVIDENCE_LINEAGE_MANIFEST_SCHEMA_VERSION,
    CandidateRecord,
    PregameGameRecord,
    VariantBEvidenceLineageManifestRecord,
)
from pregame.evidence_lineage import variant_b_evidence_lineage_event_id
from pregame.projector import project_game
from pregame.store import PregameEventStore
from pregame.variant_b_audit_integration import _sha256
from pregame.variant_b_evidence import evidence_id_for_payload, load_variant_b_evidence


@dataclass(frozen=True)
class ManifestBackedVariantBAuditRefreshResult:
    """The readiness decision and, only after it passes, the nested audit result."""

    manifest_id: str | None
    evidence_id: str | None
    candidate_id: str
    game_id: str | None
    model_generation_snapshot_id: str
    evidence_sidecar_digest: str | None
    evidence_sidecar_reference: str | None
    observation_ids: tuple[str, ...]
    assessment_ids: tuple[str, ...]
    manifest_ready: bool
    audit_result: CentralVariantBAuditRunResult | None
    projected_game: PregameGameRecord | None
    error: str | None = None


class ManifestBackedVariantBAuditRefreshService:
    """Require a pre-registered immutable manifest before running Stage 11.3B."""

    def __init__(
        self,
        *,
        store: PregameEventStore,
        candidates: CandidateRegistryService,
        central_audit: CentralSingleGameVariantBAuditService,
    ) -> None:
        self._store = store
        self._candidates = candidates
        self._central_audit = central_audit

    def run(
        self,
        *,
        candidate_id: str,
        model_generation_snapshot_id: str,
        evidence_path: Path,
        manifest_id: str,
        rules_path: Path,
        build_timestamp_utc: datetime,
        output_path: Path,
        recorded_at_utc: datetime,
    ) -> ManifestBackedVariantBAuditRefreshResult:
        try:
            _require_utc(build_timestamp_utc, "build_timestamp_utc")
            _require_utc(recorded_at_utc, "recorded_at_utc")
        except (AttributeError, CentralVariantBAuditError) as exc:
            return self._invalid(
                candidate_id=candidate_id,
                model_generation_snapshot_id=model_generation_snapshot_id,
                manifest_id=manifest_id,
                error=str(exc),
            )

        candidate = self._candidates.get_candidate(candidate_id)
        if candidate is None:
            return self._invalid(
                candidate_id=candidate_id,
                model_generation_snapshot_id=model_generation_snapshot_id,
                manifest_id=manifest_id,
                error="candidate not found",
            )

        try:
            evidence = load_variant_b_evidence(Path(evidence_path))
        except (OSError, ValueError) as exc:
            return self._invalid(
                candidate_id=candidate_id,
                model_generation_snapshot_id=model_generation_snapshot_id,
                manifest_id=manifest_id,
                game_id=candidate.game_id,
                error=f"evidence load failed: {exc}",
            )

        evidence_id = evidence_id_for_payload(evidence)
        digest = _sha256(evidence.to_json_dict())
        state = project_game(self._store, candidate.game_id)
        if state is None:
            return self._invalid(
                candidate_id=candidate_id,
                model_generation_snapshot_id=model_generation_snapshot_id,
                manifest_id=manifest_id,
                evidence_id=evidence_id,
                game_id=candidate.game_id,
                evidence_sidecar_digest=digest,
                error="central game state is missing",
            )

        manifest = self._find_manifest(state, manifest_id, evidence_id)
        if isinstance(manifest, str):
            return self._invalid(
                candidate_id=candidate_id,
                model_generation_snapshot_id=model_generation_snapshot_id,
                manifest_id=manifest_id,
                evidence_id=evidence_id,
                game_id=candidate.game_id,
                evidence_sidecar_digest=digest,
                projected_game=state,
                error=manifest,
            )

        error = self._readiness_error(
            candidate=candidate,
            state=state,
            manifest=manifest,
            evidence=evidence,
            evidence_id=evidence_id,
            digest=digest,
            build_timestamp_utc=build_timestamp_utc,
            recorded_at_utc=recorded_at_utc,
        )
        if error is not None:
            return self._invalid(
                candidate_id=candidate_id,
                model_generation_snapshot_id=model_generation_snapshot_id,
                manifest_id=manifest.manifest_id,
                evidence_id=evidence_id,
                game_id=candidate.game_id,
                evidence_sidecar_digest=digest,
                manifest=manifest,
                projected_game=state,
                error=error,
            )

        try:
            audit_result = self._central_audit.run(
                candidate_id=candidate_id,
                model_generation_snapshot_id=model_generation_snapshot_id,
                evidence_path=Path(evidence_path),
                rules_path=Path(rules_path),
                build_timestamp_utc=build_timestamp_utc,
                output_path=Path(output_path),
                recorded_at_utc=recorded_at_utc,
            )
        except CentralVariantBAuditError as exc:
            return self._invalid(
                candidate_id=candidate_id,
                model_generation_snapshot_id=model_generation_snapshot_id,
                manifest_id=manifest.manifest_id,
                evidence_id=evidence_id,
                game_id=candidate.game_id,
                evidence_sidecar_digest=digest,
                manifest=manifest,
                projected_game=project_game(self._store, candidate.game_id),
                error=str(exc),
                manifest_ready=True,
            )

        if (
            audit_result.candidate_id != manifest.candidate_id
            or audit_result.game_id != manifest.game_id
            or audit_result.evidence_id != manifest.evidence_id
        ):
            return self._invalid(
                candidate_id=candidate_id,
                model_generation_snapshot_id=model_generation_snapshot_id,
                manifest_id=manifest.manifest_id,
                evidence_id=evidence_id,
                game_id=candidate.game_id,
                evidence_sidecar_digest=digest,
                manifest=manifest,
                projected_game=audit_result.projected_game,
                error="central audit result identity mismatch",
                manifest_ready=True,
            )

        return ManifestBackedVariantBAuditRefreshResult(
            manifest_id=manifest.manifest_id,
            evidence_id=evidence_id,
            candidate_id=candidate_id,
            game_id=candidate.game_id,
            model_generation_snapshot_id=model_generation_snapshot_id,
            evidence_sidecar_digest=digest,
            evidence_sidecar_reference=manifest.evidence_sidecar_reference,
            observation_ids=manifest.observation_ids,
            assessment_ids=manifest.assessment_ids,
            manifest_ready=True,
            audit_result=audit_result,
            projected_game=audit_result.projected_game,
        )

    def _find_manifest(
        self, state: PregameGameRecord, manifest_id: str, evidence_id: str
    ) -> VariantBEvidenceLineageManifestRecord | str:
        matches = [
            manifest
            for manifest in state.variant_b_evidence_lineage_manifests
            if manifest.manifest_id == manifest_id
        ]
        if len(matches) != 1:
            return "explicit manifest_id was not found exactly once"
        indexes = [
            index
            for index in state.variant_b_evidence_lineage_by_evidence_id
            if index.evidence_id == evidence_id
        ]
        if len(indexes) != 1 or indexes[0].manifest_id != manifest_id:
            return "evidence_id lineage index does not match explicit manifest_id"
        return matches[0]

    def _readiness_error(
        self,
        *,
        candidate: CandidateRecord,
        state: PregameGameRecord,
        manifest: VariantBEvidenceLineageManifestRecord,
        evidence,
        evidence_id: str,
        digest: str,
        build_timestamp_utc: datetime,
        recorded_at_utc: datetime,
    ) -> str | None:
        if self._store.get_event(variant_b_evidence_lineage_event_id(evidence_id)) is None:
            return "manifest event is missing"
        if manifest.evidence_id != evidence_id:
            return "manifest evidence_id does not match official sidecar"
        if manifest.evidence_sidecar_digest != digest:
            return "manifest sidecar digest does not match official sidecar"
        if manifest.candidate_id != candidate.candidate_id or manifest.game_id != candidate.game_id:
            return "manifest candidate or game mismatch"
        if manifest.audit_stage != "PREKICK":
            return "manifest audit stage is not PREKICK"
        if manifest.schema_version != DEFAULT_VARIANT_B_EVIDENCE_LINEAGE_MANIFEST_SCHEMA_VERSION:
            return "unsupported manifest schema version"
        if not manifest.assessment_ids:
            return "manifest assessment IDs are required"
        if state.game_id != manifest.game_id:
            return "projected state game mismatch"
        if not self._sidecar_matches_candidate(evidence, candidate):
            return "sidecar identity does not match authoritative candidate"
        if not (
            manifest.prepared_at_utc
            <= manifest.recorded_at_utc
            <= build_timestamp_utc
            <= recorded_at_utc
        ):
            return "manifest and audit timestamps are out of order"
        return None

    @staticmethod
    def _sidecar_matches_candidate(evidence, candidate: CandidateRecord) -> bool:
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
        return {key: getattr(evidence, key) for key in expected} == expected

    @staticmethod
    def _invalid(
        *,
        candidate_id: str,
        model_generation_snapshot_id: str,
        manifest_id: str | None,
        error: str,
        evidence_id: str | None = None,
        game_id: str | None = None,
        evidence_sidecar_digest: str | None = None,
        manifest: VariantBEvidenceLineageManifestRecord | None = None,
        projected_game: PregameGameRecord | None = None,
        manifest_ready: bool = False,
    ) -> ManifestBackedVariantBAuditRefreshResult:
        return ManifestBackedVariantBAuditRefreshResult(
            manifest_id=manifest_id,
            evidence_id=evidence_id,
            candidate_id=candidate_id,
            game_id=game_id,
            model_generation_snapshot_id=model_generation_snapshot_id,
            evidence_sidecar_digest=evidence_sidecar_digest,
            evidence_sidecar_reference=(
                manifest.evidence_sidecar_reference if manifest is not None else None
            ),
            observation_ids=manifest.observation_ids if manifest is not None else (),
            assessment_ids=manifest.assessment_ids if manifest is not None else (),
            manifest_ready=manifest_ready,
            audit_result=None,
            projected_game=projected_game,
            error=error,
        )
