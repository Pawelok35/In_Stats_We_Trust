"""Shadow calibration research for adding near-miss GOM picks without changing CORE."""

from __future__ import annotations

import json
import math
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from statistics import mean, pstdev
from typing import Any, Iterable

from metrics.ats_features import (
    HOLDOUT_SEASONS,
    PAYOUT_LOSS,
    PAYOUT_RISK,
    PAYOUT_WIN,
    SEASONS,
    TRAIN_SEASONS,
    VALIDATION_SEASONS,
    _pick_outcome,
    _result_map,
    _summarize,
    _team_prior_features,
)
from utils.team_aliases import normalize_team_code

DEFAULT_OUTPUT = Path("data/results/strategy_search/gom_calibration_shadow_report.md")

VARIANT_DIRS = {
    "B": Path("data/picks_variant_b_edge_focus"),
    "C": Path("data/picks_variant_c_psdiff"),
    "D": Path("data/picks_variant_d_balanced"),
    "J": Path("data/picks_variant_j"),
    "K": Path("data/picks_variant_k"),
    "M": Path("data/picks_variant_m"),
}


@dataclass(frozen=True)
class ShadowPick:
    season: int
    week: int
    home: str
    away: str
    pick_team: str
    opponent: str
    confidence: float
    edge: float
    handicap: float
    model_margin: float
    outcome: str
    profit: float
    risk: float
    pool: str
    consensus_count: int
    margin_dispersion: float
    pressure_matchup_disadvantage: float | None
    third_down_luck_support: float | None
    residual_bias_edge: float
    residual_volatility: float
    shadow_score: float


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _key(record: dict[str, Any]) -> tuple[int, int, str, str]:
    return (
        int(record.get("season") or 0),
        int(record.get("week") or 0),
        normalize_team_code(record.get("home")),
        normalize_team_code(record.get("away")),
    )


def _load_variant_records(
    seasons: Iterable[int] = SEASONS,
) -> dict[str, dict[tuple[int, int, str, str], dict[str, Any]]]:
    data: dict[str, dict[tuple[int, int, str, str], dict[str, Any]]] = {}
    for variant, root in VARIANT_DIRS.items():
        variant_rows: dict[tuple[int, int, str, str], dict[str, Any]] = {}
        for season in seasons:
            season_dir = root / str(season)
            if not season_dir.exists():
                continue
            for path in sorted(season_dir.glob("week_*.jsonl")):
                for line in path.read_text(encoding="utf-8").splitlines():
                    if not line.strip():
                        continue
                    record = json.loads(line)
                    variant_rows[_key(record)] = record
        data[variant] = variant_rows
    return data


def _is_core(record: dict[str, Any]) -> bool:
    return (
        str(record.get("tag", "")).upper() == "GOM"
        and int(record.get("week") or 0) >= 3
        and _safe_float(record.get("confidence")) >= 85
        and _safe_float(record.get("edge_vs_line")) >= 4
        and abs(_safe_float(record.get("handicap"))) <= 7
    )


def _is_near_miss(record: dict[str, Any]) -> bool:
    if str(record.get("tag", "")).upper() != "GOM":
        return False
    week = int(record.get("week") or 0)
    confidence = _safe_float(record.get("confidence"))
    edge = _safe_float(record.get("edge_vs_line"))
    abs_handicap = abs(_safe_float(record.get("handicap")))
    if week < 3 or abs_handicap > 8 or _is_core(record):
        return False
    return (
        (80 <= confidence < 85 and edge >= 3)
        or (confidence >= 80 and 3 <= edge < 4)
        or (7 < abs_handicap <= 8 and confidence >= 85 and edge >= 4)
    )


def _oriented_margin(record: dict[str, Any], side: str) -> float | None:
    home = normalize_team_code(record.get("home"))
    away = normalize_team_code(record.get("away"))
    model_margin = _safe_float(record.get("model_margin"), default=math.nan)
    if math.isnan(model_margin):
        return None
    if side == home:
        return model_margin
    if side == away:
        return -model_margin
    return None


def _consensus_features(
    records_by_variant: dict[str, dict[tuple[int, int, str, str], dict[str, Any]]],
    key: tuple[int, int, str, str],
    side: str,
) -> tuple[int, float]:
    margins: list[float] = []
    consensus = 0
    for variant_rows in records_by_variant.values():
        record = variant_rows.get(key)
        if not record:
            continue
        if normalize_team_code(record.get("model_winner")) == side:
            consensus += 1
        margin = _oriented_margin(record, side)
        if margin is not None:
            margins.append(margin)
    dispersion = pstdev(margins) if len(margins) >= 2 else 0.0
    return consensus, dispersion


def _actual_team_margin(
    result: tuple[Any, Any] | None,
    home: str,
    away: str,
    team: str,
) -> float | None:
    if not result or result[0] is None or result[1] is None:
        return None
    home_margin = float(result[0]) - float(result[1])
    if team == home:
        return home_margin
    if team == away:
        return -home_margin
    return None


def _residual_lookup(
    records_by_variant: dict[str, dict[tuple[int, int, str, str], dict[str, Any]]],
    results: dict[tuple[int, int, str, str], tuple[Any, Any]],
) -> dict[tuple[int, int, str], tuple[float, float]]:
    """Return prior residual bias/std by season, week cutoff and team from D variant records."""

    d_records = records_by_variant.get("D", {})
    by_team: dict[tuple[int, str], list[tuple[int, float]]] = defaultdict(list)
    for key, record in d_records.items():
        season, week, home, away = key
        result = results.get(key)
        for team in (home, away):
            actual = _actual_team_margin(result, home, away, team)
            predicted = _oriented_margin(record, team)
            if actual is None or predicted is None:
                continue
            by_team[(season, team)].append((week, actual - predicted))

    lookup: dict[tuple[int, int, str], tuple[float, float]] = {}
    for (season, team), residuals in by_team.items():
        for week in range(1, 23):
            prior = [value for prior_week, value in residuals if prior_week < week]
            if not prior:
                lookup[(season, week, team)] = (0.0, 14.0)
            elif len(prior) == 1:
                lookup[(season, week, team)] = (prior[0] * 0.5, 14.0)
            else:
                lookup[(season, week, team)] = (mean(prior) * 0.5, pstdev(prior) or 14.0)
    return lookup


def _context_features(
    season: int,
    week: int,
    pick_team: str,
    opponent: str,
) -> tuple[float | None, float | None]:
    features = _team_prior_features(season, week)
    pick_row = features.get(pick_team, {})
    opp_row = features.get(opponent, {})
    pressure_allowed_pick = pick_row.get("pressure_allowed_proxy")
    pressure_created_pick = pick_row.get("pressure_created_proxy")
    pressure_allowed_opp = opp_row.get("pressure_allowed_proxy")
    pressure_created_opp = opp_row.get("pressure_created_proxy")
    pressure = None
    if None not in (
        pressure_allowed_pick,
        pressure_created_pick,
        pressure_allowed_opp,
        pressure_created_opp,
    ):
        pressure_faced_pick = (
            _safe_float(pressure_allowed_pick) + _safe_float(pressure_created_opp)
        ) / 2
        pressure_faced_opp = (
            _safe_float(pressure_allowed_opp) + _safe_float(pressure_created_pick)
        ) / 2
        pressure = pressure_faced_pick - pressure_faced_opp
    off_3doe = pick_row.get("off_3doe")
    def_3doe = pick_row.get("def_3doe")
    third = None if None in (off_3doe, def_3doe) else _safe_float(off_3doe) + _safe_float(def_3doe)
    return pressure, third


def _score_pick(
    *,
    confidence: float,
    edge: float,
    consensus_count: int,
    margin_dispersion: float,
    pressure: float | None,
    third_down: float | None,
    residual_bias_edge: float,
    residual_volatility: float,
) -> float:
    """Transparent shadow score; positive means stronger near-miss candidate."""

    score = 0.0
    score += (confidence - 80.0) * 0.10
    score += (edge - 3.0) * 0.25
    score += (consensus_count - 3) * 0.40
    score -= max(0.0, margin_dispersion - 7.0) * 0.08
    score -= max(0.0, (pressure or 0.0) - 0.04) * 4.0
    score -= max(0.0, (third_down or 0.0) - 0.08) * 2.0
    score += residual_bias_edge * 0.02
    score -= max(0.0, residual_volatility - 14.0) * 0.03
    return score


def build_shadow_picks(seasons: Iterable[int] = SEASONS) -> list[ShadowPick]:
    records_by_variant = _load_variant_records(seasons)
    results = _result_map(seasons)
    residuals = _residual_lookup(records_by_variant, results)
    output: list[ShadowPick] = []
    d_records = records_by_variant.get("D", {})
    context_cache: dict[tuple[int, int, str, str], tuple[float | None, float | None]] = {}
    for key, record in d_records.items():
        if not (_is_core(record) or _is_near_miss(record)):
            continue
        season, week, home, away = key
        outcome = _pick_outcome(record, results.get(key))
        if outcome is None:
            continue
        pick_team = normalize_team_code(record.get("model_winner"))
        opponent = away if pick_team == home else home
        consensus_count, margin_dispersion = _consensus_features(records_by_variant, key, pick_team)
        context_key = (season, week, pick_team, opponent)
        if context_key not in context_cache:
            context_cache[context_key] = _context_features(season, week, pick_team, opponent)
        pressure, third_down = context_cache[context_key]
        pick_bias, pick_vol = residuals.get((season, week, pick_team), (0.0, 14.0))
        opp_bias, opp_vol = residuals.get((season, week, opponent), (0.0, 14.0))
        residual_bias_edge = pick_bias - opp_bias
        residual_volatility = (pick_vol + opp_vol) / 2.0
        confidence = _safe_float(record.get("confidence"))
        edge = _safe_float(record.get("edge_vs_line"))
        score = _score_pick(
            confidence=confidence,
            edge=edge,
            consensus_count=consensus_count,
            margin_dispersion=margin_dispersion,
            pressure=pressure,
            third_down=third_down,
            residual_bias_edge=residual_bias_edge,
            residual_volatility=residual_volatility,
        )
        output.append(
            ShadowPick(
                season=season,
                week=week,
                home=home,
                away=away,
                pick_team=pick_team,
                opponent=opponent,
                confidence=confidence,
                edge=edge,
                handicap=_safe_float(record.get("handicap")),
                model_margin=_safe_float(record.get("model_margin")),
                outcome=outcome,
                profit=(
                    PAYOUT_WIN if outcome == "win" else PAYOUT_LOSS if outcome == "loss" else 0.0
                ),
                risk=PAYOUT_RISK,
                pool="CORE" if _is_core(record) else "NEAR_MISS",
                consensus_count=consensus_count,
                margin_dispersion=margin_dispersion,
                pressure_matchup_disadvantage=pressure,
                third_down_luck_support=third_down,
                residual_bias_edge=residual_bias_edge,
                residual_volatility=residual_volatility,
                shadow_score=score,
            )
        )
    return output


def _as_summary_rows(rows: list[ShadowPick]) -> list[Any]:
    # _summarize only needs season/week/home/away/outcome/profit/risk attributes.
    return list(rows)


def _summary(rows: list[ShadowPick]) -> dict[str, Any]:
    return _summarize(_as_summary_rows(rows))


def _split_summary(rows: list[ShadowPick], seasons: set[int]) -> str:
    selected = [row for row in rows if row.season in seasons]
    summary = _summary(selected)
    return (
        f"{summary['profit']:+.1f}u/{summary['bets']} "
        f"({summary['wins']}-{summary['losses']}-{summary['pushes']})"
    )


def _select_shadow_additions(
    near_miss: list[ShadowPick],
    *,
    min_score: float,
    top_per_season: int,
) -> list[ShadowPick]:
    selected: list[ShadowPick] = []
    for season in SEASONS:
        season_rows = [
            row for row in near_miss if row.season == season and row.shadow_score >= min_score
        ]
        selected.extend(
            sorted(season_rows, key=lambda row: row.shadow_score, reverse=True)[:top_per_season]
        )
    return selected


def write_gom_calibration_shadow_report(output_path: Path = DEFAULT_OUTPUT) -> Path:
    picks = build_shadow_picks(SEASONS)
    core = sorted([row for row in picks if row.pool == "CORE"], key=lambda row: row.shadow_score)
    near_miss = [row for row in picks if row.pool == "NEAR_MISS"]
    candidate_settings = [
        ("score>=1.25 top1/season", 1.25, 1),
        ("score>=1.00 top1/season", 1.00, 1),
        ("score>=0.75 top1/season", 0.75, 1),
        ("score>=1.00 top2/season", 1.00, 2),
    ]

    lines = [
        "# GOM Calibration Shadow Report",
        "",
        "CORE remains the official champion. This report tests whether a transparent shadow "
        "calibration score can add near-miss GOM picks without changing CORE.",
        "",
        "Near-miss pool:",
        "",
        "- variant D",
        "- tag GOM",
        "- week >= 3",
        "- abs(handicap) <= 8",
        "- outside CORE",
        "- confidence 80-84 with edge >= 3, or edge 3-4 with confidence >= 80, or cap8 extension",
        "",
        "Shadow score features:",
        "",
        "- confidence and edge",
        "- variant consensus count across B/C/D/J/K/M",
        "- model margin dispersion across variants",
        "- pressure matchup disadvantage",
        "- third-down luck support",
        "- prior residual bias and residual volatility",
        "",
        "## Summary",
        "",
        "| Strategy | Bets | W-L-P | Profit | ROI | Worst Season | Max DD | Train | "
        "Validation | Holdout |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    core_summary = _summary(core)
    lines.append(
        "| CORE | {bets} | {wins}-{losses}-{pushes} | {profit:+.1f}u | {roi:.1%} | "
        "{worst:+.1f}u | {dd:+.1f}u | {train} | {val} | {holdout} |".format(
            bets=core_summary["bets"],
            wins=core_summary["wins"],
            losses=core_summary["losses"],
            pushes=core_summary["pushes"],
            profit=core_summary["profit"],
            roi=core_summary["roi"],
            worst=core_summary["worst_season"],
            dd=core_summary["drawdown"],
            train=_split_summary(core, TRAIN_SEASONS),
            val=_split_summary(core, VALIDATION_SEASONS),
            holdout=_split_summary(core, HOLDOUT_SEASONS),
        )
    )
    near_miss_summary = _summary(near_miss)
    lines.append(
        "| NEAR-MISS POOL only | {bets} | {wins}-{losses}-{pushes} | {profit:+.1f}u | "
        "{roi:.1%} | {worst:+.1f}u | {dd:+.1f}u | {train} | {val} | {holdout} |".format(
            bets=near_miss_summary["bets"],
            wins=near_miss_summary["wins"],
            losses=near_miss_summary["losses"],
            pushes=near_miss_summary["pushes"],
            profit=near_miss_summary["profit"],
            roi=near_miss_summary["roi"],
            worst=near_miss_summary["worst_season"],
            dd=near_miss_summary["drawdown"],
            train=_split_summary(near_miss, TRAIN_SEASONS),
            val=_split_summary(near_miss, VALIDATION_SEASONS),
            holdout=_split_summary(near_miss, HOLDOUT_SEASONS),
        )
    )
    for label, min_score, top_per_season in candidate_settings:
        additions = _select_shadow_additions(
            near_miss,
            min_score=min_score,
            top_per_season=top_per_season,
        )
        combined = core + additions
        summary = _summary(combined)
        add_summary = _summary(additions)
        lines.append(
            "| CORE + {label} | {bets} | {wins}-{losses}-{pushes} | {profit:+.1f}u | "
            "{roi:.1%} | {worst:+.1f}u | {dd:+.1f}u | {train} | {val} | {holdout} |".format(
                label=label,
                bets=summary["bets"],
                wins=summary["wins"],
                losses=summary["losses"],
                pushes=summary["pushes"],
                profit=summary["profit"],
                roi=summary["roi"],
                worst=summary["worst_season"],
                dd=summary["drawdown"],
                train=_split_summary(additions, TRAIN_SEASONS),
                val=_split_summary(additions, VALIDATION_SEASONS),
                holdout=_split_summary(additions, HOLDOUT_SEASONS),
            )
        )
        lines.append(
            "| additions only | {bets} | {wins}-{losses}-{pushes} | {profit:+.1f}u | "
            "{roi:.1%} |  |  |  |  |  |".format(
                bets=add_summary["bets"],
                wins=add_summary["wins"],
                losses=add_summary["losses"],
                pushes=add_summary["pushes"],
                profit=add_summary["profit"],
                roi=add_summary["roi"],
            )
        )

    lines.extend(
        [
            "",
            "## Top Near-Miss Candidates By Shadow Score",
            "",
            "| Season | Week | Matchup | Pick | Score | C | Edge | H | Consensus | "
            "Dispersion | Pressure | ThirdDown | ResidBias | Vol | Outcome | Profit |",
            "|---:|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|",
        ]
    )
    for row in sorted(near_miss, key=lambda item: item.shadow_score, reverse=True)[:40]:
        lines.append(
            "| {season} | {week} | {away}@{home} | {pick} | {score:.2f} | {conf:.1f} | "
            "{edge:.1f} | {handicap:+.1f} | {consensus} | {disp:.2f} | {pressure} | "
            "{third} | {bias:+.2f} | {vol:.2f} | {outcome} | {profit:+.1f}u |".format(
                season=row.season,
                week=row.week,
                away=row.away,
                home=row.home,
                pick=row.pick_team,
                score=row.shadow_score,
                conf=row.confidence,
                edge=row.edge,
                handicap=row.handicap,
                consensus=row.consensus_count,
                disp=row.margin_dispersion,
                pressure=(
                    "n/a"
                    if row.pressure_matchup_disadvantage is None
                    else f"{row.pressure_matchup_disadvantage:.3f}"
                ),
                third=(
                    "n/a"
                    if row.third_down_luck_support is None
                    else f"{row.third_down_luck_support:.3f}"
                ),
                bias=row.residual_bias_edge,
                vol=row.residual_volatility,
                outcome=row.outcome,
                profit=row.profit,
            )
        )

    lines.extend(
        [
            "",
            "## Decision",
            "",
            "This is a shadow report only. Do not replace CORE unless a frozen rule improves "
            "out-of-sample performance and survives the 2026 forward test.",
        ]
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path
