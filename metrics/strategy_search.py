"""Search simple betting strategy filters across historical pick outputs."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import polars as pl
import yaml

from utils.team_aliases import normalize_team_code

PAYOUTS = {
    "GOY": (3.6, 4.0),
    "GOM": (2.7, 3.0),
    "GOW": (1.8, 2.0),
    "VALUE PLAY": (0.9, 1.0),
    "NEUTRAL": (0.0, 0.0),
}

DEFAULT_VARIANT_DIRS = [
    "picks_variant_b_edge_focus",
    "picks_variant_c_psdiff",
    "picks_variant_d_balanced",
    "picks_variant_j",
    "picks_variant_k",
    "picks_variant_m",
]

TAG_SETS = [
    ("GOY",),
    ("GOM",),
    ("GOW",),
    ("VALUE PLAY",),
    ("GOY", "GOM"),
    ("GOY", "GOW"),
    ("GOM", "GOW"),
    ("GOY", "GOM", "GOW"),
    ("GOY", "GOM", "GOW", "VALUE PLAY"),
]


@dataclass(frozen=True)
class StrategyRule:
    variant: str
    tags: tuple[str, ...]
    confidence_min: float
    edge_min: float
    handicap_mode: str
    start_week: int = 1
    max_abs_handicap: float | None = None

    @property
    def description(self) -> str:
        text = (
            f"{self.variant} | tags={'+'.join(self.tags)} | "
            f"confidence>={self.confidence_min:g} | edge>={self.edge_min:g} | "
            f"{self.handicap_mode}"
        )
        if self.start_week > 1:
            text += f" | week>={self.start_week}"
        if self.max_abs_handicap is not None:
            text += f" | abs(handicap)<={self.max_abs_handicap:g}"
        return text


def _completed_result_map(
    data_root: Path,
    seasons: Iterable[int],
) -> dict[tuple[int, int, str, str], tuple[Any, Any]]:
    results: dict[tuple[int, int, str, str], tuple[Any, Any]] = {}
    for season in seasons:
        path = data_root / "schedules" / f"{season}.parquet"
        if not path.exists():
            continue
        df = pl.read_parquet(path)
        if "game_type" in df.columns:
            df = df.filter(pl.col("game_type") == "REG")
        needed = {"week", "home_team", "away_team", "home_score", "away_score"}
        if needed - set(df.columns):
            continue
        for row in df.select(list(needed)).to_dicts():
            home = normalize_team_code(row.get("home_team"))
            away = normalize_team_code(row.get("away_team"))
            if home and away:
                results[(season, int(row["week"]), home, away)] = (
                    row.get("home_score"),
                    row.get("away_score"),
                )
    return results


def _safe_float(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _pick_outcome(pick: dict[str, Any], result: tuple[Any, Any] | None) -> str:
    if not result or result[0] is None or result[1] is None:
        return "pending"
    home_score = int(result[0])
    away_score = int(result[1])
    home = normalize_team_code(pick.get("home"))
    away = normalize_team_code(pick.get("away"))
    model_winner = normalize_team_code(pick.get("model_winner"))
    if model_winner == home:
        margin = home_score - away_score
    elif model_winner == away:
        margin = away_score - home_score
    else:
        return "pending"
    ats_margin = margin + _safe_float(pick.get("handicap"))
    if ats_margin > 0:
        return "win"
    if ats_margin < 0:
        return "loss"
    return "push"


def load_pick_rows(
    *,
    data_root: Path,
    seasons: Iterable[int],
    variant_dirs: Iterable[str],
) -> list[dict[str, Any]]:
    season_list = list(seasons)
    results = _completed_result_map(data_root, season_list)
    rows: list[dict[str, Any]] = []
    for directory in variant_dirs:
        pick_root = data_root / directory
        if not pick_root.exists():
            continue
        variant = directory.removeprefix("picks_") if directory != "picks" else "baseline"
        for season in season_list:
            season_dir = pick_root / str(season)
            if not season_dir.exists():
                continue
            for path in sorted(season_dir.glob("week_*.jsonl")):
                for line in path.read_text(encoding="utf-8").splitlines():
                    if not line.strip():
                        continue
                    pick = json.loads(line)
                    home = normalize_team_code(pick.get("home"))
                    away = normalize_team_code(pick.get("away"))
                    week = int(pick.get("week", 0))
                    tag = str(pick.get("tag", "")).upper()
                    outcome = _pick_outcome(pick, results.get((season, week, home, away)))
                    win_units, loss_units = PAYOUTS.get(tag, (0.0, 0.0))
                    if outcome == "win":
                        profit = win_units
                    elif outcome == "loss":
                        profit = -loss_units
                    else:
                        profit = 0.0
                    rows.append(
                        {
                            "season": season,
                            "week": week,
                            "variant": variant,
                            "tag": tag,
                            "confidence": _safe_float(pick.get("confidence")),
                            "edge": _safe_float(pick.get("edge_vs_line")),
                            "handicap": _safe_float(pick.get("handicap")),
                            "outcome": outcome,
                            "profit": profit,
                            "risk": (
                                loss_units
                                if tag != "NEUTRAL" and outcome in {"win", "loss", "push"}
                                else 0.0
                            ),
                        }
                    )
    return rows


def _row_matches(row: dict[str, Any], rule: StrategyRule) -> bool:
    if row["variant"] != rule.variant:
        return False
    if int(row.get("week") or 0) < rule.start_week:
        return False
    if row["tag"] not in rule.tags:
        return False
    if row["confidence"] < rule.confidence_min:
        return False
    if row["edge"] < rule.edge_min:
        return False
    if rule.handicap_mode == "favorite" and row["handicap"] >= 0:
        return False
    if rule.handicap_mode == "dog" and row["handicap"] <= 0:
        return False
    if rule.max_abs_handicap is not None and abs(float(row["handicap"])) > rule.max_abs_handicap:
        return False
    return True


def evaluate_rule(
    rows: list[dict[str, Any]],
    rule: StrategyRule,
    seasons: Iterable[int],
) -> dict[int, dict[str, float]]:
    stats = {
        season: {
            "profit": 0.0,
            "risk": 0.0,
            "bets": 0,
            "wins": 0,
            "losses": 0,
            "pushes": 0,
        }
        for season in seasons
    }
    for row in rows:
        if row["season"] not in stats or not _row_matches(row, rule):
            continue
        season_stats = stats[row["season"]]
        season_stats["profit"] += float(row["profit"])
        season_stats["risk"] += float(row["risk"])
        season_stats["bets"] += 1
        season_stats["wins"] += 1 if row["outcome"] == "win" else 0
        season_stats["losses"] += 1 if row["outcome"] == "loss" else 0
        season_stats["pushes"] += 1 if row["outcome"] == "push" else 0
    return stats


def load_strategy_rule(path: Path) -> StrategyRule:
    """Load one fixed strategy rule from YAML."""

    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    tags = tuple(str(item).upper() for item in payload.get("tags", []))
    if not tags:
        raise ValueError(f"Strategy rule has no tags: {path}")
    return StrategyRule(
        variant=str(payload["variant"]),
        tags=tags,
        confidence_min=float(payload.get("confidence_min", 0)),
        edge_min=float(payload.get("edge_min", 0)),
        handicap_mode=str(payload.get("handicap_mode", "any")),
        start_week=int(payload.get("start_week", 1)),
        max_abs_handicap=(
            None
            if payload.get("max_abs_handicap") is None
            else float(payload.get("max_abs_handicap"))
        ),
    )


def _summarize_stats(stats: dict[int, dict[str, float]]) -> dict[str, float]:
    total_profit = sum(item["profit"] for item in stats.values())
    total_risk = sum(item["risk"] for item in stats.values())
    total_bets = sum(item["bets"] for item in stats.values())
    min_profit = min(item["profit"] for item in stats.values()) if stats else 0.0
    positive_seasons = sum(1 for item in stats.values() if item["profit"] > 0)
    return {
        "units": total_profit,
        "risk": total_risk,
        "roi": total_profit / total_risk if total_risk else 0.0,
        "bets": total_bets,
        "min_season_units": min_profit,
        "positive_seasons": positive_seasons,
    }


def summarize_rule_by_season(
    rows: list[dict[str, Any]],
    rule: StrategyRule,
    seasons: Iterable[int],
) -> list[dict[str, Any]]:
    """Return one compact performance row per season for a fixed strategy rule."""

    stats = evaluate_rule(rows, rule, seasons)
    output: list[dict[str, Any]] = []
    for season in seasons:
        item = stats[season]
        decisions = item["wins"] + item["losses"]
        output.append(
            {
                "season": season,
                "bets": int(item["bets"]),
                "wins": int(item["wins"]),
                "losses": int(item["losses"]),
                "pushes": int(item["pushes"]),
                "profit": float(item["profit"]),
                "risk": float(item["risk"]),
                "win_rate": item["wins"] / decisions if decisions else 0.0,
                "roi": item["profit"] / item["risk"] if item["risk"] else 0.0,
            }
        )
    return output


def max_drawdown_units(rows: list[dict[str, Any]], rule: StrategyRule) -> float:
    """Calculate max drawdown in units using season/week row order."""

    matched = sorted(
        (row for row in rows if _row_matches(row, rule)),
        key=lambda row: (int(row["season"]), int(row["week"])),
    )
    equity = 0.0
    peak = 0.0
    drawdown = 0.0
    for row in matched:
        equity += float(row["profit"])
        peak = max(peak, equity)
        drawdown = min(drawdown, equity - peak)
    return drawdown


def walk_forward_windows(
    rows: list[dict[str, Any]],
    rule: StrategyRule,
    *,
    start_season: int,
    end_season: int,
) -> list[dict[str, Any]]:
    """Evaluate expanding-window train history against each next season."""

    windows: list[dict[str, Any]] = []
    for test_season in range(start_season + 1, end_season + 1):
        train_seasons = list(range(start_season, test_season))
        test_stats = evaluate_rule(rows, rule, [test_season])[test_season]
        train_summary = _summarize_stats(evaluate_rule(rows, rule, train_seasons))
        windows.append(
            {
                "train": f"{start_season}-{test_season - 1}",
                "test_season": test_season,
                "train_units": train_summary["units"],
                "train_min_season_units": train_summary["min_season_units"],
                "test_units": test_stats["profit"],
                "test_bets": int(test_stats["bets"]),
                "test_wins": int(test_stats["wins"]),
                "test_losses": int(test_stats["losses"]),
                "test_pushes": int(test_stats["pushes"]),
                "test_roi": (
                    test_stats["profit"] / test_stats["risk"] if test_stats["risk"] else 0.0
                ),
            }
        )
    return windows


def write_fixed_strategy_report(
    *,
    rows: list[dict[str, Any]],
    rule: StrategyRule,
    output_path: Path,
    start_season: int,
    end_season: int,
    title: str = "Fixed Strategy Report",
) -> Path:
    """Write a Markdown report for one fixed strategy rule."""

    seasons = list(range(start_season, end_season + 1))
    season_rows = summarize_rule_by_season(rows, rule, seasons)
    totals = {
        "bets": sum(row["bets"] for row in season_rows),
        "wins": sum(row["wins"] for row in season_rows),
        "losses": sum(row["losses"] for row in season_rows),
        "pushes": sum(row["pushes"] for row in season_rows),
        "profit": sum(row["profit"] for row in season_rows),
        "risk": sum(row["risk"] for row in season_rows),
    }
    total_roi = totals["profit"] / totals["risk"] if totals["risk"] else 0.0
    min_season = min((row["profit"] for row in season_rows), default=0.0)
    drawdown = max_drawdown_units(rows, rule)
    walk_rows = walk_forward_windows(
        rows,
        rule,
        start_season=start_season,
        end_season=end_season,
    )

    lines = [
        f"# {title}",
        "",
        f"Rule: `{rule.description}`",
        f"Seasons: {start_season}-{end_season}",
        "",
        "## Summary",
        "",
        f"- Bets: {totals['bets']}",
        f"- W-L-P: {totals['wins']}-{totals['losses']}-{totals['pushes']}",
        f"- Profit: {totals['profit']:+.1f}u",
        f"- ROI: {total_roi:.1%}",
        f"- Worst season: {min_season:+.1f}u",
        f"- Max drawdown: {drawdown:+.1f}u",
        "",
        "## Season Results",
        "",
        "| Season | Bets | W-L-P | Units | ROI |",
        "|---:|---:|---:|---:|---:|",
    ]
    for row in season_rows:
        lines.append(
            "| {season} | {bets} | {wins}-{losses}-{pushes} | {profit:+.1f}u | "
            "{roi:.1%} |".format(**row)
        )

    lines.extend(
        [
            "",
            "## Walk Forward",
            "",
            "| Train | Test | Test Bets | Test W-L-P | Train Units | "
            "Train Worst Season | Test Units | Test ROI |",
            "|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in walk_rows:
        lines.append(
            "| {train} | {test_season} | {test_bets} | "
            "{test_wins}-{test_losses}-{test_pushes} | {train_units:+.1f}u | "
            "{train_min_season_units:+.1f}u | {test_units:+.1f}u | "
            "{test_roi:.1%} |".format(**row)
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path


def search_strategies(
    *,
    data_root: Path,
    train_seasons: list[int],
    holdout_seasons: list[int],
    variant_dirs: list[str] | None = None,
    min_bets_per_train_season: int = 3,
    top_n: int = 50,
) -> list[dict[str, Any]]:
    variant_dirs = variant_dirs or DEFAULT_VARIANT_DIRS
    all_seasons = sorted(set(train_seasons + holdout_seasons))
    rows = load_pick_rows(data_root=data_root, seasons=all_seasons, variant_dirs=variant_dirs)
    variants = sorted({row["variant"] for row in rows})
    confidence_thresholds = [0, 70, 80, 85, 90, 95]
    edge_thresholds = [0, 4, 8, 10, 12, 15]
    handicap_modes = ["any", "favorite", "dog"]

    candidates: list[dict[str, Any]] = []
    for variant in variants:
        for tags in TAG_SETS:
            for confidence_min in confidence_thresholds:
                for edge_min in edge_thresholds:
                    for handicap_mode in handicap_modes:
                        rule = StrategyRule(
                            variant=variant,
                            tags=tags,
                            confidence_min=confidence_min,
                            edge_min=edge_min,
                            handicap_mode=handicap_mode,
                        )
                        train_stats = evaluate_rule(rows, rule, train_seasons)
                        if not all(
                            item["bets"] >= min_bets_per_train_season and item["profit"] > 0
                            for item in train_stats.values()
                        ):
                            continue
                        holdout_stats = evaluate_rule(rows, rule, holdout_seasons)
                        train_summary = _summarize_stats(train_stats)
                        holdout_summary = _summarize_stats(holdout_stats)
                        candidates.append(
                            {
                                "rule": rule,
                                "description": rule.description,
                                "train_stats": train_stats,
                                "holdout_stats": holdout_stats,
                                "train": train_summary,
                                "holdout": holdout_summary,
                            }
                        )

    candidates.sort(
        key=lambda item: (
            item["holdout"]["units"],
            item["train"]["units"],
            item["train"]["min_season_units"],
            item["train"]["bets"],
        ),
        reverse=True,
    )
    return candidates[:top_n]


def write_strategy_search_outputs(
    candidates: list[dict[str, Any]],
    *,
    output_dir: Path,
    train_seasons: list[int],
    holdout_seasons: list[int],
) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "candidates.csv"
    md_path = output_dir / "top_candidates.md"

    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        fieldnames = [
            "rank",
            "description",
            "train_units",
            "train_roi",
            "train_bets",
            "train_min_season_units",
            "holdout_units",
            "holdout_roi",
            "holdout_bets",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for rank, item in enumerate(candidates, start=1):
            writer.writerow(
                {
                    "rank": rank,
                    "description": item["description"],
                    "train_units": round(item["train"]["units"], 2),
                    "train_roi": round(item["train"]["roi"], 4),
                    "train_bets": int(item["train"]["bets"]),
                    "train_min_season_units": round(item["train"]["min_season_units"], 2),
                    "holdout_units": round(item["holdout"]["units"], 2),
                    "holdout_roi": round(item["holdout"]["roi"], 4),
                    "holdout_bets": int(item["holdout"]["bets"]),
                }
            )

    lines = [
        "# Strategy Search Candidates",
        "",
        f"Train seasons: {', '.join(map(str, train_seasons))}",
        f"Holdout seasons: {', '.join(map(str, holdout_seasons))}",
        "",
        "| Rank | Rule | Train Units | Train Min Season | Holdout Units | Holdout ROI |",
        "|---:|---|---:|---:|---:|---:|",
    ]
    for rank, item in enumerate(candidates[:20], start=1):
        rule_description = item["description"].replace("|", "/")
        lines.append(
            "| {rank} | {rule} | {train_units:+.1f}u | {min_units:+.1f}u | "
            "{holdout_units:+.1f}u | {holdout_roi:.1%} |".format(
                rank=rank,
                rule=rule_description,
                train_units=item["train"]["units"],
                min_units=item["train"]["min_season_units"],
                holdout_units=item["holdout"]["units"],
                holdout_roi=item["holdout"]["roi"],
            )
        )
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return csv_path, md_path
