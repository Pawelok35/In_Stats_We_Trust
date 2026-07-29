from pathlib import Path

import polars as pl

from app import reports


def test_week1_form_uses_preseason_rolling_seed(tmp_path: Path, monkeypatch):
    seed = tmp_path / "through_1.parquet"
    pl.DataFrame(
        {
            "TEAM": ["LA", "SF"],
            "core_points_per_drive_diff": [1.01, 0.44],
        }
    ).write_parquet(seed)
    monkeypatch.setattr(reports, "rolling_core12_through_path", lambda season, week: str(seed))

    table = reports._metric_form_table(
        2026,
        1,
        "LA",
        "SF",
        column_name="core_points_per_drive_diff",
        as_percent=False,
    )

    assert "_No data available yet._" not in table
    assert "| LA | 1.010 | 1.010 | 1.010 |" in table
    assert "| SF | 0.440 | 0.440 | 0.440 |" in table
