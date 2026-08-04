from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError

from pregame.candidate_registry import CandidateRegistryService
from pregame.contracts import (
    CandidateRecord,
    InjuryObservationPayload,
    OperatorAssessorMetadata,
    StructuredManualEvidenceAssessmentRecord,
    StructuredManualEvidenceRecord,
    VariantBEvidenceLineageManifestRecord,
)
from pregame.events import (
    PregameEventType,
    StructuredManualEvidenceAssessmentStatus,
    StructuredManualEvidenceAssessorType,
    StructuredManualEvidenceCategory,
)
from pregame.evidence_lineage import (
    VariantBEvidenceLineageError,
    VariantBEvidenceLineageRegistryService,
    variant_b_evidence_lineage_event_id,
    variant_b_evidence_lineage_manifest_id,
)
from pregame.jsonl_store import JsonlPregameEventStore
from pregame.manual_evidence import StructuredManualEvidenceRegistryService
from pregame.manual_evidence_assessment import StructuredManualEvidenceAssessmentRegistryService
from pregame.market_history import MarketSnapshotHistoryService
from pregame.store import AppendStatus, InMemoryPregameEventStore
from pregame.variant_b_audit_integration import _sha256
from pregame.variant_b_evidence import load_variant_b_evidence

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "stage_11_2" / "acceptance"
EVIDENCE_PATH = FIXTURES / "evidence.json"
NOW = datetime(2026, 9, 10, 18, tzinfo=timezone.utc)


def candidate() -> CandidateRecord:
    return CandidateRecord.model_validate(json.loads((FIXTURES / "candidate.json").read_text()))


def services(store):
    candidates = CandidateRegistryService(store)
    observations = StructuredManualEvidenceRegistryService(
        store=store, candidates=candidates, market_history=MarketSnapshotHistoryService(store)
    )
    assessments = StructuredManualEvidenceAssessmentRegistryService(
        store=store, candidates=candidates
    )
    lineage = VariantBEvidenceLineageRegistryService(store=store, candidates=candidates)
    return candidates, observations, assessments, lineage


def setup(store):
    candidates, observations, assessments, lineage = services(store)
    value = candidate()
    assert candidates.record_candidate(value, recorded_at_utc=NOW).status == AppendStatus.APPENDED
    observation = StructuredManualEvidenceRecord(
        observation_id="obs-1",
        game_id=value.game_id,
        category=StructuredManualEvidenceCategory.INJURY,
        source_name="Official Team",
        source_type="OFFICIAL",
        source_reference="source:obs-1",
        observed_at_utc=NOW - timedelta(hours=1),
        recorded_at_utc=NOW - timedelta(hours=1),
        candidate_id=value.candidate_id,
        payload=InjuryObservationPayload(
            team=value.away, player_name="Player One", report_status="QUESTIONABLE"
        ),
    )
    assert (
        observations.record(observation=observation).append_result.status == AppendStatus.APPENDED
    )
    assessment = StructuredManualEvidenceAssessmentRecord(
        assessment_id="assessment-1",
        game_id=value.game_id,
        category=StructuredManualEvidenceCategory.INJURY,
        assessment_scope="availability",
        observation_ids=("obs-1",),
        assessor=OperatorAssessorMetadata(
            assessor_type=StructuredManualEvidenceAssessorType.OPERATOR,
            assessor_id="operator:daniel",
        ),
        as_of_utc=NOW,
        assessed_at_utc=NOW,
        recorded_at_utc=NOW,
        status=StructuredManualEvidenceAssessmentStatus.PASS,
        reason_codes=(),
        candidate_id=value.candidate_id,
    )
    assert assessments.record(assessment=assessment).append_result.status == AppendStatus.APPENDED
    return value, observation, assessment, lineage


def manifest(
    value,
    *,
    observation_ids=("obs-1",),
    assessment_ids=("assessment-1",),
    reference="fixture:evidence",
):
    sidecar = load_variant_b_evidence(EVIDENCE_PATH)
    digest = _sha256(sidecar.to_json_dict())
    manifest_id = variant_b_evidence_lineage_manifest_id(
        evidence_id=sidecar.evidence_id,
        candidate_id=value.candidate_id,
        game_id=value.game_id,
        audit_stage="PREKICK",
        observation_ids=observation_ids,
        assessment_ids=assessment_ids,
        evidence_sidecar_digest=digest,
        schema_version="variant_b_evidence_lineage_manifest.v1",
    )
    return VariantBEvidenceLineageManifestRecord(
        manifest_id=manifest_id,
        evidence_id=sidecar.evidence_id,
        candidate_id=value.candidate_id,
        game_id=value.game_id,
        audit_stage="PREKICK",
        observation_ids=observation_ids,
        assessment_ids=assessment_ids,
        evidence_sidecar_digest=digest,
        evidence_sidecar_reference=reference,
        prepared_at_utc=NOW,
        recorded_at_utc=NOW,
    )


def test_valid_manifest_is_deterministic_and_projects_by_evidence_id():
    store = InMemoryPregameEventStore()
    value, _, _, lineage = setup(store)
    first = manifest(value)
    second = manifest(value)
    assert first.manifest_id == second.manifest_id
    result = lineage.record(manifest=first, evidence_path=EVIDENCE_PATH)
    assert result.append_result.status == AppendStatus.APPENDED
    state = result.projected_game
    assert state.variant_b_evidence_lineage_manifests == (first,)
    assert state.variant_b_evidence_lineage_by_evidence_id[0].evidence_id == first.evidence_id
    assert state.variant_b_evidence_lineage_by_evidence_id[0].manifest_id == first.manifest_id


def test_idempotency_conflict_and_sidecar_input_immutability():
    store = InMemoryPregameEventStore()
    value, _, _, lineage = setup(store)
    item = manifest(value)
    before = EVIDENCE_PATH.read_bytes()
    assert (
        lineage.record(manifest=item, evidence_path=EVIDENCE_PATH).append_result.status
        == AppendStatus.APPENDED
    )
    assert (
        lineage.record(manifest=item, evidence_path=EVIDENCE_PATH).append_result.status
        == AppendStatus.ALREADY_EXISTS
    )
    changed = item.model_copy(update={"evidence_sidecar_reference": "fixture:changed"})
    assert (
        lineage.record(manifest=changed, evidence_path=EVIDENCE_PATH).append_result.status
        == AppendStatus.CONFLICT
    )
    assert len(store.list_events(value.game_id)) == 4
    assert EVIDENCE_PATH.read_bytes() == before
    assert variant_b_evidence_lineage_event_id(item.evidence_id).endswith(item.evidence_id)


def test_invalid_path_digest_identity_and_explicit_lineage_fail_closed(tmp_path):
    store = InMemoryPregameEventStore()
    value, _, _, lineage = setup(store)
    item = manifest(value)
    with pytest.raises(VariantBEvidenceLineageError, match="sidecar load failed"):
        lineage.record(manifest=item, evidence_path=tmp_path / "missing.json")
    with pytest.raises(VariantBEvidenceLineageError, match="digest"):
        lineage.record(
            manifest=item.model_copy(update={"evidence_sidecar_digest": "wrong"}),
            evidence_path=EVIDENCE_PATH,
        )
    with pytest.raises(VariantBEvidenceLineageError, match="observation_id was not found"):
        lineage.record(
            manifest=manifest(value, observation_ids=("missing",)),
            evidence_path=EVIDENCE_PATH,
        )
    with pytest.raises(VariantBEvidenceLineageError, match="assessment_id was not found"):
        lineage.record(
            manifest=manifest(value, assessment_ids=("missing",)),
            evidence_path=EVIDENCE_PATH,
        )


def test_manifest_validates_assessment_consistency_and_as_of():
    store = InMemoryPregameEventStore()
    value, _, _, lineage = setup(store)
    with pytest.raises(VariantBEvidenceLineageError, match="requires observations"):
        lineage.record(manifest=manifest(value, observation_ids=()), evidence_path=EVIDENCE_PATH)
    future = manifest(value).model_copy(update={"prepared_at_utc": NOW - timedelta(minutes=1)})
    with pytest.raises(VariantBEvidenceLineageError, match="assessment as_of"):
        lineage.record(manifest=future, evidence_path=EVIDENCE_PATH)
    with pytest.raises(ValidationError, match="canonical ordered"):
        VariantBEvidenceLineageManifestRecord.model_validate(
            {**manifest(value).model_dump(), "observation_ids": ("z", "a")}
        )


def test_jsonl_restart_preserves_manifest_state(tmp_path):
    path = tmp_path / "events.jsonl"
    store = JsonlPregameEventStore(path)
    value, _, _, lineage = setup(store)
    item = manifest(value)
    assert (
        lineage.record(manifest=item, evidence_path=EVIDENCE_PATH).append_result.status
        == AppendStatus.APPENDED
    )
    restarted = JsonlPregameEventStore(path)
    _, _, _, after_restart = services(restarted)
    result = after_restart.record(manifest=item, evidence_path=EVIDENCE_PATH)
    assert result.append_result.status == AppendStatus.ALREADY_EXISTS
    assert result.projected_game.variant_b_evidence_lineage_manifests[0].assessment_ids == (
        "assessment-1",
    )


def test_manifest_event_contains_references_not_full_payloads():
    store = InMemoryPregameEventStore()
    value, _, _, lineage = setup(store)
    item = manifest(value)
    lineage.record(manifest=item, evidence_path=EVIDENCE_PATH)
    event = store.get_event(variant_b_evidence_lineage_event_id(item.evidence_id))
    assert "payload" not in event.payload
    assert "point_results" not in event.payload
    assert "source_pick" not in event.payload
    assert event.event_type == PregameEventType.VARIANT_B_EVIDENCE_LINEAGE_RECORDED
