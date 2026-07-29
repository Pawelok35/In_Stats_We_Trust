from __future__ import annotations

import argparse
import contextlib
import io
import sys
from pathlib import Path
from typing import Dict, List

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from metrics.variant_registry import ACTIVE_STATUSES, filter_variants, load_variants  # noqa: E402
from scripts import evaluate_picks, matchup_batch  # noqa: E402
from utils.paths import week_lines_path  # noqa: E402

PAYOUTS = {
    "GOY": (3.6, 4.0),
    "GOM": (2.7, 3.0),
    "GOW": (1.8, 2.0),
    "VALUE PLAY": (0.9, 1.0),
    "NEUTRAL": (0.0, 0.0),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run batch + evaluation for multiple tag-rule variants."
    )
    parser.add_argument(
        "--variants-file",
        type=Path,
        default=Path("config/tag_variants.yaml"),
        help="YAML file with variants (name/tag_config/picks_dir).",
    )
    parser.add_argument(
        "--season",
        type=int,
        default=2025,
        help="Season to evaluate (default: 2025).",
    )
    parser.add_argument(
        "--start-week",
        type=int,
        default=6,
        help="Start week (default: 6).",
    )
    parser.add_argument(
        "--end-week",
        type=int,
        default=10,
        help="End week, inclusive (default: 10).",
    )
    parser.add_argument(
        "--manual-results",
        type=Path,
        default=Path("data/results/manual_results.jsonl"),
        help="Optional JSONL file with manual results.",
    )
    parser.add_argument(
        "--regenerate",
        action="store_true",
        help="Regenerate matchup_batch outputs for every selected variant and week.",
    )
    parser.add_argument(
        "--status",
        action="append",
        choices=["champion", "challenger", "experimental", "retired"],
        help=(
            "Filter variants by lifecycle status. Defaults to champion + challenger. "
            "Can be provided multiple times."
        ),
    )
    parser.add_argument(
        "--variant",
        action="append",
        help="Run only the named variant. Can be provided multiple times.",
    )
    return parser.parse_args()


def regenerate_variant(
    variant: Dict[str, str],
    weeks: List[int],
    season: int,
) -> None:
    tag_config = Path(variant["tag_config"])
    picks_dir = Path(variant["picks_dir"])
    picks_dir.mkdir(parents=True, exist_ok=True)

    for week in weeks:
        config_path = week_lines_path(season, week)
        sink = io.StringIO()
        with contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
            matchup_batch.run_batch(
                config_path=config_path,
                output_dir=None,
                default_window=None,
                strict=False,
                combined_output=None,
                picks_dir=picks_dir,
                tag_config=tag_config,
            )


def evaluate_variant(
    name: str,
    variant: Dict[str, str],
    season: int,
    start_week: int,
    end_week: int,
    manual_path: Path | None,
) -> Dict[str, Dict]:
    picks_dir = Path(variant["picks_dir"])
    tag_filter = None
    picks = evaluate_picks.load_picks(picks_dir, season, start_week, end_week)
    manual = evaluate_picks.load_manual_results(manual_path, season=season) if manual_path else {}
    results = evaluate_picks.load_results(season, manual)
    summary = evaluate_picks.evaluate_picks(picks, results, tag_filter)
    return summary


def format_line(tag: str, stats: Dict[str, float]) -> tuple[str, float]:
    wins = int(stats.get("wins", 0))
    losses = int(stats.get("losses", 0))
    pushes = int(stats.get("pushes", 0))
    pending = int(stats.get("pending", 0))
    win_unit, loss_unit = PAYOUTS.get(tag, (0.0, 0.0))
    units = wins * win_unit - losses * loss_unit
    record = f"{wins}-{losses}"
    if pending:
        record += f", {pending} pend"
    if pushes:
        record += f", {pushes} push"
    text = f"{units:+.1f}u ({record})"
    return text, units


def print_summary(name: str, summary: Dict[str, Dict]) -> None:
    print(f"\n=== {name} ===")
    print("Tag             Result (units / record)")
    print("---------------------------------------")
    total_units = 0.0
    for tag in ("GOY", "GOM", "GOW", "VALUE PLAY", "NEUTRAL"):
        stats = summary.get(tag, {"wins": 0, "losses": 0, "pushes": 0, "pending": 0})
        text, units = format_line(tag, stats)
        total_units += units
        print(f"{tag:<15} {text}")
    print(f"{'Total':<15} {total_units:+.1f}u")


def main() -> None:
    args = parse_args()
    weeks = list(range(args.start_week, args.end_week + 1))
    statuses = set(args.status) if args.status else set(ACTIVE_STATUSES)
    names = set(args.variant) if args.variant else None
    variants = filter_variants(
        load_variants(args.variants_file),
        statuses=statuses,
        names=names,
    )
    if not variants:
        raise SystemExit("No variants selected. Check --status/--variant filters.")

    selected = ", ".join(f"{variant['name']}[{variant['status']}]" for variant in variants)
    print(f"Selected variants: {selected}")

    if args.regenerate:
        for variant in variants:
            regenerate_variant(variant, weeks, args.season)

    for variant in variants:
        name = variant["name"]
        summary = evaluate_variant(
            name,
            variant,
            args.season,
            args.start_week,
            args.end_week,
            args.manual_results,
        )
        print_summary(name, summary)


if __name__ == "__main__":
    main()
