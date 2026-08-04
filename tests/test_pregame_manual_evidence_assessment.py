from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from pregame.candidate_registry import CandidateRegistryService
from pregame.contracts import (
    CandidateRecord,
    DeterministicRuleAssessorMetadata,
    GptLlmAssessorMetadata,
    InjuryObservationPayload,
    OperatorAssessorMetadata,
    ResearchProcessAssessorMetadata,
    StructuredManualEvidenceAssessmentRecord,
    StructuredManualEvidenceRecord,
)
from pregame.events import (
    PregameEventType,
    StructuredManualEvidenceAssessmentStatus,
    StructuredManualEvidenceAssessorType,
    StructuredManualEvidenceCategory,
)
from pregame.jsonl_store import JsonlPregameEventStore
from pregame.manual_evidence import StructuredManualEvidenceRegistryService
from pregame.manual_evidence_assessment import (
    StructuredManualEvidenceAssessmentError,
    StructuredManualEvidenceAssessmentRegistryService,
    structured_manual_evidence_assessment_event_id,
)
from pregame.market_history import MarketSnapshotHistoryService
from pregame.store import AppendStatus, InMemoryPregameEventStore
from pregame.variant_b_evidence import EvidenceStatus

GAME_ID = "2026_w01_BUF_at_HOU"
OTHER_GAME_ID = "2026_w01_NE_at_SEA"
NOW = datetime(2026, 9, 8, 18, tzinfo=timezone.utc)


def candidate(*, game_id: str = GAME_ID, candidate_id: str = "candidate-1") -> CandidateRecord:
    return CandidateRecord(
        candidate_id=candidate_id,
        game_id=game_id,
        season=2026,
        week=1,
        away="BUF",
        home="HOU",
        status="MODEL_CANDIDATE",
        created_at_utc=NOW,
        model_variant="variant_m",
        selected_team="BUF",
        model_tag="VALUE PLAY",
        production_eligible=True,
    )


def observation(
    *,
    observation_id: str = "injury-1",
    game_id: str = GAME_ID,
    source_name: str = "Official Team",
    reported_at: datetime = NOW,
    supersedes_observation_id: str | None = None,
) -> StructuredManualEvidenceRecord:
    return StructuredManualEvidenceRecord(
        observation_id=observation_id,
        game_id=game_id,
        category=StructuredManualEvidenceCategory.INJURY,
        source_name=source_name,
        source_type="OFFICIAL",
        source_reference=f"source:{observation_id}",
        observed_at_utc=reported_at,
        recorded_at_utc=reported_at,
        supersedes_observation_id=supersedes_observation_id,
        payload=InjuryObservationPayload(
            team="BUF", player_name="Player One", report_status="QUESTIONABLE"
        ),
    )


def operator() -> OperatorAssessorMetadata:
    return OperatorAssessorMetadata(
        assessor_type=StructuredManualEvidenceAssessorType.OPERATOR,
        assessor_id="operator:daniel",
        display_name="Daniel",
    )


def assessment(
    *,
    assessment_id: str = "assessment-1",
    observation_ids: tuple[str, ...] = ("injury-1",),
    assessor=None,
    status: StructuredManualEvidenceAssessmentStatus = (
        StructuredManualEvidenceAssessmentStatus.PASS
    ),
    reason_codes: tuple[str, ...] = (),
    as_of_utc: datetime = NOW,
    assessed_at_utc: datetime = NOW,
    recorded_at_utc: datetime = NOW,
    candidate_id: str | None = None,
    supersedes_assessment_id: str | None = None,
    scope: str = "availability",
    game_id: str = GAME_ID,
) -> StructuredManualEvidenceAssessmentRecord:
    assessor = assessor or operator()
    return StructuredManualEvidenceAssessmentRecord(
        assessment_id=assessment_id,
        game_id=game_id,
        category=StructuredManualEvidenceCategory.INJURY,
        assessment_scope=scope,
        observation_ids=observation_ids,
        assessor=assessor,
        as_of_utc=as_of_utc,
        assessed_at_utc=assessed_at_utc,
        recorded_at_utc=recorded_at_utc,
        status=status,
        reason_codes=reason_codes,
        candidate_id=candidate_id,
        supersedes_assessment_id=supersedes_assessment_id,
    )


def services(store):
    candidates = CandidateRegistryService(store)
    observations = StructuredManualEvidenceRegistryService(
        store=store, candidates=candidates, market_history=MarketSnapshotHistoryService(store)
    )
    assessments = StructuredManualEvidenceAssessmentRegistryService(
        store=store, candidates=candidates
    )
    return candidates, observations, assessments


def register_observation(registry, item=None):
    assert (
        registry.record(observation=item or observation()).append_result.status
        == AppendStatus.APPENDED
    )


def test_all_assessor_types_and_status_enum_independence():
    store = InMemoryPregameEventStore()
    _, observations, registry = services(store)
    register_observation(observations)
    cases = [
        assessment(),
        assessment(
            assessment_id="gpt",
            assessor=GptLlmAssessorMetadata(
                assessor_type=StructuredManualEvidenceAssessorType.GPT_LLM,
                assessor_id="gpt:run-1",
                provider="OpenAI",
                model_name="gpt-test",
                model_version="1",
                prompt_template_version="v1",
            ),
        ),
        assessment(
            assessment_id="rule",
            assessor=DeterministicRuleAssessorMetadata(
                assessor_type=StructuredManualEvidenceAssessorType.DETERMINISTIC_RULE,
                assessor_id="rule:injury",
                rule_profile_id="injury-profile",
                rule_version="v1",
            ),
        ),
        assessment(
            assessment_id="process",
            assessor=ResearchProcessAssessorMetadata(
                assessor_type=StructuredManualEvidenceAssessorType.RESEARCH_PROCESS,
                assessor_id="process:weekly",
                process_id="weekly-review",
                process_version="v1",
            ),
        ),
    ]
    for item in cases:
        assert registry.record(assessment=item).append_result.status == AppendStatus.APPENDED
    state = registry.record(assessment=cases[0]).projected_game
    assert len(state.active_structured_manual_evidence_assessments) == 4
    assert StructuredManualEvidenceAssessmentStatus.PASS is not EvidenceStatus.PASS


@pytest.mark.parametrize(
    ("status", "observation_ids", "reason_codes", "valid"),
    [
        (StructuredManualEvidenceAssessmentStatus.PASS, ("injury-1",), (), True),
        (StructuredManualEvidenceAssessmentStatus.WARNING, (), ("CHECK",), False),
        (StructuredManualEvidenceAssessmentStatus.BLOCKING, (), ("BLOCK",), False),
        (StructuredManualEvidenceAssessmentStatus.PENDING, (), ("WAIT",), False),
        (StructuredManualEvidenceAssessmentStatus.NO_DATA, (), ("MISSING",), True),
        (StructuredManualEvidenceAssessmentStatus.NOT_DUE, (), ("TOO_EARLY",), True),
        (StructuredManualEvidenceAssessmentStatus.NO_DATA, (), (), False),
    ],
)
def test_status_observation_rules(status, observation_ids, reason_codes, valid):
    if valid:
        assert assessment(status=status, observation_ids=observation_ids, reason_codes=reason_codes)
    else:
        with pytest.raises(ValidationError):
            assessment(status=status, observation_ids=observation_ids, reason_codes=reason_codes)


def test_contract_rejects_bad_metadata_timestamps_and_boundary_fields():
    with pytest.raises(ValidationError):
        GptLlmAssessorMetadata(
            assessor_type=StructuredManualEvidenceAssessorType.GPT_LLM,
            assessor_id="gpt",
            provider="OpenAI",
            model_name="gpt-test",
        )
    with pytest.raises(ValidationError):
        assessment(as_of_utc=datetime(2026, 9, 8, 18))
    with pytest.raises(ValidationError):
        assessment(as_of_utc=NOW + timedelta(minutes=1))
    for field in (
        "report_status",
        "wind_speed",
        "tickets_percentage",
        "source_name",
        "approve_bet",
        "stake",
        "executed_spread",
        "final_operator_decision",
        "settlement",
        "CLV",
    ):
        with pytest.raises(ValidationError):
            StructuredManualEvidenceAssessmentRecord.model_validate(
                {**assessment().model_dump(), field: "forbidden"}
            )


def test_explicit_observation_candidate_and_as_of_validation():
    store = InMemoryPregameEventStore()
    candidates, observations, registry = services(store)
    item = candidate()
    assert candidates.record_candidate(item, recorded_at_utc=NOW).status == AppendStatus.APPENDED
    register_observation(observations)
    assert (
        registry.record(assessment=assessment(candidate_id=item.candidate_id)).append_result.status
        == AppendStatus.APPENDED
    )
    with pytest.raises(
        StructuredManualEvidenceAssessmentError, match="observation_id was not found"
    ):
        registry.record(
            assessment=assessment(assessment_id="unknown", observation_ids=("missing",))
        )
    later = observation(observation_id="later", reported_at=NOW + timedelta(minutes=2))
    register_observation(observations, later)
    with pytest.raises(StructuredManualEvidenceAssessmentError, match="effective after"):
        registry.record(assessment=assessment(assessment_id="future", observation_ids=("later",)))
    other = candidate(game_id=OTHER_GAME_ID, candidate_id="other")
    assert candidates.record_candidate(other, recorded_at_utc=NOW).status == AppendStatus.APPENDED
    with pytest.raises(StructuredManualEvidenceAssessmentError, match="another game"):
        registry.record(assessment=assessment(assessment_id="bad-candidate", candidate_id="other"))


def test_supersession_active_as_of_and_multiple_assessors(tmp_path):
    store = JsonlPregameEventStore(tmp_path / "events.jsonl")
    _, observations, registry = services(store)
    register_observation(observations)
    old = assessment()
    assert registry.record(assessment=old).append_result.status == AppendStatus.APPENDED
    new = assessment(
        assessment_id="assessment-2",
        supersedes_assessment_id="assessment-1",
        status=StructuredManualEvidenceAssessmentStatus.WARNING,
        reason_codes=("NEW_REPORT",),
        as_of_utc=NOW + timedelta(minutes=2),
        assessed_at_utc=NOW + timedelta(minutes=2),
        recorded_at_utc=NOW + timedelta(minutes=2),
    )
    state = registry.record(assessment=new).projected_game
    assert state.superseded_structured_manual_evidence_assessment_ids == ("assessment-1",)
    assert [item.assessment_id for item in state.active_structured_manual_evidence_assessments] == [
        "assessment-2"
    ]
    assert (
        state.latest_structured_manual_evidence_assessment_by_scope_assessor[0].assessment_id
        == "assessment-2"
    )

    gpt = assessment(
        assessment_id="assessment-gpt",
        assessor=GptLlmAssessorMetadata(
            assessor_type=StructuredManualEvidenceAssessorType.GPT_LLM,
            assessor_id="gpt:1",
            provider="OpenAI",
            model_name="gpt-test",
            model_version="1",
            prompt_digest="abc",
        ),
    )
    state = registry.record(assessment=gpt).projected_game
    assert {item.assessment_id for item in state.active_structured_manual_evidence_assessments} == {
        "assessment-2",
        "assessment-gpt",
    }
    restarted = JsonlPregameEventStore(tmp_path / "events.jsonl")
    _, _, after_restart = services(restarted)
    assert after_restart.record(assessment=gpt).append_result.status == AppendStatus.ALREADY_EXISTS


def test_observation_superseded_before_as_of_is_rejected_but_later_correction_is_historical():
    store = InMemoryPregameEventStore()
    _, observations, registry = services(store)
    register_observation(observations)
    replacement = observation(
        observation_id="injury-2",
        reported_at=NOW + timedelta(minutes=2),
        supersedes_observation_id="injury-1",
    )
    register_observation(observations, replacement)
    with pytest.raises(StructuredManualEvidenceAssessmentError, match="superseded"):
        registry.record(
            assessment=assessment(
                as_of_utc=NOW + timedelta(minutes=3),
                assessed_at_utc=NOW + timedelta(minutes=3),
                recorded_at_utc=NOW + timedelta(minutes=3),
            )
        )
    historical = assessment(
        assessment_id="historical",
        as_of_utc=NOW,
        assessed_at_utc=NOW + timedelta(minutes=3),
        recorded_at_utc=NOW + timedelta(minutes=3),
    )
    assert registry.record(assessment=historical).append_result.status == AppendStatus.APPENDED


def test_idempotency_conflict_and_no_implicit_manifest():
    store = InMemoryPregameEventStore()
    _, observations, registry = services(store)
    register_observation(observations)
    first = assessment()
    assert registry.record(assessment=first).append_result.status == AppendStatus.APPENDED
    assert registry.record(assessment=first).append_result.status == AppendStatus.ALREADY_EXISTS
    conflict = assessment(
        status=StructuredManualEvidenceAssessmentStatus.WARNING, reason_codes=("CHECK",)
    )
    assert registry.record(assessment=conflict).append_result.status == AppendStatus.CONFLICT
    assert len(store.list_events(GAME_ID)) == 2
    assert all(
        event.event_type != PregameEventType.VARIANT_B_RESEARCH_RECORDED
        for event in store.list_events(GAME_ID)
    )
    assert structured_manual_evidence_assessment_event_id("assessment-1") == (
        "structured-manual-evidence-assessment:assessment-1"
    )
