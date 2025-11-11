from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

TRACKED_TAGS = {"GOY", "GOM", "GOW"}
STAKE_RULES = {
    "ULTRA": 3.0,
    "DUAL": 2.0,
    "DIAMOND": 2.5,
    "BASE": 1.0,
    "IGNORE": 0.0,
}
RESULT_PAYOUT = {"WIN": 0.9, "LOSS": -1.0, "PUSH": 0.0}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze convergence between three ISWT variants.")
    parser.add_argument("--variant-m", type=Path, required=True, help="JSONL z pickami modelu bazowego (M).")
    parser.add_argument("--variant-d", type=Path, required=True, help="JSONL z pickami wariantu D.")
    parser.add_argument("--variant-b", type=Path, required=True, help="JSONL z pickami wariantu B.")
    parser.add_argument(
        "--week-label",
        type=str,
        help="Etykieta tygodnia do raportu (np. 'Week 11'). Gdy puste, wylicz z danych.",
    )
    return parser.parse_args()


def load_records(path: Path, *, filter_tracked: bool = False) -> List[Dict]:
    if not path.exists():
        raise FileNotFoundError(path)
    records: List[Dict] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            if filter_tracked:
                tag = str(data.get("tag", "")).upper()
                if tag not in TRACKED_TAGS:
                    continue
            records.append(data)
    return records


def normalize_key(record: Dict) -> Tuple[int, int, Tuple[str, str]]:
    season = int(record["season"])
    week = int(record["week"])
    teams = tuple(sorted((record["home"], record["away"])))
    return season, week, teams


def index_records(records: Iterable[Dict]) -> Dict[Tuple[int, int, Tuple[str, str]], Dict]:
    return {normalize_key(rec): rec for rec in records}


def determine_category(has_m: bool, has_d: bool, has_b: bool) -> str:
    if not has_m:
        return "IGNORE"
    if has_d and has_b:
        return "ULTRA"
    if has_d:
        return "DUAL"
    if has_b:
        return "DIAMOND"
    return "BASE"


def evaluate_pick(record: Dict) -> Optional[str]:
    if "home_score" not in record or "away_score" not in record:
        return None
    if record["home_score"] is None or record["away_score"] is None:
        return None
    if record.get("handicap") is None:
        return None
    home_score = float(record["home_score"])
    away_score = float(record["away_score"])
    pick_side = record["model_winner"]
    handicap = float(record["handicap"])
    if pick_side == record["home"]:
        margin = home_score - away_score
    else:
        margin = away_score - home_score
    ats_margin = margin + handicap
    if ats_margin > 0:
        return "WIN"
    if ats_margin < 0:
        return "LOSS"
    return "PUSH"


def build_entry(
    key: Tuple[int, int, Tuple[str, str]],
    picks_m: Dict,
    picks_d: Dict,
    picks_b: Dict,
) -> Optional[Dict]:
    m = picks_m.get(key)
    if m is None:
        return None
    d = picks_d.get(key)
    b = picks_b.get(key)
    category = determine_category(True, d is not None, b is not None)
    match_label = f"{m['home']} vs {m['away']}"
    stake = STAKE_RULES[category]
    result = evaluate_pick(m)
    config_text = " | ".join(
        [
            f"M:{m['tag']}→{m['model_winner']}",
            f"D:{d['tag']}→{d['model_winner']}" if d else "D:-",
            f"B:{b['tag']}→{b['model_winner']}" if b else "B:-",
        ]
    )
    tag_combo = (m["tag"], d["tag"] if d else "-", b["tag"] if b else "-")
    return {
        "category": category,
        "stake": stake,
        "label": match_label,
        "result": result,
        "season": m["season"],
        "week": m["week"],
        "config_text": config_text,
        "tag_combo": tag_combo,
    }


def aggregate(entries: List[Dict]) -> Tuple[Dict[str, Dict], Dict[Tuple[str, str, str], int]]:
    summary: Dict[str, Dict] = {}
    for cat in STAKE_RULES:
        summary[cat] = {"count": 0, "stake_sum": 0.0, "labels": [], "results": []}
    combos: Dict[Tuple[str, str, str], int] = defaultdict(int)

    for entry in entries:
        cat = entry["category"]
        summary[cat]["count"] += 1
        summary[cat]["stake_sum"] += entry["stake"]
        summary[cat]["labels"].append(f"{entry['label']} ({entry['config_text']})")
        summary[cat]["results"].append(entry["result"])
        combos[entry["tag_combo"]] += 1
    return summary, combos


def compute_roi(entries: List[Dict]) -> Tuple[float, float]:
    pnl = 0.0
    staked = 0.0
    for entry in entries:
        result = entry["result"]
        stake = entry["stake"]
        if result not in RESULT_PAYOUT:
            continue
        pnl += RESULT_PAYOUT[result] * stake
        if result is not None:
            staked += stake
    roi = (pnl / staked * 100) if staked > 0 else 0.0
    return pnl, roi


def format_examples(labels: List[str], limit: int = 3) -> str:
    if not labels:
        return "-"
    return ", ".join(labels[:limit])


def build_commentary(summary: Dict[str, Dict]) -> Tuple[str, float, float]:
    total = sum(summary[cat]["count"] for cat in summary)
    high_convergence = summary["ULTRA"]["count"] + summary["DUAL"]["count"] + summary["DIAMOND"]["count"]
    ratio = (high_convergence / total) if total else 0.0
    if ratio >= 0.6:
        stance = "Tydzień wygląda agresywnie – modele często się pokrywają."
    elif ratio >= 0.35:
        stance = "Zbieżność umiarkowana; warto selekcjonować najlepsze nakładki."
    else:
        stance = "Modele są rozbieżne – graj ostrożnie i stawiaj tylko na najwyższe sygnały."

    dominant_cat = max(summary.items(), key=lambda item: item[1]["count"])[0]
    dominant_msg = f"Najwięcej sygnałów daje kategoria {dominant_cat}."
    rec_stake = summary["ULTRA"]["stake_sum"] + summary["DUAL"]["stake_sum"] + summary["DIAMOND"]["stake_sum"]
    projected_gain = rec_stake * ((0.82 * 0.9) - 0.18)
    return f"{dominant_msg} {stance}", rec_stake, projected_gain


def main() -> None:
    args = parse_args()
    picks_m = index_records(load_records(args.variant_m, filter_tracked=True))
    picks_d = index_records(load_records(args.variant_d, filter_tracked=True))
    picks_b = index_records(load_records(args.variant_b, filter_tracked=True))

    entries: List[Dict] = []
    for key in sorted(picks_m.keys()):
        entry = build_entry(key, picks_m, picks_d, picks_b)
        if entry:
            entries.append(entry)
    summary, combos = aggregate(entries)
    total_picks = sum(s["count"] for s in summary.values())
    total_stake = sum(s["stake_sum"] for s in summary.values())
    avg_stake = (total_stake / total_picks) if total_picks else 0.0
    pnl, roi = compute_roi(entries)
    commentary, rec_stake, projected_gain = build_commentary(summary)

    if args.week_label:
        week_label = args.week_label
    else:
        weeks = {entry["week"] for entry in entries}
        week_label = f"Week {weeks.pop()}" if len(weeks) == 1 else "Selected Weeks"

    print(f"\n### 📊 ISWT Model Convergence Report ({week_label})")
    print("| Kategoria | Liczba | Śr. Stawka | Przykłady |")
    print("|:--------- | -----: | ---------: |:--------- |")
    for cat in ("ULTRA", "DUAL", "DIAMOND", "BASE", "IGNORE"):
        count = summary[cat]["count"]
        stake_sum = summary[cat]["stake_sum"]
        avg = (stake_sum / count) if count else 0.0
        examples = format_examples(summary[cat]["labels"])
        print(f"| {cat} | {count} | {avg:.1f} | {examples} |")

    print("\n**Statystyki:**")
    print(f"- Laczna liczba pickow: {total_picks}")
    print(f"- Suma stawek: {total_stake:.1f}u")
    print(f"- Sr. stawka/pick: {avg_stake:.2f}u")
    if total_stake > 0 and any(entry['result'] for entry in entries):
        print(f"- Szac. ROI (na podstawie wynikow): {roi:.1f}%")
    else:
        print("- Szac. ROI: brak danych (brak wynikow ATS).")

    print("\n**Konfiguracje tagow (M | D | B):**")
    if combos:
        print("| M | D | B | Liczba |")
        print("|:--|:--|:--| -----:|")
        for combo, count in sorted(combos.items(), key=lambda item: item[1], reverse=True):
            m_tag, d_tag, b_tag = combo
            print(f"| {m_tag} | {d_tag} | {b_tag} | {count} |")
    else:
        print("- brak danych -")

    print("\n**Komentarz ekspercki:**")
    print(f"{commentary} Łączny aktualny PnL (jeśli dostępne wyniki): {pnl:.2f}u.")

    premium_count = summary["ULTRA"]["count"] + summary["DUAL"]["count"] + summary["DIAMOND"]["count"]
    print(f"\n### 🧠 REKOMENDACJA ({week_label})")
    print(f"- liczba picków = {premium_count} (m + inne warianty)")
    print(f"- łączny stake ≈ {rec_stake:.1f}u")
    print(f"- prognozowany zysk (82% hit rate, 0.9/-1 system) ≈ {projected_gain:.1f}u")


if __name__ == "__main__":
    main()
