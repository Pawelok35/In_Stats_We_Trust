"""Schema contracts and validation utilities for data processing layers."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Dict, Iterable, Tuple

import polars as pl
import yaml

from utils.logging import get_logger

logger = get_logger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONTRACTS_PATH = PROJECT_ROOT / "config" / "contracts.yaml"

# Supported dtype aliases mapped to Polars dtypes.
_DTYPE_ALIASES: Dict[str, pl.DataType] = {
    "Int8": pl.Int8,
    "Int16": pl.Int16,
    "Int32": pl.Int32,
    "Int64": pl.Int64,
    "UInt8": pl.UInt8,
    "UInt16": pl.UInt16,
    "UInt32": pl.UInt32,
    "UInt64": pl.UInt64,
    "Float32": pl.Float32,
    "Float64": pl.Float64,
    "Boolean": pl.Boolean,
    "Utf8": pl.Utf8,
    "Datetime": pl.Datetime,
    "Date": pl.Date,
}


@dataclass(frozen=True)
class ColumnSpec:
    """Specification for a single column in a schema contract."""

    name: str
    dtype: pl.DataType
    optional: bool = False


@dataclass(frozen=True)
class ContractSpec:
    """Normalized representation of a contract definition."""

    name: str
    columns: Tuple[ColumnSpec, ...]
    keys: Tuple[str, ...]
    description: str | None = None


def _coerce_path(path: Path | None) -> Path:
    if path is None:
        return DEFAULT_CONTRACTS_PATH
    resolved = path if path.is_absolute() else PROJECT_ROOT / path
    return resolved.resolve()


def _parse_colspec(raw: str, contract_name: str) -> ColumnSpec:
    if ":" not in raw:
        raise ValueError(f"[{contract_name}] column spec missing dtype delimiter ':' -> {raw!r}")

    name_part, dtype_part = raw.split(":", 1)
    name = name_part.strip()
    if not name:
        raise ValueError(f"[{contract_name}] column spec missing column name -> {raw!r}")

    optional = dtype_part.endswith("?")
    dtype_name = dtype_part.rstrip("?").strip()
    if not dtype_name:
        raise ValueError(f"[{contract_name}] column spec missing dtype -> {raw!r}")

    try:
        dtype = _DTYPE_ALIASES[dtype_name]
    except KeyError as exc:
        raise ValueError(f"[{contract_name}] unsupported dtype alias '{dtype_name}'") from exc

    return ColumnSpec(name=name, dtype=dtype, optional=optional)


@lru_cache(maxsize=1)
def _load_contracts(path: Path) -> Dict[str, ContractSpec]:
    if not path.exists():
        raise FileNotFoundError(f"Contract configuration not found at {path}")

    with path.open("r", encoding="utf-8") as handle:
        raw_payload = yaml.safe_load(handle) or {}

    contracts: Dict[str, ContractSpec] = {}
    for name, payload in raw_payload.items():
        required_columns = payload.get("required_columns", [])
        if not isinstance(required_columns, Iterable):
            raise TypeError(f"[{name}] required_columns must be an iterable")

        columns = tuple(_parse_colspec(col, name) for col in required_columns)
        keys_raw = payload.get("keys", [])
        if not isinstance(keys_raw, Iterable):
            raise TypeError(f"[{name}] keys must be an iterable")

        keys = tuple(str(k) for k in keys_raw)

        description = payload.get("description")
        contracts[name] = ContractSpec(
            name=name,
            columns=columns,
            keys=keys,
            description=str(description) if description is not None else None,
        )

    if not contracts:
        raise ValueError(f"No contracts defined in {path}")

    logger.debug("Loaded %s contract definitions from %s", len(contracts), path)
    return contracts


def get_contract(name: str, *, path: Path | None = None) -> ContractSpec:
    """Return the parsed contract specification for the requested name."""

    resolved = _coerce_path(path)
    contracts = _load_contracts(resolved)
    try:
        return contracts[name]
    except KeyError as exc:
        available = ", ".join(sorted(contracts))
        raise KeyError(f"Unknown contract '{name}'. Available: {available}") from exc


def _dtype_matches(expected: pl.DataType, actual: pl.DataType) -> bool:
    if expected == actual:
        return True

    # Allow narrower integers to satisfy a wider integer contract.
    if expected in {pl.Int64, pl.Int32, pl.Int16, pl.Int8}:
        return actual in {
            pl.Int64,
            pl.Int32,
            pl.Int16,
            pl.Int8,
            pl.UInt8,
            pl.UInt16,
            pl.UInt32,
            pl.UInt64,
        }

    if expected in {pl.Float64, pl.Float32}:
        return actual in {pl.Float64, pl.Float32}

    return False


def validate_df(
    df: pl.DataFrame,
    contract_name: str,
    *,
    path: Path | None = None,
) -> pl.DataFrame:
    """Validate a Polars DataFrame against a named schema contract.

    Parameters
    ----------
    df:
        DataFrame to validate.
    contract_name:
        Name of the contract defined under ``config/contracts.yaml``.
    path:
        Optional path override for an alternative contract configuration file.

    Returns
    -------
    pl.DataFrame
        The original dataframe, allowing validation to be chained fluently.

    Raises
    ------
    TypeError
        If ``df`` is not a Polars DataFrame.
    ValueError
        If validation fails.
    """

    if not isinstance(df, pl.DataFrame):
        raise TypeError("validate_df expects a polars.DataFrame instance")

    contract = get_contract(contract_name, path=path)
    schema = df.schema

    missing_columns = [
        spec.name for spec in contract.columns if not spec.optional and spec.name not in schema
    ]
    if missing_columns:
        missing = ", ".join(missing_columns)
        raise ValueError(f"[{contract_name}] missing required columns: {missing}")

    for spec in contract.columns:
        if spec.name not in schema:
            continue

        actual_dtype = schema[spec.name]
        if not _dtype_matches(spec.dtype, actual_dtype):
            raise ValueError(
                f"[{contract_name}] column '{spec.name}' has dtype {actual_dtype}, "
                f"expected {spec.dtype}"
            )

    missing_keys = [key for key in contract.keys if key not in schema]
    if missing_keys:
        missing = ", ".join(missing_keys)
        raise ValueError(f"[{contract_name}] missing key columns: {missing}")

    logger.debug(
        "[%s] validation successful (rows=%s, cols=%s)",
        contract_name,
        df.height,
        df.width,
    )
    return df


def list_contracts(*, path: Path | None = None) -> Tuple[str, ...]:
    """Return the names of all available contracts."""

    resolved = _coerce_path(path)
    return tuple(sorted(_load_contracts(resolved)))
