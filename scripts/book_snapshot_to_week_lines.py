from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert a book screen snapshot YAML to week lines YAML.")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def load_snapshot(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise SystemExit(f"Snapshot must be a YAML mapping: {path}")
    if not isinstance(payload.get("book_snapshot"), dict):
        raise SystemExit("Missing book_snapshot mapping.")
    if not isinstance(payload.get("games"), list):
        raise SystemExit("Missing games list.")
    return payload


def as_float(value: Any, *, field: str, game: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise SystemExit(f"{game}: invalid numeric {field}={value!r}") from exc


def as_int_or_none(value: Any) -> int | None:
    if value in (None, "", "UNKNOWN"):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def american_price_or_none(value: Any) -> int | None:
    if value in (None, "", "UNKNOWN"):
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None

    # Source screenshots may contain either American odds (-110/+105) or
    # decimal odds (1.91/2.05). Store model-facing prices as American odds.
    if numeric <= -100 or numeric >= 100:
        return int(round(numeric))
    if numeric <= 1:
        return None
    if numeric >= 2:
        return int(round((numeric - 1) * 100))
    return int(round(-100 / (numeric - 1)))


def team_code(value: Any) -> str:
    if value is False:
        return "NO"
    return str(value or "").upper()


def _existing_matchup_context(payload: dict[str, Any] | None) -> dict[tuple[str, str], dict[str, Any]]:
    if not payload:
        return {}
    matchups = payload.get("matchups")
    if not isinstance(matchups, list):
        return {}
    context: dict[tuple[str, str], dict[str, Any]] = {}
    for matchup in matchups:
        if not isinstance(matchup, dict):
            continue
        away = team_code(matchup.get("away"))
        home = team_code(matchup.get("home"))
        if away and home:
            context[(away, home)] = matchup
    return context


def _context_bool(game: dict[str, Any], existing: dict[str, Any], key: str) -> bool:
    if key in game:
        return bool(game[key])
    return bool(existing.get(key, False))


def build_lines(
    snapshot: dict[str, Any],
    *,
    existing_lines: dict[str, Any] | None = None,
) -> dict[str, Any]:
    meta = snapshot["book_snapshot"]
    season = int(meta["season"])
    week = int(meta["week"])
    book = meta.get("book") or "UNKNOWN"
    captured_at = meta.get("captured_at_utc") or "UNKNOWN"
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    existing_context = _existing_matchup_context(existing_lines)
    matchups = []
    for index, game in enumerate(snapshot["games"], start=1):
        if not isinstance(game, dict):
            raise SystemExit(f"games[{index}] must be a mapping.")
        away = team_code(game.get("away"))
        home = team_code(game.get("home"))
        label = f"{away} @ {home}"
        if not away or not home:
            raise SystemExit(f"games[{index}] missing away/home.")

        home_spread = as_float(game.get("home_spread"), field="home_spread", game=label)
        total = as_float(game.get("total_over"), field="total_over", game=label)
        home_spread_price = american_price_or_none(game.get("home_spread_price"))
        away_spread_price = american_price_or_none(game.get("away_spread_price"))
        line_quality = game.get("game_line_quality") or "UNKNOWN"
        context = existing_context.get((away, home), {})

        matchups.append(
            {
                "report": f"data/reports/comparisons/{season}_w{week}/{home}_vs_{away}.md",
                "home": home,
                "away": away,
                "spread": home_spread,
                "total": total,
                # Market screenshots usually do not carry schedule context. Preserve
                # the values exported from the canonical NFL schedule unless the
                # snapshot explicitly overrides them.
                "prime_time": _context_bool(game, context, "prime_time"),
                "neutral_site": _context_bool(game, context, "neutral_site"),
                "book": book,
                "price": home_spread_price,
                "decision_ts_utc": captured_at,
                "source": "book_snapshot",
                "source_game_date_local": game.get("game_date_local"),
                "source_game_time_local": game.get("game_time_local"),
                "line_quality": line_quality,
                "notes": game.get("notes"),
                "away_moneyline": american_price_or_none(game.get("away_moneyline")),
                "home_moneyline": american_price_or_none(game.get("home_moneyline")),
                "away_spread": game.get("away_spread"),
                "away_spread_price": away_spread_price,
                "home_spread": game.get("home_spread"),
                "home_spread_price": home_spread_price,
                "total_over": game.get("total_over"),
                "total_over_price": american_price_or_none(game.get("total_over_price")),
                "total_under": game.get("total_under"),
                "total_under_price": american_price_or_none(game.get("total_under_price")),
                "source_away_moneyline": game.get("away_moneyline"),
                "source_home_moneyline": game.get("home_moneyline"),
                "source_away_spread_price": game.get("away_spread_price"),
                "source_home_spread_price": game.get("home_spread_price"),
                "source_total_over_price": game.get("total_over_price"),
                "source_total_under_price": game.get("total_under_price"),
            }
        )

    return {
        "season": season,
        "week": week,
        "source": "book_snapshot",
        "book": book,
        "captured_at_utc": captured_at,
        "generated_at_utc": generated_at,
        "matchups": matchups,
    }


def main() -> None:
    args = parse_args()
    snapshot = load_snapshot(args.input)
    existing_lines = None
    if args.output.exists():
        loaded = yaml.safe_load(args.output.read_text(encoding="utf-8")) or {}
        if isinstance(loaded, dict):
            existing_lines = loaded
    payload = build_lines(snapshot, existing_lines=existing_lines)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=False), encoding="utf-8")
    print(f"[OK] Saved lines: {args.output} ({len(payload['matchups'])} games)")


if __name__ == "__main__":
    main()
