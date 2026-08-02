from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from pregame.candidate_registry import CandidateRegistryService
from pregame.contracts import CandidateRecord
from pregame.model_output_adapter import MatchupBatchPickOutputAdapter, ModelOutputImportError
from pregame.store import InMemoryPregameEventStore
from pregame.variant_b_audit_integration import (
    StructuredVariantBAuditBuildStatus,
    build_structured_variant_b_audit,
)
from pregame.variant_b_evidence import evidence_id_for_payload, validate_variant_b_evidence
from scripts import build_structured_variant_b_audit as entry_point
from tests.helpers.stage_11_2_acceptance_factory import (
    build_source_model_record,
    build_stage_11_2_test_case,
)

ROOT_DIR = Path(__file__).resolve().parents[1]
RULES_PATH = ROOT_DIR / "config" / "variant_b_rules_prekick.yaml"
MISSING = object()


def _adapter() -> tuple[CandidateRegistryService, MatchupBatchPickOutputAdapter]:
    registry = CandidateRegistryService(InMemoryPregameEventStore())
    return registry, MatchupBatchPickOutputAdapter(registry)


def _write_source_record(tmp_path, record: dict, *, name: str = "model.jsonl") -> Path:
    path = tmp_path / name
    path.write_text(json.dumps(record) + "\n", encoding="utf-8")
    return path


def _run_cli(capsys, *, candidate_path: Path, evidence_path: Path, output_path: Path):
    test_case = build_stage_11_2_test_case()
    exit_code = entry_point.main(
        [
            "--candidate",
            str(candidate_path),
            "--evidence",
            str(evidence_path),
            "--rules",
            str(RULES_PATH),
            "--build-timestamp",
            test_case.generated_at_utc.isoformat().replace("+00:00", "Z"),
            "--output",
            str(output_path),
        ]
    )
    return exit_code, json.loads(capsys.readouterr().out)


def test_adapter_preserves_authoritative_model_generation_quote_id(tmp_path):
    registry, adapter = _adapter()
    record = build_source_model_record()
    record["model_generation_quote_id"] = "TEST_QUOTE_001"

    result = adapter.import_jsonl(
        _write_source_record(tmp_path, record),
        season=2026,
        week=1,
        model_variant="variant_m",
        recorded_at_utc=build_stage_11_2_test_case().generated_at_utc,
    )
    candidate = registry.get_candidate(result.candidate_ids[0])

    assert candidate is not None
    assert candidate.source_metadata["model_pick"]["model_generation_quote_id"] == "TEST_QUOTE_001"


@pytest.mark.parametrize(
    "value",
    [pytest.param(MISSING, id="missing"), None, "", "   ", 123],
)
def test_adapter_rejects_missing_or_invalid_model_generation_quote_id(tmp_path, value):
    registry, adapter = _adapter()
    record = build_source_model_record()
    if value is MISSING:
        record.pop("model_generation_quote_id")
    else:
        record["model_generation_quote_id"] = value

    with pytest.raises(ModelOutputImportError, match="model_generation_quote_id"):
        adapter.import_jsonl(
            _write_source_record(tmp_path, record),
            season=2026,
            week=1,
            model_variant="variant_m",
            recorded_at_utc=build_stage_11_2_test_case().generated_at_utc,
        )
    assert registry.list_candidates(2026, 1) == []


def test_persisted_candidate_without_quote_id_fails_contract_and_pure_core():
    test_case = build_stage_11_2_test_case()
    payload = test_case.candidate.to_json_dict()
    payload["source_metadata"]["model_pick"].pop("model_generation_quote_id")

    with pytest.raises(ValidationError, match="model_generation_quote_id"):
        CandidateRecord.model_validate(payload)

    invalid_candidate = test_case.candidate.model_copy(deep=True)
    invalid_candidate.source_metadata["model_pick"].pop("model_generation_quote_id")
    result = build_structured_variant_b_audit(
        candidate=invalid_candidate,
        evidence=test_case.evidence,
        rules_config=test_case.rules,
        audit_stage="PREKICK",
        generated_at_utc=test_case.generated_at_utc,
    )

    assert result.build_status == StructuredVariantBAuditBuildStatus.BLOCKED_PRECONDITION
    assert result.audit_output is None
    assert "SOURCE_PICK_FIELD_MISSING:model_generation_quote_id" in result.warnings


def test_cli_fails_closed_without_quote_id_even_with_candidate_timestamp_evidence_and_filename(
    tmp_path, capsys
):
    test_case = build_stage_11_2_test_case()
    candidate_payload = test_case.candidate.to_json_dict()
    candidate_payload["source_metadata"]["model_pick"].pop("model_generation_quote_id")
    candidate_path = tmp_path / "candidate_TEST_QUOTE_001.json"
    evidence_path = tmp_path / "evidence.json"
    output_path = tmp_path / "audit.json"
    candidate_path.write_text(json.dumps(candidate_payload), encoding="utf-8")

    evidence_payload = test_case.evidence.to_json_dict()
    evidence_payload["evidence_sources"][0]["data_fields"] = {
        "model_generation_quote_id": "EVIDENCE_QUOTE_001"
    }
    evidence_payload["evidence_id"] = evidence_id_for_payload(evidence_payload)
    evidence_path.write_text(
        json.dumps(validate_variant_b_evidence(evidence_payload).to_json_dict()),
        encoding="utf-8",
    )

    exit_code, payload = _run_cli(
        capsys,
        candidate_path=candidate_path,
        evidence_path=evidence_path,
        output_path=output_path,
    )

    assert exit_code != 0
    assert payload["status"] == "INVALID_INPUT"
    assert payload["written"] is False
    assert not output_path.exists()


def test_valid_provenance_reaches_source_pick_and_cli_remains_idempotent(tmp_path, capsys):
    test_case = build_stage_11_2_test_case()
    result = build_structured_variant_b_audit(
        candidate=test_case.candidate,
        evidence=test_case.evidence,
        rules_config=test_case.rules,
        audit_stage="PREKICK",
        generated_at_utc=test_case.generated_at_utc,
    )
    candidate_path = tmp_path / "candidate.json"
    evidence_path = tmp_path / "evidence.json"
    output_path = tmp_path / "audit.json"
    candidate_path.write_text(json.dumps(test_case.candidate.to_json_dict()), encoding="utf-8")
    evidence_path.write_text(json.dumps(test_case.evidence.to_json_dict()), encoding="utf-8")

    assert result.build_status == StructuredVariantBAuditBuildStatus.BUILT
    assert result.source_pick["model_generation_quote_id"] == "quote-1"
    assert result.source_pick["quote_id"] == "quote-1"
    assert result.audit_output["source_pick"]["model_generation_quote_id"] == "quote-1"

    first_exit, first = _run_cli(
        capsys,
        candidate_path=candidate_path,
        evidence_path=evidence_path,
        output_path=output_path,
    )
    second_exit, second = _run_cli(
        capsys,
        candidate_path=candidate_path,
        evidence_path=evidence_path,
        output_path=output_path,
    )

    assert first_exit == 0
    assert first["status"] == "WRITTEN" and first["written"] is True
    assert second_exit == 0
    assert second["status"] == "ALREADY_EXISTS_IDENTICAL" and second["written"] is False
