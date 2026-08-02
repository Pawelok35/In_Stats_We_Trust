from __future__ import annotations

import json
from datetime import datetime, timezone

from pregame.variant_b_audit_orchestrator import (
    StructuredVariantBAuditOrchestrationStatus,
    StructuredVariantBAuditOrchestrator,
)
from tests.test_pregame_variant_b_audit_integration import candidate, evidence, rules

NOW = datetime(2026, 9, 10, 18, tzinfo=timezone.utc)


def write_inputs(tmp_path, candidate_value=None):
    candidate_value = candidate_value or candidate()
    evidence_value = evidence(candidate_value=candidate_value)
    candidate_path = tmp_path / "candidate.json"
    evidence_path = tmp_path / "evidence.json"
    candidate_path.write_text(json.dumps(candidate_value.to_json_dict()), encoding="utf-8")
    evidence_path.write_text(json.dumps(evidence_value.to_json_dict()), encoding="utf-8")
    return candidate_path, evidence_path


def test_successful_write_and_identical_rerun_are_immutable(tmp_path):
    candidate_path, evidence_path = write_inputs(tmp_path)
    output = tmp_path / "audit.json"
    orchestrator = StructuredVariantBAuditOrchestrator()

    first = orchestrator.run(
        candidate_path=candidate_path,
        evidence_path=evidence_path,
        rules_config=rules(),
        build_timestamp=NOW,
        output_path=output,
    )
    original = output.read_bytes()
    second = orchestrator.run(
        candidate_path=candidate_path,
        evidence_path=evidence_path,
        rules_config=rules(),
        build_timestamp=NOW,
        output_path=output,
    )

    assert first.status == StructuredVariantBAuditOrchestrationStatus.WRITTEN
    assert first.written is True
    assert second.status == StructuredVariantBAuditOrchestrationStatus.ALREADY_EXISTS_IDENTICAL
    assert second.written is False
    assert output.read_bytes() == original


def test_blocked_core_does_not_create_or_replace_artifact(tmp_path):
    candidate_path, evidence_path = write_inputs(tmp_path)
    output = tmp_path / "audit.json"
    output.write_bytes(b"existing")
    payload = json.loads(candidate_path.read_text(encoding="utf-8"))
    payload["source_metadata"]["model_pick"].pop("market_scope")
    candidate_path.write_text(json.dumps(payload), encoding="utf-8")

    result = StructuredVariantBAuditOrchestrator().run(
        candidate_path=candidate_path,
        evidence_path=evidence_path,
        rules_config=rules(),
        build_timestamp=NOW,
        output_path=output,
    )

    assert result.status == StructuredVariantBAuditOrchestrationStatus.BLOCKED
    assert result.written is False
    assert output.read_bytes() == b"existing"


def test_different_existing_artifact_is_not_overwritten(tmp_path):
    candidate_path, evidence_path = write_inputs(tmp_path)
    output = tmp_path / "audit.json"
    output.write_bytes(b"different")

    result = StructuredVariantBAuditOrchestrator().run(
        candidate_path=candidate_path,
        evidence_path=evidence_path,
        rules_config=rules(),
        build_timestamp=NOW,
        output_path=output,
    )

    assert result.status == StructuredVariantBAuditOrchestrationStatus.COLLISION
    assert output.read_bytes() == b"different"
