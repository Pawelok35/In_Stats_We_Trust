"""
Export historical Weather Scale picks (Supercell/Vortex/Cyclone/etc.) for a variant.

For each pick JSONL, we classify by edge_vs_line / confidence and join with results
from manual overrides + schedule. Output is a CSV with one row per qualifying pick.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts import evaluate_picks  # noqa: E402
from scripts.export_model_matrix import _handicap_for_pick, _resolve_spread_home, compute_result  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export Weather Scale history for a pick variant.")
    parser.add_argument("--season", type=int, required=True, help="Season, e.g. 2025")
    parser.add_argument("--start-week", type=int, default=1, help="First week to include (default: 1)")
    parser.add_argument("--end-week", type=int, default=18, help="Last week to include (default: 18)")
    parser.add_argument(
        "--variant-m-dir",
        type=Path,
        default=Path("data/picks_variant_m"),
        help="Directory with weekly JSONL pick files for variant M.",
    )
    parser.add_argument(
        "--variant-d-dir",
        type=Path,
        default=Path("data/picks_variant_d_balanced"),
        help="Directory with weekly JSONL pick files for variant D.",
    )
    parser.add_argument(
        "--variant-b-dir",
        type=Path,
        default=Path("data/picks_variant_b_edge_focus"),
        help="Directory with weekly JSONL pick files for variant B (used for edge/conf thresholds).",
    )
    parser.add_argument(
        "--manual-results",
        type=Path,
        default=Path("data/results/manual_results.jsonl"),
        help="Manual results overrides (JSONL).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/results/weather_scale_history.csv"),
        help="Output CSV path.",
    )
    return parser.parse_args()


def rating(edge: float, conf: float) -> Tuple[str, float] | None:
    """
    Tighter thresholds to prioritize higher-quality signals.
    """
    if conf >= 98 and edge >= 27:
        return "Ultimate Supercell", 4.0
    if edge >= 8 and conf >= 85:
        return "Supercell", 3.5
    if 6 <= edge < 8 and conf >= 80:
        return "Vortex", 3.0
    if 4 <= edge < 6 and conf >= 70:
        return "Cyclone", 2.5
    if 3 <= edge < 4 and conf >= 65:
        return "Gale", 2.0
    if 2 <= edge < 3 and conf >= 60:
        return "Breeze", 1.5
    return None


def load_picks(variant_dir: Path, season: int, start_week: int, end_week: int) -> Iterable[dict]:
    season_dir = variant_dir / str(season)
    if not season_dir.exists():
        return []
    for path in sorted(season_dir.glob("week_*.jsonl")):
        try:
            week = int(path.stem.split("_")[1])
        except Exception:
            continue
        if week < start_week or week > end_week:
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def main() -> None:
    args = parse_args()
    manual = evaluate_picks.load_manual_results(args.manual_results, season=args.season)
    results = evaluate_picks.load_results(args.season, manual)

    rows: List[Dict] = []

    # Load picks for M/D/B
    picks_m = {(p["home"], p["away"]): p for p in load_picks(args.variant_m_dir, args.season, args.start_week, args.end_week)}
    picks_d = {(p["home"], p["away"]): p for p in load_picks(args.variant_d_dir, args.season, args.start_week, args.end_week)}
    picks_b = {(p["home"], p["away"]): p for p in load_picks(args.variant_b_dir, args.season, args.start_week, args.end_week)}

    priority_tags = {"GOY", "GOM", "GOW"}

    for matchup in sorted(set(picks_m) & set(picks_d) & set(picks_b)):
        m = picks_m[matchup]
        d = picks_d[matchup]
        b = picks_b[matchup]

        # Consensus winner across M/D/B
        if len({m.get("model_winner"), d.get("model_winner"), b.get("model_winner")}) != 1:
            continue

        # Optional: prioritize only high-signal tags
        if {m.get("tag"), d.get("tag"), b.get("tag")} - priority_tags:
            continue

        edge = float(b["edge_vs_line"])
        conf = float(b["confidence"])
        rated = rating(edge, conf)
        if not rated:
            continue

        code, stake = rated
        key = (int(b["week"]), b["home"], b["away"])
        game = results.get(key, {})
        spread_home = _resolve_spread_home(b)
        handicap_for_pick = _handicap_for_pick(b, spread_home)
        ats_margin, result = compute_result(b, game, handicap_for_pick)

        rows.append(
            {
                "season": b["season"],
                "week": b["week"],
                "rating": code,
                "stake": stake,
                "home_team": b["home"],
                "away_team": b["away"],
                "model_winner": b.get("model_winner"),
                "edge_vs_line": edge,
                "confidence": conf,
                "tag_m": m.get("tag"),
                "tag_d": d.get("tag"),
                "tag_b": b.get("tag"),
                "result": result,
                "ats_margin": ats_margin,
                "home_score": game.get("home_score"),
                "away_score": game.get("away_score"),
            }
        )

    rows.sort(key=lambda r: (int(r["week"]), r["rating"], r["home_team"]))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "season",
        "week",
        "rating",
        "stake",
        "home_team",
        "away_team",
        "model_winner",
        "edge_vs_line",
        "confidence",
        "tag_m",
        "tag_d",
        "tag_b",
        "result",
        "ats_margin",
        "home_score",
        "away_score",
    ]
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"[ok] zapisano {len(rows)} rekordów do {args.output}")


if __name__ == "__main__":
    main()
