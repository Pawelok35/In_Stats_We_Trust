from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from pregame.candidate_registry import CandidateRegistryService
from pregame.central_variant_b_audit import CentralSingleGameVariantBAuditService
from pregame.contracts import (
    CandidateRecord,
    InjuryObservationPayload,
    MarketSnapshot,
    OperatorAssessorMetadata,
    StructuredManualEvidenceAssessmentRecord,
    StructuredManualEvidenceRecord,
    VariantBEvidenceLineageManifestRecord,
)
from pregame.events import (
    ExecutableStatus,
    MarketQualityStatus,
    MarketType,
    SnapshotKind,
    StructuredManualEvidenceAssessmentStatus,
    StructuredManualEvidenceAssessorType,
    StructuredManualEvidenceCategory,
)
from pregame.evidence_lineage import (
    VariantBEvidenceLineageRegistryService,
    variant_b_evidence_lineage_manifest_id,
)
from pregame.jsonl_store import JsonlPregameEventStore
from pregame.manifest_backed_variant_b_refresh import (
    ManifestBackedVariantBAuditRefreshService,
)
from pregame.manual_evidence import StructuredManualEvidenceRegistryService
from pregame.manual_evidence_assessment import StructuredManualEvidenceAssessmentRegistryService
from pregame.market_history import MarketSnapshotHistoryService
from pregame.projector import project_game
from pregame.store import AppendStatus, InMemoryPregameEventStore
from pregame.variant_b_audit_integration import _sha256
from pregame.variant_b_audit_orchestrator import StructuredVariantBAuditOrchestrationStatus
from pregame.variant_b_evidence import load_variant_b_evidence

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "stage_11_2" / "acceptance"
RULES = ROOT / "config" / "variant_b_rules_prekick.yaml"
NOW = datetime(2026, 9, 10, 18, tzinfo=timezone.utc)


class CountingCentralAudit:
    def __init__(self, inner: CentralSingleGameVariantBAuditService) -> None:
        self.inner = inner
        self.calls = 0

    def run(self, **kwargs):
        self.calls += 1
        return self.inner.run(**kwargs)


def candidate() -> CandidateRecord:
    return CandidateRecord.model_validate(json.loads((FIXTURES / "candidate.json").read_text()))


def market_snapshot(value: CandidateRecord) -> MarketSnapshot:
    pick = value.source_metadata["model_pick"]
    return MarketSnapshot(
        snapshot_id="quote-1",
        game_id=value.game_id,
        snapshot_kind=SnapshotKind.INITIAL,
        captured_at_utc=NOW,
        book=pick["model_generation_book"],
        source=pick["odds_source"],
        market_type=MarketType.SPREAD,
        quality_status=MarketQualityStatus.MARKET_GRADE,
        executable_status=ExecutableStatus.CONFIRMED,
        selected_side=value.selected_team,
        spread=pick["model_generation_spread_selected_team"],
        spread_price=pick["model_generation_price"],
    )


def setup(store, *, blocked: bool = False):
    value = candidate().model_copy(deep=True)
    if blocked:
        value.source_metadata["model_pick"].pop("market_scope")
    candidates = CandidateRegistryService(store)
    markets = MarketSnapshotHistoryService(store)
    observations = StructuredManualEvidenceRegistryService(
        store=store, candidates=candidates, market_history=markets
    )
    assessments = StructuredManualEvidenceAssessmentRegistryService(
        store=store, candidates=candidates
    )
    assert candidates.record_candidate(value, recorded_at_utc=NOW).status == AppendStatus.APPENDED
    assert (
        markets.record_snapshot(market_snapshot(value), recorded_at_utc=NOW).status
        == AppendStatus.APPENDED
    )
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
    lineage = VariantBEvidenceLineageRegistryService(store=store, candidates=candidates)
    central = CountingCentralAudit(
        CentralSingleGameVariantBAuditService(
            candidates=candidates, market_history=markets, store=store
        )
    )
    return value, lineage, central


def manifest(value: CandidateRecord) -> VariantBEvidenceLineageManifestRecord:
    evidence = load_variant_b_evidence(FIXTURES / "evidence.json")
    digest = _sha256(evidence.to_json_dict())
    manifest_id = variant_b_evidence_lineage_manifest_id(
        evidence_id=evidence.evidence_id,
        candidate_id=value.candidate_id,
        game_id=value.game_id,
        audit_stage="PREKICK",
        observation_ids=("obs-1",),
        assessment_ids=("assessment-1",),
        evidence_sidecar_digest=digest,
        schema_version="variant_b_evidence_lineage_manifest.v1",
    )
    return VariantBEvidenceLineageManifestRecord(
        manifest_id=manifest_id,
        evidence_id=evidence.evidence_id,
        candidate_id=value.candidate_id,
        game_id=value.game_id,
        audit_stage="PREKICK",
        observation_ids=("obs-1",),
        assessment_ids=("assessment-1",),
        evidence_sidecar_digest=digest,
        evidence_sidecar_reference="fixture:evidence",
        prepared_at_utc=NOW,
        recorded_at_utc=NOW,
    )


def refresh(store, value, central):
    return ManifestBackedVariantBAuditRefreshService(
        store=store,
        candidates=CandidateRegistryService(store),
        central_audit=central,
    )


def register_manifest(lineage, item):
    result = lineage.record(manifest=item, evidence_path=FIXTURES / "evidence.json")
    assert result.append_result.status == AppendStatus.APPENDED


def run(service, value, item, tmp_path, **overrides):
    values = {
        "candidate_id": value.candidate_id,
        "model_generation_snapshot_id": "quote-1",
        "evidence_path": FIXTURES / "evidence.json",
        "manifest_id": item.manifest_id,
        "rules_path": RULES,
        "build_timestamp_utc": NOW,
        "output_path": tmp_path / "audit.json",
        "recorded_at_utc": NOW,
    }
    values.update(overrides)
    return service.run(**values)


def test_first_refresh_and_identical_rerun_are_manifest_backed(tmp_path):
    store = InMemoryPregameEventStore()
    value, lineage, central = setup(store)
    item = manifest(value)
    register_manifest(lineage, item)
    service = refresh(store, value, central)
    before = (FIXTURES / "evidence.json").read_bytes()

    first = run(service, value, item, tmp_path)
    artifact = (tmp_path / "audit.json").read_bytes()
    second = run(service, value, item, tmp_path)

    assert first.manifest_ready and second.manifest_ready
    assert (
        first.audit_result.orchestration_result.status
        == StructuredVariantBAuditOrchestrationStatus.WRITTEN
    )
    assert (
        second.audit_result.orchestration_result.status
        == StructuredVariantBAuditOrchestrationStatus.ALREADY_EXISTS_IDENTICAL
    )
    assert central.calls == 2
    assert (tmp_path / "audit.json").read_bytes() == artifact
    assert (FIXTURES / "evidence.json").read_bytes() == before
    state = second.projected_game
    assert state.latest_successful_structured_variant_b_audit.evidence_id == item.evidence_id
    assert state.variant_b_evidence_lineage_by_evidence_id[0].manifest_id == item.manifest_id


def test_missing_or_mismatched_manifest_never_calls_central_audit(tmp_path):
    store = InMemoryPregameEventStore()
    value, lineage, central = setup(store)
    item = manifest(value)
    service = refresh(store, value, central)

    missing = run(service, value, item, tmp_path)
    assert not missing.manifest_ready and central.calls == 0
    assert not (tmp_path / "audit.json").exists()

    register_manifest(lineage, item)
    mismatch = run(service, value, item, tmp_path, manifest_id="manifest:wrong")
    assert not mismatch.manifest_ready and central.calls == 0


def test_time_gate_and_missing_sidecar_fail_before_central_audit(tmp_path):
    store = InMemoryPregameEventStore()
    value, lineage, central = setup(store)
    item = manifest(value)
    register_manifest(lineage, item)
    service = refresh(store, value, central)

    early = run(service, value, item, tmp_path, build_timestamp_utc=NOW - timedelta(seconds=1))
    missing = run(service, value, item, tmp_path, evidence_path=tmp_path / "missing.json")

    assert not early.manifest_ready
    assert not missing.manifest_ready
    assert central.calls == 0


def test_blocked_refresh_preserves_manifest_and_records_attempt(tmp_path):
    store = InMemoryPregameEventStore()
    value, lineage, central = setup(store, blocked=True)
    item = manifest(value)
    register_manifest(lineage, item)

    result = run(refresh(store, value, central), value, item, tmp_path)

    assert result.manifest_ready
    assert (
        result.audit_result.orchestration_result.status
        == StructuredVariantBAuditOrchestrationStatus.BLOCKED
    )
    assert result.audit_result.evidence_id == item.evidence_id
    assert (
        result.projected_game.latest_structured_variant_b_audit_attempt.evidence_id
        == item.evidence_id
    )
    assert not (tmp_path / "audit.json").exists()


def test_snapshot_failure_occurs_after_ready_gate_without_artifact(tmp_path):
    store = InMemoryPregameEventStore()
    value, lineage, central = setup(store)
    item = manifest(value)
    register_manifest(lineage, item)

    result = run(
        refresh(store, value, central),
        value,
        item,
        tmp_path,
        model_generation_snapshot_id="missing-snapshot",
    )

    assert result.manifest_ready
    assert result.audit_result is None
    assert central.calls == 1
    assert not (tmp_path / "audit.json").exists()


def test_late_manifest_registration_joins_existing_audit_without_duplication(tmp_path):
    store = InMemoryPregameEventStore()
    value, lineage, central = setup(store)
    item = manifest(value)
    existing = central.inner.run(
        candidate_id=value.candidate_id,
        model_generation_snapshot_id="quote-1",
        evidence_path=FIXTURES / "evidence.json",
        rules_path=RULES,
        build_timestamp_utc=NOW,
        output_path=tmp_path / "audit.json",
        recorded_at_utc=NOW,
    )
    assert (
        existing.orchestration_result.status == StructuredVariantBAuditOrchestrationStatus.WRITTEN
    )
    audit_event_id = existing.central_event_id

    register_manifest(lineage, item)
    result = run(refresh(store, value, central), value, item, tmp_path)

    assert (
        result.audit_result.orchestration_result.status
        == StructuredVariantBAuditOrchestrationStatus.ALREADY_EXISTS_IDENTICAL
    )
    assert result.audit_result.central_event_id == audit_event_id
    assert result.audit_result.central_append_result.status == AppendStatus.ALREADY_EXISTS


def test_jsonl_restart_preserves_manifest_audit_join(tmp_path):
    path = tmp_path / "events.jsonl"
    store = JsonlPregameEventStore(path)
    value, lineage, central = setup(store)
    item = manifest(value)
    register_manifest(lineage, item)
    result = run(refresh(store, value, central), value, item, tmp_path)
    assert (
        result.audit_result.orchestration_result.status
        == StructuredVariantBAuditOrchestrationStatus.WRITTEN
    )

    state = project_game(JsonlPregameEventStore(path), value.game_id)
    assert state.latest_successful_structured_variant_b_audit.evidence_id == item.evidence_id
    assert state.variant_b_evidence_lineage_by_evidence_id[0].manifest_id == item.manifest_id
