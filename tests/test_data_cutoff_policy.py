from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import polars as pl
import pytest
import yaml

from etl.l3_aggregate import _aggregate as l3_aggregate
from metrics.core12 import compute as core12_compute
from metrics.form_windows import compute_form_windows
from scripts import matchup_batch
from utils.data_cutoff import MISSING_SAFE_SNAPSHOT, resolve_safe_snapshot
from utils.preflight import validate_model_preflight


def _write_l3_week(
    root: Path,
    season: int,
    week: int,
    *,
    team: str = "BUF",
    epa: float | None = 0.1,
    game_id: str | None = None,
    def_epa: float | None = 0.1,
) -> None:
    path = root / "data" / "l3_team_week" / str(season) / f"{week}.parquet"
    path.parent.mkdir(parents=True, exist_ok=True)
    pl.DataFrame(
        {
            "season": [season],
            "week": [week],
            "TEAM": [team],
            "game_id": [game_id or f"{season}_{week}_{team}"],
            "drives": [10],
            "plays": [60],
            "epa_off_mean": [epa],
            "success_rate_off": [0.45],
            "epa_def_mean": [def_epa],
            "success_rate_def": [0.41],
            "tempo": [6.0],
        }
    ).write_parquet(path)


def test_week6_last3_uses_weeks_3_4_5_and_excludes_week6(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    for week, epa in [(1, 1.0), (2, 2.0), (3, 3.0), (4, 4.0), (5, 5.0), (6, 100.0), (7, 200.0)]:
        _write_l3_week(tmp_path, 2026, week, epa=epa)

    result = compute_form_windows(2026, 6, ["BUF"])
    last3 = result.filter(pl.col("window") == "last 3 games").to_dicts()[0]

    assert last3["source_weeks_BUF"] == "3,4,5"
    assert last3["max_source_week_BUF"] == 5
    assert last3["data_cutoff_status_BUF"] == "AVAILABLE"
    assert last3["epa_off_mean_avg_BUF"] == pytest.approx(4.0)


def test_week6_last5_uses_weeks_1_to_5(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    for week, epa in [(1, 1.0), (2, 2.0), (3, 3.0), (4, 4.0), (5, 5.0), (6, 100.0), (7, 200.0)]:
        _write_l3_week(tmp_path, 2026, week, epa=epa)

    result = compute_form_windows(2026, 6, ["BUF"])
    last5 = result.filter(pl.col("window") == "last 5 games").to_dicts()[0]

    assert last5["source_weeks_BUF"] == "1,2,3,4,5"
    assert last5["max_source_week_BUF"] == 5
    assert last5["epa_off_mean_avg_BUF"] == pytest.approx(3.0)


def test_week6_defensive_last3_and_last5_exclude_weeks_6_and_7(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    for week, value in [
        (1, 1.0),
        (2, 2.0),
        (3, 3.0),
        (4, 4.0),
        (5, 5.0),
        (6, 100.0),
        (7, 200.0),
    ]:
        _write_l3_week(tmp_path, 2026, week, epa=0.1, def_epa=value)

    result = compute_form_windows(2026, 6, ["BUF"])
    last5 = result.filter(pl.col("window") == "last 5 games").to_dicts()[0]
    last3 = result.filter(pl.col("window") == "last 3 games").to_dicts()[0]

    assert last5["source_weeks_BUF"] == "1,2,3,4,5"
    assert last5["epa_def_mean_avg_BUF"] == pytest.approx(3.0)
    assert last3["source_weeks_BUF"] == "3,4,5"
    assert last3["epa_def_mean_avg_BUF"] == pytest.approx(4.0)


def test_future_week_file_is_never_loaded_for_week6(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    for week in [1, 2, 3, 4, 5, 7]:
        _write_l3_week(tmp_path, 2026, week, epa=float(week))

    result = compute_form_windows(2026, 6, ["BUF"])
    season = result.filter(pl.col("window") == "weeks 1-5").to_dicts()[0]

    assert season["source_weeks_BUF"] == "1,2,3,4,5"
    assert season["max_source_week_BUF"] == 5


def test_safe_snapshot_falls_back_to_previous_week(tmp_path):
    path = tmp_path / "data" / "rolling_core12" / "2026" / "through_4.parquet"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("placeholder", encoding="utf-8")

    result = resolve_safe_snapshot(
        season=2026,
        analysis_week=6,
        requested_through_week=5,
        path_factory=lambda season, week: (
            tmp_path / "data" / "rolling_core12" / str(season) / f"through_{week}.parquet"
        ),
    )

    assert result.resolved_through_week == 4
    assert result.fallback_used is True
    assert result.cutoff_safe is True


def test_unsafe_snapshot_does_not_fall_forward(tmp_path):
    path = tmp_path / "data" / "rolling_core12" / "2026" / "through_6.parquet"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("placeholder", encoding="utf-8")

    result = resolve_safe_snapshot(
        season=2026,
        analysis_week=6,
        requested_through_week=5,
        path_factory=lambda season, week: (
            tmp_path / "data" / "rolling_core12" / str(season) / f"through_{week}.parquet"
        ),
    )

    assert result.status == MISSING_SAFE_SNAPSHOT
    assert result.path is None


def test_week1_returns_insufficient_current_season_data(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    result = compute_form_windows(2026, 1, ["BUF"])
    row = result.filter(pl.col("window") == "last 3 games").to_dicts()[0]

    assert row["games_in_window_BUF"] == 0
    assert row["data_cutoff_status_BUF"] == "INSUFFICIENT_CURRENT_SEASON_DATA"
    assert row["epa_off_mean_avg_BUF"] is None


def test_duplicate_team_week_is_detected(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    path = tmp_path / "data" / "l3_team_week" / "2026" / "1.parquet"
    path.parent.mkdir(parents=True, exist_ok=True)
    pl.DataFrame(
        {
            "season": [2026, 2026],
            "week": [1, 1],
            "TEAM": ["BUF", "BUF"],
            "game_id": ["same", "same"],
            "drives": [10, 10],
            "plays": [60, 60],
            "epa_off_mean": [0.1, 0.2],
            "success_rate_off": [0.4, 0.5],
            "epa_def_mean": [0.1, 0.2],
            "success_rate_def": [0.4, 0.5],
            "tempo": [6.0, 6.0],
        }
    ).write_parquet(path)

    with pytest.raises(ValueError, match="Duplicate rolling source rows"):
        compute_form_windows(2026, 2, ["BUF"])


def test_core12_keeps_missing_epa_null_and_flags_quality(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    l3_df = pl.DataFrame(
        {
            "season": [2026],
            "week": [1],
            "TEAM": ["BUF"],
            "epa_off_mean": [None],
            "epa_def_mean": [0.1],
            "success_rate_off": [0.5],
            "success_rate_def": [0.4],
            "explosive_play_rate_off": [0.1],
            "third_down_conv_off": [0.4],
            "points_per_drive_diff": [0.2],
            "ypp_diff": [0.3],
            "turnover_margin": [0.0],
            "redzone_td_rate_off": [0.5],
            "pressure_rate_def": [0.2],
            "tempo": [6.0],
        }
    )

    result = core12_compute(l3_df, 2026, 1)
    row = result.to_dicts()[0]

    assert row["core_epa_off"] is None
    assert row["data_quality_status"] == "MISSING_REQUIRED_METRICS"
    assert row["model_input_complete"] is False
    assert "core_epa_off" in row["missing_required_metrics"]
    assert row["nulls_replaced_with_zero"] == 0


def test_preflight_blocks_mismatched_future_week_inside_allowed_source_file(tmp_path):
    _write_l3_week(tmp_path, 2026, 5)
    path = tmp_path / "data" / "l3_team_week" / "2026" / "5.parquet"
    df = pl.read_parquet(path).with_columns(pl.lit(6).alias("week"))
    df.write_parquet(path)

    result = validate_model_preflight(
        season=2026,
        analysis_week=6,
        data_root=tmp_path / "data",
        strict_mode=True,
    )

    assert result.status == "BLOCKED"
    assert result.leakage_detected is True


def test_data_sources_registry_declares_manual_and_active_sources_consistently():
    data = yaml.safe_load(Path("config/data_sources.yaml").read_text(encoding="utf-8"))
    sources = data["data_sources"]

    assert sources["main_model_pbp"]["provider"] == "filesystem"
    assert "l1" in sources["main_model_pbp"]["pipeline"]
    assert sources["schedule"]["load_method"] == "nfl_data_py.import_schedules"
    assert sources["live_scenario"]["provider"] == "nflreadpy"

    manual_sources = ["market_lines", "injuries", "roster_depth_chart", "public_betting"]
    for name in manual_sources:
        status = str(sources[name]["automation_status"])
        assert "MANUAL" in status
        assert status != "AUTOMATED"

    for source in sources.values():
        assert "provider" in source
        assert "local_source" in source
        assert "consumer" in source


def test_controlled_workflow_writes_pick_after_safe_preflight(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    l3_path = tmp_path / "data" / "l3_team_week" / "2025" / "1.parquet"
    l3_path.parent.mkdir(parents=True, exist_ok=True)
    pl.DataFrame(
        {
            "season": [2025, 2025],
            "week": [1, 1],
            "TEAM": ["BAL", "MIA"],
            "game_id": ["2025_1_BAL_MIA", "2025_1_BAL_MIA"],
            "drives": [10, 10],
            "plays": [60, 58],
            "epa_off_mean": [1.0, 0.5],
            "success_rate_off": [0.45, 0.41],
                "epa_def_mean": [0.1, 0.2],
                "success_rate_def": [0.4, 0.44],
                "explosive_play_rate_off": [0.1, 0.08],
                "third_down_conv_off": [0.42, 0.38],
                "points_per_drive_diff": [0.4, -0.4],
                "ypp_off": [5.8, 5.2],
                "ypp_def": [5.2, 5.8],
                "ypp_diff": [0.6, -0.6],
                "turnover_margin": [0.0, 0.0],
                "redzone_td_rate_off": [0.55, 0.5],
                "pressure_rate_def": [0.22, 0.18],
                "tempo": [6.0, 5.8],
            }
        ).write_parquet(l3_path)

    form = compute_form_windows(2025, 2, ["BAL", "MIA"])
    assert form.filter(pl.col("window") == "last 5 games").to_dicts()[0][
        "max_source_week_BAL"
    ] == 1

    l3_df = pl.read_parquet(l3_path)
    core12 = core12_compute(l3_df, 2025, 1)
    assert core12.to_dicts()[0]["data_quality_status"] == "OK"

    report = tmp_path / "data" / "reports" / "comparisons" / "2025_w2" / "BAL_vs_MIA.md"
    report.parent.mkdir(parents=True)
    report.write_text("# BAL vs MIA\n", encoding="utf-8")
    config = tmp_path / "week2_lines.yaml"
    config.write_text(
        f"""
matchups:
  - home: BAL
    away: MIA
    spread: -3.5
    total: 44.5
    report: {report}
""",
        encoding="utf-8",
    )

    def fake_run(*args, **kwargs):
        return SimpleNamespace(
            text="analysis",
            projection=SimpleNamespace(
                tag="GOM",
                model_winner="BAL",
                market_winner="BAL",
                confidence=86.0,
                adv_model=7.0,
                adv_market=3.5,
                edge_vs_line=4.0,
                winner_line=-3.5,
            ),
        )

    monkeypatch.setattr(matchup_batch.matchup_analyzer, "run", fake_run)
    picks_dir = tmp_path / "picks"
    matchup_batch.run_batch(
        config_path=config,
        output_dir=None,
        default_window=None,
        strict=True,
        combined_output=None,
        picks_dir=picks_dir,
        tag_config=None,
    )

    record = yaml.safe_load((picks_dir / "2025" / "week_02.jsonl").read_text())
    assert record["tag"] == "GOM"
    assert record["preflight"]["status"] == "PASS"
    assert record["preflight"]["maximum_feature_week"] == 1


def test_controlled_workflow_blocks_pick_when_source_contains_future_week(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_l3_week(tmp_path, 2025, 1, team="BAL", epa=1.0)
    bad_path = tmp_path / "data" / "l3_team_week" / "2025" / "1.parquet"
    pl.read_parquet(bad_path).with_columns(pl.lit(2).alias("week")).write_parquet(bad_path)

    report = tmp_path / "data" / "reports" / "comparisons" / "2025_w2" / "BAL_vs_MIA.md"
    report.parent.mkdir(parents=True)
    report.write_text("# BAL vs MIA\n", encoding="utf-8")
    config = tmp_path / "week2_lines.yaml"
    config.write_text(
        f"""
matchups:
  - home: BAL
    away: MIA
    spread: -3.5
    total: 44.5
    report: {report}
""",
        encoding="utf-8",
    )

    with pytest.raises(RuntimeError, match="preflight validation blocked"):
        matchup_batch.run_batch(
            config_path=config,
            output_dir=None,
            default_window=None,
            strict=True,
            combined_output=None,
            picks_dir=tmp_path / "picks",
            tag_config=None,
        )

    assert not (tmp_path / "picks" / "2025" / "week_02.jsonl").exists()


def _minimal_l2_rows(*, include_epa: bool = True, third_attempts: int = 0) -> pl.DataFrame:
    rows = []
    total_rows = max(third_attempts, 2)
    for idx in range(total_rows):
        is_third = 1 if idx < third_attempts else 0
        row = {
            "season": 2026,
            "week": 1,
            "game_id": "G1",
            "play_id": idx + 1,
            "TEAM": "BUF",
            "OPP": "MIA",
            "drive": 1,
            "play_type": "pass" if idx % 2 == 0 else "run",
            "success": 0.0,
            "yards_gained": 3.0,
            "yardline_100": 50.0,
            "is_dropback": 1 if idx % 2 == 0 else 0,
            "is_pressure": 0,
            "is_explosive": 0,
            "is_turnover": 0,
            "is_offensive_td": 0,
            "in_redzone": 0,
            "is_third_down": is_third,
            "third_down_converted": 0,
            "play_description": "test play",
        }
        if include_epa:
            row["epa"] = None
        rows.append(row)
    return pl.DataFrame(rows)


def test_l3_missing_epa_column_remains_null_not_zero():
    result = l3_aggregate(_minimal_l2_rows(include_epa=False))
    row = result.to_dicts()[0]

    assert row["epa_off_mean"] is None
    assert row["epa_def_mean"] is None


def test_l3_missing_epa_values_remain_null_not_zero():
    result = l3_aggregate(_minimal_l2_rows(include_epa=True))
    row = result.to_dicts()[0]

    assert row["epa_off_mean"] is None
    assert row["epa_def_mean"] is None


def test_l3_third_down_without_denominator_is_null():
    result = l3_aggregate(_minimal_l2_rows(include_epa=True, third_attempts=0))
    row = result.to_dicts()[0]

    assert row["third_down_conv_off"] is None


def test_l3_true_zero_third_down_rate_is_valid_zero():
    result = l3_aggregate(_minimal_l2_rows(include_epa=True, third_attempts=5))
    row = result.to_dicts()[0]

    assert row["third_down_conv_off"] == pytest.approx(0.0)


def test_preflight_blocks_pick_when_required_metric_is_null(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    l3_path = tmp_path / "data" / "l3_team_week" / "2025" / "1.parquet"
    l3_path.parent.mkdir(parents=True, exist_ok=True)
    pl.DataFrame(
        {
            "season": [2025, 2025],
            "week": [1, 1],
            "TEAM": ["BAL", "MIA"],
            "game_id": ["2025_1_BAL_MIA", "2025_1_BAL_MIA"],
            "drives": [10, 10],
            "plays": [60, 58],
            "epa_off_mean": [None, 0.5],
            "epa_def_mean": [0.1, 0.2],
            "success_rate_off": [0.45, 0.41],
            "success_rate_def": [0.4, 0.44],
            "ypp_off": [5.8, 5.2],
            "ypp_def": [5.2, 5.8],
            "ypp_diff": [0.6, -0.6],
            "tempo": [6.0, 5.8],
        }
    ).write_parquet(l3_path)

    report = tmp_path / "data" / "reports" / "comparisons" / "2025_w2" / "BAL_vs_MIA.md"
    report.parent.mkdir(parents=True)
    report.write_text("# BAL vs MIA\n", encoding="utf-8")
    config = tmp_path / "week2_lines.yaml"
    config.write_text(
        f"""
matchups:
  - home: BAL
    away: MIA
    spread: -3.5
    total: 44.5
    report: {report}
""",
        encoding="utf-8",
    )

    with pytest.raises(RuntimeError, match="missing required model metric"):
        matchup_batch.run_batch(
            config_path=config,
            output_dir=None,
            default_window=None,
            strict=True,
            combined_output=None,
            picks_dir=tmp_path / "picks",
            tag_config=None,
        )

    assert not (tmp_path / "picks" / "2025" / "week_02.jsonl").exists()
