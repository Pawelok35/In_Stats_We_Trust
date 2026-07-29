from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def run_step(command: list[str]) -> None:
    print("running=" + " ".join(command))
    subprocess.run(command, cwd=REPO_ROOT, check=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run live watch settlement and weekly review for one NFL week.")
    parser.add_argument("--season", type=int, required=True)
    parser.add_argument("--week", type=int, required=True)
    parser.add_argument("--data-root", type=Path, default=Path("data"))
    parser.add_argument("--min-review-plays", type=int, default=10)
    parser.add_argument("--skip-settlement", action="store_true")
    parser.add_argument("--skip-review", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    python = sys.executable
    base = [
        "--season",
        str(args.season),
        "--week",
        str(args.week),
        "--data-root",
        str(args.data_root),
    ]
    if not args.skip_settlement:
        run_step([python, "scripts/settle_live_watch.py", *base])
    if not args.skip_review:
        run_step(
            [
                python,
                "scripts/live_watch_weekly_review.py",
                *base,
                "--min-review-plays",
                str(args.min_review_plays),
            ]
        )
    print("live_watch_week_flow=done")


if __name__ == "__main__":
    main()
