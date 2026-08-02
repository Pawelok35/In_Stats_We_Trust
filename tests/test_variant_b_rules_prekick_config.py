from __future__ import annotations

import json
from pathlib import Path

from scripts import build_structured_variant_b_audit as entry_point
from tests.helpers.stage_11_2_acceptance_factory import build_stage_11_2_test_case

ROOT_DIR = Path(__file__).resolve().parents[1]
PREKICK_RULES_PATH = ROOT_DIR / "config" / "variant_b_rules_prekick.yaml"
MULTI_STAGE_RULES_PATH = ROOT_DIR / "config" / "variant_b_rules.yaml"


def _write_shared_inputs(tmp_path):
    test_case = build_stage_11_2_test_case()
    candidate_path = tmp_path / "candidate.json"
    evidence_path = tmp_path / "evidence.json"
    candidate_path.write_text(
        json.dumps(test_case.candidate.to_json_dict()),
        encoding="utf-8",
    )
    evidence_path.write_text(
        json.dumps(test_case.evidence.to_json_dict()),
        encoding="utf-8",
    )
    return test_case, candidate_path, evidence_path


def test_single_stage_prekick_yaml_is_semantically_identical_to_shared_factory_rules():
    loaded = entry_point.load_rules(PREKICK_RULES_PATH)
    expected = build_stage_11_2_test_case().rules

    assert loaded == expected
    assert loaded["audit_stages"] == ["PREKICK"]
    assert len(loaded["audit_stages"]) == 1


def test_single_candidate_cli_accepts_explicit_prekick_rules(tmp_path, capsys):
    test_case, candidate_path, evidence_path = _write_shared_inputs(tmp_path)
    output_path = tmp_path / "audit.json"

    exit_code = entry_point.main(
        [
            "--candidate",
            str(candidate_path),
            "--evidence",
            str(evidence_path),
            "--rules",
            str(PREKICK_RULES_PATH),
            "--build-timestamp",
            test_case.generated_at_utc.isoformat().replace("+00:00", "Z"),
            "--output",
            str(output_path),
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["status"] == "WRITTEN"
    assert payload["written"] is True
    assert output_path.exists()


def test_multi_stage_rules_remain_distinct_and_cli_rejects_them(tmp_path, capsys):
    test_case, candidate_path, evidence_path = _write_shared_inputs(tmp_path)
    multi_stage_rules = entry_point.load_rules(MULTI_STAGE_RULES_PATH)
    output_path = tmp_path / "audit.json"

    assert len(multi_stage_rules["audit_stages"]) > 1
    exit_code = entry_point.main(
        [
            "--candidate",
            str(candidate_path),
            "--evidence",
            str(evidence_path),
            "--rules",
            str(MULTI_STAGE_RULES_PATH),
            "--build-timestamp",
            test_case.generated_at_utc.isoformat().replace("+00:00", "Z"),
            "--output",
            str(output_path),
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 3
    assert payload["status"] == "INVALID_INPUT"
    assert payload["error"] == "rules_config must contain exactly one explicit audit stage"
    assert not output_path.exists()
