"""TEST_ONLY fixture generator.

Not for production candidate or evidence generation.
"""

# ruff: noqa: E402

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from pregame.contracts import CandidateRecord
from pregame.variant_b_audit_integration import (
    StructuredVariantBAuditBuildStatus,
    _canonical_json,
    build_structured_variant_b_audit,
)
from pregame.variant_b_evidence import load_variant_b_evidence
from tests.helpers.stage_11_2_acceptance_factory import (
    build_stage_11_2_test_case,
)


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description=__doc__)
    value.add_argument("--output-dir", required=True, type=Path)
    return value


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    output_dir = args.output_dir
    test_case = build_stage_11_2_test_case()
    _require_built(
        test_case.candidate,
        test_case.evidence,
        test_case.rules,
        test_case.generated_at_utc,
    )

    payloads = {
        "candidate.json": _canonical_json(test_case.candidate.to_json_dict()).encode("utf-8"),
        "evidence.json": _canonical_json(test_case.evidence.to_json_dict()).encode("utf-8"),
    }
    try:
        _write_fixture_pair(output_dir, payloads)
        candidate = CandidateRecord.model_validate_json(
            (output_dir / "candidate.json").read_text("utf-8")
        )
        evidence = load_variant_b_evidence(output_dir / "evidence.json")
        _require_built(candidate, evidence, test_case.rules, test_case.generated_at_utc)
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"fixture generation failed: {exc}", file=sys.stderr)
        return 1
    return 0


def _require_built(candidate, evidence, rules, generated_at_utc) -> None:
    result = build_structured_variant_b_audit(
        candidate=candidate,
        evidence=evidence,
        rules_config=rules,
        audit_stage="PREKICK",
        generated_at_utc=generated_at_utc,
    )
    if result.build_status != StructuredVariantBAuditBuildStatus.BUILT:
        raise RuntimeError(f"pure core did not build fixture case: {result.build_status.value}")


def _write_fixture_pair(output_dir: Path, payloads: dict[str, bytes]) -> None:
    if output_dir.exists() and not output_dir.is_dir():
        raise ValueError("output-dir must be a directory")
    existing = {name: output_dir / name for name in payloads if (output_dir / name).exists()}
    for name, path in existing.items():
        if path.read_bytes() != payloads[name]:
            raise RuntimeError(f"fixture collision for {path}")
    output_dir.mkdir(parents=True, exist_ok=True)
    created: list[Path] = []
    try:
        for name, content in payloads.items():
            path = output_dir / name
            if path.exists():
                continue
            _atomic_write(path, content)
            created.append(path)
    except OSError:
        for path in created:
            path.unlink(missing_ok=True)
        raise


def _atomic_write(path: Path, content: bytes) -> None:
    temp_path = path.with_suffix(path.suffix + ".tmp")
    try:
        with temp_path.open("xb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
    except OSError:
        temp_path.unlink(missing_ok=True)
        raise


if __name__ == "__main__":
    raise SystemExit(main())
