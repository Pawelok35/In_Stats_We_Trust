from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.variant_b_audit import clean_team


LEDGER_SCHEMA_VERSION = "variant_b_learning_ledger.v1"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def stable_hash(payload: dict[str, Any], prefix: str) -> str:
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20]
    return f"{prefix}_{digest}"


def write_jsonl_append(path: Path, records: Iterable[dict[str, Any]]) -> int:
    rows = list(records)
    if not rows:
        return 0
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for record in rows:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    return len(rows)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def safe_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(result):
        return None
    return result


def selected_team_from_pick(pick: dict[str, Any]) -> str:
    return clean_team(pick.get("model_winner") or pick.get("selected_team"))


def opponent_for_selected(pick: dict[str, Any], selected_team: str) -> str:
    home = clean_team(pick.get("home"))
    away = clean_team(pick.get("away"))
    if selected_team == home:
        return away
    if selected_team == away:
        return home
    return "UNKNOWN"


def pick_id_from_audit(audit: dict[str, Any]) -> str:
    return str(audit.get("pick_id") or "unknown_pick")


def point_statuses(audit: dict[str, Any]) -> dict[str, str]:
    statuses: dict[str, str] = {}
    for point in audit.get("audit_points", []):
        number = point.get("point_number")
        name = point.get("point_name")
        if number is None:
            continue
        statuses[f"{number}_{name}"] = str(point.get("status") or "UNKNOWN")
    return statuses


def hard_blockers(audit: dict[str, Any]) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    for point in audit.get("audit_points", []):
        status = str(point.get("status") or "UNKNOWN")
        missing = point.get("missing_data") or []
        if status in {"INCOMPLETE", "FAILED", "BLOCKED"} and missing:
            for item in missing:
                failures.append(
                    {
                        "point_number": point.get("point_number"),
                        "point_name": point.get("point_name"),
                        "status": status,
                        "missing_data": item,
                    }
                )
    return failures


def build_records(audit: dict[str, Any], *, ledger_recorded_at_utc: str, source_file: Path) -> dict[str, list[dict[str, Any]]]:
    pick = audit.get("source_pick") or {}
    event = audit.get("event") or {}
    pick_id = pick_id_from_audit(audit)
    season = int(event.get("season") or pick.get("season") or 0)
    week = int(event.get("week") or pick.get("week") or 0)
    home = clean_team(event.get("home") or pick.get("home"))
    away = clean_team(event.get("away") or pick.get("away"))
    selected_team = clean_team(event.get("selected_team") or selected_team_from_pick(pick))
    opponent = opponent_for_selected({"home": home, "away": away}, selected_team)

    game_identity = {
        "season": season,
        "week": week,
        "home": home,
        "away": away,
    }
    game_id = stable_hash(game_identity, "game")

    quote_identity = {
        "game_id": game_id,
        "selected_team": selected_team,
        "market": pick.get("market") or "spread",
        "spread": safe_float(pick.get("handicap") if pick.get("handicap") is not None else pick.get("line")),
        "price": safe_float(pick.get("price")),
        "book": pick.get("book") or "UNKNOWN",
        "quote_timestamp_utc": pick.get("quote_timestamp_utc") or pick.get("decision_ts_utc"),
        "executable_status": pick.get("executable_status") or "UNKNOWN",
    }
    market_quote_id = pick.get("quote_id") or stable_hash(quote_identity, "quote")

    feature_identity = {
        "game_id": game_id,
        "selected_team": selected_team,
        "model_version": pick.get("model_version"),
        "data_cutoff": pick.get("data_cutoff"),
        "config_sha256": pick.get("config_sha256"),
        "generated_at": pick.get("generated_at"),
    }
    feature_snapshot_id = stable_hash(feature_identity, "features")

    model_run_identity = {
        "game_id": game_id,
        "selected_team": selected_team,
        "model_version": pick.get("model_version"),
        "commit_sha": pick.get("commit_sha"),
        "config_sha256": pick.get("config_sha256"),
        "generated_at": pick.get("generated_at"),
        "market_quote_id": market_quote_id,
    }
    model_run_id = stable_hash(model_run_identity, "modelrun")

    prediction_identity = {
        "model_run_id": model_run_id,
        "selected_team": selected_team,
        "spread": quote_identity["spread"],
        "p_cover": safe_float(pick.get("p_cover")),
        "p_push": safe_float(pick.get("p_push")),
        "p_loss": safe_float(pick.get("p_loss")),
    }
    model_prediction_id = stable_hash(prediction_identity, "prediction")

    audit_identity = {
        "model_run_id": model_run_id,
        "pick_id": pick_id,
        "audit_stage": audit.get("audit_stage"),
        "audit_generated_at_utc": audit.get("generated_at_utc"),
        "source_file": str(source_file.relative_to(REPO_ROOT) if source_file.is_relative_to(REPO_ROOT) else source_file),
    }
    audit_id = stable_hash(audit_identity, "audit")

    common = {
        "schema_version": LEDGER_SCHEMA_VERSION,
        "ledger_recorded_at_utc": ledger_recorded_at_utc,
        "source_audit_file": str(source_file.relative_to(REPO_ROOT) if source_file.is_relative_to(REPO_ROOT) else source_file),
    }

    records: dict[str, list[dict[str, Any]]] = {
        "games": [
            {
                **common,
                "game_id": game_id,
                "season": season,
                "week": week,
                "home_team": home,
                "away_team": away,
                "neutral_site": bool(event.get("neutral_site") or pick.get("neutral_site")),
                "kickoff_utc": pick.get("kickoff_utc"),
            }
        ],
        "feature_snapshots": [
            {
                **common,
                "feature_snapshot_id": feature_snapshot_id,
                "game_id": game_id,
                "selected_team": selected_team,
                "opponent": opponent,
                "as_of_utc": pick.get("generated_at") or pick.get("decision_ts_utc"),
                "available_to_model_at_utc": pick.get("generated_at") or pick.get("decision_ts_utc"),
                "data_cutoff": pick.get("data_cutoff"),
                "model_version": pick.get("model_version"),
                "config_sha256": pick.get("config_sha256"),
                "config_hashes": pick.get("config_hashes") or {},
                "availability_status": "AVAILABLE",
                "feature_values_status": "MVP_METADATA_ONLY",
            }
        ],
        "market_quotes": [
            {
                **common,
                "market_quote_id": market_quote_id,
                "game_id": game_id,
                "selected_team": selected_team,
                "market": pick.get("market") or "spread",
                "market_scope": pick.get("market_scope") or "FULL_GAME",
                "book": pick.get("book") or "UNKNOWN",
                "selected_team_spread": quote_identity["spread"],
                "price_american": quote_identity["price"],
                "quote_timestamp_utc": quote_identity["quote_timestamp_utc"],
                "executable_status": quote_identity["executable_status"],
                "source_type": pick.get("source_type") or pick.get("odds_source") or "UNKNOWN",
                "target_stake": pick.get("target_stake"),
                "accepted_stake": pick.get("accepted_stake"),
                "house_rules_checked": bool(pick.get("house_rules_checked")),
                "evidence_grade": "MARKET_GRADE" if quote_identity["executable_status"] in {"betslip_checked", "accepted_ticket"} else "PREVIEW",
            }
        ],
        "model_runs": [
            {
                **common,
                "model_run_id": model_run_id,
                "parent_model_run_id": pick.get("parent_model_run_id"),
                "game_id": game_id,
                "feature_snapshot_id": feature_snapshot_id,
                "market_quote_id": market_quote_id,
                "selected_team": selected_team,
                "model_version": pick.get("model_version"),
                "model_code_hash": pick.get("commit_sha"),
                "code_is_dirty": bool(pick.get("code_is_dirty")),
                "training_data_hash": pick.get("training_data_hash"),
                "generated_at_utc": pick.get("generated_at"),
                "prediction_horizon": pick.get("window") or "pregame",
                "model_proof_status": pick.get("model_proof_status"),
            }
        ],
        "model_predictions": [
            {
                **common,
                "model_prediction_id": model_prediction_id,
                "model_run_id": model_run_id,
                "selected_team": selected_team,
                "opponent": opponent,
                "predicted_margin_selected_team": safe_float(pick.get("model_margin")),
                "market_spread_selected_team": quote_identity["spread"],
                "edge_vs_line": safe_float(pick.get("edge_vs_line")),
                "tag": pick.get("tag"),
                "confidence": safe_float(pick.get("confidence")),
                "p_cover": safe_float(pick.get("p_cover")),
                "p_push": safe_float(pick.get("p_push")),
                "p_loss": safe_float(pick.get("p_loss")),
                "margin_distribution_id": pick.get("margin_distribution_id"),
                "margin_pmf_method": pick.get("margin_pmf_method"),
                "margin_pmf_path": pick.get("margin_pmf_path"),
                "margin_pmf_sample_size": pick.get("margin_pmf_sample_size"),
                "acceptable_quote_frontier_id": pick.get("acceptable_quote_frontier_id"),
                "acceptable_quote_frontier_path": pick.get("acceptable_quote_frontier_path"),
            }
        ],
        "audit_results": [
            {
                **common,
                "audit_id": audit_id,
                "model_run_id": model_run_id,
                "pick_id": pick_id,
                "framework_version": audit.get("framework_version"),
                "audit_stage": audit.get("audit_stage"),
                "audit_generated_at_utc": audit.get("generated_at_utc"),
                "point_statuses": point_statuses(audit),
                "final_summary": audit.get("final_summary"),
            }
        ],
        "process_failures": [],
    }

    for failure in hard_blockers(audit):
        failure_identity = {
            "audit_id": audit_id,
            "point_number": failure.get("point_number"),
            "point_name": failure.get("point_name"),
            "missing_data": failure.get("missing_data"),
        }
        records["process_failures"].append(
            {
                **common,
                "process_failure_id": stable_hash(failure_identity, "failure"),
                "audit_id": audit_id,
                "model_run_id": model_run_id,
                **failure,
            }
        )

    return records


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Append Variant B audit outputs to the learning ledger.")
    parser.add_argument("--season", type=int, required=True)
    parser.add_argument("--week", type=int, required=True)
    parser.add_argument("--audit-dir", type=Path)
    parser.add_argument("--output-root", type=Path, default=Path("data/learning_ledger"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    audit_dir = args.audit_dir or Path("research") / "variant_b_week_flow" / str(args.season) / f"week_{args.week:02d}"
    audit_path = audit_dir if audit_dir.is_absolute() else REPO_ROOT / audit_dir
    if not audit_path.exists():
        raise SystemExit(f"Audit directory not found: {audit_path}")

    output_root = args.output_root if args.output_root.is_absolute() else REPO_ROOT / args.output_root
    output_dir = output_root / str(args.season) / f"week_{args.week:02d}"
    ledger_recorded_at_utc = utc_now_iso()

    by_table: dict[str, list[dict[str, Any]]] = {
        "games": [],
        "feature_snapshots": [],
        "market_quotes": [],
        "model_runs": [],
        "model_predictions": [],
        "audit_results": [],
        "process_failures": [],
    }
    audit_files = sorted(path for path in audit_path.glob("*.json") if path.name != "summary.json")
    for path in audit_files:
        audit = read_json(path)
        records = build_records(audit, ledger_recorded_at_utc=ledger_recorded_at_utc, source_file=path)
        for table, table_records in records.items():
            by_table.setdefault(table, []).extend(table_records)

    counts: dict[str, int] = {}
    for table, records in by_table.items():
        counts[table] = write_jsonl_append(output_dir / f"{table}.jsonl", records)

    manifest = {
        "schema_version": LEDGER_SCHEMA_VERSION,
        "ledger_recorded_at_utc": ledger_recorded_at_utc,
        "season": args.season,
        "week": args.week,
        "audit_dir": str(audit_path.relative_to(REPO_ROOT) if audit_path.is_relative_to(REPO_ROOT) else audit_path),
        "output_dir": str(output_dir.relative_to(REPO_ROOT) if output_dir.is_relative_to(REPO_ROOT) else output_dir),
        "audit_files": len(audit_files),
        "appended_counts": counts,
        "append_only_note": "Records are appended. Previous rows are not modified or deleted.",
    }
    manifest_path = output_dir / f"manifest_{ledger_recorded_at_utc.replace(':', '').replace('-', '')}.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"[OK] learning ledger appended: {output_dir}")
    print(json.dumps(counts, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
