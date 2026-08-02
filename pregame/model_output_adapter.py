"""Adapter for the current frozen matchup_batch JSONL pick output."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from pregame.candidate_registry import CandidateRegistryService
from pregame.contracts import CandidateRecord
from pregame.events import CandidateStatus
from pregame.store import AppendStatus

_REQUIRED_FIELDS = frozenset(
    {
        "season",
        "week",
        "home",
        "away",
        "tag",
        "model_winner",
        "confidence",
        "model_margin",
        "market_margin",
        "edge_vs_line",
        "handicap",
        "price",
        "model_version",
        "preflight",
        "model_generation_quote_id",
    }
)


class ModelOutputImportError(ValueError):
    """Raised when a frozen model-output artifact cannot form a safe import plan."""

    def __init__(
        self,
        source_ref: str,
        reason: str,
        *,
        line_number: int | None = None,
        game_id: str | None = None,
        candidate_id: str | None = None,
    ) -> None:
        self.source_ref = source_ref
        self.reason = reason
        self.line_number = line_number
        self.game_id = game_id
        self.candidate_id = candidate_id
        location = f" line {line_number}" if line_number is not None else ""
        super().__init__(f"Model output import error for {source_ref}{location}: {reason}")


@dataclass(frozen=True)
class CandidateImportResult:
    """Structured outcome for one pre-validated model-output import."""

    scan_id: str
    source_ref: str
    source_sha256: str
    total_rows: int
    candidate_count: int
    blocked_count: int
    appended_count: int
    already_exists_count: int
    conflict_count: int
    error_count: int
    candidate_ids: tuple[str, ...]
    warnings: tuple[str, ...]


def model_scan_id(
    records: list[dict[str, Any]], *, season: int, week: int, model_variant: str
) -> str:
    """Return a semantic scan ID independent of JSON whitespace and row order."""

    normalized = sorted(_canonical_json(record) for record in records)
    payload = {
        "season": season,
        "week": week,
        "model_variant": model_variant,
        "records": normalized,
    }
    digest = hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()
    return f"model-scan:{season}:{week}:{model_variant}:{digest}"


def candidate_id_for_scan(
    scan_id: str, *, game_id: str, selected_team: str, model_variant: str
) -> str:
    """Return deterministic candidate identity for one source candidate in a scan."""

    payload = _canonical_json(
        {
            "scan_id": scan_id,
            "game_id": game_id,
            "selected_team": selected_team,
            "model_variant": model_variant,
        }
    )
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]
    return f"candidate:{digest}"


class MatchupBatchPickOutputAdapter:
    """Import current matchup_batch pick JSONL into a CandidateRegistryService."""

    def __init__(self, registry: CandidateRegistryService) -> None:
        self._registry = registry

    def import_jsonl(
        self,
        path: Path,
        *,
        season: int,
        week: int,
        model_variant: str,
        recorded_at_utc: datetime,
        source_ref: str | None = None,
    ) -> CandidateImportResult:
        """Pre-validate an entire pick file and then append its candidates."""

        _require_utc(recorded_at_utc)
        path = Path(path)
        resolved_ref = source_ref or _safe_source_ref(path)
        records = self._read_records(path, resolved_ref)
        scan_id = model_scan_id(records, season=season, week=week, model_variant=model_variant)
        source_sha256 = scan_id.rsplit(":", maxsplit=1)[-1]
        candidates = self._build_candidates(
            records,
            scan_id=scan_id,
            source_ref=resolved_ref,
            source_sha256=source_sha256,
            season=season,
            week=week,
            model_variant=model_variant,
            recorded_at_utc=recorded_at_utc,
        )

        preflight = [self._registry.preflight_candidate(candidate) for candidate in candidates]
        conflicts = [result for result in preflight if result.status == AppendStatus.CONFLICT]
        if conflicts:
            raise ModelOutputImportError(
                resolved_ref,
                "candidate event conflict detected before append",
                candidate_id=conflicts[0].event_id,
            )

        appended = 0
        already_exists = 0
        for candidate, planned in zip(candidates, preflight, strict=True):
            if planned.status == AppendStatus.ALREADY_EXISTS:
                already_exists += 1
                continue
            result = self._registry.record_candidate(candidate, recorded_at_utc=recorded_at_utc)
            if result.status == AppendStatus.APPENDED:
                appended += 1
            elif result.status == AppendStatus.ALREADY_EXISTS:
                already_exists += 1
            else:
                raise ModelOutputImportError(
                    resolved_ref,
                    "candidate event conflict during append; retry is safe",
                    candidate_id=candidate.candidate_id,
                )

        return CandidateImportResult(
            scan_id=scan_id,
            source_ref=resolved_ref,
            source_sha256=source_sha256,
            total_rows=len(records),
            candidate_count=len(candidates),
            blocked_count=sum(
                candidate.status != CandidateStatus.MODEL_CANDIDATE for candidate in candidates
            ),
            appended_count=appended,
            already_exists_count=already_exists,
            conflict_count=0,
            error_count=0,
            candidate_ids=tuple(candidate.candidate_id for candidate in candidates),
            warnings=tuple(warning for candidate in candidates for warning in candidate.warnings),
        )

    def _read_records(self, path: Path, source_ref: str) -> list[dict[str, Any]]:
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            raise ModelOutputImportError(
                source_ref, f"unable to read source artifact: {exc}"
            ) from exc
        if not lines:
            raise ModelOutputImportError(source_ref, "source JSONL is empty")

        records: list[dict[str, Any]] = []
        for line_number, line in enumerate(lines, start=1):
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ModelOutputImportError(
                    source_ref,
                    "invalid JSON",
                    line_number=line_number,
                ) from exc
            if not isinstance(record, dict):
                raise ModelOutputImportError(
                    source_ref,
                    "record must be a JSON object",
                    line_number=line_number,
                )
            records.append(record)
        return records

    def _build_candidates(
        self,
        records: list[dict[str, Any]],
        *,
        scan_id: str,
        source_ref: str,
        source_sha256: str,
        season: int,
        week: int,
        model_variant: str,
        recorded_at_utc: datetime,
    ) -> list[CandidateRecord]:
        candidates: list[CandidateRecord] = []
        seen_keys: set[tuple[str, str, str]] = set()
        for line_number, record in enumerate(records, start=1):
            candidate = _candidate_from_record(
                record,
                scan_id=scan_id,
                source_ref=source_ref,
                source_sha256=source_sha256,
                season=season,
                week=week,
                model_variant=model_variant,
                recorded_at_utc=recorded_at_utc,
                line_number=line_number,
            )
            key = (candidate.game_id, candidate.selected_team, candidate.model_variant)
            if key in seen_keys:
                raise ModelOutputImportError(
                    source_ref,
                    "duplicate source candidate key in one scan",
                    line_number=line_number,
                    game_id=candidate.game_id,
                    candidate_id=candidate.candidate_id,
                )
            seen_keys.add(key)
            candidates.append(candidate)
        return sorted(candidates, key=lambda candidate: candidate.candidate_id)


def _candidate_from_record(
    record: dict[str, Any],
    *,
    scan_id: str,
    source_ref: str,
    source_sha256: str,
    season: int,
    week: int,
    model_variant: str,
    recorded_at_utc: datetime,
    line_number: int,
) -> CandidateRecord:
    missing = sorted(_REQUIRED_FIELDS - record.keys())
    if missing:
        raise ModelOutputImportError(
            source_ref,
            f"missing required source fields: {', '.join(missing)}",
            line_number=line_number,
        )
    if record["season"] != season or record["week"] != week:
        raise ModelOutputImportError(
            source_ref,
            "source season/week does not match import context",
            line_number=line_number,
        )
    if record["model_version"] != model_variant:
        raise ModelOutputImportError(
            source_ref,
            "source model_version does not match import context",
            line_number=line_number,
        )
    if not all(
        isinstance(record[field], str) and record[field].strip()
        for field in ("home", "away", "model_winner", "tag")
    ):
        raise ModelOutputImportError(
            source_ref, "invalid team or tag field", line_number=line_number
        )
    quote_id = record["model_generation_quote_id"]
    if not isinstance(quote_id, str) or not quote_id.strip():
        raise ModelOutputImportError(
            source_ref,
            "model_generation_quote_id must be a non-empty string",
            line_number=line_number,
        )
    preflight = record["preflight"]
    if not isinstance(preflight, dict) or not isinstance(
        preflight.get("production_eligible"), bool
    ):
        raise ModelOutputImportError(
            source_ref,
            "preflight.production_eligible must be an explicit boolean",
            line_number=line_number,
        )
    game_id = f"{season}_w{week:02d}_{record['away']}_at_{record['home']}"
    selected_team = record["model_winner"]
    model_generated_at_utc = _parse_model_timestamp(
        record.get("generated_at"), source_ref=source_ref, line_number=line_number
    )
    warnings = list(_string_list(record.get("warnings"), "warnings", source_ref, line_number))
    if model_generated_at_utc is None:
        warnings.append("MODEL_GENERATED_AT_UNKNOWN")
    reason_codes = list(
        _string_list(record.get("reason_codes"), "reason_codes", source_ref, line_number)
    )
    production_eligible = preflight["production_eligible"]
    status = CandidateStatus.MODEL_CANDIDATE if production_eligible else CandidateStatus.BLOCKED
    if preflight.get("status") == "BYPASSED_UNSAFE":
        status = CandidateStatus.BLOCKED
        warnings.append("BYPASSED_UNSAFE")
    candidate_id = candidate_id_for_scan(
        scan_id,
        game_id=game_id,
        selected_team=selected_team,
        model_variant=model_variant,
    )
    try:
        return CandidateRecord(
            candidate_id=candidate_id,
            game_id=game_id,
            season=season,
            week=week,
            away=record["away"],
            home=record["home"],
            status=status,
            created_at_utc=recorded_at_utc,
            model_variant=model_variant,
            selected_team=selected_team,
            model_tag=record["tag"],
            production_eligible=production_eligible,
            confidence=float(record["confidence"]),
            edge_vs_line=float(record["edge_vs_line"]),
            model_margin=float(record["model_margin"]),
            market_margin_at_scan=float(record["market_margin"]),
            spread_at_scan=float(record["handicap"]),
            price_at_scan=_optional_int(record["price"], "price", source_ref, line_number),
            preflight_status=_optional_text(preflight.get("status")),
            warnings=warnings,
            reason_codes=reason_codes,
            model_generated_at_utc=model_generated_at_utc,
            scan_id=scan_id,
            source_ref=source_ref,
            source_sha256=source_sha256,
            source_record_number=line_number,
            source_metadata={
                "model_pick": dict(record),
                "preflight": preflight,
                "market": record.get("market"),
                "away": record["away"],
                "home": record["home"],
            },
        )
    except (TypeError, ValueError) as exc:
        raise ModelOutputImportError(
            source_ref,
            f"invalid source value: {exc}",
            line_number=line_number,
            game_id=game_id,
            candidate_id=candidate_id,
        ) from exc


def _parse_model_timestamp(value: Any, *, source_ref: str, line_number: int) -> datetime | None:
    if value in (None, ""):
        return None
    if not isinstance(value, str):
        raise ModelOutputImportError(
            source_ref, "generated_at must be a string", line_number=line_number
        )
    try:
        timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ModelOutputImportError(
            source_ref, "generated_at is invalid", line_number=line_number
        ) from exc
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise ModelOutputImportError(
            source_ref,
            "generated_at must be timezone-aware",
            line_number=line_number,
        )
    return timestamp.astimezone(timezone.utc)


def _string_list(value: Any, field: str, source_ref: str, line_number: int) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list) or not all(
        isinstance(item, str) and item.strip() for item in value
    ):
        raise ModelOutputImportError(
            source_ref, f"{field} must be a list of non-empty strings", line_number=line_number
        )
    return tuple(value)


def _optional_int(value: Any, field: str, source_ref: str, line_number: int) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise ModelOutputImportError(
            source_ref, f"{field} must be an integer or null", line_number=line_number
        )
    return value


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    return value if isinstance(value, str) and value.strip() else None


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    )


def _safe_source_ref(path: Path) -> str:
    return path.as_posix() if not path.is_absolute() else path.name


def _require_utc(value: datetime) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("recorded_at_utc must be timezone-aware")
    if value.utcoffset() != timedelta(0):
        raise ValueError("recorded_at_utc must be in UTC")
