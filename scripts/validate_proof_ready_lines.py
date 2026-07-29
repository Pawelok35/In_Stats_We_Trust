from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from utils.team_aliases import normalize_team_code

REQUIRED_TOP_LEVEL = {"season", "week", "matchups"}
REQUIRED_MATCHUP_FIELDS = {"home", "away", "spread", "total"}
REQUIRED_PROOF_FIELDS = {"book", "price", "decision_ts_utc"}


def load_lines_config(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"Lines config must be a YAML mapping: {path}")
    return payload


def validate_config(payload: dict[str, Any]) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    missing_top = sorted(REQUIRED_TOP_LEVEL - set(payload))
    for field in missing_top:
        issues.append({"scope": "top_level", "field": field, "message": "missing top-level field"})

    matchups = payload.get("matchups")
    if not isinstance(matchups, list):
        issues.append({"scope": "top_level", "field": "matchups", "message": "must be a list"})
        matchups = []

    rows = []
    for index, matchup in enumerate(matchups):
        if not isinstance(matchup, dict):
            issues.append(
                {
                    "scope": "matchup",
                    "index": index,
                    "field": None,
                    "message": "matchup entry must be a mapping",
                }
            )
            continue
        row_issues = validate_matchup(matchup, index)
        issues.extend(row_issues)
        rows.append(
            {
                "index": index,
                "home": normalize_team_code(matchup.get("home")),
                "away": normalize_team_code(matchup.get("away")),
                "proof_ready": not row_issues,
                "issue_count": len(row_issues),
            }
        )

    return {
        "season": payload.get("season"),
        "week": payload.get("week"),
        "matchups": len(matchups),
        "proof_ready_matchups": sum(1 for row in rows if row["proof_ready"]),
        "not_ready_matchups": sum(1 for row in rows if not row["proof_ready"]),
        "proof_ready": not issues and bool(matchups),
        "issues": issues,
        "rows": rows,
    }


def validate_matchup(matchup: dict[str, Any], index: int) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for field in sorted(REQUIRED_MATCHUP_FIELDS | REQUIRED_PROOF_FIELDS):
        if matchup.get(field) in (None, ""):
            issues.append(
                {
                    "scope": "matchup",
                    "index": index,
                    "game": _game_label(matchup),
                    "field": field,
                    "message": "missing required field",
                }
            )

    for numeric_field in ("spread", "total", "price"):
        if matchup.get(numeric_field) not in (None, ""):
            try:
                float(matchup[numeric_field])
            except (TypeError, ValueError):
                issues.append(
                    {
                        "scope": "matchup",
                        "index": index,
                        "game": _game_label(matchup),
                        "field": numeric_field,
                        "message": "must be numeric",
                    }
                )

    timestamp = matchup.get("decision_ts_utc")
    if timestamp not in (None, "") and not _is_utc_timestamp(str(timestamp)):
        issues.append(
            {
                "scope": "matchup",
                "index": index,
                "game": _game_label(matchup),
                "field": "decision_ts_utc",
                "message": "must be an ISO-8601 UTC timestamp",
            }
        )

    if matchup.get("line") not in (None, ""):
        try:
            float(matchup["line"])
        except (TypeError, ValueError):
            issues.append(
                {
                    "scope": "matchup",
                    "index": index,
                    "game": _game_label(matchup),
                    "field": "line",
                    "message": "must be numeric when provided",
                }
            )

    return issues


def _is_utc_timestamp(value: str) -> bool:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() == timezone.utc.utcoffset(parsed)


def _game_label(matchup: dict[str, Any]) -> str:
    away = normalize_team_code(matchup.get("away")) or "UNKNOWN"
    home = normalize_team_code(matchup.get("home")) or "UNKNOWN"
    return f"{away} @ {home}"


def write_markdown_report(report: dict[str, Any], output_path: Path, source_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Proof-Ready Lines Validation",
        "",
        f"Source: `{source_path}`",
        f"Season/week: {report.get('season')}/W{report.get('week')}",
        "",
        "## Summary",
        "",
        f"- Matchups: {report['matchups']}",
        f"- Proof-ready matchups: {report['proof_ready_matchups']}",
        f"- Not-ready matchups: {report['not_ready_matchups']}",
        f"- Proof-ready week: {report['proof_ready']}",
        "",
        "## Matchups",
        "",
        "| # | Game | Proof-ready | Issues |",
        "|---:|---|---|---:|",
    ]
    for row in report["rows"]:
        lines.append(
            f"| {row['index']} | {row['away']} @ {row['home']} | "
            f"{row['proof_ready']} | {row['issue_count']} |"
        )

    lines.extend(["", "## Issues", ""])
    if not report["issues"]:
        lines.append("No issues found.")
    else:
        lines.extend(["| Scope | # | Game | Field | Message |", "|---|---:|---|---|---|"])
        for issue in report["issues"]:
            lines.append(
                "| {scope} | {index} | {game} | `{field}` | {message} |".format(
                    scope=issue.get("scope", ""),
                    index=issue.get("index", ""),
                    game=issue.get("game", ""),
                    field=issue.get("field", ""),
                    message=issue.get("message", ""),
                )
            )
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path


def default_output_path(config_path: Path, report: dict[str, Any]) -> Path:
    season = report.get("season") or "unknown"
    week = report.get("week") or "unknown"
    return Path("data/proof_ready_checks") / str(season) / f"week_{int(week):02d}_lines_check.md"


def validate_file(config_path: Path, output_path: Path | None = None) -> tuple[dict[str, Any], Path]:
    payload = load_lines_config(config_path)
    report = validate_config(payload)
    destination = output_path or default_output_path(config_path, report)
    write_markdown_report(report, destination, config_path)
    return report, destination


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate weekly line YAML for proof-ready freeze.")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--json", action="store_true", help="Print machine-readable summary.")
    parser.add_argument(
        "--fail-on-not-ready",
        action="store_true",
        help="Exit with code 1 when the week is not proof-ready.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report, output_path = validate_file(args.config, args.output)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"report={output_path}")
        print(f"proof_ready={report['proof_ready']}")
        print(f"proof_ready_matchups={report['proof_ready_matchups']}")
        print(f"not_ready_matchups={report['not_ready_matchups']}")
    if args.fail_on_not_ready and not report["proof_ready"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
