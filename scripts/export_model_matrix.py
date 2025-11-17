from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any, Dict, List, Tuple

import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts import evaluate_picks

Key = Tuple[int, str, str]


def _resolve_spread_home(record: Dict[str, Any]) -> float | None:
    """Return spread for the home team, preferring explicit spread over handicap."""
    for key in ("spread", "handicap"):
        value = record.get(key)
        if value in (None, ""):
            continue
        try:
            return float(value)
        except (TypeError, ValueError):
            continue
    return None


def _handicap_for_pick(record: Dict[str, Any], spread_home: float | None) -> float | None:
    """Return handicap from the pick perspective using the home spread baseline."""
    if spread_home is None:
        return None
    pick_side = record.get("model_winner")
    if pick_side == record.get("home"):
        return spread_home
    if pick_side == record.get("away"):
        return -spread_home
    return spread_home


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Eksportuje picki variantów M/D/B w formacie długim."
    )
    parser.add_argument("--season", type=int, required=True)
    parser.add_argument("--start-week", type=int, default=1)
    parser.add_argument("--end-week", type=int, default=18)
    parser.add_argument(
        "--variant-m-dir",
        type=Path,
        default=Path("data/picks_variant_m"),
    )
    parser.add_argument(
        "--variant-d-dir",
        type=Path,
        default=Path("data/picks_variant_d_balanced"),
    )
    parser.add_argument(
        "--variant-b-dir",
        type=Path,
        default=Path("data/picks_variant_b_edge_focus"),
    )
    parser.add_argument(
        "--manual-results",
        type=Path,
        default=Path("data/results/manual_results.jsonl"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/reports/model_picks.csv"),
    )
    return parser.parse_args()


def load_picks(base_dir: Path, args: argparse.Namespace) -> List[Dict]:
    return evaluate_picks.load_picks(base_dir, args.season, args.start_week, args.end_week)


def load_results(args: argparse.Namespace) -> Dict[Key, Dict]:
    manual = evaluate_picks.load_manual_results(args.manual_results)
    return evaluate_picks.load_results(args.season, manual)


def compute_result(
    pick: Dict, game: Dict | None, handicap_for_pick: float | None
) -> Tuple[float | None, str]:
    if not game or game.get("home_score") is None or game.get("away_score") is None:
        return None, "PENDING"
    home_score = float(game["home_score"])
    away_score = float(game["away_score"])
    pick_side = pick["model_winner"]
    if pick_side == pick.get("home"):
        margin = home_score - away_score
    elif pick_side == pick.get("away"):
        margin = away_score - home_score
    else:
        margin = home_score - away_score
    handicap = handicap_for_pick or 0.0
    ats_margin = margin + handicap
    if ats_margin > 0:
        result = "WIN"
    elif ats_margin < 0:
        result = "LOSS"
    else:
        result = "PUSH"
    return ats_margin, result


def build_rows(variant: str, picks: List[Dict], results: Dict[Key, Dict]) -> List[Dict]:
    rows: List[Dict] = []
    for pick in picks:
        key = (int(pick["week"]), pick["home"], pick["away"])
        game = results.get(key)
        spread_home = _resolve_spread_home(pick)
        handicap_for_pick = _handicap_for_pick(pick, spread_home)
        ats_margin, result = compute_result(pick, game, handicap_for_pick)
        row = {
            "variant": variant,
            "season": pick["season"],
            "week": pick["week"],
            "tag": pick.get("tag"),
            "home_team": pick["home"],
            "away_team": pick["away"],
            "model_winner": pick.get("model_winner"),
            "market_winner": pick.get("market_winner"),
            "spread_home": spread_home,
            "handicap_for_pick": handicap_for_pick,
            "home_score": None if not game else game.get("home_score"),
            "away_score": None if not game else game.get("away_score"),
            "ats_margin": ats_margin,
            "result": result,
        }
        rows.append(row)
    return rows


def write_csv(rows: List[Dict], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "variant",
        "season",
        "week",
        "tag",
        "home_team",
        "away_team",
        "model_winner",
        "market_winner",
        "spread_home",
        "handicap_for_pick",
        "home_score",
        "away_score",
        "ats_margin",
        "result",
    ]
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    args = parse_args()
    results = load_results(args)

    rows: List[Dict] = []
    rows += build_rows("m", load_picks(args.variant_m_dir, args), results)
    rows += build_rows("d", load_picks(args.variant_d_dir, args), results)
    rows += build_rows("b", load_picks(args.variant_b_dir, args), results)

    rows.sort(key=lambda r: (r["variant"], r["week"], r["home_team"]))
    write_csv(rows, args.output)
    print(f"[ok] zapisano {len(rows)} rekordów do {args.output}")


if __name__ == "__main__":
    main()
