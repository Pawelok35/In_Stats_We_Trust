"""Explicit single-candidate entry point for the Variant B audit orchestrator."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from pregame.variant_b_audit_orchestrator import (
    StructuredVariantBAuditOrchestrationStatus,
    StructuredVariantBAuditOrchestrator,
)

EXIT_CODES = {
    StructuredVariantBAuditOrchestrationStatus.WRITTEN: 0,
    StructuredVariantBAuditOrchestrationStatus.ALREADY_EXISTS_IDENTICAL: 0,
    StructuredVariantBAuditOrchestrationStatus.BLOCKED: 2,
    StructuredVariantBAuditOrchestrationStatus.INVALID_INPUT: 3,
    StructuredVariantBAuditOrchestrationStatus.COLLISION: 4,
    StructuredVariantBAuditOrchestrationStatus.IO_ERROR: 5,
}


def parse_utc_timestamp(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise argparse.ArgumentTypeError("build timestamp must be ISO-8601 UTC") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise argparse.ArgumentTypeError("build timestamp must be UTC")
    return parsed.astimezone(timezone.utc)


def load_rules(path: Path) -> dict[str, Any]:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise argparse.ArgumentTypeError(f"rules load failed: {exc}") from exc
    if not isinstance(value, dict):
        raise argparse.ArgumentTypeError("rules must be a mapping")
    return value


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description=__doc__)
    value.add_argument("--candidate", required=True, type=Path)
    value.add_argument("--evidence", required=True, type=Path)
    value.add_argument("--rules", required=True, type=Path)
    value.add_argument("--build-timestamp", required=True, type=parse_utc_timestamp)
    value.add_argument("--output", required=True, type=Path)
    return value


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        rules_config = load_rules(args.rules)
    except argparse.ArgumentTypeError as exc:
        print(json.dumps({"status": "INVALID_INPUT", "written": False, "error": str(exc)}))
        return 3
    result = StructuredVariantBAuditOrchestrator().run(
        candidate_path=args.candidate,
        evidence_path=args.evidence,
        rules_config=rules_config,
        build_timestamp=args.build_timestamp,
        output_path=args.output,
    )
    payload = asdict(result)
    payload["status"] = result.status.value
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return EXIT_CODES[result.status]


if __name__ == "__main__":
    raise SystemExit(main())
