import polars as pl
import pytest

from utils.guards import check_no_inf, check_no_nan_in_keys


def test_check_no_nan_in_keys_passes_on_valid_keys():
    df = pl.DataFrame(
        {
            "season": [2025, 2025],
            "week": [8, 9],
            "identifier": ["A", "B"],
        }
    )

    # Should not raise.
    check_no_nan_in_keys(df, ["season", "week", "identifier"])


def test_check_no_nan_in_keys_missing_column():
    df = pl.DataFrame({"season": [2025]})

    with pytest.raises(ValueError, match="Key column 'week' not present"):
        check_no_nan_in_keys(df, ["season", "week"])


def test_check_no_nan_in_keys_detects_null():
    df = pl.DataFrame({"season": [2025, None], "week": [8, 8]})

    with pytest.raises(ValueError, match="NULL detected in key column 'season'"):
        check_no_nan_in_keys(df, ["season"])


def test_check_no_nan_in_keys_detects_nan():
    df = pl.DataFrame({"season": [2025.0, float("nan")], "week": [8, 9]})

    with pytest.raises(ValueError, match="NaN detected in key column 'season'"):
        check_no_nan_in_keys(df, ["season"])


def test_check_no_inf_raises_on_infinite_values():
    df = pl.DataFrame({"a": [1.0, float("inf")], "b": [1, 2]})

    with pytest.raises(ValueError, match="INF detected in column 'a'"):
        check_no_inf(df)


def test_check_no_inf_ignores_non_float_columns():
    df = pl.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})

    # Should not raise, no float columns.
    check_no_inf(df)
