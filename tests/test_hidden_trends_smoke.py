import polars as pl

from metrics.hidden_trends import compute


def test_hidden_trends_stub_returns_empty_dataframe():
    df = compute(
        df_l3=pl.DataFrame({"season": [2025], "week": [8], "TEAM": ["AAA"]}),
        df_l4_core=pl.DataFrame({"TEAM": ["AAA"]}),
    )
    assert isinstance(df, pl.DataFrame)
    assert df.is_empty()
