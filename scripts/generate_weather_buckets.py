from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
import polars as pl

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts import evaluate_picks
from metrics.form_windows import compute_form_windows
from utils.guardrails import (
    apply_guardrails,
    apply_guardrails_v2,
    apply_guardrails_v2_1,
    apply_value_buffer_guard,
    load_guardrails,
)

TAG_POINTS = {"GOY": 3, "GOM": 2, "GOW": 1}
VARIANT_WEIGHTS = {"J": 1.0, "C": 0.91, "K": 0.88}
BUCKETS = [
    ("Calm", 0.0, 2.9),
    ("Breeze", 2.9, 3.2),
    ("Gale", 3.2, 4.8),
    ("Cyclone", 4.8, 6.0),
    ("Supercell", 6.0, float("inf")),
]
BUCKET_STAKES = {
    "Calm": 1.0,
    "Breeze": 1.0,  # nie wymienione w briefie, traktujemy jak Calm
    "Gale": 2.0,
    "Vortex": 3.0,
    "Cyclone": 4.0,
    "Supercell": 4.0,
    "Ultimate Supercell": 4.0,
}


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


def _form_windows_for_teams(season: int, week: int, teams: List[str]) -> pl.DataFrame:
    teams = sorted({t.upper() for t in teams})
    if not teams:
        return pl.DataFrame()
    return compute_form_windows(season=season, current_week=week, teams=teams)


def _extract_window_row(form_df: pl.DataFrame, window_label: str) -> Dict:
    if form_df.is_empty():
        return {}
    subset = form_df.filter(pl.col("window") == window_label)
    return subset.to_dicts()[0] if subset.height else {}


def _append_rail_guard_logs(records: List[Dict]) -> None:
    if not records:
        return
    path = Path("data/internal_checks/rail_guard_log.jsonl")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def build_weather_table(season: int, week: int, guardrails_cfg: Dict, mode: str = "v2") -> pd.DataFrame:
    df = load_picks_for_week(season, week)
    if df.empty:
        return pd.DataFrame()
    # form windows for all teams involved
    all_teams = set(df["home"].tolist()) | set(df["away"].tolist())
    form_df = _form_windows_for_teams(season, week, list(all_teams))
    last3_row = _extract_window_row(form_df, "last 3 games")
    last5_row = _extract_window_row(form_df, "last 5 games")

    def _safe_float(val: object) -> Optional[float]:
        try:
            return float(val)
        except (TypeError, ValueError):
            return None

    rail_guard_logs: List[Dict] = []
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
        # Guardrails: faworyt = pick_team, underdog = drugi
        dog_team = home if pick_team == away else away
        matchup_metrics = {
            "fav": pick_team,
            "dog": dog_team,
            "last3": last3_row,
            "last5": last5_row,
        }
        if mode == "v2_1":
            adj_rating, adj_bucket, notes, level = apply_guardrails_v2_1(
                matchup=matchup_metrics,
                bucket=bucket,
                rating=rating,
                guardrails=guardrails_cfg,
            )
        elif mode == "v2":
            adj_rating, adj_bucket, notes, level = apply_guardrails_v2(
                matchup=matchup_metrics,
                bucket=bucket,
                rating=rating,
                guardrails=guardrails_cfg,
            )
        else:
            adj_rating, adj_bucket, notes = apply_guardrails(
                matchup=matchup_metrics,
                bucket=bucket,
                rating=rating,
                guardrails=guardrails_cfg,
            )
            level = 0 if not notes else 1
        # Re-assign bucket if rating zmienił się dodatkowo (dla v1)
        if mode == "v1" and adj_bucket == bucket:
            adj_bucket = assign_bucket(adj_rating, ultimate=False)

        spread_val = _safe_float(ref.get("handicap") if ref.get("handicap") is not None else ref.get("spread"))
        predicted_margin_val = _safe_float(ref.get("model_margin"))
        guard_bucket, value_buffer, rg_status, rg_action, rg_notes = apply_value_buffer_guard(
            predicted_margin=predicted_margin_val,
            spread=spread_val,
            original_bucket=adj_bucket,
            guardrail_level=level,
        )

        rail_guard_logs.append(
            {
                "season": season,
                "week": week,
                "home_team": home,
                "away_team": away,
                "spread": spread_val,
                "predicted_margin": predicted_margin_val,
                "value_buffer": value_buffer,
                "original_bucket": adj_bucket,
                "guard_bucket": guard_bucket,
                "rail_guard_status": rg_status,
                "rail_guard_action": rg_action,
                "guardrail_level": level,
                "notes": rg_notes,
            }
        )

        adj_bucket = guard_bucket
        rows.append(
            {
                "season": season,
                "week": week,
                "home_team": home,
                "away_team": away,
                "pick_team": pick_team,
                "rating": round(adj_rating, 3),
                "bucket": adj_bucket,
                "stake_u": BUCKET_STAKES.get(adj_bucket, 1.0),
                "guardrails_mode": mode,
                "guardrail_level": level,
                "guardrail_notes": ";".join(notes) if notes else "",
                "handicap": ref.get("handicap"),
                "value_buffer": value_buffer,
                "rail_guard_status": rg_status,
                "rail_guard_action": rg_action,
            }
        )
    _append_rail_guard_logs(rail_guard_logs)
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
    parser.add_argument(
        "--guardrails",
        type=Path,
        default=None,
        help="Path to guardrails YAML (default depends on --guardrails-mode)",
    )
    parser.add_argument(
        "--guardrails-mode",
        choices=["v1", "v2", "v2_1"],
        default="v2",
        help="Select guardrails logic (default: v2).",
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

    # pick guardrails file based on mode (unless explicitly set)
    if args.guardrails is None:
        if args.guardrails_mode in ("v2", "v2_1"):
            guardrails_path = Path("config/guardrails_v2.yaml")
        else:
            guardrails_path = Path("config/guardrails.yaml")
    else:
        guardrails_path = args.guardrails

    guardrails_cfg = load_guardrails(guardrails_path)

    tables = []
    for wk in weeks:
        tbl = build_weather_table(args.season, wk, guardrails_cfg, mode=args.guardrails_mode)
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

    out_path = args.output
    if out_path.name == "weather_bucket_games.csv":
        out_path = out_path.with_name(f"weather_bucket_games_season{args.season}.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(out_path, index=False)
    print(f"Wrote {len(table)} rows to {out_path}")


if __name__ == "__main__":
    main()
