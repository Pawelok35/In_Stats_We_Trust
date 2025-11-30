from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, Tuple

import pandas as pd


def load_variant(season: int, week: int, variant: str) -> Dict[Tuple[str, str], dict]:
    """
    Wczytaj picki jednego wariantu (np. B / F / D).
    Zwraca mapowanie (home, away) -> rekord.
    """
    key = variant.lower()
    path = Path(f"data/picks_variant_{key}/{season}/week_{week:02d}.jsonl")
    records: Dict[Tuple[str, str], dict] = {}
    if not path.exists():
        return records
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        records[(rec["home"], rec["away"])] = rec
    return records


def dir_for(vdict: Dict[Tuple[str, str], dict], home: str, away: str) -> str:
    rec = vdict.get((home, away))
    if not rec:
        return "-"
    tag = str(rec.get("tag", "")).upper()
    side = rec.get("model_winner", "-")
    return f"{tag}->{side}" if tag else f"->{side}"


def pick_spread(
    home: str,
    away: str,
    pick: str,
    row_handicap,
    vb: Dict[Tuple[str, str], dict],
    vf: Dict[Tuple[str, str], dict],
    vd: Dict[Tuple[str, str], dict],
) -> str:
    def from_rec(rec: dict) -> str | None:
        # prefer 'spread' (home perspective); fallback to handicap
        spread_home = rec.get("spread")
        hcap = rec.get("handicap")
        try:
            if spread_home is not None and spread_home != "":
                spread_home = float(spread_home)
                if pick == home:
                    return f"{spread_home:+.1f}"
                if pick == away:
                    return f"{-spread_home:+.1f}"
            if hcap is not None and hcap != "":
                hcap = float(hcap)
                if pick == home:
                    return f"{hcap:+.1f}"
                if pick == away:
                    return f"{-hcap:+.1f}"
        except (TypeError, ValueError):
            return None
        return None

    # prefer B, then F, then D
    rec = vb.get((home, away)) or vf.get((home, away)) or vd.get((home, away))
    if rec:
        val = from_rec(rec)
        if val is not None:
            return val

    # fallback: handicap z wiersza CSV
    try:
        hcap_row = float(row_handicap)
    except (TypeError, ValueError):
        return "N/A"
    if pick == home:
        return f"{hcap_row:+.1f}"
    if pick == away:
        return f"{-hcap_row:+.1f}"
    return "N/A"


def build_table(season: int, week: int, mode: str) -> str:
    bucket_path = Path(f"data/results/weather_bucket_games_season{season}.csv")
    if not bucket_path.exists():
        raise FileNotFoundError(bucket_path)
    df = pd.read_csv(bucket_path)
    df = df[(df["week"] == week) & (df["guardrails_mode"] == mode)]
    if df.empty:
        return f"Brak picków dla season={season}, week={week}, mode={mode}."

    vb = load_variant(season, week, "b_edge_focus")
    vf = load_variant(season, week, "f")
    vd = load_variant(season, week, "d_balanced")

    df = df.sort_values(["stake_u", "rating"], ascending=[False, False])
    lines = [
        f"**Weather Scale Picks ({mode}):**",
        "| Codename | Rating | Stake | Mecz | Modele / kierunek |",
        "|:-------- | ------:| -----:|:-----|:------------------ |",
    ]

    for _, r in df.iterrows():
        home, away = r.home_team, r.away_team
        pick = r.pick_team
        spread_disp = pick_spread(home, away, pick, r.get("handicap"), vb, vf, vd)
        match = f"{home} vs {away} (-> ** {pick} {spread_disp} **)"
        cfg_text = f"`B:{dir_for(vb, home, away)} | F:{dir_for(vf, home, away)} | D:{dir_for(vd, home, away)}`"
        lines.append(
            f"| {r.bucket} | {float(r.rating):.2f} | {float(r.stake_u):.1f}u | {match} | {cfg_text} |"
        )

    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Show Weather Scale Picks from generated bucket CSV.")
    parser.add_argument("--season", type=int, required=True, help="Season, e.g. 2025")
    parser.add_argument("--week", type=int, required=True, help="Week number, e.g. 12")
    parser.add_argument(
        "--guardrails-mode",
        choices=["v1", "v2", "v2_1"],
        default="v2_1",
        help="Guardrails mode to display (default: v2_1)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print(build_table(args.season, args.week, args.guardrails_mode))


if __name__ == "__main__":
    main()
