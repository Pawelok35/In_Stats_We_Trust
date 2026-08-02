from datetime import datetime, timezone
from pathlib import Path

from pregame.contracts import (
    CandidateRecord,
    FinalQuoteRuntimePolicy,
    MarketSnapshot,
    VariantBPointResult,
    VariantBResearchRecord,
)
from pregame.events import (
    CandidateStatus,
    ExecutableStatus,
    FinalQuoteGateStatus,
    MarketQualityStatus,
    MarketType,
    SnapshotKind,
    VariantBPolicyBuildReason,
    VariantBPolicyBuildStatus,
    VariantBResearchKind,
    VariantBResearchStatus,
)
from pregame.final_quote_gate import evaluate_final_quote
from pregame.variant_b_policy_adapter import build_final_quote_policy
from pregame.variant_b_research import adapt_variant_b_output

NOW = datetime(2026, 9, 10, 18, tzinfo=timezone.utc)


def candidate(**changes):
    data = dict(
        candidate_id="candidate-1",
        game_id="2026_w01_BUF_at_HOU",
        season=2026,
        week=1,
        away="BUF",
        home="HOU",
        status=CandidateStatus.MODEL_CANDIDATE,
        created_at_utc=NOW,
        model_variant="variant_m",
        selected_team="BUF",
        model_tag="VALUE PLAY",
        production_eligible=True,
    )
    data.update(changes)
    return CandidateRecord(**data)


def runtime(**changes):
    data = dict(
        runtime_policy_id="runtime-1",
        source="operator",
        created_at_utc=NOW,
        max_quote_age_seconds=300,
        allowed_quality_statuses=(MarketQualityStatus.MARKET_GRADE,),
        allowed_executable_statuses=(ExecutableStatus.CONFIRMED,),
        allowed_books=("BOOK_A",),
        key_numbers=(3.0, 7.0),
        reject_key_number_loss=True,
    )
    data.update(changes)
    return FinalQuoteRuntimePolicy(**data)


def research(**changes):
    points = tuple(
        VariantBPointResult(
            point_id=i,
            point_name=f"point {i}",
            status="PASS",
            blocking=False,
            evidence_present=True,
        )
        for i in range(1, 20)
    )
    data = dict(
        research_id="research-1",
        candidate_id="candidate-1",
        game_id="2026_w01_BUF_at_HOU",
        model_variant="variant_m",
        selected_team="BUF",
        research_kind=VariantBResearchKind.FULL_RESEARCH,
        research_status=VariantBResearchStatus.APPROVED,
        framework_version="v1",
        audit_schema_version="v1",
        source_ref="audit.json",
        source_sha256="a" * 64,
        generated_at_utc=NOW,
        recorded_at_utc=NOW,
        expected_point_count=19,
        present_point_count=19,
        sections_complete=True,
        point_results=points,
        research_approved=True,
        acceptable_quote_frontier_raw={
            "selected_team": "BUF",
            "market_type": "SPREAD",
            "minimum_acceptable_spread": -3.0,
            "minimum_acceptable_price": -110,
        },
        no_chase_raw={"represented_by_frontier": True},
        key_number_check_raw={"key_numbers": [3.0, 7.0], "reject_key_number_loss": True},
    )
    data.update(changes)
    return VariantBResearchRecord(**data)


def test_builds_policy_only_from_explicit_structured_fields():
    result = build_final_quote_policy(
        candidate=candidate(), research=research(), runtime_policy=runtime(), built_at_utc=NOW
    )
    assert result.status == VariantBPolicyBuildStatus.BUILT
    assert result.policy is not None
    assert result.policy.minimum_acceptable_spread == -3.0
    assert result.policy.minimum_acceptable_price == -110
    assert result.policy.key_numbers == (3.0, 7.0)


def test_path_only_frontier_and_unstructured_no_chase_fail_closed():
    result = build_final_quote_policy(
        candidate=candidate(),
        research=research(
            acceptable_quote_frontier_raw={"acceptable_quote_frontier_path": "frontier.json"},
            no_chase_raw={"no_chase_status": "PASS"},
        ),
        runtime_policy=runtime(),
        built_at_utc=NOW,
    )
    assert result.policy is None
    assert VariantBPolicyBuildReason.FRONTIER_NOT_STRUCTURED in result.reason_codes
    assert VariantBPolicyBuildReason.NO_CHASE_NOT_STRUCTURED in result.reason_codes


def test_missing_key_number_source_has_no_hidden_default():
    result = build_final_quote_policy(
        candidate=candidate(),
        research=research(key_number_check_raw=None),
        runtime_policy=runtime(key_numbers=None, reject_key_number_loss=None),
        built_at_utc=NOW,
    )
    assert result.policy is None
    assert VariantBPolicyBuildReason.KEY_NUMBER_POLICY_MISSING in result.reason_codes


def test_policy_id_is_independent_of_build_timestamp():
    first = build_final_quote_policy(
        candidate=candidate(), research=research(), runtime_policy=runtime(), built_at_utc=NOW
    )
    later = build_final_quote_policy(
        candidate=candidate(),
        research=research(),
        runtime_policy=runtime(),
        built_at_utc=datetime(2026, 9, 10, 19, tzinfo=timezone.utc),
    )
    assert first.policy is not None and later.policy is not None
    assert first.policy.policy_id == later.policy.policy_id


def test_unapproved_research_and_legacy_recommendation_cannot_build_policy():
    result = build_final_quote_policy(
        candidate=candidate(),
        research=research(
            research_approved=False,
            research_status=VariantBResearchStatus.COMPLETE,
            legacy_audit_recommendation={"verdict": "PLAY"},
        ),
        runtime_policy=runtime(),
        built_at_utc=NOW,
    )
    assert result.policy is None
    assert VariantBPolicyBuildReason.RESEARCH_NOT_APPROVED in result.reason_codes
    assert "LEGACY_RECOMMENDATION_IGNORED" in result.warnings


def test_current_real_variant_b_artifact_fails_closed_without_text_parsing():
    import json

    path = Path("research/variant_b_week_flow/2026/week_01/2026_w01_BUF_at_HOU_BUF.json")
    payload = json.loads(path.read_text(encoding="utf-8"))
    record = adapt_variant_b_output(
        payload,
        candidate=candidate(model_generated_at_utc=NOW),
        research_kind=VariantBResearchKind.FULL_RESEARCH,
        recorded_at_utc=NOW,
        source_ref=path.name,
    )
    result = build_final_quote_policy(
        candidate=candidate(), research=record, runtime_policy=runtime(), built_at_utc=NOW
    )
    assert result.policy is None
    assert result.status in {
        VariantBPolicyBuildStatus.BLOCKED,
        VariantBPolicyBuildStatus.INCOMPLETE,
    }
    assert VariantBPolicyBuildReason.RESEARCH_BLOCKED in result.reason_codes
    assert VariantBPolicyBuildReason.FRONTIER_NOT_STRUCTURED in result.reason_codes


def test_built_policy_integrates_with_gate_without_operator_promotion():
    result = build_final_quote_policy(
        candidate=candidate(spread_at_scan=-2.5),
        research=research(),
        runtime_policy=runtime(),
        built_at_utc=NOW,
    )
    assert result.policy is not None
    quote = MarketSnapshot(
        snapshot_id="final-1",
        game_id="2026_w01_BUF_at_HOU",
        snapshot_kind=SnapshotKind.FINAL,
        captured_at_utc=NOW,
        book="BOOK_A",
        source="book",
        market_type=MarketType.SPREAD,
        quality_status=MarketQualityStatus.MARKET_GRADE,
        executable_status=ExecutableStatus.CONFIRMED,
        selected_side="BUF",
        spread=-2.5,
        spread_price=-110,
    )
    gate = evaluate_final_quote(
        candidate(spread_at_scan=-2.5), quote, result.policy, evaluated_at_utc=NOW
    )
    assert gate.primary_status == FinalQuoteGateStatus.FINAL_QUOTE_VALID
    assert gate.passed is True
