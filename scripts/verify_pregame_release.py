"""Release gate for the central pregame workflow and frozen Champion CORE."""

from __future__ import annotations

import subprocess
import sys


def main() -> int:
    commands = [
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "tests/test_pregame_weekly_cli.py",
            "tests/test_pregame_wager_execution_settlement.py",
            "tests/test_pregame_wager_execution_clv.py",
        ],
        [sys.executable, "-m", "pytest", "-q", "tests/test_champion_core_regression.py"],
    ]
    for command in commands:
        print("$", " ".join(command))
        completed = subprocess.run(command, check=False)
        if completed.returncode != 0:
            return completed.returncode
    print("RELEASE_GATE: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
