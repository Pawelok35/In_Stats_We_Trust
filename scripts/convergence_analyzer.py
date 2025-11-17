from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

TRACKED_TAGS = {"GOY", "GOM", "GOW"}
TAG_POINTS = {"GOY": 3, "GOM": 2, "GOW": 1}
MODEL_WEIGHTS = {"M": 1.0, "D": 0.7, "B": 0.4}
ULTIMATE_CONF_THRESHOLD = 98.0
ULTIMATE_EDGE_THRESHOLD = 27.0
ULTIMATE_BUCKET = ("Ultimate Supercell", 4.0)
WEATHER_BUCKETS = [
    ("Supercell", 3.5, 6.0, math.inf),
    ("Vortex", 3.0, 5.0, 6.0),
    ("Cyclone", 2.5, 4.0, 5.0),
    ("Gale", 2.0, 3.0, 4.0),
    ("Breeze", 1.5, 2.0, 3.0),
    ("Calm", 1.0, 0.0, 2.0),
]
BASE_BUCKET = ("Base", 0.5)

STAKE_RULES = {
    "ULTRA": 3.0,
    "DUAL": 2.0,
    "DIAMOND": 2.5,
    "BASE": 1.0,
    "IGNORE": 0.0,
}
RESULT_PAYOUT = {"WIN": 0.9, "LOSS": -1.0, "PUSH": 0.0}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze convergence between three ISWT variants."
    )
    parser.add_argument(
        "--variant-m", type=Path, required=True, help="JSONL z pickami modelu bazowego (M)."
    )
    parser.add_argument(
        "--variant-d", type=Path, required=True, help="JSONL z pickami wariantu D."
    )
    parser.add_argument(
        "--variant-b", type=Path, required=True, help="JSONL z pickami wariantu B."
    )
    parser.add_argument(
        "--week-label",
        type=str,
        help="Etykieta tygodnia do raportu (np. 'Week 11'). Gdy puste, wylicz z danych.",
    )
    parser.add_argument(
        "--weather-only",
        action="store_true",
        help="Wypisz wyłącznie tabelę 'Weather Scale Picks' (bez dodatkowych sekcji).",
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
    margin = home_score - away_score if pick_side == record["home"] else away_score - home_score
    ats_margin = margin + handicap
    if ats_margin > 0:
        return "WIN"
    if ats_margin < 0:
        return "LOSS"
    return "PUSH"


def tag_value(tag: Optional[str]) -> int:
    if not tag:
        return 0
    return TAG_POINTS.get(tag.upper(), 0)


def compute_rating(tag_m: Optional[str], tag_d: Optional[str], tag_b: Optional[str]) -> float:
    rating = 0.0
    rating += tag_value(tag_m) * MODEL_WEIGHTS["M"]
    rating += tag_value(tag_d) * MODEL_WEIGHTS["D"]
    rating += tag_value(tag_b) * MODEL_WEIGHTS["B"]
    return rating


def assign_weather(
    tag_m: Optional[str],
    tag_d: Optional[str],
    tag_b: Optional[str],
    rating: float,
    *,
    ultimate: bool = False,
) -> Tuple[str, float]:
    if ultimate:
        return ULTIMATE_BUCKET
    if not tag_d and not tag_b:
        return BASE_BUCKET
    for name, stake, low, high in WEATHER_BUCKETS:
        if low <= rating < high:
            return name, stake
    return WEATHER_BUCKETS[-1][0], WEATHER_BUCKETS[-1][1]


def _extract_conf_and_edge(picks: Iterable[Dict]) -> Tuple[Optional[float], Optional[float]]:
    confidences: list[float] = []
    edges: list[float] = []
    for pick in picks:
        conf = pick.get("confidence")
        try:
            conf_value = float(conf)
            edge_value = abs(float(pick.get("edge_vs_line")))
        except (TypeError, ValueError):
            return None, None
        confidences.append(conf_value)
        edges.append(edge_value)
    if not confidences or not edges:
        return None, None
    return min(confidences), min(edges)


def _is_ultimate_signal(
    tag_m: Optional[str],
    tag_d: Optional[str],
    tag_b: Optional[str],
    conf_min: Optional[float],
    edge_min: Optional[float],
) -> bool:
    if not conf_min or not edge_min:
        return False
    if not all(tag == "GOY" for tag in (tag_m, tag_d, tag_b)):
        return False
    return conf_min >= ULTIMATE_CONF_THRESHOLD and edge_min >= ULTIMATE_EDGE_THRESHOLD


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
    result = evaluate_pick(m)
    m_tag = m.get("tag")
    d_tag = d.get("tag") if d else None
    b_tag = b.get("tag") if b else None
    rating = compute_rating(m_tag, d_tag, b_tag)
    conf_min, edge_min = _extract_conf_and_edge(tuple(p for p in (m, d, b) if p))
    ultimate_signal = _is_ultimate_signal(m_tag, d_tag, b_tag, conf_min, edge_min)
    weather_code, weather_stake = assign_weather(
        m_tag,
        d_tag,
        b_tag,
        rating,
        ultimate=ultimate_signal,
    )
    config_text = " | ".join(
        [
            f"M:{m_tag}->{m['model_winner']}",
            f"D:{d_tag}->{d['model_winner']}" if d else "D:-",
            f"B:{b_tag}->{b['model_winner']}" if b else "B:-",
        ]
    )
    tag_combo = (m_tag or "-", d_tag or "-", b_tag or "-")
    home_spread = None
    pick_spread = None
    try:
        home_spread = float(m.get("spread")) if m.get("spread") not in (None, "") else None
    except (TypeError, ValueError):
        home_spread = None
    pick_team = m.get("model_winner")
    if home_spread is not None and pick_team:
        if pick_team == m.get("home"):
            pick_spread = home_spread
        elif pick_team == m.get("away"):
            pick_spread = -home_spread
        else:
            pick_spread = None
    return {
        "category": category,
        "stake": STAKE_RULES[category],
        "label": match_label,
        "result": result,
        "season": m["season"],
        "week": m["week"],
        "config_text": config_text,
        "tag_combo": tag_combo,
        "tag_m": m_tag,
        "tag_d": d_tag,
        "tag_b": b_tag,
        "rating": rating,
        "weather_code": weather_code,
        "weather_stake": weather_stake,
        "pick_team": m.get("model_winner"),
        "ultimate_signal": ultimate_signal,
        "ultimate_conf_min": conf_min,
        "ultimate_edge_min": edge_min,
        "home_spread": home_spread,
        "pick_spread": pick_spread,
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
        stake = entry["weather_stake"]
        if result not in RESULT_PAYOUT:
            continue
        pnl += RESULT_PAYOUT[result] * stake
        if result is not None and result != "PENDING":
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


def print_weather_table(entries: List[Dict]) -> None:
    print("\n**Weather Scale Picks:**")
    print("| Codename | Rating | Stake | Mecz | Modele / kierunek |")
    print("|:-------- | ------:| -----:|:-----|:------------------ |")
    ultimate_rows = [e for e in entries if e.get("ultimate_signal")]
    if not ultimate_rows:
        print("| Ultimate Supercell | - | - | BRAK | - |")
    else:
        ultimate_rows_sorted = sorted(
            ultimate_rows,
            key=lambda e: (e["ultimate_conf_min"] or 0.0, e["ultimate_edge_min"] or 0.0),
            reverse=True,
        )
        for entry in ultimate_rows_sorted:
            spread_display = (
                f"{entry['pick_spread']:+.1f}"
                if entry.get("pick_spread") is not None
                else "N/A"
            )
            print(
                f"| {entry['weather_code']} | {entry['rating']:.2f} | {entry['weather_stake']:.1f}u "
                f"| {entry['label']} (→ {entry['pick_team']} {spread_display}) | {entry['config_text']} |"
            )

    regular_rows = [e for e in entries if not e.get("ultimate_signal")]
    regular_rows.sort(key=lambda e: (e["weather_stake"], e["rating"]), reverse=True)
    for entry in regular_rows:
        spread_display = (
            f"{entry['pick_spread']:+.1f}"
            if entry.get("pick_spread") is not None
            else "N/A"
        )
        print(
            f"| {entry['weather_code']} | {entry['rating']:.2f} | {entry['weather_stake']:.1f}u "
            f"| {entry['label']} (→ {entry['pick_team']} {spread_display}) | {entry['config_text']} |"
        )


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
    total_stake = sum(entry["weather_stake"] for entry in entries)
    avg_stake = (total_stake / total_picks) if total_picks else 0.0
    pnl, roi = compute_roi(entries)
    commentary, rec_stake, projected_gain = build_commentary(summary)

    if args.week_label:
        week_label = args.week_label
    else:
        weeks = {entry["week"] for entry in entries}
        week_label = f"Week {weeks.pop()}" if len(weeks) == 1 else "Selected Weeks"

    if args.weather_only:
        print_weather_table(entries)
        return

    print(f"\n### 📊 ISWT Model Convergence Report ({week_label})")
    print("| Kategoria | Liczba | Śr. stawka (legacy) | Przykłady |")
    print("|:--------- | -----: | -------------------: |:--------- |")
    for cat in ("ULTRA", "DUAL", "DIAMOND", "BASE", "IGNORE"):
        count = summary[cat]["count"]
        stake_sum = summary[cat]["stake_sum"]
        avg = (stake_sum / count) if count else 0.0
        examples = format_examples(summary[cat]["labels"])
        print(f"| {cat} | {count} | {avg:.1f} | {examples} |")

    print("\n**Statystyki:**")
    print(f"- Łączna liczba picków: {total_picks}")
    print(f"- Suma stawek (weather scale): {total_stake:.1f}u")
    print(f"- Śr. stawka/pick: {avg_stake:.2f}u")
    if total_stake > 0 and any(entry["result"] for entry in entries):
        print(f"- Szac. ROI (na podstawie wyników): {roi:.1f}%")
    else:
        print("- Szac. ROI: brak danych (brak wyników ATS).")

    print("\n**Konfiguracje tagów (M | D | B):**")
    if combos:
        print("| M | D | B | Liczba |")
        print("|:--|:--|:--| -----:|")
        for combo, count in sorted(combos.items(), key=lambda item: item[1], reverse=True):
            m_tag, d_tag, b_tag = combo
            print(f"| {m_tag} | {d_tag} | {b_tag} | {count} |")
    else:
        print("- brak danych -")

    print_weather_table(entries)

    print("\n**Komentarz ekspercki:**")
    print(f"{commentary} Łączny aktualny PnL (jeśli dostępne wyniki): {pnl:.2f}u.")

    premium_count = summary["ULTRA"]["count"] + summary["DUAL"]["count"] + summary["DIAMOND"]["count"]
    print(f"\n### 🧠 REKOMENDACJA ({week_label})")
    print(f"- liczba picków = {premium_count} (M + inne warianty)")
    print(f"- łączny stake ≈ {rec_stake:.1f}u")
    print(f"- prognozowany zysk (82% hit rate, 0.9/-1 system) ≈ {projected_gain:.1f}u")


if __name__ == "__main__":
    main()


