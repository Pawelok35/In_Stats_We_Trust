from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from metrics.backtest import backtest_picks, load_picks, load_results

WIN_RETURN_PER_UNIT = 100 / 110
ACTION_TAGS = {"GOY", "GOM", "GOW", "VALUE PLAY"}

PHASES = {
    "early_w2_w5": (2, 5),
    "middle_w6_w11": (6, 11),
    "late_w12_w17": (12, 17),
}

STAKING_PLANS = {
    "tracking": {
        "early_w2_w5": {"VALUE PLAY": 0.0, "GOW": 0.0, "GOM": 0.0, "GOY": 0.0},
        "middle_w6_w11": {"VALUE PLAY": 0.5, "GOW": 0.5, "GOM": 0.5, "GOY": 0.5},
        "late_w12_w17": {"VALUE PLAY": 0.5, "GOW": 1.0, "GOM": 1.0, "GOY": 1.0},
    },
    "flat_by_phase": {
        "early_w2_w5": {"VALUE PLAY": 0.5, "GOW": 0.5, "GOM": 0.5, "GOY": 0.5},
        "middle_w6_w11": {"VALUE PLAY": 1.0, "GOW": 1.0, "GOM": 1.0, "GOY": 1.0},
        "late_w12_w17": {"VALUE PLAY": 1.0, "GOW": 1.0, "GOM": 1.0, "GOY": 1.0},
    },
    "conservative_phase": {
        "early_w2_w5": {"VALUE PLAY": 0.0, "GOW": 0.5, "GOM": 0.5, "GOY": 0.5},
        "middle_w6_w11": {"VALUE PLAY": 0.5, "GOW": 0.75, "GOM": 1.0, "GOY": 1.0},
        "late_w12_w17": {"VALUE PLAY": 0.5, "GOW": 1.0, "GOM": 1.5, "GOY": 2.0},
    },
    "balanced_phase": {
        "early_w2_w5": {"VALUE PLAY": 0.25, "GOW": 0.5, "GOM": 0.75, "GOY": 1.0},
        "middle_w6_w11": {"VALUE PLAY": 0.5, "GOW": 1.0, "GOM": 1.25, "GOY": 1.5},
        "late_w12_w17": {"VALUE PLAY": 0.75, "GOW": 1.0, "GOM": 1.5, "GOY": 2.0},
    },
    "late_aggressive": {
        "early_w2_w5": {"VALUE PLAY": 0.0, "GOW": 0.0, "GOM": 0.0, "GOY": 0.0},
        "middle_w6_w11": {"VALUE PLAY": 0.5, "GOW": 1.0, "GOM": 1.0, "GOY": 1.0},
        "late_w12_w17": {"VALUE PLAY": 1.0, "GOW": 2.0, "GOM": 3.0, "GOY": 4.0},
    },
    "selected_phase_tier": {
        "early_w2_w5": {"VALUE PLAY": 0.25, "GOW": 0.5, "GOM": 0.75, "GOY": 1.0},
        "middle_w6_w11": {"VALUE PLAY": 0.5, "GOW": 1.0, "GOM": 1.25, "GOY": 1.5},
        "late_w12_w17": {"VALUE PLAY": 1.0, "GOW": 2.0, "GOM": 3.0, "GOY": 4.0},
    },
}


def _phase_for_week(week: int) -> str | None:
    for phase, (start, end) in PHASES.items():
        if start <= week <= end:
            return phase
    return None


def _stake(row: dict[str, Any], plan: dict[str, dict[str, float]]) -> float:
    phase = _phase_for_week(int(row["week"]))
    if phase is None:
        return 0.0
    tag = str(row.get("tag", "")).upper()
    return float(plan.get(phase, {}).get(tag, 0.0))


def _profit(outcome: str, stake: float) -> float:
    if outcome == "win":
        return stake * WIN_RETURN_PER_UNIT
    if outcome == "loss":
        return -stake
    return 0.0


def _summarize(rows: list[dict[str, Any]], plan: dict[str, dict[str, float]]) -> dict[str, Any]:
    wins = losses = pushes = staked_bets = 0
    risk = profit = equity = peak = 0.0
    max_drawdown = 0.0
    max_loss_streak = 0
    current_loss_streak = 0

    ordered = sorted(rows, key=lambda row: (int(row["season"]), int(row["week"])))
    for row in ordered:
        stake = _stake(row, plan)
        if stake <= 0:
            continue

        outcome = row["outcome"]
        if outcome == "win":
            wins += 1
            staked_bets += 1
            risk += stake
            current_loss_streak = 0
        elif outcome == "loss":
            losses += 1
            staked_bets += 1
            risk += stake
            current_loss_streak += 1
            max_loss_streak = max(max_loss_streak, current_loss_streak)
        elif outcome == "push":
            pushes += 1
            staked_bets += 1
            risk += stake
            current_loss_streak = 0
        else:
            continue

        delta = _profit(outcome, stake)
        profit += delta
        equity += delta
        peak = max(peak, equity)
        max_drawdown = min(max_drawdown, equity - peak)

    decisions = wins + losses
    return {
        "bets": staked_bets,
        "wins": wins,
        "losses": losses,
        "pushes": pushes,
        "win_rate": wins / decisions if decisions else 0.0,
        "risk": risk,
        "profit": profit,
        "roi": profit / risk if risk else 0.0,
        "max_drawdown": max_drawdown,
        "max_loss_streak": max_loss_streak,
    }


def _row(label: str, summary: dict[str, Any]) -> str:
    return (
        f"| {label} | {summary['bets']} | {summary['wins']}-{summary['losses']}-"
        f"{summary['pushes']} | {summary['win_rate']:.1%} | {summary['risk']:.2f}u | "
        f"{summary['profit']:+.2f}u | {summary['roi']:.1%} | "
        f"{summary['max_drawdown']:+.2f}u | {summary['max_loss_streak']} |"
    )


def _phase_rows(rows: list[dict[str, Any]], phase: str) -> list[dict[str, Any]]:
    start, end = PHASES[phase]
    return [row for row in rows if start <= int(row["week"]) <= end]


def run(
    *,
    seasons: list[int],
    picks_dir: Path,
    data_root: Path,
    manual_results: Path | None,
    output: Path,
) -> Path:
    rows: list[dict[str, Any]] = []
    for season in seasons:
        picks = load_picks(picks_dir, season, 2, 17)
        results = load_results(data_root, season, manual_results)
        graded = backtest_picks(picks, results)
        rows.extend(row for row in graded if str(row.get("tag", "")).upper() in ACTION_TAGS)

    lines = [
        "# Season Phase Staking Backtest",
        "",
        "This is a historical backtest screen, not prospective edge proof.",
        "",
        f"Seasons: {', '.join(str(season) for season in seasons)}",
        "Phases:",
        "- early_w2_w5",
        "- middle_w6_w11",
        "- late_w12_w17",
        "",
        "## Staking Plans",
        "",
        "| Plan | Early W2-5 | Middle W6-11 | Late W12-17 |",
        "|---|---|---|---|",
    ]
    for name, plan in STAKING_PLANS.items():
        early = _format_plan(plan["early_w2_w5"])
        middle = _format_plan(plan["middle_w6_w11"])
        late = _format_plan(plan["late_w12_w17"])
        lines.append(f"| {name} | {early} | {middle} | {late} |")

    lines.extend(
        [
            "",
            "## Overall By Plan",
            "",
            "| Plan | Bets | W-L-P | Win% | Risk | Units | ROI | Max DD | Max Loss Streak |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for name, plan in STAKING_PLANS.items():
        lines.append(_row(name, _summarize(rows, plan)))

    for phase in PHASES:
        phase_only = _phase_rows(rows, phase)
        lines.extend(
            [
                "",
                f"## {phase}",
                "",
                "| Plan | Bets | W-L-P | Win% | Risk | Units | ROI | Max DD | Max Loss Streak |",
                "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
            ]
        )
        for name, plan in STAKING_PLANS.items():
            lines.append(_row(name, _summarize(phase_only, plan)))

    lines.extend(
        [
            "",
            "## Practical Recommendation",
            "",
            "- Use phase-aware staking only as forward tracking until prospective ledger confirms it.",
            "- The main risk control is not only unit size, but also max weekly exposure and skipping NEUTRAL.",
            "- Late-season aggressive looks attractive historically, but it still creates larger drawdowns when a bad cluster appears.",
        ]
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output


def _format_plan(plan: dict[str, float]) -> str:
    return f"VP {plan['VALUE PLAY']}, GOW {plan['GOW']}, " f"GOM {plan['GOM']}, GOY {plan['GOY']}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Backtest phase-aware staking plans.")
    parser.add_argument("--season", type=int, action="append", dest="seasons")
    parser.add_argument("--picks-dir", type=Path, default=Path("data/picks_variant_m"))
    parser.add_argument("--data-root", type=Path, default=Path("data"))
    parser.add_argument(
        "--manual-results", type=Path, default=Path("data/results/manual_results.jsonl")
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("research/season_phase_staking_variant_m_2015_2025.md"),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    seasons = args.seasons or list(range(2015, 2026))
    output = run(
        seasons=seasons,
        picks_dir=args.picks_dir,
        data_root=args.data_root,
        manual_results=args.manual_results,
        output=args.output,
    )
    print(f"report={output}")


if __name__ == "__main__":
    main()
