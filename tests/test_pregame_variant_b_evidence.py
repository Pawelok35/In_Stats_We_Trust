from pathlib import Path

import pytest

from pregame.variant_b_evidence import (
    EVIDENCE_PROMPT_VERSION,
    EVIDENCE_SCHEMA_VERSION,
    POINT_NAMES,
    VARIANT_B_POINT_DEFINITIONS,
    SidecarWriteStatus,
    evidence_id_for_payload,
    load_variant_b_evidence,
    validate_variant_b_evidence,
    write_variant_b_evidence_sidecar,
)

NOW = "2026-09-10T18:00:00Z"


def payload():
    points = []
    for point_id, name, _ in VARIANT_B_POINT_DEFINITIONS:
        points.append(
            {
                "point_id": point_id,
                "point_name": name,
                "status": "PASS",
                "gpt_assessment": "evidence",
                "blocking_assessment": "NONE",
                "summary": "short fact",
                "evidence_items": ["source-1"],
                "structured_data": {},
                "data_complete": True,
                "no_data_reason": None,
            }
        )
    value = {
        "evidence_id": "placeholder",
        "schema_version": EVIDENCE_SCHEMA_VERSION,
        "prompt_version": EVIDENCE_PROMPT_VERSION,
        "candidate_id": "candidate-1",
        "game_id": "2026_w01_BUF_at_HOU",
        "season": 2026,
        "week": 1,
        "away_team": "BUF",
        "home_team": "HOU",
        "selected_team": "BUF",
        "model_variant": "variant_m",
        "research_kind": "FULL_RESEARCH",
        "generated_at_utc": NOW,
        "recorded_at_utc": NOW,
        "source_ref": "gpt",
        "expected_point_count": 19,
        "point_results": points,
        "evidence_sources": [
            {
                "evidence_source_id": "source-1",
                "source_type": "MODEL_OUTPUT",
                "source_name": "Synthetic model",
                "source_ref": "synthetic://model",
                "captured_at_utc": NOW,
                "reliability": "HIGH",
                "fact_summary": "Synthetic test evidence.",
                "supports_assessment": "MODEL",
            }
        ],
        "probability_assessment": {
            "p_cover": 0.6,
            "p_push": 0.0,
            "p_loss": 0.4,
            "method": "model",
            "source_refs": ["source-1"],
            "generated_at_utc": NOW,
        },
        "acceptable_quote_frontier": {
            "selected_team": "BUF",
            "market_type": "SPREAD",
            "minimum_acceptable_spread": -3.0,
            "minimum_acceptable_price": -110,
            "frontier_basis": "model",
            "source_refs": ["source-1"],
            "effective_at_utc": NOW,
        },
        "no_chase": {
            "represented_by_frontier": True,
            "source_refs": ["source-1"],
            "rationale": "same frontier",
            "effective_at_utc": NOW,
        },
        "key_number_policy": {
            "key_numbers": [3, 7, 10, 14],
            "reject_key_number_loss": True,
            "source_refs": ["source-1"],
            "methodology_note": "explicit",
        },
        "injury_evidence": [
            {
                "player": "Player",
                "team": "BUF",
                "position": "QB",
                "role": "starter",
                "starter_status": "STARTER",
                "practice_status": "FULL",
                "game_status": "ACTIVE",
                "injury_type": "none",
                "reported_at_utc": NOW,
                "source_ref": "official",
                "impact": "LOW",
                "blocking_assessment": "NONE",
            }
        ],
        "public_betting_evidence": [
            {
                "market_type": "SPREAD",
                "side": "BUF",
                "bet_percentage": 55,
                "money_percentage": None,
                "source": "source",
                "source_scope": "aggregate",
                "captured_at_utc": NOW,
                "reliability": "MEDIUM",
            }
        ],
        "weather_evidence": [
            {
                "venue": "HOU",
                "roof_status": "INDOOR",
                "forecast_for_utc": NOW,
                "captured_at_utc": NOW,
                "source_ref": "weather",
                "reliability": "HIGH",
                "impact_assessment": "LOW",
            }
        ],
        "market_evidence": [],
        "blocking_risk_codes_reported": [],
        "warnings_reported": [],
        "overall_summary": "Evidence only",
        "source_count": 1,
    }
    value["evidence_id"] = evidence_id_for_payload(value)
    return value


def test_registry_has_exact_current_19_points():
    assert len(VARIANT_B_POINT_DEFINITIONS) == 19
    assert list(POINT_NAMES) == list(range(1, 20))


def test_valid_sidecar_round_trip_and_atomic_write(tmp_path: Path):
    evidence = validate_variant_b_evidence(payload())
    assert evidence.completeness_summary()["structurally_ready_for_variant_b_import"] is True
    first = write_variant_b_evidence_sidecar(evidence, output_root=tmp_path)
    assert first.status == SidecarWriteStatus.WRITTEN
    assert load_variant_b_evidence(Path(first.path)).evidence_id == evidence.evidence_id
    assert (
        write_variant_b_evidence_sidecar(evidence, output_root=tmp_path).status
        == SidecarWriteStatus.ALREADY_EXISTS
    )


@pytest.mark.parametrize(
    "field", ["operator_decision", "final_pick", "approved_pick", "stake", "place_bet"]
)
def test_forbidden_operator_extras_are_rejected(field):
    value = payload()
    value[field] = "forbidden"
    with pytest.raises(ValueError):
        validate_variant_b_evidence(value)


def test_missing_point_and_bad_probability_fail_closed():
    value = payload()
    value["point_results"] = value["point_results"][:-1]
    with pytest.raises(ValueError):
        validate_variant_b_evidence(value)
    value = payload()
    value["probability_assessment"]["p_loss"] = 0.3
    with pytest.raises(ValueError):
        validate_variant_b_evidence(value)


def test_deterministic_id_excludes_recorded_timestamp():
    one = payload()
    two = payload()
    two["recorded_at_utc"] = "2026-09-10T19:00:00Z"
    assert evidence_id_for_payload(one) == evidence_id_for_payload(two)
