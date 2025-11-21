from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts import evaluate_picks

TAG_POINTS = {"GOY": 3, "GOM": 2, "GOW": 1}
VARIANT_WEIGHTS = {"J": 1.0, "C": 0.91, "K": 0.88}
BUCKETS = [
    ("Calm", 0.0, 2.5),
    ("Breeze", 2.5, 3.5),
    ("Gale", 3.5, 4.6),
    ("Cyclone", 4.6, 5.6),
    ("Vortex", 5.6, 6.6),
    ("Supercell", 6.6, float("inf")),
]


def load_picks_for_week(season: int, week: int) -> pd.DataFrame:
    variants: List[Tuple[str, Path]] = [
        ("J", Path("data") / "picks_variant_j" / str(season) / f"week_{week:02d}.jsonl"),
        ("C", Path("data") / "picks_variant_c_psdiff" / str(season) / f"week_{week:02d}.jsonl"),
        ("K", Path("data") / "picks_variant_k" / str(season) / f"week_{week:02d}.jsonl"),
    ]
    records: List[Dict] = []
    for variant, path in variants:
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            tag = str(rec.get("tag", "")).upper()
            if tag not in TAG_POINTS:
                continue  # pomijamy sygnały inne niż GOY/GOM/GOW
            rec["tag"] = tag
            rec["variant"] = variant
            records.append(rec)
    return pd.DataFrame(records)


def assign_bucket(rating: float, ultimate: bool) -> str:
    if ultimate:
        return "Ultimate Supercell"
    for name, low, high in BUCKETS:
        if low <= rating < high:
            return name
    return BUCKETS[-1][0]


def build_weather_table(season: int, week: int) -> pd.DataFrame:
    df = load_picks_for_week(season, week)
    if df.empty:
        return pd.DataFrame()
    rows: List[Dict] = []
    for (home, away), grp in df.groupby(["home", "away"]):
        rating = 0.0
        for _, row in grp.iterrows():
            rating += TAG_POINTS.get(str(row.get("tag", "")).upper(), 0) * VARIANT_WEIGHTS.get(
                row["variant"], 0.0
            )
        # ultimate: wszystkie GOY + min confidence/edge_vs_line spełniają progi
        tags = [str(t).upper() for t in grp["tag"].tolist() if isinstance(t, str)]
        confs: list[float] = []
        edges: list[float] = []
        complete = True
        for _, row in grp.iterrows():
            try:
                conf_val = float(row.get("confidence"))
                edge_val = abs(float(row.get("edge_vs_line")))
            except (TypeError, ValueError):
                complete = False
                break
            confs.append(conf_val)
            edges.append(edge_val)
        ultimate = (
            len(tags) == 3
            and all(t == "GOY" for t in tags)
            and complete
            and len(confs) == 3
            and len(edges) == 3
            and min(confs) >= 99.5
            and min(edges) >= 35.0
            and rating >= 8.0
        )
        bucket = assign_bucket(rating, ultimate)
        ref = grp[grp["variant"] == "J"].iloc[0] if not grp[grp["variant"] == "J"].empty else grp.iloc[0]
        pick_team = ref["model_winner"]
        rows.append(
            {
                "season": season,
                "week": week,
                "home_team": home,
                "away_team": away,
                "pick_team": pick_team,
                "rating": round(rating, 3),
                "bucket": bucket,
                "handicap": ref.get("handicap"),
            }
        )
    return pd.DataFrame(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Weather Scale buckets from pick variants J/C/K.")
    parser.add_argument("--season", type=int, required=True, help="Season, e.g. 2025")
    parser.add_argument("--week", type=int, help="Single week number, e.g. 12")
    parser.add_argument("--start-week", type=int, help="Start week (inclusive) for range generation.")
    parser.add_argument("--end-week", type=int, help="End week (inclusive) for range generation.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/results/weather_bucket_games.csv"),
        help="CSV output path (default: data/results/weather_bucket_games.csv)",
    )
    parser.add_argument(
        "--manual-results",
        type=Path,
        default=Path("data/results/manual_results.jsonl"),
        help="Optional JSONL with manual results to score picks (for WIN/LOSS/PUSH).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.start_week and args.end_week:
        weeks = list(range(args.start_week, args.end_week + 1))
    elif args.week:
        weeks = [args.week]
    else:
        raise SystemExit("Podaj --week lub zakres --start-week/--end-week.")

    tables = []
    for wk in weeks:
        tbl = build_weather_table(args.season, wk)
        if tbl.empty:
            print(f"[WARN] Skipping week {wk}: no GOY/GOM/GOW picks found.")
            continue
        tables.append(tbl)
    if not tables:
        raise SystemExit("Brak picków w podanym zakresie tygodni.")
    table = pd.concat(tables, ignore_index=True)
    # compute result if scores available
    manual = evaluate_picks.load_manual_results(args.manual_results)
    results = evaluate_picks.load_results(args.season, manual)
    def compute_result(row: pd.Series) -> str:
        key = (int(row["week"]), row["home_team"], row["away_team"])
        game = results.get(key)
        if not game or pd.isna(game.get("home_score")) or pd.isna(game.get("away_score")):
            return "PENDING"
        home_score = int(game["home_score"])
        away_score = int(game["away_score"])
        pick = row["pick_team"]
        handicap = row.get("handicap")
        try:
            handicap_val = float(handicap)
        except (TypeError, ValueError):
            return "PENDING"
        margin = home_score - away_score if pick == row["home_team"] else away_score - home_score
        ats_margin = margin + handicap_val
        if ats_margin > 0:
            return "WIN"
        if ats_margin == 0:
            return "PUSH"
        return "LOSS"
    table["result"] = table.apply(compute_result, axis=1)
    table = table.drop(columns=["handicap"])

    out_path = args.output
    if out_path.name == "weather_bucket_games.csv":
        out_path = out_path.with_name(f"weather_bucket_games_season{args.season}.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(out_path, index=False)
    print(f"Wrote {len(table)} rows to {out_path}")


if __name__ == "__main__":
    main()
