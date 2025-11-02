"""nfl_data_py-backed source loader for L1 ingestion.

Ten provider robi dwie rzeczy:
1. pobiera play-by-play z nfl_data_py dla całego sezonu,
2. odfiltrowuje tydzień,
3. konwertuje pandas -> polars,
4. zapisuje surowy parquet do data/sources/nfl/<season>/<season>_<week>.parquet,
5. zwraca polars.DataFrame (tydzień), żeby reszta pipeline'u mogła pracować normalnie.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import polars as pl

from utils.logging import get_logger

logger = get_logger(__name__)


def _import_nfl_data_py():
    """Lazy import żeby nie crashować na starcie kiedy pakiet nie jest zainstalowany."""
    try:
        import nfl_data_py  # type: ignore
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise RuntimeError(
            "Provider 'nfl_data_py' requires the nfl_data_py package. "
            "Install it or switch settings.data_sources.provider to 'filesystem'."
        ) from exc
    return nfl_data_py


def _ensure_season_dir(season: int) -> Path:
    """
    Upewnij się że istnieje katalog:
    data/sources/nfl/<season>/
    Zwróć Path do tego katalogu.
    """
    season_dir = Path("data") / "sources" / "nfl" / str(season)
    season_dir.mkdir(parents=True, exist_ok=True)
    return season_dir


def _target_path(season: int, week: int) -> Path:
    """
    Ścieżka gdzie zapisujemy surowy parquet:
    data/sources/nfl/<season>/<season>_<week>.parquet
    """
    season_dir = _ensure_season_dir(season)
    filename = f"{season}_{week}.parquet"
    return season_dir / filename


def _write_raw_parquet(df_week_pl: pl.DataFrame, season: int, week: int) -> Path:
    """
    Zapisz tygodniowy wycinek danych jako parquet do naszego archiwum.
    """
    out_path = _target_path(season, week)

    if df_week_pl.is_empty():
        logger.warning(
            "Attempting to write EMPTY weekly dataframe for season=%s week=%s to %s",
            season,
            week,
            out_path,
        )

    df_week_pl.write_parquet(out_path)
    logger.info("Wrote raw weekly parquet to %s", out_path)
    return out_path


def load_week(season: int, week: int) -> pl.DataFrame:
    """
    Publiczna funkcja używana przez L1 ingest przy provider='nfl_data_py'.

    Zwraca Polars DataFrame z danymi tylko dla (season, week).
    Po drodze zapisuje też data/sources/nfl/<season>/<season>_<week>.parquet
    żebyśmy mieli archiwum i powtarzalność.

    Dane wejściowe pochodzą z nfl_data_py.import_pbp_data([season]),
    potem filtrujemy df["week"] == week.
    """

    nfl_data_py = _import_nfl_data_py()

    logger.info(
        "Downloading nfl_data_py play-by-play for season=%s, will filter week=%s",
        season,
        week,
    )

    # pełny sezon jako pandas.DataFrame
    pbp = nfl_data_py.import_pbp_data([season])  # type: ignore[attr-defined]

    # filtrujemy na jeden tydzień
    filtered = pbp[(pbp["season"] == season) & (pbp["week"] == week)]
    if filtered.empty:
        logger.warning(
            "nfl_data_py returned no rows for season=%s week=%s",
            season,
            week,
        )

    # konwersja pandas -> polars
    df_week_pl = pl.from_pandas(filtered, include_index=False)

    # zapis surowego parquet do katalogu źródeł
    _write_raw_parquet(df_week_pl, season, week)

    # zwracamy polars DF do dalszej obróbki w pipeline L1->L2->L3->L4
    return df_week_pl
