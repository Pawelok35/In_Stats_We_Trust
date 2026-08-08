"""Local week-game selector helpers for Live Scenario GUI."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


class ScheduleLoadError(RuntimeError):
    """Raised when current-week schedule cannot be loaded."""


@dataclass(frozen=True)
class WeekGamePerspective:
    team: str
    opponent: str
    side: str
    spread: float | None
    role: str


@dataclass(frozen=True)
class WeekGame:
    game_id: str
    season: int
    week: int
    away: str
    home: str
    game_date: str
    game_time: str
    neutral_site: bool | None
    spread_line: float | None
    spread_source: str
    spread_status: str
    schedule_source: str
    schedule_timestamp_utc: str
    model_status: str
    model_tag: str | None
    model_selected_team: str | None
    model_edge: float | None
    model_margin: float | None

    @property
    def label(self) -> str:
        return f"{self.away} @ {self.home}"

    def perspective(self, team: str) -> WeekGamePerspective:
        selected = team.strip().upper()
        if selected not in {self.away, self.home}:
            raise ValueError(f"Perspective team {team!r} is not in {self.away} @ {self.home}")
        side = "away" if selected == self.away else "home"
        opponent = self.home if side == "away" else self.away
        spread = perspective_spread(self.spread_line, side)
        return WeekGamePerspective(
            team=selected,
            opponent=opponent,
            side=side,
            spread=spread,
            role=spread_role(spread),
        )


def local_schedule_candidates(
    data_root: Path, season: int, season_type: str = "REG"
) -> list[Path]:
    schedule_type = _normalize_season_type(season_type)
    if schedule_type == "PRE":
        return [
            data_root / "nflverse" / "raw" / "schedules" / f"schedules_{season}_pre.parquet",
            data_root / "schedules" / f"{season}_pre.parquet",
            data_root / "schedules" / f"{season}_pre.csv",
            data_root / "nflverse" / "raw" / "schedules" / "schedules.parquet",
        ]
    return [
        season_schedule_snapshot_path(data_root, season),
        data_root / "schedules" / f"{season}.parquet",
        data_root / "nflverse" / "raw" / "schedules" / "schedules.parquet",
    ]


def season_schedule_snapshot_path(
    data_root: Path, season: int, season_type: str = "REG"
) -> Path:
    if _normalize_season_type(season_type) == "PRE":
        return data_root / "nflverse" / "raw" / "schedules" / f"schedules_{season}_pre.parquet"
    return data_root / "nflverse" / "raw" / "schedules" / f"schedules_{season}.parquet"


def load_week_games(
    data_root: Path,
    season: int,
    week: int,
    picks_path: Path | None = None,
    refresh_if_missing: bool = True,
    refresh_provider: Any | None = None,
    season_type: str = "REG",
) -> tuple[list[WeekGame], dict[str, Any]]:
    data_root = Path(data_root)
    schedule_type = _normalize_season_type(season_type)
    refresh_error = None
    if refresh_if_missing and not _local_current_schedule_contains_season(
        data_root, season, schedule_type
    ):
        try:
            _refresh_schedule_from_nflreadpy(
                data_root=data_root,
                season=season,
                provider=refresh_provider,
                season_type=schedule_type,
            )
        except Exception as exc:
            refresh_error = exc

    schedule, source_path, diagnostics = _load_local_schedule(
        data_root, season, week, schedule_type
    )
    if schedule.empty and refresh_error is not None:
        raise ScheduleLoadError(f"Schedule refresh failed: {refresh_error}") from refresh_error

    picks = _load_pick_metadata(picks_path)
    games = [
        _row_to_week_game(row, source_path=source_path, picks=picks)
        for _, row in schedule.iterrows()
    ]
    metadata = {
        "season": season,
        "week": week,
        "season_type": schedule_type,
        "games_found": len(games),
        "schedule_source": str(source_path) if source_path else "MISSING",
        "schedule_timestamp_utc": _path_timestamp_utc(source_path) if source_path else None,
        "picks_path": str(picks_path) if picks_path else None,
        "refresh_error": str(refresh_error) if refresh_error else None,
        "diagnostics": diagnostics,
    }
    return games, metadata


def perspective_spread(spread_line: float | None, side: str) -> float | None:
    if spread_line is None:
        return None
    return spread_line if side == "away" else -spread_line


def spread_role(spread: float | None) -> str:
    if spread is None:
        return "PICKEM_OR_UNKNOWN"
    if spread < 0:
        return "FAVORITE"
    if spread > 0:
        return "UNDERDOG"
    return "PICKEM_OR_UNKNOWN"


def invert_score_pair(raw: str) -> str:
    text = (raw or "").strip()
    if not text:
        return ""
    separator = "-" if "-" in text else ":"
    parts = [part.strip() for part in text.split(separator)]
    if len(parts) != 2:
        return raw
    return f"{parts[1]}-{parts[0]}"


def game_key(away: str, home: str) -> str:
    return f"{away.upper()}@{home.upper()}"


def label_for_active_pick(record: dict, games: dict[str, WeekGame]) -> str | None:
    away = str(record.get("away") or "").upper()
    home = str(record.get("home") or "").upper()
    label = f"{away} @ {home}"
    return label if label in games else None


def _load_local_schedule(
    data_root: Path,
    season: int,
    week: int,
    season_type: str = "REG",
) -> tuple[pd.DataFrame, Path | None, dict[str, Any]]:
    diagnostics = {"sources_checked": []}
    schedule_type = _normalize_season_type(season_type)
    for path in local_schedule_candidates(data_root, season, schedule_type):
        source_diag: dict[str, Any] = {"path": str(path), "exists": path.exists()}
        if not path.exists():
            diagnostics["sources_checked"].append(source_diag)
            continue
        frame = _read_schedule_frame(path)
        source_diag["rows_loaded"] = len(frame)
        source_diag["seasons"] = _seasons_present(frame)
        if frame.empty:
            diagnostics["sources_checked"].append(source_diag)
            continue
        season_rows = frame
        if "season" in frame.columns:
            season_rows = frame[frame["season"].astype("Int64") == season]
        source_diag["after_season"] = len(season_rows)
        week_rows = season_rows
        if "week" in week_rows.columns:
            week_rows = week_rows[week_rows["week"].astype("Int64") == week]
        source_diag["after_week"] = len(week_rows)
        typed_rows = week_rows
        if "game_type" in typed_rows.columns:
            matches_type = (
                typed_rows["game_type"].fillna("REG").astype(str).str.upper()
                == schedule_type
            )
            typed_rows = typed_rows[matches_type]
        source_diag[f"after_{schedule_type.lower()}"] = len(typed_rows)
        diagnostics["sources_checked"].append(source_diag)
        if typed_rows.empty:
            continue
        sorted_rows = typed_rows.sort_values(["gameday", "gametime", "away_team", "home_team"])
        return sorted_rows, path, diagnostics
    return pd.DataFrame(), None, diagnostics


def _local_current_schedule_contains_season(
    data_root: Path, season: int, season_type: str = "REG"
) -> bool:
    schedule_type = _normalize_season_type(season_type)
    for path in local_schedule_candidates(data_root, season, schedule_type):
        if _source_contains_season(path, season, schedule_type):
            return True
    return False


def _source_contains_season(path: Path, season: int, season_type: str = "REG") -> bool:
    if not path.exists():
        return False
    try:
        frame = _read_schedule_frame(path, columns=["season", "game_type"])
    except Exception:
        return False
    if frame.empty or "season" not in frame.columns:
        return False
    if season not in set(frame["season"].dropna().astype(int).tolist()):
        return False
    if "game_type" not in frame.columns:
        return _normalize_season_type(season_type) == "REG"
    return _normalize_season_type(season_type) in set(
        frame["game_type"].fillna("REG").astype(str).str.upper()
    )


def _refresh_schedule_from_nflreadpy(
    *,
    data_root: Path,
    season: int,
    provider: Any | None = None,
    season_type: str = "REG",
) -> Path:
    nfl = provider
    if nfl is None:
        import nflreadpy as nfl  # type: ignore[no-redef]

    frame = nfl.load_schedules([season])
    if hasattr(frame, "to_pandas"):
        frame = frame.to_pandas()
    elif not isinstance(frame, pd.DataFrame):
        frame = pd.DataFrame(frame)
    if frame.empty:
        raise ScheduleLoadError(f"nflreadpy returned no schedule rows for season {season}.")
    schedule_type = _normalize_season_type(season_type)
    if "game_type" in frame.columns:
        frame = frame[frame["game_type"].fillna("REG").astype(str).str.upper() == schedule_type]
    if frame.empty:
        raise ScheduleLoadError(
            f"nflreadpy returned no {schedule_type} schedule rows for season {season}."
        )
    path = season_schedule_snapshot_path(data_root, season, schedule_type)
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(path, index=False)
    return path


def _normalize_season_type(value: str) -> str:
    normalized = str(value or "REG").strip().upper()
    aliases = {"REGULAR": "REG", "REGULAR_SEASON": "REG", "PRESEASON": "PRE"}
    normalized = aliases.get(normalized, normalized)
    if normalized not in {"REG", "PRE"}:
        raise ValueError("season_type must be REG or PRE")
    return normalized


def _read_schedule_frame(path: Path, columns: list[str] | None = None) -> pd.DataFrame:
    if path.suffix.lower() == ".csv":
        frame = pd.read_csv(path, usecols=columns)
    else:
        frame = pd.read_parquet(path, columns=columns)
    return frame


def _seasons_present(frame: pd.DataFrame) -> list[int]:
    if frame.empty or "season" not in frame.columns:
        return []
    return sorted(frame["season"].dropna().astype(int).unique().tolist())


def _load_pick_metadata(path: Path | None) -> dict[str, dict[str, Any]]:
    if path is None or not path.exists():
        return {}
    records: dict[str, dict[str, Any]] = {}
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            away = str(row.get("away") or "").upper()
            home = str(row.get("home") or "").upper()
            if away and home:
                records[game_key(away, home)] = row
    return records


def _row_to_week_game(
    row: pd.Series,
    *,
    source_path: Path | None,
    picks: dict[str, dict],
) -> WeekGame:
    away = str(row.get("away_team") or row.get("away") or "").upper()
    home = str(row.get("home_team") or row.get("home") or "").upper()
    pick = picks.get(game_key(away, home), {})
    tag = _clean_str(pick.get("tag"))
    selected = _clean_str(pick.get("model_winner"))
    model_status = _model_status(tag, selected)
    spread_line = _float_or_none(row.get("spread_line"))
    fallback_game_id = f"{row.get('season')}_w{int(row.get('week')):02d}_{away}_at_{home}"
    return WeekGame(
        game_id=_clean_str(row.get("game_id")) or fallback_game_id,
        season=int(row.get("season")),
        week=int(row.get("week")),
        away=away,
        home=home,
        game_date=_clean_str(row.get("gameday")),
        game_time=_clean_str(row.get("gametime")),
        neutral_site=_neutral_status(row),
        spread_line=spread_line,
        spread_source="local_schedule.spread_line" if spread_line is not None else "local_schedule",
        spread_status="AVAILABLE" if spread_line is not None else "MISSING",
        schedule_source=str(source_path) if source_path else "MISSING",
        schedule_timestamp_utc=_path_timestamp_utc(source_path) if source_path else "",
        model_status=model_status,
        model_tag=tag or None,
        model_selected_team=selected or None,
        model_edge=_float_or_none(pick.get("edge_vs_line")),
        model_margin=_float_or_none(pick.get("model_margin")),
    )


def _model_status(tag: str, selected: str) -> str:
    if not tag and not selected:
        return "NO MODEL PICK"
    if tag == "NEUTRAL":
        return "NEUTRAL / NO ACTION"
    return f"MODEL PICK: {selected} / {tag}" if selected and tag else "MODEL PICK"


def _neutral_status(row: pd.Series) -> bool | None:
    location = _clean_str(row.get("location")).upper()
    if location == "NEUTRAL":
        return True
    if location:
        return False
    return None


def _float_or_none(value: Any) -> float | None:
    try:
        if value is None or pd.isna(value):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _clean_str(value: Any) -> str:
    if value is None or pd.isna(value):
        return ""
    return str(value).strip()


def _path_timestamp_utc(path: Path | None) -> str:
    if path is None or not path.exists():
        return ""
    return (
        datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
        .replace(microsecond=0)
        .isoformat()
    )
