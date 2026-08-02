from __future__ import annotations

from pregame.events import CandidateStatus
from pregame.variant_b_audit_integration import (
    StructuredVariantBAuditBuildReason,
    StructuredVariantBAuditBuildStatus,
    build_structured_variant_b_audit,
)
from pregame.variant_b_evidence import evidence_id_for_payload, validate_variant_b_evidence
from tests.helpers.stage_11_2_acceptance_factory import FIXED_UTC_TIMESTAMP as NOW
from tests.helpers.stage_11_2_acceptance_factory import (
    build_stage_11_2_test_case,
    build_structured_evidence,
)


def candidate(*, away="BUF", home="HOU", selected_team="BUF", **changes):
    value = build_stage_11_2_test_case(
        away=away,
        home=home,
        selected_team=selected_team,
    ).candidate
    return value.model_copy(update=changes) if changes else value


def evidence(*, candidate_value=None, **changes):
    return build_structured_evidence(candidate_value or candidate(), **changes)


def rules():
    return build_stage_11_2_test_case().rules


def build(candidate_value=None, evidence_value=None):
    candidate_value = candidate_value or candidate()
    evidence_value = evidence_value or evidence(candidate_value=candidate_value)
    return build_structured_variant_b_audit(
        candidate=candidate_value,
        evidence=evidence_value,
        rules_config=rules(),
        audit_stage="PREKICK",
        generated_at_utc=NOW,
    )


def test_builds_canonical_audit_from_authoritative_away_candidate():
    result = build()

    assert result.build_status == StructuredVariantBAuditBuildStatus.BUILT
    assert result.source_pick["away"] == "BUF"
    assert result.source_pick["home"] == "HOU"
    assert result.audit_output["event"]["away"] == "BUF"
    assert result.audit_output["event"]["home"] == "HOU"
    assert isinstance(result.audit_output["source_pick"]["p_push"], float)


def test_selected_home_team_does_not_change_authoritative_matchup_sides():
    candidate_value = candidate(away="CLE", home="JAX", selected_team="JAX")
    result = build(candidate_value)

    assert result.build_status == StructuredVariantBAuditBuildStatus.BUILT
    assert result.audit_output["event"] == {
        "season": 2026,
        "week": 1,
        "home": "JAX",
        "away": "CLE",
        "selected_team": "JAX",
        "neutral_site": False,
    }


def test_evidence_matchup_mismatch_blocks_without_wrapper_output():
    candidate_value = candidate()
    bad_evidence = evidence(candidate_value=candidate_value, home_team="MIA")
    result = build(candidate_value, bad_evidence)

    assert result.build_status == StructuredVariantBAuditBuildStatus.BLOCKED_PRECONDITION
    assert StructuredVariantBAuditBuildReason.EVIDENCE_MATCHUP_MISMATCH in result.reason_codes
    assert result.audit_output is None


def test_evidence_market_mismatch_blocks_without_overriding_candidate_quote():
    candidate_value = candidate()
    candidate_value.source_metadata["model_pick"]["market"] = "MONEYLINE"

    result = build(candidate_value)

    assert result.build_status == StructuredVariantBAuditBuildStatus.BLOCKED_PRECONDITION
    assert StructuredVariantBAuditBuildReason.EVIDENCE_MARKET_MISMATCH in result.reason_codes
    assert result.audit_output is None


def test_candidate_identity_mismatch_blocks_without_parsing_game_id():
    candidate_value = candidate(game_id="2026_w01_MIA_at_NYJ")
    result = build(candidate_value)

    assert result.build_status == StructuredVariantBAuditBuildStatus.BLOCKED_PRECONDITION
    assert StructuredVariantBAuditBuildReason.CANDIDATE_GAME_ID_MISMATCH in result.reason_codes
    assert result.audit_output is None


def test_incomplete_quote_provenance_blocks_without_defaulting():
    candidate_value = candidate()
    candidate_value.source_metadata["model_pick"].pop("model_generation_book")
    result = build(candidate_value)

    assert result.build_status == StructuredVariantBAuditBuildStatus.BLOCKED_PRECONDITION
    assert result.reason_codes == (StructuredVariantBAuditBuildReason.SOURCE_PICK_FIELD_MISSING,)
    assert "SOURCE_PICK_FIELD_MISSING:book" in result.warnings


def test_blocked_candidate_and_incomplete_evidence_are_fail_closed():
    candidate_value = candidate(status=CandidateStatus.BLOCKED, production_eligible=False)
    incomplete = evidence(candidate_value=candidate_value)
    incomplete = incomplete.model_copy(update={"point_results": incomplete.point_results[:-1]})
    result = build(candidate_value, incomplete)

    assert result.build_status == StructuredVariantBAuditBuildStatus.BLOCKED_PRECONDITION
    assert StructuredVariantBAuditBuildReason.CANDIDATE_BLOCKED in result.reason_codes
    assert StructuredVariantBAuditBuildReason.EVIDENCE_NOT_STRUCTURALLY_READY in result.reason_codes


def test_blocking_evidence_status_is_not_returned_as_a_success():
    candidate_value = candidate()
    payload = evidence(candidate_value=candidate_value).to_json_dict()
    payload["point_results"][0]["status"] = "BLOCKING_RISK"
    payload["point_results"][0]["blocking_assessment"] = "BLOCK"
    payload["evidence_id"] = evidence_id_for_payload(payload)
    blocking = validate_variant_b_evidence(payload)

    result = build(candidate_value, blocking)

    assert result.build_status == StructuredVariantBAuditBuildStatus.BLOCKED_PRECONDITION
    assert (
        StructuredVariantBAuditBuildReason.STRUCTURED_AUDIT_BLOCKING_STATUS in result.reason_codes
    )
    assert result.audit_output is None


def test_build_is_deterministic_and_does_not_mutate_inputs():
    candidate_value = candidate()
    evidence_value = evidence(candidate_value=candidate_value)
    candidate_before = candidate_value.to_json_dict()
    evidence_before = evidence_value.to_json_dict()

    first = build(candidate_value, evidence_value)
    second = build(candidate_value, evidence_value)

    assert first == second
    assert candidate_value.to_json_dict() == candidate_before
    assert evidence_value.to_json_dict() == evidence_before
