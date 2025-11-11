from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List, Sequence, Tuple

import yaml

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts import matchup_analyzer

REPORT_PATTERN = re.compile(r"(?P<season>\d{4})_w(?P<week>\d+)", re.IGNORECASE)


def load_config(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Nie znaleziono pliku konfiguracyjnego: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not data or "matchups" not in data:
        raise ValueError("Konfiguracja musi zawierać klucz 'matchups'.")
    if not isinstance(data["matchups"], Sequence):
        raise ValueError("'matchups' musi być listą wpisów.")
    return list(data["matchups"])


def build_namespace(entry: Dict[str, Any], output_path: Path | None) -> SimpleNamespace:
    try:
        spread = float(entry["spread"])
        total = float(entry["total"])
    except KeyError as exc:
        raise KeyError(f"Brak wymaganej wartości '{exc.args[0]}' w konfiguracji {entry}") from exc
    return SimpleNamespace(
        spread=spread,
        total=total,
        prime_time=bool(entry.get("prime_time", False)),
        neutral_site=bool(entry.get("neutral_site", False)),
        window=entry.get("window", "season"),
        output=output_path,
    )


def sanitize_filename(home: str, away: str) -> str:
    return f"{home.lower()}_vs_{away.lower()}_analysis.md"


def normalize_team(value: Any) -> str:
    if isinstance(value, bool):
        raise ValueError("Kody drużyn takie jak 'NO' muszą być ujęte w cudzysłowy w YAML.")
    return str(value).upper()


def infer_season_week(report_path: Path) -> Tuple[int, int] | None:
    match = REPORT_PATTERN.search(report_path.as_posix())
    if not match:
        return None
    return int(match.group("season")), int(match.group("week"))


def load_tag_rules(path: Path | None) -> None:
    if not path:
        return
    config = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not config:
        return
    rules = {str(tag).upper(): rule for tag, rule in config.items()}
    matchup_analyzer.set_tag_rules(rules)


def run_batch(
    config_path: Path,
    output_dir: Path | None,
    default_window: str | None,
    strict: bool,
    combined_output: Path | None,
    picks_dir: Path,
    tag_config: Path | None,
) -> None:
    config_path = config_path if config_path.is_absolute() else ROOT_DIR / config_path
    entries = load_config(config_path)

    load_tag_rules(tag_config)

    if output_dir:
        output_dir = output_dir if output_dir.is_absolute() else ROOT_DIR / output_dir
        output_dir.mkdir(parents=True, exist_ok=True)

    if combined_output:
        combined_output = combined_output if combined_output.is_absolute() else ROOT_DIR / combined_output
        combined_output.parent.mkdir(parents=True, exist_ok=True)

    combined_sections: List[Tuple[str, str, str]] = []
    pick_records: Dict[Tuple[int, int], List[Dict[str, Any]]] = defaultdict(list)

    for entry in entries:
        report = Path(entry["report"])
        home = normalize_team(entry["home"])
        away = normalize_team(entry["away"])
        report = report if report.is_absolute() else ROOT_DIR / report
        if not report.exists():
            raise FileNotFoundError(f"Raport nie istnieje: {report}")

        target_path: Path | None = None
        if entry.get("output"):
            target_path = Path(entry["output"])
            if not target_path.is_absolute():
                target_path = ROOT_DIR / target_path
        elif output_dir:
            target_path = output_dir / sanitize_filename(home, away)

        if target_path:
            target_path.parent.mkdir(parents=True, exist_ok=True)

        window = entry.get("window", default_window or "season")
        entry["window"] = window
        ns = build_namespace(entry, target_path)

        try:
            analysis = matchup_analyzer.run(report, home, away, ns)
        except Exception as exc:
            if strict:
                raise RuntimeError(f"Błąd podczas analizowania {home} vs {away} ({report}): {exc}") from exc
            print(f"[WARN] Pomijam {home} vs {away}: {exc}", file=sys.stderr)
            continue

        combined_sections.append((home, away, analysis.text))

        if target_path:
            target_path.write_text(analysis.text, encoding="utf-8")
            print(f"[OK] {home} vs {away} -> {target_path}")
        else:
            print(f"\n===== {home} vs {away} =====")
            print(analysis.text)

        season_week = infer_season_week(report)
        if season_week:
            season, week = season_week
            record = {
                "season": season,
                "week": week,
                "home": home,
                "away": away,
                "tag": analysis.projection.tag,
                "model_winner": analysis.projection.model_winner,
                "market_winner": analysis.projection.market_winner,
                "confidence": round(analysis.projection.confidence, 1),
                "model_margin": round(analysis.projection.adv_model, 2),
                "market_margin": round(analysis.projection.adv_market, 2),
                "edge_vs_line": round(analysis.projection.edge_vs_line, 2),
                "handicap": round(analysis.projection.winner_line, 1),
                "spread": ns.spread,
                "total": ns.total,
                "window": window,
                "prime_time": ns.prime_time,
                "neutral_site": ns.neutral_site,
                "report": str(report.relative_to(ROOT_DIR)) if report.is_relative_to(ROOT_DIR) else str(report),
                "generated_at": datetime.now(tz=timezone.utc).isoformat(timespec="seconds"),
            }
            pick_records[(season, week)].append(record)

    if combined_output:
        if not combined_sections:
            print(f"[WARN] Nie wygenerowano żadnych analiz – pominąłem zapis {combined_output}")
        else:
            lines: List[str] = ["# Weekly Matchup Summary", ""]
            for idx, (home, away, text) in enumerate(combined_sections, 1):
                lines.append(f"## {home} vs {away}")
                lines.append("")
                lines.append(text.strip())
                lines.append("")
                if idx != len(combined_sections):
                    lines.append("---")
                    lines.append("")
            combined_output.write_text("\n".join(lines), encoding="utf-8")
            print(f"[OK] Zapisano zbiorczy raport w {combined_output}")

    if pick_records:
        for (season, week), records in pick_records.items():
            picks_path = picks_dir / str(season) / f"week_{week:02d}.jsonl"
            picks_path.parent.mkdir(parents=True, exist_ok=True)
            with picks_path.open("w", encoding="utf-8") as handle:
                for record in records:
                    handle.write(json.dumps(record, ensure_ascii=False) + "\n")
            print(f"[INFO] Zapisano log picków: {picks_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Batch runner for matchup analyzer.")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config/week10_lines.yaml"),
        help="Plik YAML z definicjami meczów.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Katalog docelowy na pliki wynikowe (opcjonalny).",
    )
    parser.add_argument(
        "--window",
        choices=list(matchup_analyzer.WINDOW_COLUMNS.keys()),
        help="Domyślne okno formy (nadpisywane per wpis).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Zatrzymaj batch przy pierwszym błędzie (domyślnie pomijaj spotkania).",
    )
    parser.add_argument(
        "--combined-output",
        type=Path,
        help="Jeśli ustawione, zapisuje jeden zbiorczy plik Markdown z wszystkimi analizami.",
    )
    parser.add_argument(
        "--picks-dir",
        type=Path,
        default=Path("data/picks"),
        help="Katalog na logi picków (domyślnie data/picks).",
    )
    parser.add_argument(
        "--tag-config",
        type=Path,
        help="Plik YAML z niestandardowymi progami klasyfikacji tagów.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    picks_dir = args.picks_dir if args.picks_dir.is_absolute() else ROOT_DIR / args.picks_dir
    run_batch(
        args.config,
        args.output_dir,
        args.window,
        args.strict,
        args.combined_output,
        picks_dir,
        args.tag_config if args.tag_config else None,
    )


if __name__ == "__main__":
    main()
