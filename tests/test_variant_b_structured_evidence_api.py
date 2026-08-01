from scripts.variant_b_audit import (
    DEFAULT_RULES_CONFIG,
    StructuredVariantBEvidenceError,
    build_audit,
    build_audit_with_structured_evidence,
)


def record():
    return {
        "season": 2026,
        "week": 1,
        "away": "BUF",
        "home": "HOU",
        "selected_team": "BUF",
        "model_winner": "BUF",
        "model_version": "variant_m",
        "tag": "VALUE PLAY",
        "confidence": 75,
        "edge_vs_line": 2.0,
        "model_margin": -4.0,
        "market_margin": -2.0,
        "handicap": -2.0,
        "price": -110,
        "quote_timestamp_utc": "2026-09-10T18:00:00Z",
        "quote_id": "quote-1",
        "book": "BOOK",
        "executable_status": "CONFIRMED",
        "market_scope": "FULL_GAME",
    }


def evidence():
    return {
        "schema_version": "variant_b_gpt_evidence.v1",
        "prompt_version": "variant_b_structured_19_point_evidence.v1",
        "evidence_id": "variant-b-gpt-evidence:test",
        "candidate_id": "candidate-1",
        "game_id": "2026_w01_BUF_at_HOU",
        "selected_team": "BUF",
        "model_variant": "variant_m",
        "research_kind": "FULL_RESEARCH",
        "expected_point_count": 19,
        "point_results": [
            {
                "point_id": i,
                "point_name": f"point-{i}",
                "status": "PASS",
                "summary": "evidence",
                "evidence_items": ["source-1"],
                "data_complete": True,
                "blocking_assessment": "NONE",
                "risk_codes": [],
                "structured_data": {},
            }
            for i in range(1, 20)
        ],
        "probability_assessment": {"p_cover": 0.6, "p_push": 0.0, "p_loss": 0.4},
        "acceptable_quote_frontier": {
            "selected_team": "BUF",
            "minimum_acceptable_spread": -3.0,
            "minimum_acceptable_price": -110,
        },
        "no_chase": {"represented_by_frontier": True},
        "key_number_policy": {"key_numbers": [3, 7], "reject_key_number_loss": True},
        "source_count": 1,
        "generated_at_utc": "2026-09-10T18:00:00Z",
    }


def test_legacy_build_audit_remains_available():
    output = build_audit(record(), DEFAULT_RULES_CONFIG, "PREKICK")
    assert [point["point_number"] for point in output["audit_points"]] == [1, 2, 6, 7, 8, 9, 18, 19]


def test_wrapper_uses_existing_builders_for_18_and_19():
    output = build_audit_with_structured_evidence(
        record(), DEFAULT_RULES_CONFIG, "PREKICK", evidence()
    )
    assert [point["point_number"] for point in output["audit_points"]] == list(range(1, 20))
    assert output["audit_points"][17]["point_name"] == "process_quality"
    assert output["audit_points"][18]["point_name"] == "final_operator_decision"
    assert output["structured_evidence_metadata"]["evidence_id"] == "variant-b-gpt-evidence:test"


def test_wrapper_rejects_candidate_team_conflict():
    value = evidence()
    value["selected_team"] = "HOU"
    try:
        build_audit_with_structured_evidence(record(), DEFAULT_RULES_CONFIG, "PREKICK", value)
    except StructuredVariantBEvidenceError as exc:
        assert exc.reason == "STRUCTURED_EVIDENCE_CONFLICT"
    else:
        raise AssertionError("conflicting evidence must be rejected")
