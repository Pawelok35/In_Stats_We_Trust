from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def run(cmd: list[str], *, desc: str) -> None:
    print(f"\n=== {desc} ===")
    print(">>> " + " ".join(cmd))
    result = subprocess.run(cmd, cwd=REPO_ROOT, check=False)
    if result.returncode != 0:
        raise SystemExit(f"{desc} failed with exit code {result.returncode}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run proof-ready prospective weekly flow.")
    parser.add_argument("--season", type=int, required=True)
    parser.add_argument("--week", type=int, required=True)
    parser.add_argument("--lines-config", type=Path)
    parser.add_argument("--variant", default="variant_m")
    parser.add_argument("--operator", default="daniel")
    parser.add_argument("--metrics-season", type=int)
    parser.add_argument("--reference-week", type=int)
    parser.add_argument("--preseason-seed-source", type=Path)
    parser.add_argument("--preseason-seed-destination", type=Path)
    parser.add_argument("--skip-previews", action="store_true")
    parser.add_argument("--skip-freeze", action="store_true")
    parser.add_argument(
        "--allow-not-proof-ready",
        action="store_true",
        help="Allow candidate scan to continue when line proof fields are incomplete.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    season = args.season
    week = args.week
    lines_config = args.lines_config or Path("config") / "lines" / str(season) / f"week{week}_lines.yaml"
    variant = args.variant
    tag_config = Path("config") / "tag_rules" / f"{variant}.yaml"
    picks_dir = Path("data") / f"picks_{variant}"
    picks_path = picks_dir / str(season) / f"week_{week:02d}.jsonl"
    output_dir = Path("data") / "reports" / "generated" / f"week{week:02d}"
    summary_path = Path("data") / "reports" / "generated" / f"week{week:02d}_summary.md"

    validate_cmd = [
        sys.executable,
        "scripts/validate_proof_ready_lines.py",
        "--config",
        str(lines_config),
    ]
    if not args.allow_not_proof_ready:
        validate_cmd.append("--fail-on-not-ready")
    run(validate_cmd, desc="Validate proof-ready lines")

    if args.preseason_seed_source and args.preseason_seed_destination:
        run(
            [
                sys.executable,
                "scripts/seed_preseason_rolling_snapshot.py",
                "--source",
                str(args.preseason_seed_source),
                "--destination",
                str(args.preseason_seed_destination),
                "--overwrite",
            ],
            desc="Seed preseason rolling snapshot",
        )

    if not args.skip_previews:
        preview_cmd = [
            sys.executable,
            "-X",
            "utf8",
            "scripts/generate_matchup_previews.py",
            "--season",
            str(season),
            "--week",
            str(week),
            "--summary",
        ]
        if args.metrics_season:
            preview_cmd.extend(["--metrics-season", str(args.metrics_season)])
        if args.reference_week:
            preview_cmd.extend(["--reference-week", str(args.reference_week)])
        run(preview_cmd, desc="Generate matchup previews")

    run(
        [
            sys.executable,
            "-X",
            "utf8",
            "scripts/matchup_batch.py",
            "--config",
            str(lines_config),
            "--output-dir",
            str(output_dir),
            "--combined-output",
            str(summary_path),
            "--picks-dir",
            str(picks_dir),
            "--tag-config",
            str(tag_config),
            "--strict",
        ],
        desc=f"Generate picks for {variant}",
    )

    if not args.skip_freeze:
        run(
            [
                sys.executable,
                "scripts/freeze_prospective_picks.py",
                "--source",
                str(picks_path),
                "--operator",
                args.operator,
            ],
            desc="Freeze prospective picks",
        )

    run(
        [
            sys.executable,
            "scripts/update_prospective_ytd_report.py",
            "--season",
            str(season),
        ],
        desc="Refresh prospective YTD",
    )

    print("\n=== Prospective week flow complete ===")
    print(f"lines={lines_config}")
    print(f"picks={picks_path}")
    print(f"ledger=data/prospective_ledger/{season}/week_{week:02d}_prospective.jsonl")
    print(f"ytd=data/prospective_ledger/{season}/prospective_ytd_report.md")


if __name__ == "__main__":
    main()
