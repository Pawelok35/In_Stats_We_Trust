import polars as pl
from fastapi.testclient import TestClient

import app.api as api_module
from app.api import app


def test_health_endpoint():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_core12_preview_endpoint(tmp_path, monkeypatch):
    sample_df = pl.DataFrame(
        {
            "season": [2025],
            "week": [8],
            "TEAM": ["AAA"],
            "core_epa_off": [0.5],
            "core_epa_def": [0.1],
            "core_sr_off": [0.6],
            "core_sr_def": [0.4],
            "core_ed_sr_off": [0.3],
            "core_third_down_conv": [0.25],
            "core_ypp_diff": [0.05],
            "core_turnover_margin": [1.0],
            "core_points_per_drive_diff": [0.12],
            "core_redzone_td_rate": [0.8],
            "core_pressure_rate_def": [0.33],
            "core_explosive_play_rate_off": [0.25],
        }
    )

    monkeypatch.setattr(
        api_module,
        "path_for",
        lambda layer, season, week: tmp_path / layer / f"{season}_{week}.parquet",
    )
    monkeypatch.setattr(
        api_module,
        "read_parquet_or_raise",
        lambda path: sample_df,
    )
    monkeypatch.setattr("utils.contracts.validate_df", lambda df, *_args, **_kwargs: df)

    client = TestClient(app)
    response = client.get("/metrics/core12/preview", params={"season": 2025, "week": 8, "n": 10})
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["TEAM"] == "AAA"


def test_core12_preview_missing_returns_404(tmp_path, monkeypatch):
    monkeypatch.setattr(
        api_module,
        "path_for",
        lambda layer, season, week: tmp_path / "missing.parquet",
    )
    monkeypatch.setattr(
        api_module,
        "read_parquet_or_raise",
        lambda path: (_ for _ in ()).throw(FileNotFoundError()),
    )

    client = TestClient(app)
    response = client.get("/metrics/core12/preview", params={"season": 2025, "week": 8})
    assert response.status_code == 404
