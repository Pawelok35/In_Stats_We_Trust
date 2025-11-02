import polars as pl
import pytest

from utils.dataframes import preview_dataframe, read_parquet_or_raise


def test_read_parquet_or_raise_reads_file(tmp_path):
    target = tmp_path / "sample.parquet"
    pl.DataFrame({"a": [1]}).write_parquet(target)

    df = read_parquet_or_raise(target)
    assert df.shape == (1, 1)


def test_read_parquet_or_raise_missing(tmp_path):
    with pytest.raises(FileNotFoundError):
        read_parquet_or_raise(tmp_path / "missing.parquet")


def test_preview_dataframe_supports_sorting():
    df = pl.DataFrame(
        {
            "TEAM": ["B", "A", "C"],
            "metric": [0.2, 0.5, 0.1],
        }
    )

    preview = preview_dataframe(
        df,
        ["TEAM", "metric"],
        limit=2,
        sort_by=["metric"],
        descending=True,
    )

    assert len(preview) == 2
    assert preview[0]["TEAM"] == "A"
    assert preview[1]["TEAM"] == "B"
