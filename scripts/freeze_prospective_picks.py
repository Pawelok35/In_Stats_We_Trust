from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from utils.team_aliases import normalize_team_code

REQUIRED_PICK_FIELDS = {
    "season",
    "week",
    "home",
    "away",
    "tag",
    "model_winner",
    "confidence",
    "handicap",
}

PROOF_REQUIRED_FIELDS = {
    "market",
    "line",
    "price",
    "book",
    "decision_ts_utc",
    "model_version",
    "commit_sha",
}

PROCESS_RECOMMENDED_FIELDS = {
    "model_margin": "missing model_margin/fair line; process review will be weaker",
    "edge_vs_line": "missing edge_vs_line; cannot audit price discipline vs fair line",
    "argument_against": "missing argument_against; confirmation-bias check absent",
}


def canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in {path}:{line_no}: {exc}") from exc
        if not isinstance(record, dict):
            raise ValueError(f"Expected object in {path}:{line_no}")
        records.append(record)
    return records


def load_existing_hashes(path: Path) -> set[str]:
    if not path.exists():
        return set()
    hashes = set()
    for record in load_jsonl(path):
        record_hash = record.get("record_hash")
        if record_hash:
            hashes.add(str(record_hash))
    return hashes


def normalize_pick(record: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(record)
    if "home" in normalized:
        normalized["home"] = normalize_team_code(normalized["home"])
    if "away" in normalized:
        normalized["away"] = normalize_team_code(normalized["away"])
    if "model_winner" in normalized:
        normalized["model_winner"] = normalize_team_code(normalized["model_winner"])
    if "tag" in normalized:
        normalized["tag"] = str(normalized["tag"]).upper()
    return normalized


def disqualification_reasons(record: dict[str, Any]) -> list[str]:
    reasons = []
    missing_pick = sorted(field for field in REQUIRED_PICK_FIELDS if field not in record)
    if missing_pick:
        reasons.append("missing required pick fields: " + ", ".join(missing_pick))

    missing_proof = sorted(
        field for field in PROOF_REQUIRED_FIELDS if record.get(field) in (None, "")
    )
    if missing_proof:
        reasons.append("missing proof fields: " + ", ".join(missing_proof))

    decision_ts = record.get("decision_ts_utc")
    if decision_ts and not _is_utc_timestamp(str(decision_ts)):
        reasons.append("decision_ts_utc is not a valid UTC timestamp")

    price = record.get("price")
    if price not in (None, ""):
        try:
            float(price)
        except (TypeError, ValueError):
            reasons.append("price is not numeric")

    return reasons


def integrity_warnings(record: dict[str, Any]) -> list[str]:
    warnings = []
    if record.get("code_is_dirty") is True:
        warnings.append("code_is_dirty=true")
    if str(record.get("book", "")).upper().startswith("MANUAL"):
        warnings.append(
            "manual odds/book source; verify against external source before market-grade proof"
        )
    for field, message in PROCESS_RECOMMENDED_FIELDS.items():
        if record.get(field) in (None, ""):
            warnings.append(message)
    return warnings


def build_process_snapshot(record: dict[str, Any]) -> dict[str, Any]:
    fair_line = _safe_float(record.get("model_margin"))
    market_line = _safe_float(record.get("line"))
    market_margin = _safe_float(record.get("market_margin"))
    edge_vs_line = _safe_float(record.get("edge_vs_line"))
    price = _safe_float(record.get("price"))
    closing_line = _safe_float(record.get("closing_line"))
    closing_price = _safe_float(record.get("closing_price"))
    explicit_clv = _safe_float(record.get("clv_points"))
    process_notes = {
        "argument_against": _clean_process_text(record.get("argument_against")),
        "market_move_notes": _clean_process_text(record.get("market_move_notes")),
        "injury_role_notes": _clean_process_text(record.get("injury_role_notes")),
        "schedule_spot_notes": _clean_process_text(record.get("schedule_spot_notes")),
        "weather_notes": _clean_process_text(record.get("weather_notes")),
    }
    return {
        "schema_version": "process_snapshot.v1",
        "fair_line_source": "model_margin" if fair_line is not None else None,
        "fair_line": fair_line,
        "market_line": market_line,
        "market_margin": market_margin,
        "edge_vs_line": edge_vs_line,
        "price": price,
        "closing_line": closing_line,
        "closing_price": closing_price,
        "clv_points": explicit_clv,
        "has_fair_line": fair_line is not None,
        "has_market_line": market_line is not None,
        "has_market_price": price is not None,
        "has_decision_timestamp": bool(record.get("decision_ts_utc")),
        "has_argument_against": bool(process_notes["argument_against"]),
        "has_closing_line": closing_line is not None,
        "notes": {key: value for key, value in process_notes.items() if value not in (None, "")},
    }


def _clean_process_text(value: Any) -> str | None:
    if value in (None, ""):
        return None
    text = str(value).strip()
    if not text or text.upper().startswith("TODO"):
        return None
    return text


def _safe_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _is_utc_timestamp(value: str) -> bool:
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() == timezone.utc.utcoffset(parsed)


def build_ledger_record(
    *,
    pick: dict[str, Any],
    source_path: Path,
    frozen_at: str,
    operator: str,
) -> dict[str, Any]:
    normalized = normalize_pick(pick)
    source_hash = sha256_text(canonical_json(normalized))
    reasons = disqualification_reasons(normalized)
    warnings = integrity_warnings(normalized)
    ledger_record = {
        "schema_version": "prospective_ledger.v1",
        "ledger_id": (
            f"{normalized.get('season')}_w{int(normalized.get('week', 0)):02d}_"
            f"{normalized.get('away')}_at_{normalized.get('home')}_"
            f"{normalized.get('market', 'UNKNOWN')}_{source_hash[:12]}"
        ),
        "frozen_at_utc": frozen_at,
        "operator": operator,
        "source_path": str(source_path),
        "source_pick_hash": source_hash,
        "proof_qualified": not reasons,
        "disqualification_reasons": reasons,
        "integrity_warnings": warnings,
        "process_snapshot": build_process_snapshot(normalized),
        "pick": normalized,
    }
    ledger_record["record_hash"] = sha256_text(canonical_json(ledger_record))
    return ledger_record


def write_jsonl_append(path: Path, records: list[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = load_existing_hashes(path)
    new_records = [record for record in records if record["record_hash"] not in existing]
    if not new_records:
        return 0
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        for record in new_records:
            handle.write(canonical_json(record) + "\n")
    return len(new_records)


def write_manifest(
    path: Path, ledger_path: Path, records: list[dict[str, Any]], appended: int
) -> None:
    qualified = sum(1 for record in records if record["proof_qualified"])
    payload = {
        "schema_version": "prospective_ledger_manifest.v1",
        "ledger_path": str(ledger_path),
        "ledger_sha256": sha256_file(ledger_path) if ledger_path.exists() else None,
        "records_seen": len(records),
        "records_appended": appended,
        "proof_qualified_seen": qualified,
        "not_qualified_seen": len(records) - qualified,
        "created_at_utc": utc_now_iso(),
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def freeze_picks(
    *,
    source_path: Path,
    output_root: Path,
    operator: str,
    frozen_at: str | None = None,
) -> tuple[Path, Path, int, int]:
    records = load_jsonl(source_path)
    if not records:
        raise ValueError(f"No pick records found: {source_path}")
    first = records[0]
    season = int(first["season"])
    week = int(first["week"])
    frozen = frozen_at or utc_now_iso()
    ledger_records = [
        build_ledger_record(
            pick=record,
            source_path=source_path,
            frozen_at=frozen,
            operator=operator,
        )
        for record in records
    ]
    ledger_path = output_root / str(season) / f"week_{week:02d}_prospective.jsonl"
    manifest_path = output_root / str(season) / f"week_{week:02d}_manifest.json"
    appended = write_jsonl_append(ledger_path, ledger_records)
    write_manifest(manifest_path, ledger_path, ledger_records, appended)
    qualified = sum(1 for record in ledger_records if record["proof_qualified"])
    return ledger_path, manifest_path, appended, qualified


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Freeze pick JSONL into an append-only prospective ledger."
    )
    parser.add_argument("--source", type=Path, required=True, help="Input week_XX.jsonl pick file.")
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("data/prospective_ledger"),
        help="Root directory for prospective ledger JSONL files.",
    )
    parser.add_argument(
        "--operator", default="codex", help="Operator label written to ledger records."
    )
    parser.add_argument(
        "--frozen-at",
        help="Optional UTC freeze timestamp for tests/reproducibility, e.g. 2026-09-10T15:00:00Z.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ledger_path, manifest_path, appended, qualified = freeze_picks(
        source_path=args.source,
        output_root=args.output_root,
        operator=args.operator,
        frozen_at=args.frozen_at,
    )
    print(f"ledger={ledger_path}")
    print(f"manifest={manifest_path}")
    print(f"appended={appended}")
    print(f"proof_qualified_seen={qualified}")


if __name__ == "__main__":
    main()
