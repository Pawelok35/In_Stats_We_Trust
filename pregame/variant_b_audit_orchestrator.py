"""Explicit-path I/O boundary for pure Structured Variant B audit builds.

The orchestrator only loads validated contracts, calls the pure core once, and
atomically persists a canonical audit for successful builds.  It has no path
discovery, defaults, or repair behavior.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

from pydantic import ValidationError

from pregame.contracts import CandidateRecord
from pregame.variant_b_audit_integration import (
    StructuredVariantBAuditBuildStatus,
    _canonical_json,
    _sha256,
    build_structured_variant_b_audit,
)
from pregame.variant_b_evidence import load_variant_b_evidence


class StructuredVariantBAuditOrchestrationStatus(str, Enum):
    WRITTEN = "WRITTEN"
    ALREADY_EXISTS_IDENTICAL = "ALREADY_EXISTS_IDENTICAL"
    BLOCKED = "BLOCKED"
    INVALID_INPUT = "INVALID_INPUT"
    COLLISION = "COLLISION"
    IO_ERROR = "IO_ERROR"


@dataclass(frozen=True)
class StructuredVariantBAuditOrchestrationResult:
    status: StructuredVariantBAuditOrchestrationStatus
    output_path: str
    build_id: str | None
    canonical_digest: str | None
    candidate_id: str | None
    game_id: str | None
    blocking_reasons: tuple[str, ...]
    written: bool
    error: str | None = None


class StructuredVariantBAuditOrchestrator:
    """Run one explicit candidate/evidence build with success-only persistence."""

    def run(
        self,
        *,
        candidate_path: Path,
        evidence_path: Path,
        rules_config: Mapping[str, Any],
        build_timestamp: datetime,
        output_path: Path,
    ) -> StructuredVariantBAuditOrchestrationResult:
        candidate_result = _load_candidate(Path(candidate_path))
        if isinstance(candidate_result, str):
            return _failure(
                StructuredVariantBAuditOrchestrationStatus.INVALID_INPUT,
                output_path,
                candidate_result,
            )
        evidence_result = _load_evidence(Path(evidence_path))
        if isinstance(evidence_result, str):
            return _failure(
                StructuredVariantBAuditOrchestrationStatus.INVALID_INPUT,
                output_path,
                evidence_result,
            )
        candidate = candidate_result
        evidence = evidence_result
        try:
            core = build_structured_variant_b_audit(
                candidate=candidate,
                evidence=evidence,
                rules_config=rules_config,
                audit_stage=_audit_stage(rules_config),
                generated_at_utc=build_timestamp,
            )
        except (TypeError, ValueError) as exc:
            return _failure(
                StructuredVariantBAuditOrchestrationStatus.INVALID_INPUT,
                output_path,
                str(exc),
                candidate,
            )
        if core.build_status != StructuredVariantBAuditBuildStatus.BUILT:
            return StructuredVariantBAuditOrchestrationResult(
                status=StructuredVariantBAuditOrchestrationStatus.BLOCKED,
                output_path=str(output_path),
                build_id=core.build_id,
                canonical_digest=core.audit_output_sha256,
                candidate_id=candidate.candidate_id,
                game_id=candidate.game_id,
                blocking_reasons=tuple(reason.value for reason in core.reason_codes),
                written=False,
            )
        if core.audit_output is None or core.audit_output_sha256 is None:
            return _failure(
                StructuredVariantBAuditOrchestrationStatus.INVALID_INPUT,
                output_path,
                "missing canonical audit",
                candidate,
            )
        canonical = _canonical_json(core.audit_output).encode("utf-8")
        digest = _sha256(core.audit_output)
        if digest != core.audit_output_sha256:
            return _failure(
                StructuredVariantBAuditOrchestrationStatus.INVALID_INPUT,
                output_path,
                "core digest mismatch",
                candidate,
            )
        if (
            core.audit_output.get("event", {}).get("away") != candidate.away
            or core.audit_output.get("event", {}).get("home") != candidate.home
        ):
            return _failure(
                StructuredVariantBAuditOrchestrationStatus.INVALID_INPUT,
                output_path,
                "canonical matchup mismatch",
                candidate,
            )
        return _persist(output_path, canonical, digest, core.build_id, candidate)


def _audit_stage(rules_config: Mapping[str, Any]) -> str:
    stages = rules_config.get("audit_stages")
    if not isinstance(stages, list) or len(stages) != 1 or not isinstance(stages[0], str):
        raise ValueError("rules_config must contain exactly one explicit audit stage")
    return stages[0]


def _load_candidate(path: Path) -> CandidateRecord | str:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return CandidateRecord.model_validate(payload)
    except FileNotFoundError:
        return "candidate file missing"
    except (OSError, json.JSONDecodeError, ValidationError) as exc:
        return f"candidate load failed: {exc}"


def _load_evidence(path: Path):
    try:
        return load_variant_b_evidence(path)
    except FileNotFoundError:
        return "evidence file missing"
    except (OSError, json.JSONDecodeError, ValidationError, ValueError) as exc:
        return f"evidence load failed: {exc}"


def _persist(path: Path, content: bytes, digest: str, build_id: str, candidate: CandidateRecord):
    if not path.parent.exists():
        return _failure(
            StructuredVariantBAuditOrchestrationStatus.IO_ERROR,
            path,
            "output parent missing",
            candidate,
        )
    if path.exists():
        try:
            existing = path.read_bytes()
        except OSError as exc:
            return _failure(
                StructuredVariantBAuditOrchestrationStatus.IO_ERROR, path, str(exc), candidate
            )
        if existing == content:
            return StructuredVariantBAuditOrchestrationResult(
                StructuredVariantBAuditOrchestrationStatus.ALREADY_EXISTS_IDENTICAL,
                str(path),
                build_id,
                digest,
                candidate.candidate_id,
                candidate.game_id,
                (),
                False,
            )
        return _failure(
            StructuredVariantBAuditOrchestrationStatus.COLLISION,
            path,
            "immutable artifact collision",
            candidate,
        )
    temp = path.with_suffix(path.suffix + ".tmp")
    try:
        with temp.open("xb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, path)
    except OSError as exc:
        if temp.exists():
            temp.unlink(missing_ok=True)
        return _failure(
            StructuredVariantBAuditOrchestrationStatus.IO_ERROR, path, str(exc), candidate
        )
    return StructuredVariantBAuditOrchestrationResult(
        StructuredVariantBAuditOrchestrationStatus.WRITTEN,
        str(path),
        build_id,
        digest,
        candidate.candidate_id,
        candidate.game_id,
        (),
        True,
    )


def _failure(status, path, error, candidate=None):
    return StructuredVariantBAuditOrchestrationResult(
        status,
        str(path),
        None,
        None,
        getattr(candidate, "candidate_id", None),
        getattr(candidate, "game_id", None),
        (),
        False,
        error,
    )
