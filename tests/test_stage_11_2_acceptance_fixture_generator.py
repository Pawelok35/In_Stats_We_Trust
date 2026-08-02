from __future__ import annotations

from datetime import datetime
from pathlib import Path

from pregame.contracts import CandidateRecord
from pregame.variant_b_audit_integration import (
    StructuredVariantBAuditBuildStatus,
    build_structured_variant_b_audit,
)
from pregame.variant_b_evidence import load_variant_b_evidence
from tests.helpers.stage_11_2_acceptance_factory import (
    FIXED_UTC_TIMESTAMP,
    build_stage_11_2_test_case,
)
from tests.tools import generate_stage_11_2_acceptance_fixtures as generator


def test_shared_factory_builds_through_real_adapter_and_pure_core():
    test_case = build_stage_11_2_test_case()

    assert test_case.candidate.source_ref.endswith("source_model_record.jsonl")
    assert test_case.candidate.source_record_number == 1
    assert test_case.candidate.source_metadata["model_pick"] == test_case.source_model_record
    result = build_structured_variant_b_audit(
        candidate=test_case.candidate,
        evidence=test_case.evidence,
        rules_config=test_case.rules,
        audit_stage="PREKICK",
        generated_at_utc=test_case.generated_at_utc,
    )
    assert result.build_status == StructuredVariantBAuditBuildStatus.BUILT


def test_generator_writes_reloads_and_reruns_byte_identically(tmp_path):
    output_dir = tmp_path / "fixture-output"

    assert generator.main(["--output-dir", str(output_dir)]) == 0
    candidate_path = output_dir / "candidate.json"
    evidence_path = output_dir / "evidence.json"
    first_candidate = candidate_path.read_bytes()
    first_evidence = evidence_path.read_bytes()
    candidate = CandidateRecord.model_validate_json(candidate_path.read_text(encoding="utf-8"))
    evidence = load_variant_b_evidence(evidence_path)
    test_case = build_stage_11_2_test_case()
    result = build_structured_variant_b_audit(
        candidate=candidate,
        evidence=evidence,
        rules_config=test_case.rules,
        audit_stage="PREKICK",
        generated_at_utc=FIXED_UTC_TIMESTAMP,
    )

    assert result.build_status == StructuredVariantBAuditBuildStatus.BUILT
    assert generator.main(["--output-dir", str(output_dir)]) == 0
    assert candidate_path.read_bytes() == first_candidate
    assert evidence_path.read_bytes() == first_evidence


def test_generator_fails_closed_for_different_existing_fixture(tmp_path):
    output_dir = tmp_path / "fixture-output"
    assert generator.main(["--output-dir", str(output_dir)]) == 0
    candidate_path = output_dir / "candidate.json"
    evidence_path = output_dir / "evidence.json"
    evidence_before = evidence_path.read_bytes()
    candidate_path.write_bytes(b"different")

    assert generator.main(["--output-dir", str(output_dir)]) == 1
    assert candidate_path.read_bytes() == b"different"
    assert evidence_path.read_bytes() == evidence_before


def test_generator_removes_files_created_in_a_failed_pair_write(monkeypatch, tmp_path):
    output_dir = tmp_path / "fixture-output"
    original_write = generator._atomic_write

    def fail_evidence(path, content):
        if path.name == "evidence.json":
            raise OSError("simulated evidence write failure")
        original_write(path, content)

    monkeypatch.setattr(generator, "_atomic_write", fail_evidence)

    assert generator.main(["--output-dir", str(output_dir)]) == 1
    assert not (output_dir / "candidate.json").exists()
    assert not (output_dir / "evidence.json").exists()


def test_generator_has_explicit_output_only_no_markdown_or_production_imports():
    source = Path(generator.__file__).read_text(encoding="utf-8")
    assert "required=True" in source
    assert "research/gpt_snapshots" not in source
    assert ".md" not in source
    for directory in (Path("pregame"), Path("scripts"), Path("app"), Path("utils")):
        for path in directory.rglob("*.py"):
            content = path.read_text(encoding="utf-8")
            assert "tests.helpers.stage_11_2_acceptance_factory" not in content


def test_generator_does_not_depend_on_system_time(monkeypatch, tmp_path):
    class UnexpectedNow(datetime):
        @classmethod
        def now(cls, tz=None):
            raise AssertionError("generator must not read system time")

        @classmethod
        def utcnow(cls):
            raise AssertionError("generator must not read system time")

    monkeypatch.setattr(generator, "datetime", UnexpectedNow, raising=False)
    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"

    assert generator.main(["--output-dir", str(first_dir)]) == 0
    assert generator.main(["--output-dir", str(second_dir)]) == 0
    assert (first_dir / "candidate.json").read_bytes() == (
        second_dir / "candidate.json"
    ).read_bytes()
    assert (first_dir / "evidence.json").read_bytes() == (second_dir / "evidence.json").read_bytes()
