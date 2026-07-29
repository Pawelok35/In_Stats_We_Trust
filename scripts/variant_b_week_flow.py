from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.variant_b_audit import (
    ACTION_TAGS,
    build_audit,
    canonical_pick_id,
    clean_team,
    load_jsonl,
    load_rules_config,
)


def run(cmd: list[str], *, desc: str) -> None:
    print(f"\n=== {desc} ===")
    print(">>> " + " ".join(cmd))
    result = subprocess.run(cmd, cwd=REPO_ROOT, check=False)
    if result.returncode != 0:
        raise SystemExit(f"{desc} failed with exit code {result.returncode}")


def point_values(audit: dict[str, Any], point_number: int) -> dict[str, Any]:
    for point in audit.get("audit_points", []):
        if point.get("point_number") == point_number:
            calculations = point.get("calculations", {})
            values = calculations.get("values", {})
            return values if isinstance(values, dict) else {}
    return {}


def point_status(audit: dict[str, Any], point_number: int) -> str:
    for point in audit.get("audit_points", []):
        if point.get("point_number") == point_number:
            return str(point.get("status") or "UNKNOWN")
    return "UNKNOWN"


def pick_label(record: dict[str, Any]) -> str:
    return f"{record.get('away')}_at_{record.get('home')} {record.get('model_winner')} {record.get('tag')}"


def record_key(record: dict[str, Any]) -> tuple[int, int, str, str, str]:
    return (
        int(record.get("season", 0) or 0),
        int(record.get("week", 0) or 0),
        clean_team(record.get("away")),
        clean_team(record.get("home")),
        clean_team(record.get("model_winner") or record.get("selected_team")),
    )


def quote_key(record: dict[str, Any]) -> tuple[int, int, str, str, str]:
    return (
        int(record.get("season", 0) or 0),
        int(record.get("week", 0) or 0),
        clean_team(record.get("away")),
        clean_team(record.get("home")),
        clean_team(record.get("selected_team") or record.get("team")),
    )


def load_quote_overrides(path: Path | None) -> dict[tuple[int, int, str, str, str], dict[str, Any]]:
    if path is None or not path.exists():
        return {}
    quotes: dict[tuple[int, int, str, str, str], dict[str, Any]] = {}
    for quote in load_jsonl(path):
        quotes[quote_key(quote)] = quote
    return quotes


def attach_gpt_snapshot(record: dict[str, Any], snapshots_root: Path) -> dict[str, Any]:
    """Attach verified structural metadata for the saved 19-point GPT research.

    The prose remains evidence for the operator; only the presence of all 19
    labelled sections is machine-readable.  This prevents arbitrary GPT text
    from silently becoming a model or market input.
    """
    updated = dict(record)
    game_id = f"{int(record.get('season', 0)):04d}_w{int(record.get('week', 0)):02d}_{clean_team(record.get('away'))}_at_{clean_team(record.get('home'))}"
    path = snapshots_root.resolve() / game_id / "full_19_points.md"
    if not path.exists():
        updated["gpt_full_19_status"] = "MISSING"
        return updated
    text = path.read_text(encoding="utf-8")
    point_numbers = {int(value) for value in re.findall(r"(?im)^\s*point_number\s*:\s*(\d+)\s*$", text)}
    updated.update(
        {
            "gpt_full_19_snapshot_path": str(path.relative_to(REPO_ROOT)),
            "gpt_full_19_points_present": sorted(point_numbers),
            "gpt_full_19_status": "STRUCTURALLY_COMPLETE" if set(range(1, 20)).issubset(point_numbers) else "INCOMPLETE",
        }
    )
    return updated


def apply_quote_override(record: dict[str, Any], quote: dict[str, Any] | None) -> dict[str, Any]:
    if quote is None:
        return record
    updated = dict(record)
    field_map = {
        "book": "book",
        "spread": "handicap",
        "line": "line",
        "price": "price",
        "quote_timestamp_utc": "quote_timestamp_utc",
        "quote_id": "quote_id",
        "executable_status": "executable_status",
        "target_stake": "target_stake",
        "accepted_stake": "accepted_stake",
        "source_type": "source_type",
        "market_scope": "market_scope",
        "jurisdiction": "jurisdiction",
        "house_rules_checked": "house_rules_checked",
        "betslip_verified_at_utc": "betslip_verified_at_utc",
    }
    for source_field, target_field in field_map.items():
        if quote.get(source_field) not in (None, ""):
            updated[target_field] = quote[source_field]
    updated["odds_source"] = quote.get("odds_source") or "manual_book_quote"
    updated["odds_snapshot_type"] = quote.get("odds_snapshot_type") or "decision"
    updated["market_quote_override_applied"] = True
    updated["market_quote_override_source"] = quote.get("source_file", "quotes_file")
    return updated


def write_summary(
    rows: list[dict[str, Any]],
    output_dir: Path,
    *,
    model_proof_generated: bool,
    quotes_loaded: int,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_json = {
        "schema_version": "variant_b_week_flow_summary.v1",
        "rows": rows,
        "counts": {
            "total_audits": len(rows),
            "by_operator_action": count_by(rows, "operator_action"),
            "by_gate_state": count_by(rows, "gate_state"),
            "by_process_status": count_by(rows, "process_quality_status"),
        },
        "model_proof_generated": model_proof_generated,
        "quotes_loaded": quotes_loaded,
    }
    (output_dir / "summary.json").write_text(json.dumps(summary_json, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# Variant B Week Flow Summary",
        "",
        f"Total audits: {len(rows)}",
        "",
        "| Pick | Tag | Process | Gate | Operator Action | Hard Blockers | Audit |",
        "| --- | --- | --- | --- | --- | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            "| {pick} | {tag} | {process_quality_status} | {gate_state} | {operator_action} | {hard_blockers_count} | {audit_file} |".format(
                **row
            )
        )
    lines.append("")
    lines.append("## Action Picks")
    lines.append("")
    if rows:
        for row in rows:
            lines.append("```yaml")
            lines.append(f"pick: {row['pick']}")
            lines.append(f"selected_team: {row.get('selected_team', 'UNKNOWN')}")
            lines.append(f"tag: {row['tag']}")
            lines.append(f"edge_vs_line: {row.get('edge_vs_line', 'UNKNOWN')}")
            lines.append(f"line: {row.get('line', 'UNKNOWN')}")
            lines.append(f"price: {row.get('price', 'UNKNOWN')}")
            lines.append(f"process_quality: {row['process_quality_status']}")
            lines.append(f"gate_state: {row['gate_state']}")
            lines.append(f"operator_action: {row['operator_action']}")
            lines.append(f"hard_blockers_count: {row['hard_blockers_count']}")
            lines.append("```")
            lines.append("")
    else:
        lines.append("No VALUE PLAY/GOW/GOM/GOY picks found.")
        lines.append("")
    lines.append("")
    lines.append("## Next")
    lines.append("")
    if model_proof_generated:
        lines.append("- Model proof MVP zostal wygenerowany: p_cover, p_push, p_loss i acceptable frontier sa w pliku model_proof.")
        lines.append("- Nadal trzeba uzupelnic model-generation quote, bo nie wolno go rekonstruowac po fakcie.")
    else:
        lines.append("- Uzupelnic model proof: PMF, p_cover, p_push, p_loss, acceptable frontier, model-generation quote.")
    if quotes_loaded:
        lines.append("- Market quote file zostal wczytany; sprawdz, czy executable status i timestamp przechodza gate.")
    else:
        lines.append("- Uzupelnic market proof: named book, atomic spread+price, timestamp, executable status, target stake.")
    lines.append("- Ponownie uruchomic ten sam flow po uzupelnieniu danych.")
    (output_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def count_by(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = str(row.get(key) or "UNKNOWN")
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Variant B audits for a weekly pick file.")
    parser.add_argument("--season", type=int, required=True)
    parser.add_argument("--week", type=int, required=True)
    parser.add_argument("--variant", default="variant_m")
    parser.add_argument("--picks-file", type=Path)
    parser.add_argument("--rules", type=Path, default=Path("config/variant_b_rules.yaml"))
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--audit-stage", default="EARLY_PREVIEW")
    parser.add_argument("--all-picks", action="store_true", help="Audit every pick, not only VALUE PLAY/GOW/GOM/GOY.")
    parser.add_argument("--with-model-proof", action="store_true", help="Generate empirical PMF/p_cover/p_push/p_loss before audit.")
    parser.add_argument("--train-seasons", default="2021-2025")
    parser.add_argument("--quotes-file", type=Path, help="Manual market quote JSONL. Defaults to data/market_quotes/{season}/week_{week:02d}.jsonl when present.")
    parser.add_argument("--write-learning-ledger", action="store_true", help="Append audit outputs to data/learning_ledger after the week flow completes.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    picks_file = args.picks_file or Path("data") / f"picks_{args.variant}" / str(args.season) / f"week_{args.week:02d}.jsonl"
    output_dir = args.output_dir or Path("research") / "variant_b_week_flow" / str(args.season) / f"week_{args.week:02d}"
    picks_path = picks_file if picks_file.is_absolute() else REPO_ROOT / picks_file
    rules_path = args.rules if args.rules.is_absolute() else REPO_ROOT / args.rules
    out_path = output_dir if output_dir.is_absolute() else REPO_ROOT / output_dir
    default_quotes_file = Path("data") / "market_quotes" / str(args.season) / f"week_{args.week:02d}.jsonl"
    quotes_file = args.quotes_file or default_quotes_file
    quotes_path = quotes_file if quotes_file.is_absolute() else REPO_ROOT / quotes_file
    gpt_snapshots_root = REPO_ROOT / "research" / "gpt_snapshots" / str(args.season) / f"week_{args.week:02d}"
    if args.with_model_proof:
        model_proof_picks = out_path / "model_proof" / picks_path.name
        run(
            [
                sys.executable,
                "scripts/variant_b_model_proof.py",
                "--input",
                str(picks_path.relative_to(REPO_ROOT)),
                "--output",
                str(model_proof_picks.relative_to(REPO_ROOT)),
                "--variant",
                args.variant,
                "--train-seasons",
                args.train_seasons,
            ],
            desc="Generate Variant B model proof",
        )
        picks_path = model_proof_picks

    records = load_jsonl(picks_path)
    quote_overrides = load_quote_overrides(quotes_path)
    rules_config = load_rules_config(rules_path)
    rows: list[dict[str, Any]] = []
    audited = 0

    out_path.mkdir(parents=True, exist_ok=True)
    for record in records:
        tag = str(record.get("tag") or "").upper()
        if not args.all_picks and tag not in ACTION_TAGS:
            continue
        record = attach_gpt_snapshot(record, gpt_snapshots_root)
        record = apply_quote_override(record, quote_overrides.get(record_key(record)))
        audit = build_audit(record, rules_config, args.audit_stage)
        pick_id = canonical_pick_id(record)
        audit_file = out_path / f"{pick_id}.json"
        audit_file.write_text(json.dumps(audit, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        process_values = point_values(audit, 18)
        operator_values = point_values(audit, 19)
        rows.append(
            {
                "pick": pick_label(record),
                "pick_id": pick_id,
                "selected_team": record.get("model_winner"),
                "tag": tag,
                "edge_vs_line": record.get("edge_vs_line"),
                "line": record.get("handicap"),
                "price": record.get("price"),
                "process_quality_status": point_status(audit, 18),
                "gate_state": operator_values.get("gate_state", "UNKNOWN"),
                "operator_action": operator_values.get("operator_action", "UNKNOWN"),
                "hard_blockers_count": process_values.get("coverage", {}).get("hard_blockers_count", 0),
                "pending_not_due_count": process_values.get("coverage", {}).get("pending_not_due_count", 0),
                "audit_file": str(audit_file.relative_to(REPO_ROOT)),
            }
        )
        audited += 1

    write_summary(rows, out_path, model_proof_generated=args.with_model_proof, quotes_loaded=len(quote_overrides))
    if args.write_learning_ledger:
        run(
            [
                sys.executable,
                "scripts/variant_b_learning_ledger.py",
                "--season",
                str(args.season),
                "--week",
                str(args.week),
                "--audit-dir",
                str(out_path.relative_to(REPO_ROOT)),
            ],
            desc="Append Variant B learning ledger",
        )
    print(f"Variant B week flow complete: {audited} audits")
    print(f"summary={out_path / 'summary.md'}")


if __name__ == "__main__":
    main()
