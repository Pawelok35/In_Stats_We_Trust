from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from metrics.strategy_search import StrategyRule, TAG_SETS, _row_matches, load_pick_rows

BREAK_EVEN_WIN_RATE = 110 / 210
WIN_UNITS = 100 / 110
LOSS_UNITS = -1.0


@dataclass(frozen=True)
class EvaluatedRule:
    rule: StrategyRule
    train: dict[str, Any]
    holdout: dict[str, Any]
    seasons: list[dict[str, Any]]


def _available_pick_dirs(data_root: Path) -> list[str]:
    return sorted(path.name for path in data_root.glob("picks*") if path.is_dir())


def _profit_for_outcome(outcome: str) -> float:
    if outcome == "win":
        return WIN_UNITS
    if outcome == "loss":
        return LOSS_UNITS
    return 0.0


def _summarize_rows(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    selected = [row for row in rows if row["outcome"] in {"win", "loss", "push"}]
    wins = sum(1 for row in selected if row["outcome"] == "win")
    losses = sum(1 for row in selected if row["outcome"] == "loss")
    pushes = sum(1 for row in selected if row["outcome"] == "push")
    decisions = wins + losses
    graded = decisions + pushes
    profit = sum(_profit_for_outcome(str(row["outcome"])) for row in selected)
    risk = float(decisions)
    return {
        "bets": graded,
        "wins": wins,
        "losses": losses,
        "pushes": pushes,
        "decisions": decisions,
        "profit": profit,
        "risk": risk,
        "win_rate": wins / decisions if decisions else 0.0,
        "roi": profit / risk if risk else 0.0,
        "p_value": _binomial_survival(wins, decisions, BREAK_EVEN_WIN_RATE)
        if decisions
        else 1.0,
        "ci_low": _wilson_interval(wins, decisions)[0] if decisions else 0.0,
        "ci_high": _wilson_interval(wins, decisions)[1] if decisions else 0.0,
        "max_drawdown": _max_drawdown(selected),
    }


def _max_drawdown(rows: list[dict[str, Any]]) -> float:
    equity = 0.0
    peak = 0.0
    drawdown = 0.0
    ordered = sorted(rows, key=lambda row: (int(row["season"]), int(row["week"])))
    for row in ordered:
        equity += _profit_for_outcome(str(row["outcome"]))
        peak = max(peak, equity)
        drawdown = min(drawdown, equity - peak)
    return drawdown


def _wilson_interval(wins: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    phat = wins / n
    denom = 1 + z * z / n
    centre = phat + z * z / (2 * n)
    margin = z * math.sqrt((phat * (1 - phat) + z * z / (4 * n)) / n)
    return ((centre - margin) / denom, (centre + margin) / denom)


def _binomial_survival(k: int, n: int, p: float) -> float:
    if n <= 0:
        return 1.0
    if k <= 0:
        return 1.0
    terms = []
    log_p = math.log(p)
    log_q = math.log1p(-p)
    for i in range(k, n + 1):
        log_comb = math.lgamma(n + 1) - math.lgamma(i + 1) - math.lgamma(n - i + 1)
        terms.append(log_comb + i * log_p + (n - i) * log_q)
    max_term = max(terms)
    return min(1.0, math.exp(max_term) * sum(math.exp(term - max_term) for term in terms))


def _evaluate_rule(
    rows: list[dict[str, Any]],
    rule: StrategyRule,
    train_seasons: list[int],
    holdout_seasons: list[int],
) -> EvaluatedRule:
    train_set = set(train_seasons)
    holdout_set = set(holdout_seasons)
    matched = [row for row in rows if _row_matches(row, rule)]
    train_rows = [row for row in matched if int(row["season"]) in train_set]
    holdout_rows = [row for row in matched if int(row["season"]) in holdout_set]
    season_rows = []
    for season in sorted(train_set | holdout_set):
        summary = _summarize_rows(row for row in matched if int(row["season"]) == season)
        summary["season"] = season
        summary["split"] = "train" if season in train_set else "holdout"
        season_rows.append(summary)
    return EvaluatedRule(
        rule=rule,
        train=_summarize_rows(train_rows),
        holdout=_summarize_rows(holdout_rows),
        seasons=season_rows,
    )


def _candidate_rules(
    rows: list[dict[str, Any]],
    train_seasons: list[int],
    variant_dirs: list[str],
    min_bets_per_train_season: int,
) -> tuple[list[EvaluatedRule], int]:
    variants = sorted({row["variant"] for row in rows})
    confidence_thresholds = [0, 70, 80, 85, 90, 95]
    edge_thresholds = [0, 4, 8, 10, 12, 15]
    handicap_modes = ["any", "favorite", "dog"]
    max_abs_handicaps: list[float | None] = [None, 3.5, 7.0, 10.0]
    start_weeks = [1, 3, 5]
    train_set = set(train_seasons)

    tested = 0
    candidates: list[EvaluatedRule] = []
    for variant in variants:
        if f"picks_{variant}" not in variant_dirs and not (
            variant == "baseline" and "picks" in variant_dirs
        ):
            continue
        for tags in TAG_SETS:
            for confidence_min in confidence_thresholds:
                for edge_min in edge_thresholds:
                    for handicap_mode in handicap_modes:
                        for max_abs_handicap in max_abs_handicaps:
                            for start_week in start_weeks:
                                tested += 1
                                rule = StrategyRule(
                                    variant=variant,
                                    tags=tags,
                                    confidence_min=confidence_min,
                                    edge_min=edge_min,
                                    handicap_mode=handicap_mode,
                                    start_week=start_week,
                                    max_abs_handicap=max_abs_handicap,
                                )
                                matched = [row for row in rows if _row_matches(row, rule)]
                                per_train_season = [
                                    _summarize_rows(
                                        row
                                        for row in matched
                                        if int(row["season"]) == season
                                    )
                                    for season in train_seasons
                                ]
                                if not all(
                                    item["bets"] >= min_bets_per_train_season
                                    and item["profit"] > 0
                                    for item in per_train_season
                                ):
                                    continue
                                train_summary = _summarize_rows(
                                    row for row in matched if int(row["season"]) in train_set
                                )
                                if train_summary["decisions"] == 0:
                                    continue
                                candidates.append(
                                    EvaluatedRule(
                                        rule=rule,
                                        train=train_summary,
                                        holdout={},
                                        seasons=[],
                                    )
                                )
    return candidates, tested


def _select_train_champions(
    candidates: list[EvaluatedRule],
    rows: list[dict[str, Any]],
    train_seasons: list[int],
    holdout_seasons: list[int],
    top_n: int,
) -> list[EvaluatedRule]:
    ranked = sorted(
        candidates,
        key=lambda item: (
            item.train["profit"],
            item.train["roi"],
            item.train["decisions"],
            -abs(item.train["max_drawdown"]),
        ),
        reverse=True,
    )
    return [
        _evaluate_rule(rows, item.rule, train_seasons, holdout_seasons)
        for item in ranked[:top_n]
    ]


def _classify_evidence(top: EvaluatedRule, tested_rules: int) -> tuple[str, list[str]]:
    holdout = top.holdout
    adjusted_p = min(1.0, holdout["p_value"] * max(1, tested_rules))
    reasons = [
        f"holdout bets={holdout['bets']}, W-L-P={holdout['wins']}-{holdout['losses']}-{holdout['pushes']}",
        f"holdout ROI={holdout['roi']:.1%}, units={holdout['profit']:+.2f}",
        f"one-sided binomial p={holdout['p_value']:.4f}, Bonferroni-adjusted p={adjusted_p:.4f}",
        f"95% Wilson CI win-rate={holdout['ci_low']:.1%}-{holdout['ci_high']:.1%}",
    ]
    if holdout["decisions"] < 100:
        return "promising but underpowered", reasons
    if holdout["profit"] <= 0 or holdout["win_rate"] <= BREAK_EVEN_WIN_RATE:
        return "no confirmed holdout edge", reasons
    if adjusted_p < 0.05 and holdout["roi"] > 0:
        return "strong search-adjusted holdout evidence", reasons
    if holdout["p_value"] < 0.05 and holdout["roi"] > 0:
        return "positive holdout evidence, not search-adjusted proof", reasons
    return "weak positive holdout evidence", reasons


def _parse_datetime(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _scan_integrity(
    *,
    data_root: Path,
    variant_dirs: list[str],
    seasons: list[int],
) -> dict[str, Any]:
    total = 0
    generated_after_season = 0
    code_dirty = 0
    missing_generated_at = 0
    missing_commit = 0
    missing_price_timestamp = 0
    generated_dates: set[str] = set()

    for directory in variant_dirs:
        pick_root = data_root / directory
        if not pick_root.exists():
            continue
        for season in seasons:
            season_dir = pick_root / str(season)
            if not season_dir.exists():
                continue
            for path in sorted(season_dir.glob("week_*.jsonl")):
                for line in path.read_text(encoding="utf-8").splitlines():
                    if not line.strip():
                        continue
                    total += 1
                    record = json.loads(line)
                    generated_at = record.get("generated_at")
                    if not generated_at:
                        missing_generated_at += 1
                    else:
                        generated_dates.add(str(generated_at)[:19])
                        parsed = _parse_datetime(str(generated_at))
                        if parsed is not None and parsed.year > int(record.get("season", season)):
                            generated_after_season += 1
                    if record.get("code_is_dirty") is True:
                        code_dirty += 1
                    if not record.get("commit_sha"):
                        missing_commit += 1
                    if not (
                        record.get("decision_ts_utc")
                        or record.get("line_ts_utc")
                        or record.get("odds_ts_utc")
                        or record.get("snapshot_ts_utc")
                    ):
                        missing_price_timestamp += 1

    red_flags = []
    if generated_after_season:
        red_flags.append(
            "pick files were generated after the season year; this is historical backfill, not prospective proof"
        )
    if code_dirty:
        red_flags.append("records were generated from a dirty git worktree")
    if missing_price_timestamp:
        red_flags.append("records do not contain immutable decision-time odds timestamps")
    if missing_commit:
        red_flags.append("some records do not contain commit_sha")
    if missing_generated_at:
        red_flags.append("some records do not contain generated_at")

    return {
        "total": total,
        "generated_after_season": generated_after_season,
        "code_dirty": code_dirty,
        "missing_generated_at": missing_generated_at,
        "missing_commit": missing_commit,
        "missing_price_timestamp": missing_price_timestamp,
        "generated_dates": len(generated_dates),
        "red_flags": red_flags,
    }


def _proof_status(statistical_classification: str, integrity: dict[str, Any]) -> str:
    if integrity["red_flags"]:
        return "not a full edge proof: statistically strong historical backtest with integrity red flags"
    return statistical_classification


def _format_pct(value: float) -> str:
    return f"{value:.1%}"


def write_dossier(
    *,
    output_path: Path,
    candidates: list[EvaluatedRule],
    tested_rules: int,
    data_root: Path,
    variant_dirs: list[str],
    train_seasons: list[int],
    holdout_seasons: list[int],
    min_bets_per_train_season: int,
    integrity: dict[str, Any],
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not candidates:
        lines = [
            "# Edge Proof Dossier",
            "",
            "No candidate rule passed the train-period eligibility gates.",
            "",
            f"- Train seasons: {train_seasons}",
            f"- Holdout seasons: {holdout_seasons}",
            f"- Tested rules: {tested_rules}",
        ]
        output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return output_path

    top = candidates[0]
    classification, reasons = _classify_evidence(top, tested_rules)
    proof_status = _proof_status(classification, integrity)
    adjusted_p = min(1.0, top.holdout["p_value"] * max(1, tested_rules))
    lines = [
        "# Edge Proof Dossier",
        "",
        f"Generated from local pick ledgers under `{data_root}`.",
        "",
        "## Verdict",
        "",
        f"**Proof status:** {proof_status}",
        f"**Statistical classification before integrity gates:** {classification}",
        "",
        "This dossier is an empirical audit, not financial advice. The selected rule was ranked using train-period performance only; holdout results are reported after selection.",
        "",
        "Key holdout facts:",
    ]
    lines.extend(f"- {reason}" for reason in reasons)
    lines.extend(
        [
            "",
            "## Protocol",
            "",
            f"- Train seasons: {', '.join(map(str, train_seasons))}",
            f"- Holdout seasons: {', '.join(map(str, holdout_seasons))}",
            f"- Variant directories searched: {', '.join(variant_dirs)}",
            f"- Tested rule grid size: {tested_rules}",
            f"- Train eligibility gate: at least {min_bets_per_train_season} bets and positive flat-stake units in every train season.",
            "- Selection criterion: train profit, then train ROI, then train sample size.",
            "- Holdout was not used for selecting the champion rule.",
            "- Profit model: flat 1u risk per non-push ATS decision at -110; win = +0.9091u, loss = -1u, push = 0u.",
            "- Statistical screen: one-sided binomial test against 52.38% break-even win rate, plus Bonferroni adjustment over the searched grid.",
            "",
            "## Data Integrity Gate",
            "",
            f"- Pick records scanned: {integrity['total']}",
            f"- Records generated after season year: {integrity['generated_after_season']}",
            f"- Records generated from dirty worktree: {integrity['code_dirty']}",
            f"- Records missing decision-time odds timestamp: {integrity['missing_price_timestamp']}",
            f"- Distinct `generated_at` timestamps: {integrity['generated_dates']}",
            "",
        ]
    )
    if integrity["red_flags"]:
        lines.append("Red flags:")
        lines.extend(f"- {flag}" for flag in integrity["red_flags"])
        lines.extend(
            [
                "",
                "Integrity verdict: the numeric result can be treated as a historical backtest screen, but not as a completed proof of a tradable edge. The next required gate is a prospective, immutable paper-trading ledger.",
                "",
            ]
        )
    lines.extend(
        [
            "## Champion Rule",
            "",
            f"`{top.rule.description}`",
            "",
            "| Split | Bets | W-L-P | Win Rate | Units | ROI | Max DD | p-value | Adj. p | 95% CI |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
            _summary_row("Train", top.train, top.train["p_value"]),
            _summary_row("Holdout", top.holdout, adjusted_p),
            "",
            "## Season Breakdown",
            "",
            "| Season | Split | Bets | W-L-P | Win Rate | Units | ROI | Max DD |",
            "|---:|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in top.seasons:
        lines.append(
            "| {season} | {split} | {bets} | {wins}-{losses}-{pushes} | {win_rate} | "
            "{profit:+.2f}u | {roi} | {max_dd:+.2f}u |".format(
                season=row["season"],
                split=row["split"],
                bets=row["bets"],
                wins=row["wins"],
                losses=row["losses"],
                pushes=row["pushes"],
                win_rate=_format_pct(row["win_rate"]),
                profit=row["profit"],
                roi=_format_pct(row["roi"]),
                max_dd=row["max_drawdown"],
            )
        )

    lines.extend(
        [
            "",
            "## Top Train-Selected Candidates",
            "",
            "| Rank | Rule | Train Units | Train ROI | Holdout Units | Holdout ROI | Holdout Bets |",
            "|---:|---|---:|---:|---:|---:|---:|",
        ]
    )
    for rank, item in enumerate(candidates[:20], start=1):
        lines.append(
            "| {rank} | `{rule}` | {train_units:+.2f}u | {train_roi} | "
            "{holdout_units:+.2f}u | {holdout_roi} | {holdout_bets} |".format(
                rank=rank,
                rule=item.rule.description.replace("|", "/"),
                train_units=item.train["profit"],
                train_roi=_format_pct(item.train["roi"]),
                holdout_units=item.holdout["profit"],
                holdout_roi=_format_pct(item.holdout["roi"]),
                holdout_bets=item.holdout["bets"],
            )
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- A positive holdout is evidence only if the rule was selected without looking at holdout outcomes.",
            "- A search-adjusted proof is much harder than a positive ROI table because the grid contains many variants, thresholds and subgroups.",
            "- If adjusted p-value is not significant, the correct label is a candidate edge, not a proven edge.",
            "- The next stronger test is prospective paper-trading with immutable timestamps before kickoff.",
            "",
            "## Next Gate",
            "",
            "Promote the champion rule to prospective watch only if holdout ROI is positive, sample size is adequate, and drawdown is operationally tolerable. The prospective ledger must record decision-time line, price, source, timestamp, model version and no-bet reasons before kickoff.",
        ]
    )
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path


def _summary_row(label: str, item: dict[str, Any], adjusted_p: float) -> str:
    return (
        f"| {label} | {item['bets']} | {item['wins']}-{item['losses']}-{item['pushes']} | "
        f"{_format_pct(item['win_rate'])} | {item['profit']:+.2f}u | "
        f"{_format_pct(item['roi'])} | {item['max_drawdown']:+.2f}u | "
        f"{item['p_value']:.4f} | {adjusted_p:.4f} | "
        f"{_format_pct(item['ci_low'])}-{_format_pct(item['ci_high'])} |"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build an empirical edge proof dossier.")
    parser.add_argument("--data-root", type=Path, default=Path("data"))
    parser.add_argument("--train-seasons", nargs="+", type=int, default=[2021, 2022, 2023])
    parser.add_argument("--holdout-seasons", nargs="+", type=int, default=[2024, 2025])
    parser.add_argument("--variant-dir", action="append", dest="variant_dirs")
    parser.add_argument("--min-bets-per-train-season", type=int, default=3)
    parser.add_argument("--top-n", type=int, default=50)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("research/edge_proof_dossier.md"),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    variant_dirs = args.variant_dirs or _available_pick_dirs(args.data_root)
    seasons = sorted(set(args.train_seasons + args.holdout_seasons))
    rows = load_pick_rows(
        data_root=args.data_root,
        seasons=seasons,
        variant_dirs=variant_dirs,
    )
    raw_candidates, tested_rules = _candidate_rules(
        rows,
        train_seasons=args.train_seasons,
        variant_dirs=variant_dirs,
        min_bets_per_train_season=args.min_bets_per_train_season,
    )
    candidates = _select_train_champions(
        raw_candidates,
        rows,
        train_seasons=args.train_seasons,
        holdout_seasons=args.holdout_seasons,
        top_n=args.top_n,
    )
    integrity = _scan_integrity(
        data_root=args.data_root,
        variant_dirs=variant_dirs,
        seasons=seasons,
    )
    path = write_dossier(
        output_path=args.output,
        candidates=candidates,
        tested_rules=tested_rules,
        data_root=args.data_root,
        variant_dirs=variant_dirs,
        train_seasons=args.train_seasons,
        holdout_seasons=args.holdout_seasons,
        min_bets_per_train_season=args.min_bets_per_train_season,
        integrity=integrity,
    )
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
