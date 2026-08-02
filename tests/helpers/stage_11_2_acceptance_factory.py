"""Shared TEST_ONLY factory for the deterministic Stage 11.2 acceptance case."""

from __future__ import annotations

import copy
import json
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pregame.candidate_registry import CandidateRegistryService
from pregame.contracts import CandidateRecord
from pregame.model_output_adapter import MatchupBatchPickOutputAdapter
from pregame.store import InMemoryPregameEventStore
from pregame.variant_b_evidence import (
    EVIDENCE_PROMPT_VERSION,
    EVIDENCE_SCHEMA_VERSION,
    VARIANT_B_POINT_DEFINITIONS,
    VariantBGptEvidenceSidecar,
    evidence_id_for_payload,
    validate_variant_b_evidence,
)
from scripts.variant_b_audit import DEFAULT_RULES_CONFIG

FIXED_UTC_TIMESTAMP = datetime(2026, 9, 10, 18, tzinfo=timezone.utc)
FIXED_UTC_TIMESTAMP_TEXT = "2026-09-10T18:00:00Z"
_SOURCE_REF = "tests/fixtures/stage_11_2/acceptance/source_model_record.jsonl"


@dataclass(frozen=True)
class Stage112TestCase:
    """Complete deterministic input bundle for the Stage 11.2 pure core."""

    source_model_record: dict[str, Any]
    candidate: CandidateRecord
    evidence: VariantBGptEvidenceSidecar
    rules: dict[str, Any]
    generated_at_utc: datetime


def build_stage_11_2_test_case(
    *,
    away: str = "BUF",
    home: str = "HOU",
    selected_team: str = "BUF",
) -> Stage112TestCase:
    """Build the existing successful test case through the real model adapter."""

    source_model_record = build_source_model_record(
        away=away,
        home=home,
        selected_team=selected_team,
    )
    candidate = build_candidate_from_source_record(source_model_record)
    return Stage112TestCase(
        source_model_record=source_model_record,
        candidate=candidate,
        evidence=build_structured_evidence(candidate),
        rules=build_rules(),
        generated_at_utc=FIXED_UTC_TIMESTAMP,
    )


def build_source_model_record(
    *, away: str = "BUF", home: str = "HOU", selected_team: str = "BUF"
) -> dict[str, Any]:
    """Return the one shared successful model-source record for Stage 11.2 tests."""

    return {
        "season": 2026,
        "week": 1,
        "away": away,
        "home": home,
        "model_winner": selected_team,
        "model_version": "variant_m",
        "tag": "VALUE PLAY",
        "confidence": 75.0,
        "edge_vs_line": 2.0,
        "model_margin": -4.0,
        "market_margin": -2.0,
        "handicap": -2.0,
        "price": -110,
        "market": "SPREAD",
        "market_scope": "FULL_GAME",
        "model_generation_book": "BOOK",
        "model_generation_quote_timestamp_utc": FIXED_UTC_TIMESTAMP_TEXT,
        "model_generation_quote_id": "quote-1",
        "model_generation_spread_selected_team": -2.0,
        "model_generation_price": -110,
        "odds_source": "DIRECT_SPORTSBOOK",
        "executable_status": "CONFIRMED_EXECUTABLE",
        "neutral_site": False,
        "preflight": {"status": "PASS", "production_eligible": True},
        "generated_at": FIXED_UTC_TIMESTAMP_TEXT,
    }


def build_candidate_from_source_record(source_model_record: dict[str, Any]) -> CandidateRecord:
    """Adapt a source record using the real JSONL model-output adapter path."""

    registry = CandidateRegistryService(InMemoryPregameEventStore())
    adapter = MatchupBatchPickOutputAdapter(registry)
    with tempfile.TemporaryDirectory() as temp_dir:
        source_path = Path(temp_dir) / "source_model_record.jsonl"
        source_path.write_text(
            json.dumps(source_model_record, ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        result = adapter.import_jsonl(
            source_path,
            season=int(source_model_record["season"]),
            week=int(source_model_record["week"]),
            model_variant=str(source_model_record["model_version"]),
            recorded_at_utc=FIXED_UTC_TIMESTAMP,
            source_ref=_SOURCE_REF,
        )
    candidate = registry.get_candidate(result.candidate_ids[0])
    if candidate is None:
        raise RuntimeError("test adapter did not persist its CandidateRecord")
    return candidate


def build_structured_evidence(
    candidate: CandidateRecord,
    **changes: Any,
) -> VariantBGptEvidenceSidecar:
    """Build and validate the shared complete structured evidence sidecar."""

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
    payload: dict[str, Any] = {
        "evidence_id": "placeholder",
        "schema_version": EVIDENCE_SCHEMA_VERSION,
        "prompt_version": EVIDENCE_PROMPT_VERSION,
        "candidate_id": candidate.candidate_id,
        "game_id": candidate.game_id,
        "season": candidate.season,
        "week": candidate.week,
        "away_team": candidate.away,
        "home_team": candidate.home,
        "selected_team": candidate.selected_team,
        "model_variant": candidate.model_variant,
        "research_kind": "FULL_RESEARCH",
        "generated_at_utc": FIXED_UTC_TIMESTAMP_TEXT,
        "recorded_at_utc": FIXED_UTC_TIMESTAMP_TEXT,
        "source_ref": "gpt",
        "expected_point_count": 19,
        "point_results": points,
        "evidence_sources": [
            {
                "evidence_source_id": "source-1",
                "source_type": "TEST",
                "source_name": "Test",
                "source_ref": "test://source",
                "captured_at_utc": FIXED_UTC_TIMESTAMP_TEXT,
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
            "generated_at_utc": FIXED_UTC_TIMESTAMP_TEXT,
        },
        "acceptable_quote_frontier": {
            "selected_team": candidate.selected_team,
            "market_type": "SPREAD",
            "minimum_acceptable_spread": -3.0,
            "minimum_acceptable_price": -110,
            "frontier_basis": "model",
            "source_refs": ["source-1"],
            "effective_at_utc": FIXED_UTC_TIMESTAMP_TEXT,
        },
        "no_chase": {
            "represented_by_frontier": True,
            "source_refs": ["source-1"],
            "rationale": "frontier",
            "effective_at_utc": FIXED_UTC_TIMESTAMP_TEXT,
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


def build_rules() -> dict[str, Any]:
    """Return the existing successful PREKICK rule configuration unchanged."""

    value = copy.deepcopy(DEFAULT_RULES_CONFIG)
    value["audit_stages"] = ["PREKICK"]
    for rule in value["rules"].values():
        rule["blocking"] = False
    return value
