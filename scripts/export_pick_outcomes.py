from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Dict, Iterable, Tuple

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts import evaluate_picks

TAGS = {"GOY", "GOM", "GOW"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export GOY/GOM/GOW picks with outcomes (Win/Loss/Pending)."
    )
    parser.add_argument(
        "--variant",
        required=True,
        help="Nazwa wariantu (np. 'variant_m'); skrypt uzyje katalogu data/picks_<variant>.",
    )
    parser.add_argument("--season", type=int, default=2025, help="Sezon (domyslnie 2025).")
    parser.add_argument(
        "--start-week",
        type=int,
        help="Tydzien startowy (opcjonalnie).",
    )
    parser.add_argument(
        "--end-week",
        type=int,
        help="Tydzien koncowy (opcjonalnie).",
    )
    parser.add_argument(
        "--manual-results",
        type=Path,
        default=Path("data/results/manual_results.jsonl"),
        help="Sciezka do pliku z recznymi wynikami (domyslnie data/results/manual_results.jsonl).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/reports/pick_outcomes.csv"),
        help="Sciezka pliku wyjsciowego CSV.",
    )
    return parser.parse_args()


def load_go_tier_picks(path: Path, season: int, start_week: int | None, end_week: int | None) -> Iterable[Dict]:
    picks = evaluate_picks.load_picks(path, season, start_week, end_week)
    return [pick for pick in picks if pick.get("tag") in TAGS]


def determine_outcome(
    pick: Dict,
    results: Dict[Tuple[int, str, str], Dict],
) -> tuple[str, int | None, int | None]:
    key = (int(pick["week"]), pick["home"], pick["away"])
    game = results.get(key)
    if not game:
        return "PENDING", None, None

    home_score = game.get("home_score")
    away_score = game.get("away_score")
    if home_score is None or away_score is None:
        return "PENDING", None, None

    home_score = int(home_score)
    away_score = int(away_score)
    pick_side = pick.get("model_winner")
    margin = home_score - away_score if pick_side == pick["home"] else away_score - home_score
    handicap = float(pick.get("handicap", 0.0))
    ats_margin = margin + handicap
    if ats_margin > 0:
        return "WIN", home_score, away_score
    if ats_margin == 0:
        return "PUSH", home_score, away_score
    return "LOSS", home_score, away_score


def write_csv(rows: Iterable[Dict], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "variant",
        "season",
        "week",
        "tag",
        "home_team",
        "away_team",
        "model_winner",
        "handicap",
        "total",
        "result",
        "home_score",
        "away_score",
        "report",
    ]
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    args = parse_args()
    variant = args.variant.strip()
    picks_dir = Path(f"data/picks_{variant}")
    if not picks_dir.exists():
        raise SystemExit(f"[error] Brak katalogu z pickami: {picks_dir}")

    picks = load_go_tier_picks(picks_dir, args.season, args.start_week, args.end_week)
    if not picks:
        raise SystemExit("[error] Brak pickow GOY/GOM/GOW w zadanym zakresie.")

    manual = evaluate_picks.load_manual_results(args.manual_results, season=args.season)
    results = evaluate_picks.load_results(args.season, manual)

    rows = []
    for pick in picks:
        outcome, home_score, away_score = determine_outcome(pick, results)
        rows.append(
            {
                "variant": variant,
                "season": pick["season"],
                "week": pick["week"],
                "tag": pick["tag"],
                "home_team": pick["home"],
                "away_team": pick["away"],
                "model_winner": pick["model_winner"],
                "handicap": pick.get("handicap"),
                "total": pick.get("total"),
                "result": outcome,
                "home_score": home_score,
                "away_score": away_score,
                "report": pick.get("report"),
            }
        )

    write_csv(rows, args.output)
    print(f"[ok] Zapisano {len(rows)} rekordow do {args.output}")


if __name__ == "__main__":
    main()
