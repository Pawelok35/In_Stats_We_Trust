from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Callable

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from metrics.backtest import backtest_picks, load_picks, load_results

WIN_RETURN_PER_UNIT = 100 / 110
ACTION_TAGS = {"GOY", "GOM", "GOW", "VALUE PLAY"}

FLAT_1U = {
    "VALUE PLAY": 1.0,
    "GOW": 1.0,
    "GOM": 1.0,
    "GOY": 1.0,
}

FLAT_ALL_TAGS_1U = {
    "VALUE PLAY": 1.0,
    "GOW": 1.0,
    "GOM": 1.0,
    "GOY": 1.0,
    "NEUTRAL": 1.0,
}

CONSERVATIVE_TIER = {
    "VALUE PLAY": 0.5,
    "GOW": 1.0,
    "GOM": 1.5,
    "GOY": 2.0,
}

AGGRESSIVE_TIER = {
    "VALUE PLAY": 1.0,
    "GOW": 2.0,
    "GOM": 3.0,
    "GOY": 4.0,
}


def _profit(row: dict[str, Any], stake: float) -> float:
    outcome = row["outcome"]
    if outcome == "win":
        return stake * WIN_RETURN_PER_UNIT
    if outcome == "loss":
        return -stake
    return 0.0


def _summarize(rows: list[dict[str, Any]], stake_by_tag: dict[str, float]) -> dict[str, Any]:
    wins = losses = pushes = pending = 0
    risk = profit = 0.0
    max_drawdown = 0.0
    equity = 0.0
    peak = 0.0

    ordered = sorted(rows, key=lambda row: (int(row["season"]), int(row["week"])))
    for row in ordered:
        tag = str(row.get("tag", "")).upper()
        stake = float(stake_by_tag.get(tag, 0.0))
        outcome = row["outcome"]
        if outcome == "win":
            wins += 1
            risk += stake
        elif outcome == "loss":
            losses += 1
            risk += stake
        elif outcome == "push":
            pushes += 1
            risk += stake
        else:
            pending += 1
            continue

        delta = _profit(row, stake)
        profit += delta
        equity += delta
        peak = max(peak, equity)
        max_drawdown = min(max_drawdown, equity - peak)

    decisions = wins + losses
    return {
        "bets": wins + losses + pushes,
        "wins": wins,
        "losses": losses,
        "pushes": pushes,
        "pending": pending,
        "risk": risk,
        "profit": profit,
        "win_rate": wins / decisions if decisions else 0.0,
        "roi": profit / risk if risk else 0.0,
        "max_drawdown": max_drawdown,
    }


def _group(
    rows: list[dict[str, Any]], key_fn: Callable[[dict[str, Any]], str]
) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[key_fn(row)].append(row)
    return dict(grouped)


def _format_summary_row(label: str, item: dict[str, Any]) -> str:
    return (
        f"| {label} | {item['bets']} | {item['wins']}-{item['losses']}-{item['pushes']} | "
        f"{item['win_rate']:.1%} | {item['risk']:.2f}u | {item['profit']:+.2f}u | "
        f"{item['roi']:.1%} | {item['max_drawdown']:+.2f}u |"
    )


def _write_staking_table(lines: list[str], title: str, rows: list[dict[str, Any]]) -> None:
    staking_plans = {
        "flat_1u": FLAT_1U,
        "conservative_0.5_1_1.5_2": CONSERVATIVE_TIER,
        "aggressive_1_2_3_4": AGGRESSIVE_TIER,
    }
    lines.extend(
        [
            f"## {title}",
            "",
            "| Staking | Bets | W-L-P | Win% | Risk | Units | ROI | Max DD |",
            "|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for label, plan in staking_plans.items():
        lines.append(_format_summary_row(label, _summarize(rows, plan)))
    lines.append("")


def _write_group_table(
    lines: list[str],
    title: str,
    grouped_rows: dict[str, list[dict[str, Any]]],
    stake_by_tag: dict[str, float],
) -> None:
    lines.extend(
        [
            f"## {title}",
            "",
            "| Bucket | Bets | W-L-P | Win% | Risk | Units | ROI | Max DD |",
            "|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for label in sorted(grouped_rows):
        lines.append(_format_summary_row(label, _summarize(grouped_rows[label], stake_by_tag)))
    lines.append("")


def run_backtest(
    *,
    picks_dir: Path,
    data_root: Path,
    output: Path,
    seasons: list[int],
    from_week: int,
    to_week: int,
    manual_results: Path | None,
) -> Path:
    rows: list[dict[str, Any]] = []
    for season in seasons:
        picks = load_picks(picks_dir, season, from_week, to_week)
        results = load_results(data_root, season, manual_results)
        rows.extend(backtest_picks(picks, results))

    action_rows = [row for row in rows if str(row.get("tag", "")).upper() in ACTION_TAGS]

    lines = [
        "# Tiered Staking Backtest",
        "",
        "This is a historical backtest screen, not prospective edge proof.",
        "",
        "Scope:",
        f"- Seasons: {', '.join(str(season) for season in seasons)}",
        f"- Weeks: {from_week}-{to_week}",
        f"- Picks dir: `{picks_dir}`",
        "- Market: ATS/spread grading using stored `handicap` from pick perspective",
        "- Price model: -110",
        "",
        "Staking plans:",
        "- `flat_1u`: all action tags 1u risk",
        "- `conservative_0.5_1_1.5_2`: VALUE PLAY 0.5u, GOW 1u, GOM 1.5u, GOY 2u",
        "- `aggressive_1_2_3_4`: VALUE PLAY 1u, GOW 2u, GOM 3u, GOY 4u",
        "",
        "Important limitation:",
        "- These historical pick files are research/backfilled artifacts, not frozen before kickoff.",
        "- Use this to select candidate staking rules only. Forward proof still requires prospective ledger.",
        "",
    ]
    _write_staking_table(lines, "Action Tags Only", action_rows)
    _write_group_table(
        lines,
        "By Tag - Action Staking, NEUTRAL 0u",
        _group(rows, lambda row: row["tag"]),
        FLAT_1U,
    )
    _write_group_table(
        lines,
        "By Tag - If Every Tag Was Staked 1u",
        _group(rows, lambda row: row["tag"]),
        FLAT_ALL_TAGS_1U,
    )
    _write_group_table(
        lines,
        "By Season - Action Tags Flat 1u",
        _group(action_rows, lambda row: str(row["season"])),
        FLAT_1U,
    )
    _write_group_table(
        lines,
        "By Season - Action Tags Aggressive 1/2/3/4",
        _group(action_rows, lambda row: str(row["season"])),
        AGGRESSIVE_TIER,
    )
    lines.extend(
        [
            "## Practical Read",
            "",
            "- Compare staking plans by max drawdown, not only total units.",
            "- Aggressive staking can look better when GOY/GOM are hot, but it concentrates risk in the highest tier.",
            "- NEUTRAL is treated as 0u stake in tier plans and should remain a no-bet category.",
            "- A staking plan should not be promoted to 2026 real tracking until it survives train/holdout review.",
        ]
    )

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Backtest flat vs tiered staking on pick JSONL files."
    )
    parser.add_argument("--picks-dir", type=Path, default=Path("data/picks_variant_m"))
    parser.add_argument("--data-root", type=Path, default=Path("data"))
    parser.add_argument("--season", type=int, action="append", dest="seasons")
    parser.add_argument("--from-week", type=int, default=2)
    parser.add_argument("--to-week", type=int, default=18)
    parser.add_argument(
        "--manual-results", type=Path, default=Path("data/results/manual_results.jsonl")
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("research/tiered_staking_backtest_variant_m_2021_2025_w02_w18.md"),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    seasons = args.seasons or [2021, 2022, 2023, 2024, 2025]
    output = run_backtest(
        picks_dir=args.picks_dir,
        data_root=args.data_root,
        output=args.output,
        seasons=seasons,
        from_week=args.from_week,
        to_week=args.to_week,
        manual_results=args.manual_results,
    )
    print(f"report={output}")


if __name__ == "__main__":
    main()
