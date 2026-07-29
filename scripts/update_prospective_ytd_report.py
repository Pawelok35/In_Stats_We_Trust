from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.settle_prospective_ledger import settle


def find_ledgers(root: Path, season: int) -> list[Path]:
    season_dir = root / str(season)
    if not season_dir.exists():
        return []
    return sorted(season_dir.glob("week_*_prospective.jsonl"))


def update_ytd(
    *,
    season: int,
    ledger_root: Path,
    data_root: Path,
    output_path: Path | None = None,
) -> tuple[Path, list[dict[str, Any]]]:
    ledgers = find_ledgers(ledger_root, season)
    rows: list[dict[str, Any]] = []
    for ledger in ledgers:
        settlement_path = ledger.with_name(ledger.stem + "_settlement.md")
        report_path, summary = settle(ledger, data_root, settlement_path)
        week = _week_from_ledger_name(ledger)
        rows.append(
            {
                "week": week,
                "ledger": ledger,
                "settlement": report_path,
                **summary,
            }
        )

    destination = output_path or ledger_root / str(season) / "prospective_ytd_report.md"
    write_ytd_report(destination, season, rows)
    return destination, rows


def _week_from_ledger_name(path: Path) -> int:
    # week_01_prospective.jsonl
    parts = path.stem.split("_")
    try:
        return int(parts[1])
    except (IndexError, ValueError):
        return 0


def write_ytd_report(path: Path, season: int, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    totals = _totals(rows)
    lines = [
        f"# Prospective Edge YTD Report - {season}",
        "",
        "This report aggregates only prospective ledger files. Historical backtests are excluded.",
        "",
        "## Summary",
        "",
        f"- Weeks tracked: {len(rows)}",
        f"- Records: {totals['records']}",
        f"- Proof-qualified: {totals['proof_qualified']}",
        f"- Not qualified: {totals['not_qualified']}",
        f"- Settled qualified picks: {totals['settled']}",
        f"- Pending qualified picks: {totals['pending']}",
        f"- W-L-P: {totals['wins']}-{totals['losses']}-{totals['pushes']}",
        f"- Win rate: {totals['win_rate']:.1%}",
        f"- Units: {totals['profit_units']:+.2f}u",
        f"- ROI: {totals['roi']:.1%}",
        "",
        "## Weekly Breakdown",
        "",
        "| Week | Records | Qualified | Settled | Pending | W-L-P | Units | ROI | Settlement |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        settlement = str(row["settlement"]).replace("\\", "/")
        lines.append(
            "| {week} | {records} | {proof_qualified} | {settled} | {pending} | "
            "{wins}-{losses}-{pushes} | {profit_units:+.2f}u | {roi:.1%} | `{settlement}` |".format(
                week=row["week"],
                records=row["records"],
                proof_qualified=row["proof_qualified"],
                settled=row["settled"],
                pending=row["pending"],
                wins=row["wins"],
                losses=row["losses"],
                pushes=row["pushes"],
                profit_units=row["profit_units"],
                roi=row["roi"],
                settlement=settlement,
            )
        )
    if not rows:
        lines.append("| - | 0 | 0 | 0 | 0 | 0-0-0 | +0.00u | 0.0% | - |")

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- `Proof-qualified` means the pick had market, line, price, book, decision timestamp, model version and commit SHA at freeze time.",
            "- Pending rows are expected before final scores are available.",
            "- A positive YTD result is not final until all pending picks settle.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _totals(rows: list[dict[str, Any]]) -> dict[str, Any]:
    records = sum(row["records"] for row in rows)
    proof_qualified = sum(row["proof_qualified"] for row in rows)
    not_qualified = sum(row["not_qualified"] for row in rows)
    settled = sum(row["settled"] for row in rows)
    pending = sum(row["pending"] for row in rows)
    wins = sum(row["wins"] for row in rows)
    losses = sum(row["losses"] for row in rows)
    pushes = sum(row["pushes"] for row in rows)
    profit_units = sum(row["profit_units"] for row in rows)
    risk_units = sum(row["risk_units"] for row in rows)
    decisions = wins + losses
    return {
        "records": records,
        "proof_qualified": proof_qualified,
        "not_qualified": not_qualified,
        "settled": settled,
        "pending": pending,
        "wins": wins,
        "losses": losses,
        "pushes": pushes,
        "profit_units": profit_units,
        "risk_units": risk_units,
        "win_rate": wins / decisions if decisions else 0.0,
        "roi": profit_units / risk_units if risk_units else 0.0,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Refresh all prospective settlements and YTD report.")
    parser.add_argument("--season", type=int, required=True)
    parser.add_argument("--ledger-root", type=Path, default=Path("data/prospective_ledger"))
    parser.add_argument("--data-root", type=Path, default=Path("data"))
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report, rows = update_ytd(
        season=args.season,
        ledger_root=args.ledger_root,
        data_root=args.data_root,
        output_path=args.output,
    )
    print(f"report={report}")
    print(f"weeks={len(rows)}")
    print(f"proof_qualified={sum(row['proof_qualified'] for row in rows)}")
    print(f"settled={sum(row['settled'] for row in rows)}")


if __name__ == "__main__":
    main()
