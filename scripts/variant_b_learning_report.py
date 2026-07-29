from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def safe_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(out):
        return None
    return out


def p_bucket(value: float | None) -> str:
    if value is None:
        return "UNKNOWN"
    if value < 0.45:
        return "<45%"
    if value < 0.50:
        return "45-50%"
    if value < 0.55:
        return "50-55%"
    if value < 0.60:
        return "55-60%"
    if value < 0.65:
        return "60-65%"
    return "65%+"


def scan_ledger(root: Path) -> dict[str, list[dict[str, Any]]]:
    tables = {
        "model_runs": [],
        "model_predictions": [],
        "audit_results": [],
        "post_event_evaluations": [],
        "process_failures": [],
    }
    for week_dir in sorted(root.glob("*/*")):
        if not week_dir.is_dir():
            continue
        for table in tables:
            tables[table].extend(load_jsonl(week_dir / f"{table}.jsonl"))
    return tables


def counts(values: list[str]) -> dict[str, int]:
    out: dict[str, int] = {}
    for value in values:
        out[value] = out.get(value, 0) + 1
    return dict(sorted(out.items()))


def calibration_rows(evaluations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    settled = [row for row in evaluations if row.get("status") == "SETTLED"]
    buckets: dict[str, list[dict[str, Any]]] = {}
    for row in settled:
        buckets.setdefault(p_bucket(safe_float(row.get("p_cover"))), []).append(row)
    rows: list[dict[str, Any]] = []
    for bucket, group in sorted(buckets.items()):
        covers = sum(1 for row in group if row.get("settlement") == "COVER")
        pushes = sum(1 for row in group if row.get("settlement") == "PUSH")
        losses = sum(1 for row in group if row.get("settlement") == "LOSS")
        decisions = covers + losses
        avg_p_cover = sum(safe_float(row.get("p_cover")) or 0 for row in group) / len(group)
        rows.append(
            {
                "p_cover_bucket": bucket,
                "sample_size": len(group),
                "covers": covers,
                "pushes": pushes,
                "losses": losses,
                "cover_rate_ex_push": covers / decisions if decisions else None,
                "avg_p_cover": avg_p_cover,
                "calibration_error": (covers / decisions - avg_p_cover) if decisions else None,
            }
        )
    return rows


def write_report(path: Path, tables: dict[str, list[dict[str, Any]]], registry: dict[str, Any] | None) -> None:
    evaluations = tables["post_event_evaluations"]
    settled = [row for row in evaluations if row.get("status") == "SETTLED"]
    pending = [row for row in evaluations if str(row.get("status", "")).startswith("PENDING")]
    prediction_ids = {row.get("model_prediction_id") for row in tables["model_predictions"]}
    run_versions = counts([str(row.get("model_version") or "UNKNOWN") for row in tables["model_runs"]])
    failure_points = counts(
        [f"{row.get('point_number')}_{row.get('point_name')}" for row in tables["process_failures"]]
    )
    lines = [
        "# Variant B Learning Report",
        "",
        "## Registry",
        "",
    ]
    if registry:
        champion = registry.get("champion_model", {})
        policy = registry.get("promotion_policy", {})
        lines.extend(
            [
                f"- Champion: `{champion.get('model_version', 'UNKNOWN')}`",
                f"- Champion status: `{champion.get('status', 'UNKNOWN')}`",
                f"- Promotion policy: `{policy.get('policy_version', 'UNKNOWN')}`",
                f"- Minimum settled predictions: `{policy.get('minimum_settled_predictions', 'UNKNOWN')}`",
                "",
            ]
        )
    else:
        lines.extend(["- Registry not found.", ""])

    lines.extend(
        [
            "## Ledger Coverage",
            "",
            f"- Model runs: `{len(tables['model_runs'])}`",
            f"- Unique predictions: `{len(prediction_ids)}`",
            f"- Audit results: `{len(tables['audit_results'])}`",
            f"- Process failures: `{len(tables['process_failures'])}`",
            f"- Post-event evaluations: `{len(evaluations)}`",
            f"- Settled evaluations: `{len(settled)}`",
            f"- Pending evaluations: `{len(pending)}`",
            "",
            "## Model Versions",
            "",
        ]
    )
    if run_versions:
        for key, value in run_versions.items():
            lines.append(f"- `{key}`: {value}")
    else:
        lines.append("- No model runs.")

    lines.extend(["", "## Process Failures", ""])
    if failure_points:
        for key, value in failure_points.items():
            lines.append(f"- `{key}`: {value}")
    else:
        lines.append("- No process failures.")

    lines.extend(["", "## Calibration MVP", ""])
    cal_rows = calibration_rows(evaluations)
    if not cal_rows:
        lines.append("No settled predictions yet. Calibration starts after outcomes are available.")
    else:
        lines.extend(
            [
                "| p_cover bucket | n | covers | pushes | losses | cover rate ex-push | avg p_cover | calibration error |",
                "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for row in cal_rows:
            lines.append(
                "| {p_cover_bucket} | {sample_size} | {covers} | {pushes} | {losses} | {cover_rate_ex_push:.3f} | {avg_p_cover:.3f} | {calibration_error:.3f} |".format(
                    **{
                        **row,
                        "cover_rate_ex_push": row["cover_rate_ex_push"] or 0.0,
                        "calibration_error": row["calibration_error"] or 0.0,
                    }
                )
            )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Variant B learning ledger report.")
    parser.add_argument("--ledger-root", type=Path, default=Path("data/learning_ledger"))
    parser.add_argument("--registry", type=Path, default=Path("config/model_registry.json"))
    parser.add_argument("--output", type=Path, default=Path("research/variant_b_learning_report.md"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ledger_root = args.ledger_root if args.ledger_root.is_absolute() else REPO_ROOT / args.ledger_root
    registry_path = args.registry if args.registry.is_absolute() else REPO_ROOT / args.registry
    output = args.output if args.output.is_absolute() else REPO_ROOT / args.output
    registry = json.loads(registry_path.read_text(encoding="utf-8")) if registry_path.exists() else None
    tables = scan_ledger(ledger_root)
    write_report(output, tables, registry)
    print(f"[OK] learning report={output}")


if __name__ == "__main__":
    main()
