from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from pregame.contracts import CandidateRecord
from pregame.variant_b_audit_integration import (
    StructuredVariantBAuditBuildReason,
    StructuredVariantBAuditBuildStatus,
    _canonical_json,
    _sha256,
    build_structured_variant_b_audit,
)
from pregame.variant_b_evidence import load_variant_b_evidence
from scripts import build_structured_variant_b_audit as entry_point
from tests.helpers.stage_11_2_acceptance_factory import build_stage_11_2_test_case

ROOT_DIR = Path(__file__).resolve().parents[1]
FIXTURE_DIR = ROOT_DIR / "tests" / "fixtures" / "stage_11_2" / "acceptance"
CANDIDATE_PATH = FIXTURE_DIR / "candidate.json"
EVIDENCE_PATH = FIXTURE_DIR / "evidence.json"
README_PATH = FIXTURE_DIR / "README.md"
RULES_PATH = ROOT_DIR / "config" / "variant_b_rules_prekick.yaml"
BUILD_TIMESTAMP = datetime(2026, 9, 10, 18, tzinfo=timezone.utc)
BUILD_TIMESTAMP_TEXT = "2026-09-10T18:00:00Z"


def _load_inputs():
    candidate = CandidateRecord.model_validate_json(CANDIDATE_PATH.read_text(encoding="utf-8"))
    evidence = load_variant_b_evidence(EVIDENCE_PATH)
    rules = entry_point.load_rules(RULES_PATH)
    return candidate, evidence, rules


def _build_core():
    candidate, evidence, rules = _load_inputs()
    result = build_structured_variant_b_audit(
        candidate=candidate,
        evidence=evidence,
        rules_config=rules,
        audit_stage="PREKICK",
        generated_at_utc=BUILD_TIMESTAMP,
    )
    assert result.build_status == StructuredVariantBAuditBuildStatus.BUILT
    assert result.reason_codes == (StructuredVariantBAuditBuildReason.STRUCTURED_AUDIT_BUILT,)
    assert result.build_id and result.audit_output_sha256 and result.audit_output
    return candidate, evidence, rules, result


def _run_cli(capsys, *, output_path: Path):
    exit_code = entry_point.main(
        [
            "--candidate",
            str(CANDIDATE_PATH),
            "--evidence",
            str(EVIDENCE_PATH),
            "--rules",
            str(RULES_PATH),
            "--build-timestamp",
            BUILD_TIMESTAMP_TEXT,
            "--output",
            str(output_path),
        ]
    )
    stdout = capsys.readouterr().out
    assert stdout.count("\n") == 1
    return exit_code, json.loads(stdout)


def test_committed_fixture_contracts_and_canonical_regeneration():
    candidate, evidence, rules, _ = _build_core()
    source = candidate.source_metadata["model_pick"]
    test_case = build_stage_11_2_test_case()

    assert candidate.away and candidate.home and candidate.away != candidate.home
    assert candidate.candidate_id and candidate.selected_team and candidate.model_variant
    assert source["market"] == "SPREAD" and source["market_scope"] == "FULL_GAME"
    assert isinstance(source["model_generation_quote_id"], str)
    assert source["model_generation_quote_id"].strip()
    assert source["preflight"]["status"] == "PASS"
    assert candidate.spread_at_scan == source["handicap"]
    assert candidate.price_at_scan == source["price"]
    assert len(evidence.point_results) == 19
    assert evidence.season == candidate.season and evidence.week == candidate.week
    assert evidence.away_team == candidate.away and evidence.home_team == candidate.home
    assert evidence.selected_team == candidate.selected_team
    assert all(point.status.value != "BLOCKING_RISK" for point in evidence.point_results)
    assert rules["audit_stages"] == ["PREKICK"]
    assert CANDIDATE_PATH.read_bytes() == _canonical_json(
        test_case.candidate.to_json_dict()
    ).encode("utf-8")
    assert EVIDENCE_PATH.read_bytes() == _canonical_json(test_case.evidence.to_json_dict()).encode(
        "utf-8"
    )


def test_source_pick_preserves_identity_numbers_and_quote_provenance():
    candidate, _, _, result = _build_core()
    source = candidate.source_metadata["model_pick"]
    source_pick = result.audit_output["source_pick"]
    event = result.audit_output["event"]

    assert event["away"] == candidate.away == source["away"]
    assert event["home"] == candidate.home == source["home"]
    assert event["selected_team"] == candidate.selected_team == source["model_winner"]
    assert source_pick["candidate_id"] == candidate.candidate_id
    assert source_pick["canonical_game_id"] == candidate.game_id
    assert source_pick["season"] == candidate.season and source_pick["week"] == candidate.week
    assert source_pick["market"] == source["market"]
    assert source_pick["market_scope"] == source["market_scope"]
    assert source_pick["model_version"] == candidate.model_variant
    assert source_pick["handicap"] == candidate.spread_at_scan
    assert source_pick["price"] == candidate.price_at_scan
    assert source_pick["edge_vs_line"] == candidate.edge_vs_line
    assert source_pick["model_margin"] == candidate.model_margin
    assert source_pick["market_margin"] == candidate.market_margin_at_scan
    assert source_pick["confidence"] == candidate.confidence
    assert source_pick["tag"] == candidate.model_tag
    assert source_pick["book"] == source["model_generation_book"]
    assert source_pick["quote_timestamp_utc"] == source["model_generation_quote_timestamp_utc"]
    assert source_pick["preflight"] == source["preflight"]
    assert source_pick["model_generation_quote_id"] == source["model_generation_quote_id"]
    assert source_pick["quote_id"] == source["model_generation_quote_id"]


def test_real_cli_writes_valid_artifact_and_identical_rerun_is_immutable(tmp_path, capsys):
    candidate, _, _, core = _build_core()
    candidate_before = CANDIDATE_PATH.read_bytes()
    evidence_before = EVIDENCE_PATH.read_bytes()
    output_path = tmp_path / "stage_11_2_acceptance_audit.json"

    first_exit, first = _run_cli(capsys, output_path=output_path)
    artifact_before = output_path.read_bytes()
    artifact_hash = hashlib.sha256(artifact_before).hexdigest()
    persisted = json.loads(artifact_before)

    assert first_exit == 0
    assert first["status"] == "WRITTEN" and first["written"] is True
    assert first["candidate_id"] == candidate.candidate_id
    assert first["game_id"] == candidate.game_id
    assert first["build_id"] == core.build_id
    assert first["canonical_digest"] == core.audit_output_sha256
    assert "point_results" not in json.dumps(first)
    assert _sha256(persisted) == core.audit_output_sha256
    assert _canonical_json(persisted) == _canonical_json(core.audit_output)
    assert len(persisted["audit_points"]) == 19
    assert persisted["event"]["away"] == candidate.away
    assert persisted["event"]["home"] == candidate.home
    assert persisted["event"]["selected_team"] == candidate.selected_team
    assert persisted["source_pick"]["model_generation_quote_id"] == "quote-1"

    second_exit, second = _run_cli(capsys, output_path=output_path)

    assert second_exit == 0
    assert second["status"] == "ALREADY_EXISTS_IDENTICAL" and second["written"] is False
    assert second["build_id"] == first["build_id"]
    assert second["canonical_digest"] == first["canonical_digest"]
    assert output_path.read_bytes() == artifact_before
    assert hashlib.sha256(output_path.read_bytes()).hexdigest() == artifact_hash
    assert output_path.stat().st_size == len(artifact_before)
    assert CANDIDATE_PATH.read_bytes() == candidate_before
    assert EVIDENCE_PATH.read_bytes() == evidence_before


def test_readme_marks_fixture_as_test_only_documentation():
    readme = README_PATH.read_text(encoding="utf-8")

    for value in (
        "TEST_ONLY",
        "Production eligible: NO",
        "not a production pick",
        "not a real market audit",
        "Do not edit candidate.json manually.",
        "Do not edit evidence.json manually.",
    ):
        assert value in readme
