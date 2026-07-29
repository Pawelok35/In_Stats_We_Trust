"""nfl_data_py schedule and betting-line synchronization."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import polars as pl
import yaml

from utils.config import load_settings
from utils.team_aliases import normalize_team_code


@dataclass(frozen=True)
class ScheduleSyncResult:
    season: int
    path: Path
    rows: int


@dataclass(frozen=True)
class LinesExportResult:
    season: int
    week: int
    path: Path
    games: int


@dataclass(frozen=True)
class ResultsSyncResult:
    season: int
    path: Path
    completed_games: int
    rows: int


def _import_nfl_data_py():
    try:
        import nfl_data_py as nfl  # type: ignore
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise RuntimeError(
            "nfl_data_py is required to sync schedules and lines. "
            "Install dependencies with python -m pip install -r requirements.txt."
        ) from exc
    return nfl


def _data_root(data_root: Path | None = None) -> Path:
    return data_root or Path(load_settings().data_root)


def sync_schedule_from_nfl(season: int, *, data_root: Path | None = None) -> ScheduleSyncResult:
    """Download the season schedule from nfl_data_py and store it as local parquet."""

    if season <= 0:
        raise ValueError("season must be a positive integer.")

    nfl = _import_nfl_data_py()
    schedule_pd = nfl.import_schedules([season])
    schedule = pl.from_pandas(schedule_pd, include_index=False)
    if schedule.is_empty():
        raise ValueError(f"nfl_data_py returned no schedule rows for season={season}.")

    root = _data_root(data_root)
    path = root / "schedules" / f"{season}.parquet"
    path.parent.mkdir(parents=True, exist_ok=True)
    schedule.write_parquet(path)
    return ScheduleSyncResult(season=season, path=path, rows=schedule.height)


def _load_schedule(season: int, *, data_root: Path | None = None) -> pl.DataFrame:
    path = _data_root(data_root) / "schedules" / f"{season}.parquet"
    if not path.exists():
        sync_schedule_from_nfl(season, data_root=data_root)
    return pl.read_parquet(path)


def _bool_from_optional(value: Any) -> bool:
    return bool(value) if value is not None else False


def _is_prime_time(gametime: Any) -> bool:
    if gametime is None:
        return False
    return str(gametime) >= "19:00"


def _required_float(row: dict[str, Any], key: str, *, matchup: str) -> float:
    value = row.get(key)
    if value is None:
        raise ValueError(f"Missing {key} for {matchup}.")
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid {key} for {matchup}: {value!r}") from exc


def export_week_lines_from_schedule(
    season: int,
    week: int,
    *,
    data_root: Path | None = None,
    output_path: Path | None = None,
    overwrite: bool = True,
) -> LinesExportResult:
    """Create config/lines/<season>/weekX_lines.yaml from nfl_data_py schedule lines.

    nfl_data_py's ``spread_line`` is stored from the away team's perspective. The
    existing matchup analyzer expects the home-team spread, so this exporter
    writes ``spread = -spread_line``.
    """

    if season <= 0 or week <= 0:
        raise ValueError("season and week must be positive integers.")

    schedule = _load_schedule(season, data_root=data_root)
    if "week" not in schedule.columns:
        raise ValueError(f"Schedule for season={season} has no 'week' column.")

    required = {"home_team", "away_team", "spread_line", "total_line"}
    missing = required - set(schedule.columns)
    if missing:
        raise ValueError(f"Schedule for season={season} is missing columns: {sorted(missing)}")

    week_df = schedule.filter(pl.col("week") == week).sort(["gameday", "gametime", "home_team"])
    if week_df.is_empty():
        raise ValueError(f"No schedule rows found for season={season} week={week}.")

    matchups: list[dict[str, Any]] = []
    for row in week_df.to_dicts():
        home = normalize_team_code(row["home_team"])
        away = normalize_team_code(row["away_team"])
        matchup = f"{away} @ {home}"
        away_spread = _required_float(row, "spread_line", matchup=matchup)
        total = _required_float(row, "total_line", matchup=matchup)
        matchups.append(
            {
                "report": f"data/reports/comparisons/{season}_w{week}/{home}_vs_{away}.md",
                "home": home,
                "away": away,
                "spread": round(-away_spread, 1),
                "total": round(total, 1),
                "prime_time": _is_prime_time(row.get("gametime")),
                "neutral_site": _bool_from_optional(row.get("location") == "Neutral"),
            }
        )

    out = output_path or Path("config") / "lines" / str(season) / f"week{week}_lines.yaml"
    if out.exists() and not overwrite:
        raise FileExistsError(f"Lines file already exists: {out}")
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "source": "nfl_data_py.import_schedules",
        "season": season,
        "week": week,
        "spread_convention": "home_team_spread",
        "matchups": matchups,
    }
    out.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return LinesExportResult(season=season, week=week, path=out, games=len(matchups))


def sync_results_from_nfl(season: int, *, data_root: Path | None = None) -> ResultsSyncResult:
    """Refresh the local schedule so final scores from nfl_data_py are available."""

    schedule_result = sync_schedule_from_nfl(season, data_root=data_root)
    schedule = pl.read_parquet(schedule_result.path)
    if {"home_score", "away_score"}.issubset(schedule.columns):
        completed = schedule.filter(
            pl.col("home_score").is_not_null() & pl.col("away_score").is_not_null()
        ).height
    else:
        completed = 0
    return ResultsSyncResult(
        season=season,
        path=schedule_result.path,
        completed_games=completed,
        rows=schedule_result.rows,
    )
