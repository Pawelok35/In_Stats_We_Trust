from __future__ import annotations

import copy
from datetime import datetime, timezone

from pregame.contracts import CandidateRecord
from pregame.events import CandidateStatus
from pregame.variant_b_audit_integration import (
    StructuredVariantBAuditBuildReason,
    StructuredVariantBAuditBuildStatus,
    build_structured_variant_b_audit,
)
from pregame.variant_b_evidence import (
    EVIDENCE_PROMPT_VERSION,
    EVIDENCE_SCHEMA_VERSION,
    VARIANT_B_POINT_DEFINITIONS,
    evidence_id_for_payload,
    validate_variant_b_evidence,
)
from scripts.variant_b_audit import DEFAULT_RULES_CONFIG

NOW = datetime(2026, 9, 10, 18, tzinfo=timezone.utc)


def candidate(*, away="BUF", home="HOU", selected_team="BUF", **changes):
    model_pick = {
        "season": 2026,
        "week": 1,
        "away": away,
        "home": home,
        "model_winner": selected_team,
        "model_version": "variant_m",
        "tag": "VALUE PLAY",
        "market": "SPREAD",
        "market_scope": "FULL_GAME",
        "model_generation_book": "BOOK",
        "model_generation_quote_timestamp_utc": "2026-09-10T18:00:00Z",
        "model_generation_quote_id": "quote-1",
        "model_generation_spread_selected_team": -2.0,
        "model_generation_price": -110,
        "odds_source": "DIRECT_SPORTSBOOK",
        "executable_status": "CONFIRMED_EXECUTABLE",
        "neutral_site": False,
        "preflight": {"status": "PASS", "production_eligible": True},
    }
    payload = {
        "candidate_id": "candidate-1",
        "game_id": f"2026_w01_{away}_at_{home}",
        "season": 2026,
        "week": 1,
        "away": away,
        "home": home,
        "status": CandidateStatus.MODEL_CANDIDATE,
        "created_at_utc": NOW,
        "model_variant": "variant_m",
        "selected_team": selected_team,
        "model_tag": "VALUE PLAY",
        "production_eligible": True,
        "confidence": 75.0,
        "edge_vs_line": 2.0,
        "model_margin": -4.0,
        "market_margin_at_scan": -2.0,
        "spread_at_scan": -2.0,
        "price_at_scan": -110,
        "preflight_status": "PASS",
        "model_generated_at_utc": NOW,
        "source_metadata": {"model_pick": model_pick},
    }
    payload.update(changes)
    return CandidateRecord(**payload)


def evidence(*, candidate_value=None, **changes):
    candidate_value = candidate_value or candidate()
    timestamp = "2026-09-10T18:00:00Z"
    points = [
        {
            "point_id": point_id,
            "point_name": name,
            "status": "PASS",
            "gpt_assessment": "evidence",
            "blocking_assessment": "NONE",
            "summary": "fact",
            "evidence_items": ["source-1"],
            "data_complete": True,
        }
        for point_id, name, _ in VARIANT_B_POINT_DEFINITIONS
    ]
    payload = {
        "evidence_id": "placeholder",
        "schema_version": EVIDENCE_SCHEMA_VERSION,
        "prompt_version": EVIDENCE_PROMPT_VERSION,
        "candidate_id": candidate_value.candidate_id,
        "game_id": candidate_value.game_id,
        "season": candidate_value.season,
        "week": candidate_value.week,
        "away_team": candidate_value.away,
        "home_team": candidate_value.home,
        "selected_team": candidate_value.selected_team,
        "model_variant": candidate_value.model_variant,
        "research_kind": "FULL_RESEARCH",
        "generated_at_utc": timestamp,
        "recorded_at_utc": timestamp,
        "source_ref": "gpt",
        "expected_point_count": 19,
        "point_results": points,
        "evidence_sources": [
            {
                "evidence_source_id": "source-1",
                "source_type": "TEST",
                "source_name": "Test",
                "source_ref": "test://source",
                "captured_at_utc": timestamp,
                "reliability": "HIGH",
                "fact_summary": "fact",
                "supports_assessment": "TEST",
            }
        ],
        "probability_assessment": {
            "p_cover": 0.6,
            "p_push": 0.0,
            "p_loss": 0.4,
            "method": "model",
            "source_refs": ["source-1"],
            "generated_at_utc": timestamp,
        },
        "acceptable_quote_frontier": {
            "selected_team": candidate_value.selected_team,
            "market_type": "SPREAD",
            "minimum_acceptable_spread": -3.0,
            "minimum_acceptable_price": -110,
            "frontier_basis": "model",
            "source_refs": ["source-1"],
            "effective_at_utc": timestamp,
        },
        "no_chase": {
            "represented_by_frontier": True,
            "source_refs": ["source-1"],
            "rationale": "frontier",
            "effective_at_utc": timestamp,
        },
        "key_number_policy": {
            "key_numbers": [3.0, 7.0],
            "reject_key_number_loss": True,
            "source_refs": ["source-1"],
            "methodology_note": "explicit",
        },
        "overall_summary": "complete",
        "source_count": 1,
    }
    payload.update(changes)
    payload["evidence_id"] = evidence_id_for_payload(payload)
    return validate_variant_b_evidence(payload)


def rules():
    value = copy.deepcopy(DEFAULT_RULES_CONFIG)
    value["audit_stages"] = ["PREKICK"]
    for rule in value["rules"].values():
        rule["blocking"] = False
    return value


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
