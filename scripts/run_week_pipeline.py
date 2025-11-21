from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]


def run(cmd: list[str], *, desc: str) -> None:
    """Execute a shell command and exit early on failure."""
    printable = " ".join(cmd)
    print(f"\n=== {desc} ===")
    print(f">>> {printable}")
    result = subprocess.run(cmd, cwd=ROOT_DIR)
    if result.returncode != 0:
        raise SystemExit(
            f"❌ Step '{desc}' failed with exit code {result.returncode}. "
            f"Command: {printable}"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Orchestrate the weekly pipeline (schedule → picks → convergence)."
    )
    parser.add_argument("--season", type=int, required=True)
    parser.add_argument("--week", type=int, required=True)
    parser.add_argument(
        "--reference-week",
        type=int,
        help="Reference form window for previews (defaults to week-7, min 1).",
    )
    parser.add_argument(
        "--picks-start-week",
        type=int,
        default=1,
        help="Earliest week to regenerate pick variants (default: 1).",
    )
    parser.add_argument(
        "--manual-results",
        type=Path,
        default=Path("data/results/manual_results.jsonl"),
        help="JSONL file with manual score overrides.",
    )
    parser.add_argument(
        "--run-convergence",
        action="store_true",
        help="Run convergence analyzer after generating picks.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    season = args.season
    week = args.week

    if week <= 0:
        raise SystemExit("Week must be a positive integer.")

    through_week = week - 1
    if through_week <= 0:
        raise SystemExit("Week must be > 1 (build-cumulative requires week-1 >= 1).")

    reference_week = (
        args.reference_week if args.reference_week is not None else max(1, week - 7)
    )

    config_path = ROOT_DIR / "config" / "lines" / str(season) / f"week{week}_lines.yaml"
    if not config_path.exists():
        raise SystemExit(f"Missing config file: {config_path}")

    manual_path = args.manual_results.resolve()
    if not manual_path.exists():
        raise SystemExit(f"Missing manual results file: {manual_path}")

    output_dir = ROOT_DIR / "data" / "reports" / "generated" / f"week{week:02d}"
    summary_path = output_dir.parent / f"week{week:02d}_summary.md"

    print("\n==============================")
    print(f"🏈  IN STATS WE TRUST – WEEK {week}")
    print("==============================")
    print(f"Season:            {season}")
    print(f"Target week:       {week}")
    print(f"Through week:      {through_week}")
    print(f"Reference week:    {reference_week}")
    print(f"Config file:       {config_path.relative_to(ROOT_DIR)}")
    print(f"Output directory:  {output_dir.relative_to(ROOT_DIR)}")
    print(f"Summary markdown:  {summary_path.relative_to(ROOT_DIR)}")
    print("==============================\n")

    # 1) Update schedule
    run(
        [
            sys.executable,
            "scripts/update_schedule.py",
            "--season",
            str(season),
            "--week",
            str(week),
        ],
        desc="Update schedule",
    )

    # 2) Build cumulative form
    run(
        [
            sys.executable,
            "-m",
            "app.cli",
            "build-cumulative",
            "--season",
            str(season),
            "--through-week",
            str(through_week),
        ],
        desc="Build cumulative Core12",
    )

    # 3) Generate matchup previews
    run(
        [
            sys.executable,
            "-X",
            "utf8",
            "scripts/generate_matchup_previews.py",
            "--season",
            str(season),
            "--week",
            str(week),
            "--reference-week",
            str(reference_week),
            "--summary",
        ],
        desc="Generate matchup previews",
    )

    # 4) Run matchup batch
    run(
        [
            sys.executable,
            "-X",
            "utf8",
            "scripts/matchup_batch.py",
            "--config",
            str(config_path.relative_to(ROOT_DIR)),
            "--output-dir",
            str(output_dir.relative_to(ROOT_DIR)),
            "--combined-output",
            str(summary_path.relative_to(ROOT_DIR)),
        ],
        desc="Run matchup batch + betting analysis",
    )

    # 5) Regenerate pick variants
    run(
        [
            sys.executable,
            "-X",
            "utf8",
            "scripts/tag_variant_runner.py",
            "--season",
            str(season),
            "--start-week",
            str(args.picks_start_week),
            "--end-week",
            str(week),
            "--regenerate",
            "--manual-results",
            str(manual_path.relative_to(ROOT_DIR)),
        ],
        desc="Regenerate pick variants",
    )

    print("\n==============================")
    print("✅ Weekly pipeline completed")
    print("==============================")
    print(f"Previews dir:     data/reports/comparisons/{season}_w{week}/")
    print(f"Analysis dir:     {output_dir.relative_to(ROOT_DIR)}")
    print(f"Summary markdown: {summary_path.relative_to(ROOT_DIR)}")
    print(f"Picks:            data/picks_variant_*/{season}/week_{week:02d}.jsonl")
    print("==============================\n")

    if not args.run_convergence:
        return

    picks_base = ROOT_DIR / "data"
    variant_paths = {
        "J": picks_base / "picks_variant_j" / str(season) / f"week_{week:02d}.jsonl",
        "C": picks_base / "picks_variant_c_psdiff" / str(season) / f"week_{week:02d}.jsonl",
        "K": picks_base / "picks_variant_k" / str(season) / f"week_{week:02d}.jsonl",
    }
    missing = [k for k, path in variant_paths.items() if not path.exists()]
    if missing:
        print(
            f"[WARN] Skipping convergence analyzer – missing pick files for variants: {', '.join(missing)}"
        )
        return

    run(
        [
            sys.executable,
            "-X",
            "utf8",
            "scripts/convergence_analyzer.py",
            "--variant-j",
            str(variant_paths["J"].relative_to(ROOT_DIR)),
            "--variant-c",
            str(variant_paths["C"].relative_to(ROOT_DIR)),
            "--variant-k",
            str(variant_paths["K"].relative_to(ROOT_DIR)),
            "--week-label",
            f"Week {week}",
        ],
        desc="Run convergence analyzer",
    )
    print("🎯 Convergence analyzer completed.")


if __name__ == "__main__":
    main()
