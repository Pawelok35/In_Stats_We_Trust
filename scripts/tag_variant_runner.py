from __future__ import annotations

import argparse
import contextlib
import io
import sys
from pathlib import Path
from typing import Dict, List

import yaml

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts import matchup_batch, evaluate_picks
from utils.paths import week_lines_path

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
        help="YAML z listą wariantów (name/tag_config/picks_dir).",
    )
    parser.add_argument(
        "--season",
        type=int,
        default=2025,
        help="Sezon do oceny (domyślnie 2025).",
    )
    parser.add_argument(
        "--start-week",
        type=int,
        default=6,
        help="Tydzień początkowy (domyślnie 6).",
    )
    parser.add_argument(
        "--end-week",
        type=int,
        default=10,
        help="Tydzień końcowy włącznie (domyślnie 10).",
    )
    parser.add_argument(
        "--manual-results",
        type=Path,
        default=Path("data/results/manual_results.jsonl"),
        help="Opcjonalny plik JSONL z ręcznie wpisanymi wynikami.",
    )
    parser.add_argument(
        "--regenerate",
        action="store_true",
        help="Jeśli podane, ponownie uruchamia matchup_batch dla każdego wariantu i tygodnia.",
    )
    return parser.parse_args()


def load_variants(path: Path) -> List[Dict[str, str]]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not data or "variants" not in data:
        raise ValueError(f"Plik {path} nie zawiera sekcji 'variants'.")
    return data["variants"]


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
    manual = evaluate_picks.load_manual_results(manual_path) if manual_path else {}
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
    variants = load_variants(args.variants_file)

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
