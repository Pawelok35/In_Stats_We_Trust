from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
ACTION_TAGS = {"VALUE PLAY", "GOW", "GOM", "GOY"}


WEEKDAY_KEYS = {
    0: "monday",
    1: "tuesday",
    2: "wednesday",
    3: "thursday",
    4: "friday",
    5: "saturday",
    6: "sunday",
}


@dataclass(frozen=True)
class BotContext:
    season: int
    week: int
    previous_week: int
    variant: str
    run_date: str
    day: str

    def values(self) -> dict[str, Any]:
        return {
            "season": self.season,
            "week": self.week,
            "previous_week": self.previous_week,
            "variant": self.variant,
            "run_date": self.run_date,
            "day": self.day,
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Variant B daily workflow bot.")
    parser.add_argument("--season", type=int, required=True)
    parser.add_argument("--week", type=int, required=True)
    parser.add_argument("--previous-week", type=int)
    parser.add_argument("--variant", default=None)
    parser.add_argument("--config", type=Path, default=Path("config/variant_b_daily_bot.yaml"))
    parser.add_argument("--date", help="Override run date in YYYY-MM-DD format.")
    parser.add_argument(
        "--day",
        choices=list(WEEKDAY_KEYS.values()),
        help="Override weekday key, e.g. tuesday.",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Run command tasks. Default is dry-run/report only.",
    )
    parser.add_argument(
        "--task",
        action="append",
        help="Run/report only selected task id. Can be repeated.",
    )
    return parser.parse_args()


def load_config(path: Path) -> dict[str, Any]:
    resolved = path if path.is_absolute() else REPO_ROOT / path
    with resolved.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise SystemExit(f"Invalid config: {resolved}")
    return data


def parse_run_date(raw: str | None) -> date:
    if raw:
        return datetime.strptime(raw, "%Y-%m-%d").date()
    return datetime.now().astimezone().date()


def format_template(value: Any, mapping: dict[str, Any]) -> Any:
    if isinstance(value, str):
        return value.format(**mapping)
    if isinstance(value, list):
        return [format_template(item, mapping) for item in value]
    if isinstance(value, dict):
        return {key: format_template(item, mapping) for key, item in value.items()}
    return value


def resolve_path(raw: str) -> Path:
    path = Path(raw)
    return path if path.is_absolute() else REPO_ROOT / path


def _safe_load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _load_action_picks(context: BotContext) -> list[dict[str, Any]]:
    path = REPO_ROOT / "data" / f"picks_{context.variant}" / str(context.season) / f"week_{context.week:02d}.jsonl"
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if str(record.get("tag") or "").upper() in ACTION_TAGS:
            rows.append(record)
    return rows


def _line_context(context: BotContext) -> dict[tuple[str, str], dict[str, Any]]:
    path = REPO_ROOT / "config" / "lines" / str(context.season) / f"week{context.week}_lines.yaml"
    payload = _safe_load_yaml(path)
    matchups = payload.get("matchups")
    if not isinstance(matchups, list):
        return {}
    indexed: dict[tuple[str, str], dict[str, Any]] = {}
    for matchup in matchups:
        if not isinstance(matchup, dict):
            continue
        away = str(matchup.get("away") or "").upper()
        home = str(matchup.get("home") or "").upper()
        if away and home:
            indexed[(away, home)] = matchup
    return indexed


def _weekday_for_pick(record: dict[str, Any], lines: dict[tuple[str, str], dict[str, Any]]) -> int | None:
    away = str(record.get("away") or "").upper()
    home = str(record.get("home") or "").upper()
    context = lines.get((away, home), {})
    raw_date = str(context.get("source_game_date_local") or "")
    try:
        return datetime.fromisoformat(raw_date).weekday()
    except ValueError:
        return None


def has_action_scope(context: BotContext, scope: str) -> bool:
    picks = _load_action_picks(context)
    if not picks:
        return False
    if scope == "any":
        return True
    lines = _line_context(context)
    for record in picks:
        weekday = _weekday_for_pick(record, lines)
        if scope == "tnf" and weekday in {2, 3, 4}:
            return True
        if scope == "sunday" and weekday == 6:
            return True
        if scope == "mnf" and weekday == 0:
            return True
        if scope == "sunday_mnf" and weekday in {6, 0}:
            return True
    return False


def should_skip_task(task: dict[str, Any], context: BotContext) -> bool:
    if task.get("when_previous_week_exists") and context.previous_week < 1:
        return True
    scope = task.get("when_action_scope")
    if scope and not has_action_scope(context, str(scope)):
        return True
    return False


def run_command(command: str, *, execute: bool) -> dict[str, Any]:
    if not execute:
        return {"status": "DRY_RUN", "returncode": None}
    result = subprocess.run(command, cwd=REPO_ROOT, shell=True, check=False)
    return {
        "status": "PASS" if result.returncode == 0 else "FAIL",
        "returncode": result.returncode,
    }


def evaluate_task(
    task: dict[str, Any],
    *,
    config: dict[str, Any],
    context: BotContext,
    execute: bool,
) -> dict[str, Any]:
    mapping = context.values()
    mapping.update(format_template(config.get("paths", {}), mapping))
    rendered = format_template(task, mapping)
    task_type = rendered.get("type")
    row: dict[str, Any] = {
        "id": rendered.get("id"),
        "type": task_type,
        "label": rendered.get("label"),
    }
    if should_skip_task(rendered, context):
        row["status"] = "SKIPPED"
        row["reason"] = (
            "previous_week_not_available"
            if rendered.get("when_previous_week_exists")
            else f"no_action_candidate_in_scope:{rendered.get('when_action_scope')}"
        )
        return row

    if task_type == "command":
        command = rendered["command"]
        row["command"] = command
        row.update(run_command(command, execute=execute))
        return row

    if task_type == "check_path":
        path = resolve_path(rendered["path"])
        row["path"] = str(path.relative_to(REPO_ROOT) if path.is_relative_to(REPO_ROOT) else path)
        row["exists"] = path.exists()
        row["status"] = "PASS" if path.exists() else "MISSING"
        return row

    if task_type == "manual":
        manual_inputs = config.get("manual_inputs", {})
        manual_key = rendered.get("input")
        manual = format_template(manual_inputs.get(manual_key, {}), mapping)
        expected = manual.get("expected_path") or manual.get("expected_dir")
        expected_glob = manual.get("expected_glob")
        row["manual_input"] = manual_key
        row["description"] = manual.get("description")
        if expected_glob:
            matches = sorted(REPO_ROOT.glob(expected_glob))
            row["expected_glob"] = expected_glob
            row["matches"] = [str(path.relative_to(REPO_ROOT)) for path in matches[:10]]
            row["match_count"] = len(matches)
            if rendered.get("optional") and not matches:
                row["status"] = "OPTIONAL"
                return row
            row["status"] = "READY" if matches else "NEEDS_OPERATOR"
            return row
        if expected:
            path = resolve_path(expected)
            row["expected_path"] = str(
                path.relative_to(REPO_ROOT) if path.is_relative_to(REPO_ROOT) else path
            )
            row["exists"] = path.exists()
            if rendered.get("optional") and not path.exists():
                row["status"] = "OPTIONAL"
                return row
            row["status"] = "READY" if path.exists() else "NEEDS_OPERATOR"
        else:
            row["status"] = "OPTIONAL" if rendered.get("optional") else "NEEDS_OPERATOR"
        return row

    row["status"] = "UNKNOWN_TASK_TYPE"
    return row


def evaluate_tasks(
    tasks: list[dict[str, Any]],
    *,
    config: dict[str, Any],
    context: BotContext,
    execute: bool,
) -> list[dict[str, Any]]:
    """Evaluate tasks in order, pausing commands after missing manual evidence."""
    rows: list[dict[str, Any]] = []
    manual_blockers: list[str] = []
    for task in tasks:
        task_type = str(task.get("type") or "")
        if execute and manual_blockers and task_type == "command":
            rows.append(
                {
                    "id": task.get("id"),
                    "type": task_type,
                    "label": task.get("label"),
                    "status": "BLOCKED",
                    "reason": "missing_manual_inputs:" + ",".join(manual_blockers),
                }
            )
            continue

        row = evaluate_task(task, config=config, context=context, execute=execute)
        rows.append(row)
        if task_type == "manual" and row.get("status") == "NEEDS_OPERATOR":
            manual_key = str(row.get("manual_input") or task.get("id") or "manual")
            if manual_key not in manual_blockers:
                manual_blockers.append(manual_key)
    return rows


def write_reports(
    rows: list[dict[str, Any]],
    *,
    config: dict[str, Any],
    context: BotContext,
    day_config: dict[str, Any],
    execute: bool,
) -> Path:
    mapping = context.values()
    paths = format_template(config.get("paths", {}), mapping)
    report_template = paths.get(
        "daily_report",
        "research/daily_bot/{season}/week_{week:02d}/{run_date}_{day}.md",
    )
    report_path = resolve_path(report_template)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    json_path = report_path.with_suffix(".json")

    lines = [
        f"# Variant B Daily Bot - {context.run_date} {context.day}",
        "",
        f"Season: `{context.season}`",
        f"Week: `{context.week}`",
        f"Variant: `{context.variant}`",
        f"Mode: `{'EXECUTE' if execute else 'DRY_RUN'}`",
        "",
        f"Day plan: `{day_config.get('label', context.day)}`",
        "",
        "Objective:",
        "",
        "```text",
        str(day_config.get("objective", "")),
        "```",
        "",
        "## Tasks",
        "",
        "| Status | Task | Type | Detail |",
        "| --- | --- | --- | --- |",
    ]
    for row in rows:
        detail = (
            row.get("command")
            or row.get("expected_path")
            or row.get("expected_glob")
            or row.get("path")
            or row.get("reason")
            or ""
        )
        lines.append(
            f"| {row.get('status')} | {row.get('label')} | {row.get('type')} | `{detail}` |"
        )
    lines.extend(
        [
            "",
            "## Next Manual Inputs",
            "",
        ]
    )
    manual_rows = [row for row in rows if row.get("status") == "NEEDS_OPERATOR"]
    if manual_rows:
        for row in manual_rows:
            lines.append(f"- `{row.get('manual_input')}`: {row.get('label')}")
    else:
        lines.append("- Brak manualnych inputow oznaczonych jako missing.")
    lines.append("")

    report_path.write_text("\n".join(lines), encoding="utf-8")
    json_path.write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return report_path


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    run_date = parse_run_date(args.date)
    day = args.day or WEEKDAY_KEYS[run_date.weekday()]
    variant = args.variant or str(config.get("variant", "variant_m"))
    previous_week = args.previous_week if args.previous_week is not None else args.week - 1
    context = BotContext(
        season=args.season,
        week=args.week,
        previous_week=previous_week,
        variant=variant,
        run_date=run_date.isoformat(),
        day=day,
    )
    day_config = config.get("days", {}).get(day)
    if not day_config:
        raise SystemExit(f"No day config for day={day}")
    selected_tasks = set(args.task or [])
    tasks = [
        task
        for task in day_config.get("tasks", [])
        if not selected_tasks or task.get("id") in selected_tasks
    ]
    rows = evaluate_tasks(tasks, config=config, context=context, execute=args.execute)

    report_path = write_reports(
        rows,
        config=config,
        context=context,
        day_config=day_config,
        execute=args.execute,
    )
    print(f"[OK] Daily bot report: {report_path}")


if __name__ == "__main__":
    main()
