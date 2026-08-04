from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from pregame.candidate_registry import CandidateRegistryService
from pregame.central_variant_b_audit import (
    CentralSingleGameVariantBAuditService,
    CentralVariantBAuditError,
    central_variant_b_audit_event_id,
)
from pregame.contracts import (
    CandidateRecord,
    MarketSnapshot,
    PregameEvent,
    StructuredVariantBAuditResultRecord,
)
from pregame.events import (
    ExecutableStatus,
    MarketQualityStatus,
    MarketType,
    PregameEventType,
    SnapshotKind,
)
from pregame.jsonl_store import JsonlPregameEventStore
from pregame.market_history import MarketSnapshotHistoryService
from pregame.store import AppendStatus, InMemoryPregameEventStore
from pregame.variant_b_audit_orchestrator import StructuredVariantBAuditOrchestrationStatus

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "stage_11_2" / "acceptance"
RULES = ROOT / "config" / "variant_b_rules_prekick.yaml"
NOW = datetime(2026, 9, 10, 18, tzinfo=timezone.utc)


def candidate() -> CandidateRecord:
    return CandidateRecord.model_validate(json.loads((FIXTURES / "candidate.json").read_text()))


def snapshot(value: CandidateRecord, *, snapshot_id: str = "quote-1") -> MarketSnapshot:
    pick = value.source_metadata["model_pick"]
    return MarketSnapshot(
        snapshot_id=snapshot_id,
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


def service(store):
    candidates = CandidateRegistryService(store)
    markets = MarketSnapshotHistoryService(store)
    value = candidate()
    assert candidates.record_candidate(value, recorded_at_utc=NOW).status == AppendStatus.APPENDED
    assert (
        markets.record_snapshot(snapshot(value), recorded_at_utc=NOW).status
        == AppendStatus.APPENDED
    )
    return (
        CentralSingleGameVariantBAuditService(
            candidates=candidates, market_history=markets, store=store
        ),
        value,
    )


def run(service_value, candidate_value, tmp_path):
    return service_value.run(
        candidate_id=candidate_value.candidate_id,
        model_generation_snapshot_id="quote-1",
        evidence_path=FIXTURES / "evidence.json",
        rules_path=RULES,
        build_timestamp_utc=NOW,
        output_path=tmp_path / "audit.json",
        recorded_at_utc=NOW,
    )


def test_success_and_identical_rerun_project_one_central_event(tmp_path):
    store = InMemoryPregameEventStore()
    runner, value = service(store)

    first = run(runner, value, tmp_path)
    second = run(runner, value, tmp_path)

    assert first.orchestration_result.status == StructuredVariantBAuditOrchestrationStatus.WRITTEN
    assert first.central_append_result.status == AppendStatus.APPENDED
    assert second.orchestration_result.status == (
        StructuredVariantBAuditOrchestrationStatus.ALREADY_EXISTS_IDENTICAL
    )
    assert second.central_append_result.status == AppendStatus.ALREADY_EXISTS
    assert len(store.list_events(value.game_id)) == 3
    state = second.projected_game
    assert state.latest_structured_variant_b_audit_attempt.pure_core_status == "BUILT"
    assert (
        state.latest_successful_structured_variant_b_audit.build_id
        == first.orchestration_result.build_id
    )
    assert not list(tmp_path.glob("stage_11_3b_*.candidate.json"))


def test_existing_artifact_without_event_is_recorded_once(tmp_path):
    store = InMemoryPregameEventStore()
    runner, value = service(store)
    first = run(runner, value, tmp_path)
    store = InMemoryPregameEventStore()
    runner, value = service(store)

    recovered = run(runner, value, tmp_path)

    assert first.orchestration_result.written is True
    assert recovered.orchestration_result.status == (
        StructuredVariantBAuditOrchestrationStatus.ALREADY_EXISTS_IDENTICAL
    )
    assert recovered.central_append_result.status == AppendStatus.APPENDED


def test_snapshot_link_mismatch_fails_before_stage_11_2(tmp_path):
    store = InMemoryPregameEventStore()
    runner, value = service(store)

    with pytest.raises(CentralVariantBAuditError, match="snapshot ID"):
        runner.run(
            candidate_id=value.candidate_id,
            model_generation_snapshot_id="wrong",
            evidence_path=FIXTURES / "evidence.json",
            rules_path=RULES,
            build_timestamp_utc=NOW,
            output_path=tmp_path / "audit.json",
            recorded_at_utc=NOW,
        )

    assert not (tmp_path / "audit.json").exists()
    assert len(store.list_events(value.game_id)) == 2


def test_blocked_audit_is_projected_without_a_successful_artifact(tmp_path):
    store = InMemoryPregameEventStore()
    candidates = CandidateRegistryService(store)
    markets = MarketSnapshotHistoryService(store)
    value = candidate().model_copy(deep=True)
    value.source_metadata["model_pick"].pop("market_scope")
    assert candidates.record_candidate(value, recorded_at_utc=NOW).status == AppendStatus.APPENDED
    assert (
        markets.record_snapshot(snapshot(value), recorded_at_utc=NOW).status
        == AppendStatus.APPENDED
    )
    runner = CentralSingleGameVariantBAuditService(
        candidates=candidates, market_history=markets, store=store
    )

    result = run(runner, value, tmp_path)

    assert result.orchestration_result.status == StructuredVariantBAuditOrchestrationStatus.BLOCKED
    assert result.central_append_result.status == AppendStatus.APPENDED
    assert not (tmp_path / "audit.json").exists()
    assert result.projected_game.latest_successful_structured_variant_b_audit is None
    assert (
        result.projected_game.latest_structured_variant_b_audit_attempt.pure_core_status
        == "BLOCKED_PRECONDITION"
    )
    assert not list(tmp_path.glob("stage_11_3b_*.candidate.json"))


def test_jsonl_restart_preserves_central_audit_state(tmp_path):
    path = tmp_path / "events.jsonl"
    store = JsonlPregameEventStore(path)
    runner, value = service(store)
    first = run(runner, value, tmp_path)

    reloaded = JsonlPregameEventStore(path)
    from pregame.projector import project_game

    state = project_game(reloaded, value.game_id)
    assert (
        state.latest_successful_structured_variant_b_audit.build_id
        == first.orchestration_result.build_id
    )
    assert state.latest_structured_variant_b_audit_attempt.evidence_id == first.evidence_id


def test_later_blocked_attempt_does_not_erase_previous_success(tmp_path):
    store = InMemoryPregameEventStore()
    runner, value = service(store)
    first = run(runner, value, tmp_path)
    later = datetime(2026, 9, 10, 19, tzinfo=timezone.utc)
    payload = {
        "candidate_id": value.candidate_id,
        "game_id": value.game_id,
        "evidence_id": first.evidence_id,
        "model_generation_snapshot_id": "quote-1",
        "model_generation_quote_id": "quote-1",
        "audit_stage": "PREKICK",
        "build_timestamp_utc": later.isoformat(),
        "pure_core_status": "BLOCKED_PRECONDITION",
        "orchestration_status": "BLOCKED",
        "persistence_written": False,
        "blocking_reasons": ["EVIDENCE_CANDIDATE_MISMATCH"],
        "build_id": None,
        "canonical_digest": None,
        "artifact_ref": None,
    }
    event_id = central_variant_b_audit_event_id(payload)
    record = StructuredVariantBAuditResultRecord(event_id=event_id, **payload)
    event = PregameEvent(
        event_id=event_id,
        game_id=value.game_id,
        event_type=PregameEventType.STRUCTURED_VARIANT_B_AUDIT_RESULT_RECORDED,
        created_at_utc=later,
        effective_at_utc=later,
        source="test",
        idempotency_key=event_id,
        payload=record.to_json_dict(),
    )
    assert store.append(event).status == AppendStatus.APPENDED

    from pregame.projector import project_game

    state = project_game(store, value.game_id)
    assert (
        state.latest_structured_variant_b_audit_attempt.pure_core_status == "BLOCKED_PRECONDITION"
    )
    assert (
        state.latest_successful_structured_variant_b_audit.build_id
        == first.orchestration_result.build_id
    )
