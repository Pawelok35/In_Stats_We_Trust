from pathlib import Path

from scripts import variant_b_daily_bot as daily_bot


def _context() -> daily_bot.BotContext:
    return daily_bot.BotContext(
        season=2026,
        week=1,
        previous_week=0,
        variant="variant_m",
        run_date="2026-09-08",
        day="tuesday",
    )


def test_execute_blocks_commands_after_missing_manual_input(tmp_path: Path, monkeypatch):
    calls: list[str] = []
    monkeypatch.setattr(
        daily_bot,
        "run_command",
        lambda command, execute: calls.append(command) or {"status": "PASS", "returncode": 0},
    )
    config = {
        "manual_inputs": {
            "snapshot": {
                "expected_path": str(tmp_path / "missing.yaml"),
            }
        }
    }
    tasks = [
        {"id": "before", "type": "command", "label": "Before", "command": "before"},
        {"id": "manual", "type": "manual", "label": "Manual", "input": "snapshot"},
        {"id": "after", "type": "command", "label": "After", "command": "after"},
    ]

    rows = daily_bot.evaluate_tasks(tasks, config=config, context=_context(), execute=True)

    assert calls == ["before"]
    assert [row["status"] for row in rows] == ["PASS", "NEEDS_OPERATOR", "BLOCKED"]


def test_execute_continues_when_manual_input_exists(tmp_path: Path, monkeypatch):
    snapshot = tmp_path / "ready.yaml"
    snapshot.write_text("ready: true\n", encoding="utf-8")
    calls: list[str] = []
    monkeypatch.setattr(
        daily_bot,
        "run_command",
        lambda command, execute: calls.append(command) or {"status": "PASS", "returncode": 0},
    )
    config = {"manual_inputs": {"snapshot": {"expected_path": str(snapshot)}}}
    tasks = [
        {"id": "manual", "type": "manual", "label": "Manual", "input": "snapshot"},
        {"id": "after", "type": "command", "label": "After", "command": "after"},
    ]

    rows = daily_bot.evaluate_tasks(tasks, config=config, context=_context(), execute=True)

    assert calls == ["after"]
    assert [row["status"] for row in rows] == ["READY", "PASS"]
