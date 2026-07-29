"""Data providers for durable Live Scenario datasets."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import pandas as pd


class LiveScenarioDataProvider(Protocol):
    source_name: str
    source_version: str

    def load_pbp(self, seasons: list[int]) -> pd.DataFrame:
        """Load play-by-play rows for the requested seasons."""

    def load_schedules(self, seasons: list[int]) -> pd.DataFrame:
        """Load schedules for the requested seasons."""


def _to_pandas(frame) -> pd.DataFrame:
    if isinstance(frame, pd.DataFrame):
        return frame
    if hasattr(frame, "to_pandas"):
        return frame.to_pandas()
    raise TypeError(f"Unsupported nflreadpy frame type: {type(frame)!r}")


@dataclass(frozen=True)
class NflreadpyDataProvider:
    source_name: str = "nflreadpy"
    source_version: str = "unknown"

    def __post_init__(self) -> None:
        try:
            import nflreadpy as nfl  # noqa: F401
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "nflreadpy is required for Live Scenario data sync. "
                "Install it with: python -m pip install nflreadpy"
            ) from exc

        import nflreadpy as nfl

        object.__setattr__(self, "source_version", getattr(nfl, "__version__", "unknown"))

    def load_pbp(self, seasons: list[int]) -> pd.DataFrame:
        import nflreadpy as nfl

        return _to_pandas(nfl.load_pbp(seasons))

    def load_schedules(self, seasons: list[int]) -> pd.DataFrame:
        import nflreadpy as nfl

        return _to_pandas(nfl.load_schedules(seasons))


def raw_pbp_path(data_root: Path, season: int) -> Path:
    return data_root / "nflverse" / "raw" / "pbp" / f"play_by_play_{season}.parquet"


def raw_schedules_path(data_root: Path) -> Path:
    return data_root / "nflverse" / "raw" / "schedules" / "schedules.parquet"


def processed_dataset_path(data_root: Path) -> Path:
    return data_root / "live_scenario" / "processed" / "team_game_scenario_rows.parquet"


def live_scenario_manifest_path(data_root: Path) -> Path:
    return data_root / "live_scenario" / "manifest.json"


def load_raw_pbp(data_root: Path, seasons: list[int]) -> pd.DataFrame:
    frames = []
    for season in seasons:
        path = raw_pbp_path(data_root, season)
        if path.exists():
            frames.append(pd.read_parquet(path))
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def load_raw_schedules(data_root: Path) -> pd.DataFrame:
    path = raw_schedules_path(data_root)
    if not path.exists():
        return pd.DataFrame()
    return pd.read_parquet(path)
