"""Single source of truth for application configuration."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from pydantic import BaseModel, Field, field_validator

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SETTINGS_PATH = PROJECT_ROOT / "config" / "settings.yaml"


def _coerce_path(value: Any) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (PROJECT_ROOT / path).resolve()


class FilesystemSourceSettings(BaseModel):
    """Configuration for filesystem-backed raw data sources."""

    l1_raw_dir: Path

    @field_validator("l1_raw_dir", mode="before")
    @classmethod
    def _normalize_dir(cls, value: Any) -> Path:
        return _coerce_path(value)


class DataSourcesSettings(BaseModel):
    """Data source selection and per-source configuration."""

    provider: str
    filesystem: FilesystemSourceSettings

    @field_validator("provider")
    @classmethod
    def _provider_not_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("data_sources.provider must not be empty")
        return value


class Settings(BaseModel):
    """Application-wide configuration validated via Pydantic."""

    data_root: Path = Field(..., alias="DATA_ROOT")
    default_season: int
    default_week: int
    data_sources: DataSourcesSettings
    weights: Dict[str, float]

    @field_validator("data_root", mode="before")
    @classmethod
    def _normalize_root(cls, value: Any) -> Path:
        return _coerce_path(value)

    @field_validator("default_season", "default_week")
    @classmethod
    def _positive_numbers(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("season and week defaults must be positive integers")
        return value

    @field_validator("weights")
    @classmethod
    def _weights_not_empty(cls, value: Dict[str, float]) -> Dict[str, float]:
        if not value:
            raise ValueError("weights mapping must not be empty")
        return value


@lru_cache(maxsize=1)
def _load_settings(resolved_path: Path) -> Settings:
    if not resolved_path.exists():
        raise FileNotFoundError(f"Settings file not found at {resolved_path}")

    with resolved_path.open("r", encoding="utf-8") as handle:
        payload: Optional[Dict[str, Any]] = yaml.safe_load(handle) or {}

    return Settings.model_validate(payload)


def load_settings(path: Optional[Path] = None, *, force_reload: bool = False) -> Settings:
    """Load validated settings, caching the result for subsequent calls."""

    settings_path = (path or DEFAULT_SETTINGS_PATH).resolve()

    if force_reload:
        _load_settings.cache_clear()

    return _load_settings(settings_path)
