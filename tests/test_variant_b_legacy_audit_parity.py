import hashlib
import json
from pathlib import Path

from scripts import variant_b_audit


def _assert_types_exact(actual, expected, path="$"):
    assert type(actual) is type(expected), path
    if isinstance(actual, dict):
        assert list(actual) == list(expected), path
        for key in actual:
            _assert_types_exact(actual[key], expected[key], f"{path}.{key}")
    elif isinstance(actual, list):
        for index, (left, right) in enumerate(zip(actual, expected)):
            _assert_types_exact(left, right, f"{path}[{index}]")


def test_legacy_audit_is_type_exact_against_parent_golden_fixture(monkeypatch):
    path = Path(__file__).parent / "fixtures" / "variant_b" / "legacy_audit_parity_v1.json"
    fixture = json.loads(path.read_text(encoding="utf-8"))
    monkeypatch.setattr(variant_b_audit, "utc_now_iso", lambda: fixture["frozen_timestamp_utc"])
    for case in fixture["cases"]:
        record = dict(fixture["base_record"])
        record.update(case["changes"])
        before = json.loads(json.dumps(record))
        output = variant_b_audit.build_audit(
            record, variant_b_audit.DEFAULT_RULES_CONFIG, case["audit_stage"]
        )
        _assert_types_exact(record, before)
        canonical = json.dumps(
            output, sort_keys=True, separators=(",", ":"), ensure_ascii=True
        ).encode("utf-8")
        assert hashlib.sha256(canonical).hexdigest() == case["expected_sha256"], case["case_id"]
