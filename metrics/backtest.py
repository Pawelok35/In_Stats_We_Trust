"""Backtesting helpers for model pick JSONL outputs."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable, Optional

import polars as pl

from utils.contracts import validate_df
from utils.team_aliases import normalize_team_code

DEFAULT_WIN_UNITS = 100 / 110
DEFAULT_LOSS_UNITS = -1.0

ResultKey = tuple[int, str, str]

PICK_CONTRACT_COLUMNS = [
    "season",
    "week",
    "home",
    "away",
    "tag",
    "model_winner",
    "confidence",
    "handicap",
]


def load_picks(
    picks_dir: Path,
    season: int,
    from_week: Optional[int] = None,
    to_week: Optional[int] = None,
) -> list[dict[str, Any]]:
    """Load pick records for one season from `week_*.jsonl` files."""

    season_dir = picks_dir / str(season)
    if not season_dir.exists():
        raise FileNotFoundError(f"Pick directory does not exist: {season_dir}")

    records: list[dict[str, Any]] = []
    for path in sorted(season_dir.glob("week_*.jsonl")):
        week = int(path.stem.split("_")[1])
        if from_week is not None and week < from_week:
            continue
        if to_week is not None and week > to_week:
            continue

        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON in {path}:{line_no}: {exc}") from exc
            records.append(record)
    validate_pick_records(records)
    return records


def validate_pick_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Validate pick records against the configured PICK_OUTPUT contract."""

    if not records:
        return records

    missing: dict[int, list[str]] = {}
    for index, record in enumerate(records):
        absent = [field for field in PICK_CONTRACT_COLUMNS if field not in record]
        if absent:
            missing[index] = absent
    if missing:
        first_index = next(iter(missing))
        fields = ", ".join(missing[first_index])
        raise ValueError(f"[PICK_OUTPUT] record {first_index} missing required fields: {fields}")

    df = pl.DataFrame(
        {
            "season": [int(record["season"]) for record in records],
            "week": [int(record["week"]) for record in records],
            "home": [normalize_team_code(record["home"]) for record in records],
            "away": [normalize_team_code(record["away"]) for record in records],
            "tag": [str(record["tag"]).upper() for record in records],
            "model_winner": [normalize_team_code(record["model_winner"]) for record in records],
            "confidence": [float(record["confidence"]) for record in records],
            "handicap": [float(record["handicap"]) for record in records],
        }
    )
    validate_df(df, "PICK_OUTPUT")
    return records


def load_manual_results(
    path: Optional[Path],
    season: Optional[int] = None,
) -> dict[ResultKey, dict[str, Any]]:
    """Load manual result overrides from JSONL."""

    if path is None or not path.exists():
        return {}

    results: dict[ResultKey, dict[str, Any]] = {}
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in {path}:{line_no}: {exc}") from exc

        record_season = int(record["season"])
        if season is not None and record_season != season:
            continue

        week = int(record["week"])
        home = normalize_team_code(record["home_team"])
        away = normalize_team_code(record["away_team"])
        results[(week, home, away)] = {
            "home_score": record.get("home_score"),
            "away_score": record.get("away_score"),
        }
    return results


def load_schedule_results(data_root: Path, season: int) -> dict[ResultKey, dict[str, Any]]:
    """Load results from a local schedule parquet when available."""

    candidates = [
        data_root / "schedules" / f"{season}.parquet",
        data_root / "schedule" / f"{season}.parquet",
    ]
    schedule_path = next((path for path in candidates if path.exists()), None)
    if schedule_path is None:
        return {}

    df = pl.read_parquet(schedule_path)
    if "game_type" in df.columns:
        df = df.filter(pl.col("game_type") == "REG")

    results: dict[ResultKey, dict[str, Any]] = {}
    for row in df.to_dicts():
        week = int(row["week"])
        home = normalize_team_code(row.get("home_team") or row.get("team_a") or row.get("TEAM"))
        away = normalize_team_code(row.get("away_team") or row.get("team_b") or row.get("OPP"))
        if not home or not away:
            continue
        results[(week, home, away)] = {
            "home_score": row.get("home_score"),
            "away_score": row.get("away_score"),
        }
    return results


def load_results(
    data_root: Path,
    season: int,
    manual_results: Optional[Path] = None,
) -> dict[ResultKey, dict[str, Any]]:
    """Load schedule results and apply manual overrides."""

    results = load_schedule_results(data_root, season)
    results.update(load_manual_results(manual_results, season=season))
    return results


def confidence_bucket(confidence: Any, bucket_size: int = 10) -> str:
    """Return a stable text bucket for confidence values."""

    try:
        value = float(confidence)
    except (TypeError, ValueError):
        return "unknown"

    lower = int(value // bucket_size) * bucket_size
    upper = lower + bucket_size
    return f"{lower}-{upper}"


def grade_pick(pick: dict[str, Any], results: dict[ResultKey, dict[str, Any]]) -> dict[str, Any]:
    """Grade one pick against final scores."""

    week = int(pick["week"])
    home = normalize_team_code(pick["home"])
    away = normalize_team_code(pick["away"])
    result = results.get((week, home, away))

    base = {
        "season": int(pick.get("season", 0)),
        "week": week,
        "home": home,
        "away": away,
        "tag": str(pick.get("tag", "UNKNOWN")).upper(),
        "model_winner": normalize_team_code(pick.get("model_winner")),
        "confidence": pick.get("confidence"),
        "confidence_bucket": confidence_bucket(pick.get("confidence")),
        "edge_vs_line": pick.get("edge_vs_line"),
        "handicap": pick.get("handicap"),
        "outcome": "pending",
        "ats_margin": None,
        "profit_units": 0.0,
        "risk_units": 0.0,
    }

    if result is None or result.get("home_score") is None or result.get("away_score") is None:
        return base

    home_score = result["home_score"]
    away_score = result["away_score"]
    if _is_null_score(home_score) or _is_null_score(away_score):
        return base

    home_score_int = int(home_score)
    away_score_int = int(away_score)
    model_winner = base["model_winner"]
    if model_winner == home:
        pick_margin = home_score_int - away_score_int
    elif model_winner == away:
        pick_margin = away_score_int - home_score_int
    else:
        return base

    handicap = float(pick.get("handicap", 0.0))
    ats_margin = pick_margin + handicap
    base["ats_margin"] = ats_margin
    base["risk_units"] = 1.0

    if ats_margin > 0:
        base["outcome"] = "win"
        base["profit_units"] = DEFAULT_WIN_UNITS
    elif ats_margin < 0:
        base["outcome"] = "loss"
        base["profit_units"] = DEFAULT_LOSS_UNITS
    else:
        base["outcome"] = "push"
        base["profit_units"] = 0.0
    return base


def backtest_picks(
    picks: Iterable[dict[str, Any]],
    results: dict[ResultKey, dict[str, Any]],
    tags: Optional[set[str]] = None,
) -> list[dict[str, Any]]:
    """Grade all picks, optionally filtering to a set of tags."""

    tag_filter = {tag.upper() for tag in tags} if tags else None
    rows: list[dict[str, Any]] = []
    for pick in picks:
        tag = str(pick.get("tag", "UNKNOWN")).upper()
        if tag_filter and tag not in tag_filter:
            continue
        rows.append(grade_pick(pick, results))
    return rows


def summarize(rows: Iterable[dict[str, Any]], group_by: str = "tag") -> list[dict[str, Any]]:
    """Summarize graded picks by one row key."""

    grouped: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            group_by: "",
            "wins": 0,
            "losses": 0,
            "pushes": 0,
            "pending": 0,
            "graded": 0,
            "risk_units": 0.0,
            "profit_units": 0.0,
        }
    )
    for row in rows:
        key = str(row.get(group_by) or "unknown")
        item = grouped[key]
        item[group_by] = key
        outcome = row["outcome"]
        if outcome == "win":
            item["wins"] += 1
            item["graded"] += 1
        elif outcome == "loss":
            item["losses"] += 1
            item["graded"] += 1
        elif outcome == "push":
            item["pushes"] += 1
            item["graded"] += 1
        else:
            item["pending"] += 1
        item["risk_units"] += float(row.get("risk_units") or 0.0)
        item["profit_units"] += float(row.get("profit_units") or 0.0)

    summary = []
    for item in grouped.values():
        decisions = item["wins"] + item["losses"]
        risk = item["risk_units"]
        item["win_rate"] = item["wins"] / decisions if decisions else 0.0
        item["roi"] = item["profit_units"] / risk if risk else 0.0
        summary.append(item)

    return sorted(summary, key=lambda row: str(row[group_by]))


def format_summary_table(summary: Iterable[dict[str, Any]], label: str = "tag") -> str:
    """Format a concise text table for CLI output."""

    lines = [
        f"{label:<16} {'W':>4} {'L':>4} {'P':>4} {'Pend':>5} "
        f"{'Win%':>7} {'Units':>8} {'ROI':>7}"
    ]
    lines.append("-" * len(lines[0]))
    for row in summary:
        lines.append(
            f"{str(row[label]):<16} "
            f"{int(row['wins']):>4} "
            f"{int(row['losses']):>4} "
            f"{int(row['pushes']):>4} "
            f"{int(row['pending']):>5} "
            f"{row['win_rate'] * 100:>6.1f}% "
            f"{row['profit_units']:>+8.2f} "
            f"{row['roi'] * 100:>6.1f}%"
        )
    return "\n".join(lines)


def _is_null_score(value: Any) -> bool:
    return value != value
