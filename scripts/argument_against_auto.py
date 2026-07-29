from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


KEY_NUMBERS = (3.0, 7.0, 10.0, 14.0)


def round_to_half(value: float | None) -> float | None:
    if value is None:
        return None
    return round(value * 2) / 2


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in {path}:{line_no}: {exc}") from exc
        if not isinstance(record, dict):
            raise ValueError(f"Expected object in {path}:{line_no}")
        records.append(record)
    return records


def safe_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def key_number_note(handicap: float | None) -> tuple[str | None, str | None]:
    if handicap is None:
        return None, None
    abs_line = abs(handicap)
    if abs_line in KEY_NUMBERS:
        if handicap < 0:
            return (
                "key_number_laying_exact",
                f"Pick is laying exactly {abs_line:g}; do not chase to -{abs_line + 0.5:g}.",
            )
        return (
            "key_number_taking_exact",
            f"Pick is taking exactly +{abs_line:g}; avoid losing the hook below +{abs_line:g}.",
        )
    if abs_line in (2.5, 6.5, 9.5, 13.5):
        next_key = abs_line + 0.5
        if handicap < 0:
            return (
                "near_key_number_favorite",
                f"Favorite is just below key number {next_key:g}; price is worse if it moves to -{next_key:g}.",
            )
        return (
            "near_key_number_underdog",
            f"Underdog is just below key number +{next_key:g}; better value may require waiting for +{next_key:g}.",
        )
    if abs_line in (3.5, 7.5, 10.5, 14.5):
        prev_key = abs_line - 0.5
        if handicap < 0:
            return (
                "worse_side_of_key_favorite",
                f"Pick is laying -{abs_line:g}, already worse than key number {prev_key:g}.",
            )
        return (
                "above_key_number_underdog",
                f"Pick is taking +{abs_line:g}, which has useful protection above key number {prev_key:g}.",
        )
    return None, None


def add_flag(
    flags: list[dict[str, str]],
    *,
    rule_id: str,
    risk: str,
    reason: str,
    evidence: str = "heuristic",
) -> None:
    flags.append(
        {
            "rule_id": rule_id,
            "risk": risk,
            "reason": reason,
            "evidence_strength": evidence,
        }
    )


def build_argument_against(record: dict[str, Any]) -> dict[str, Any]:
    flags: list[dict[str, str]] = []

    week = int(record.get("week", 0) or 0)
    tag = str(record.get("tag", "")).upper()
    edge = safe_float(record.get("edge_vs_line"))
    handicap = safe_float(record.get("handicap"))
    price = safe_float(record.get("price"))
    book = str(record.get("book", ""))
    neutral_site = bool(record.get("neutral_site", False))

    if week and week <= 3:
        add_flag(
            flags,
            rule_id="early_season_uncertainty",
            risk="MEDIUM",
            reason="Week 1-3 carries elevated uncertainty because current-season sample is thin.",
            evidence="heuristic",
        )

    if edge is None:
        add_flag(
            flags,
            rule_id="missing_edge_vs_line",
            risk="HIGH",
            reason="No edge_vs_line is available, so price discipline cannot be audited.",
            evidence="process",
        )
    elif abs(edge) < 1.0:
        add_flag(
            flags,
            rule_id="thin_model_edge",
            risk="HIGH",
            reason=f"Model edge is only {edge:.2f} points; small price or input error can erase value.",
            evidence="process",
        )
    elif abs(edge) < 2.0:
        add_flag(
            flags,
            rule_id="moderate_model_edge",
            risk="MEDIUM",
            reason=f"Model edge is {edge:.2f} points; playable only if market price is not stale or worse.",
            evidence="process",
        )

    key_rule, key_reason = key_number_note(handicap)
    if key_rule and key_reason:
        risk = "HIGH" if key_rule == "worse_side_of_key_favorite" else "MEDIUM"
        add_flag(
            flags,
            rule_id=key_rule,
            risk=risk,
            reason=key_reason,
            evidence="market_structure",
        )

    if neutral_site:
        add_flag(
            flags,
            rule_id="neutral_site_context",
            risk="MEDIUM",
            reason="Neutral-site game can weaken normal home-field and travel assumptions.",
            evidence="process",
        )

    if book.upper().startswith("MANUAL"):
        add_flag(
            flags,
            rule_id="manual_market_source",
            risk="MEDIUM",
            reason="Line comes from manual consensus; verify a real book before treating the edge as market-grade.",
            evidence="process",
        )

    if price is None:
        add_flag(
            flags,
            rule_id="missing_price",
            risk="HIGH",
            reason="No price is available; EV cannot be validated.",
            evidence="process",
        )

    if tag == "NEUTRAL":
        add_flag(
            flags,
            rule_id="neutral_model_tag",
            risk="HIGH",
            reason="Model tag is NEUTRAL, so this should not be treated as an action pick.",
            evidence="model",
        )

    risk_rank = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}
    overall = "LOW"
    if flags:
        overall = max((flag["risk"] for flag in flags), key=lambda item: risk_rank[item])

    primary_reason = flags[0]["reason"] if flags else "No automatic argument against was detected."
    high_flags = [flag for flag in flags if flag["risk"] == "HIGH"]
    if high_flags:
        primary_reason = high_flags[0]["reason"]

    return {
        "risk_level": overall,
        "primary_reason": primary_reason,
        "flags": flags,
        "manual_checks_needed": [
            "opener/current line movement",
            "injury role impact",
            "weather/wind",
            "public/tickets-handle if available",
        ],
    }


def find_record(records: list[dict[str, Any]], home: str, away: str) -> dict[str, Any]:
    home = home.upper()
    away = away.upper()
    for record in records:
        if str(record.get("home", "")).upper() == home and str(record.get("away", "")).upper() == away:
            return record
    raise ValueError(f"No pick found for {away} at {home}")


def render_markdown(record: dict[str, Any], argument: dict[str, Any]) -> str:
    title = f"{record.get('away')} at {record.get('home')} - argument_against_auto"
    model_margin = safe_float(record.get("model_margin"))
    edge_vs_line = safe_float(record.get("edge_vs_line"))
    handicap = safe_float(record.get("handicap"))
    lines = [
        f"# {title}",
        "",
        "## Pick Snapshot",
        "",
        f"- Tag: {record.get('tag')}",
        f"- Model winner: {record.get('model_winner')}",
        f"- Handicap: {round_to_half(handicap)}",
        f"- Model margin raw: {record.get('model_margin')}",
        f"- Model margin rounded: {round_to_half(model_margin)}",
        f"- Edge vs line raw: {record.get('edge_vs_line')}",
        f"- Edge vs line rounded: {round_to_half(edge_vs_line)}",
        f"- Book/source: {record.get('book')} / {record.get('odds_source')}",
        "",
        "## Auto Argument Against",
        "",
        f"- Risk level: {argument['risk_level']}",
        f"- Primary reason: {argument['primary_reason']}",
        "",
        "## Flags",
        "",
    ]
    for flag in argument["flags"]:
        lines.append(
            f"- {flag['risk']} | {flag['rule_id']} | {flag['reason']} "
            f"({flag['evidence_strength']})"
        )
    if not argument["flags"]:
        lines.append("- No automatic flags.")
    lines.extend(["", "## Manual Checks Needed", ""])
    for check in argument["manual_checks_needed"]:
        lines.append(f"- {check}")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--picks-file", type=Path, required=True)
    parser.add_argument("--home", required=True)
    parser.add_argument("--away", required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    records = load_jsonl(args.picks_file)
    record = find_record(records, args.home, args.away)
    argument = build_argument_against(record)
    markdown = render_markdown(record, argument)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(markdown, encoding="utf-8")
    print(markdown)


if __name__ == "__main__":
    main()
