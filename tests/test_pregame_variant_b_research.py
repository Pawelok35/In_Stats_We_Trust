from __future__ import annotations

import copy
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from pregame.candidate_registry import CandidateRegistryService
from pregame.contracts import CandidateRecord
from pregame.events import (
    CandidateStatus,
    DecisionLevel,
    VariantBResearchKind,
    VariantBResearchStatus,
)
from pregame.projector import project_game
from pregame.store import AppendStatus, InMemoryPregameEventStore
from pregame.variant_b_research import (
    VariantBResearchError,
    VariantBResearchRegistryService,
    adapt_variant_b_output,
)

GAME_ID = "2026_w01_BUF_at_HOU"
AUDIT_PATH = Path("research/variant_b_week_flow/2026/week_01/2026_w01_BUF_at_HOU_BUF.json")


def utc_at(hour: int) -> datetime:
    return datetime(2026, 9, 10, hour, tzinfo=timezone.utc)


def current_audit() -> dict:
    return json.loads(AUDIT_PATH.read_text(encoding="utf-8"))


def candidate(**changes) -> CandidateRecord:
    payload = dict(
        candidate_id="candidate-1",
        game_id=GAME_ID,
        season=2026,
        week=1,
        status=CandidateStatus.MODEL_CANDIDATE,
        created_at_utc=utc_at(18),
        model_variant="variant_m",
        selected_team="BUF",
        model_tag="VALUE PLAY",
        production_eligible=True,
    )
    payload.update(changes)
    return CandidateRecord(**payload)


def test_current_machine_readable_output_is_adapted_fail_closed():
    record = adapt_variant_b_output(
        current_audit(),
        candidate=candidate(),
        research_kind=VariantBResearchKind.FULL_RESEARCH,
        recorded_at_utc=utc_at(20),
        source_ref="fixture.json",
    )

    assert record.audit_schema_version == "variant_b_audit_output.v1"
    assert record.framework_version == "variant_b_audit_v1"
    assert record.expected_point_count == 19
    assert record.present_point_count == 8
    assert record.sections_complete is False
    assert record.research_status == VariantBResearchStatus.BLOCKED
    assert record.research_approved is False
    assert "PXQ-01" in record.blocking_risk_codes
    assert record.legacy_audit_recommendation["operator_action"] == "RETURN_FOR_MODEL_RERUN"
    assert record.acceptable_quote_frontier_raw["acceptable_quote_frontier_id"]
    assert "GPT_19_POINT_EVIDENCE_IS_MARKDOWN_NOT_IMPORTED" in record.warnings


def test_pxq02_missing_probabilities_or_frontier_cannot_be_approved():
    payload = complete_audit()
    payload["source_pick"].pop("p_cover")
    payload["source_pick"].pop("acceptable_quote_frontier_id")
    payload["source_pick"].pop("acceptable_quote_frontier_path")
    record = adapt_variant_b_output(
        payload,
        candidate=candidate(),
        research_kind=VariantBResearchKind.FULL_RESEARCH,
        recorded_at_utc=utc_at(20),
        source_ref="fixture.json",
    )

    assert record.research_status == VariantBResearchStatus.INCOMPLETE
    assert record.research_approved is False
    assert "RESEARCH_APPROVAL_NOT_STRUCTURALLY_DETERMINABLE" in record.warnings


def test_complete_structured_audit_can_be_approved_without_creating_operator_decision():
    record = adapt_variant_b_output(
        complete_audit(),
        candidate=candidate(),
        research_kind=VariantBResearchKind.FINAL_REFRESH,
        recorded_at_utc=utc_at(20),
        source_ref="fixture.json",
    )

    assert record.research_status == VariantBResearchStatus.APPROVED
    assert record.research_approved is True
    assert record.legacy_audit_recommendation["gate_state"] == "OPEN"


def test_registry_projects_latest_record_and_revokes_then_restores_approval():
    store = InMemoryPregameEventStore()
    candidates = CandidateRegistryService(store)
    candidates.record_candidate(candidate(), recorded_at_utc=utc_at(18))
    registry = VariantBResearchRegistryService(store, candidates)
    approved = adapt_variant_b_output(
        complete_audit(),
        candidate=candidate(),
        research_kind=VariantBResearchKind.FULL_RESEARCH,
        recorded_at_utc=utc_at(20),
        source_ref="approved.json",
    )
    blocked_payload = current_audit()
    blocked_payload["generated_at_utc"] = "2026-09-10T21:00:00Z"
    blocked = adapt_variant_b_output(
        blocked_payload,
        candidate=candidate(),
        research_kind=VariantBResearchKind.DELTA_UPDATE,
        recorded_at_utc=utc_at(22),
        source_ref="blocked.json",
    )
    restored_payload = complete_audit()
    restored_payload["generated_at_utc"] = "2026-09-10T23:00:00Z"
    restored = adapt_variant_b_output(
        restored_payload,
        candidate=candidate(),
        research_kind=VariantBResearchKind.FINAL_REFRESH,
        recorded_at_utc=datetime(2026, 9, 10, 23, tzinfo=timezone.utc),
        source_ref="restored.json",
    )

    assert registry.record_research(approved).status == AppendStatus.APPENDED
    assert registry.get_latest_approved_research("candidate-1").research_id == approved.research_id
    registry.record_research(blocked)
    assert registry.get_latest_approved_research("candidate-1") is None
    assert project_game(store, GAME_ID).variant_b_research_approved is False
    registry.record_research(restored)
    projected = project_game(store, GAME_ID)
    assert projected.variant_b_research_approved is True
    assert projected.current_decision_level == DecisionLevel.MODEL_CANDIDATE
    assert projected.operator_decision is None


def test_registry_retry_is_idempotent_and_candidate_mismatches_fail():
    store = InMemoryPregameEventStore()
    candidates = CandidateRegistryService(store)
    item = candidate()
    candidates.record_candidate(item, recorded_at_utc=utc_at(18))
    registry = VariantBResearchRegistryService(store, candidates)
    record = adapt_variant_b_output(
        current_audit(),
        candidate=item,
        research_kind=VariantBResearchKind.FULL_RESEARCH,
        recorded_at_utc=utc_at(20),
        source_ref="fixture.json",
    )
    assert registry.record_research(record).status == AppendStatus.APPENDED
    assert registry.record_research(record).status == AppendStatus.ALREADY_EXISTS
    wrong = current_audit()
    wrong["event"]["selected_team"] = "HOU"
    with pytest.raises(VariantBResearchError, match="selected_team"):
        adapt_variant_b_output(
            wrong,
            candidate=item,
            research_kind=VariantBResearchKind.FULL_RESEARCH,
            recorded_at_utc=utc_at(20),
            source_ref="fixture.json",
        )


def test_import_file_reads_current_json_contract_and_retries_idempotently(tmp_path):
    path = tmp_path / "variant_b_audit.json"
    path.write_text(AUDIT_PATH.read_text(encoding="utf-8"), encoding="utf-8")
    store = InMemoryPregameEventStore()
    candidates = CandidateRegistryService(store)
    item = candidate()
    candidates.record_candidate(item, recorded_at_utc=utc_at(18))
    registry = VariantBResearchRegistryService(store, candidates)

    first = registry.import_file(
        path,
        candidate_id=item.candidate_id,
        research_kind=VariantBResearchKind.FULL_RESEARCH,
        recorded_at_utc=utc_at(20),
    )
    second = registry.import_file(
        path,
        candidate_id=item.candidate_id,
        research_kind=VariantBResearchKind.FULL_RESEARCH,
        recorded_at_utc=utc_at(21),
    )

    assert first.append_result.status == AppendStatus.APPENDED
    assert second.append_result.status == AppendStatus.ALREADY_EXISTS


def complete_audit() -> dict:
    payload = copy.deepcopy(current_audit())
    by_id = {point["point_number"]: point for point in payload["audit_points"]}
    for point_id in range(1, 20):
        point = by_id.get(point_id)
        if point is None:
            point = {
                "point_number": point_id,
                "point_name": f"point_{point_id}",
                "status": "COMPLETE",
                "due_status": "DUE",
                "confirmed_facts": ["fixture"],
                "triggered_rules": [],
                "calculations": {"values": {}},
                "narrative": "fixture",
            }
            payload["audit_points"].append(point)
            by_id[point_id] = point
        point["status"] = "COMPLETE"
        point["triggered_rules"] = []
    by_id[18]["calculations"] = {
        "values": {"readiness": {"final_prekick_readiness": "PREKICK_READY"}}
    }
    by_id[19]["calculations"] = {
        "values": {"gate_state": "OPEN", "operator_action": "READY_FOR_NEXT_AUDIT_STAGE"}
    }
    return payload
