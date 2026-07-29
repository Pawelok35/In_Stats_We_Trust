import polars as pl
import yaml

from app.nfl_data_sync import export_week_lines_from_schedule


def test_export_week_lines_from_schedule_uses_home_spread(tmp_path):
    schedule_path = tmp_path / "schedules" / "2026.parquet"
    schedule_path.parent.mkdir(parents=True)
    pl.DataFrame(
        {
            "season": [2026, 2026],
            "week": [1, 1],
            "gameday": ["2026-09-09", "2026-09-10"],
            "gametime": ["20:20", "13:00"],
            "away_team": ["NE", "CHI"],
            "home_team": ["SEA", "CAR"],
            "location": ["Home", "Home"],
            "spread_line": [3.5, -2.5],
            "total_line": [44.5, 41.5],
        }
    ).write_parquet(schedule_path)
    output_path = tmp_path / "week1_lines.yaml"

    result = export_week_lines_from_schedule(
        2026,
        1,
        data_root=tmp_path,
        output_path=output_path,
    )

    assert result.games == 2
    payload = yaml.safe_load(output_path.read_text(encoding="utf-8"))
    assert payload["spread_convention"] == "home_team_spread"
    assert payload["matchups"][0]["home"] == "SEA"
    assert payload["matchups"][0]["away"] == "NE"
    assert payload["matchups"][0]["spread"] == -3.5
    assert payload["matchups"][0]["total"] == 44.5
    assert payload["matchups"][0]["prime_time"] is True
    assert payload["matchups"][1]["home"] == "CAR"
    assert payload["matchups"][1]["spread"] == 2.5


def test_export_week_lines_from_schedule_normalizes_historical_aliases(tmp_path):
    schedule_path = tmp_path / "schedules" / "2019.parquet"
    schedule_path.parent.mkdir(parents=True)
    pl.DataFrame(
        {
            "season": [2019],
            "week": [2],
            "gameday": ["2019-09-15"],
            "gametime": ["16:05"],
            "away_team": ["KC"],
            "home_team": ["OAK"],
            "location": ["Home"],
            "spread_line": [-7.0],
            "total_line": [53.5],
        }
    ).write_parquet(schedule_path)
    output_path = tmp_path / "week2_lines.yaml"

    export_week_lines_from_schedule(
        2019,
        2,
        data_root=tmp_path,
        output_path=output_path,
    )

    payload = yaml.safe_load(output_path.read_text(encoding="utf-8"))
    assert payload["matchups"][0]["home"] == "LV"
    assert payload["matchups"][0]["report"] == "data/reports/comparisons/2019_w2/LV_vs_KC.md"


def test_export_week_lines_from_schedule_fails_when_line_missing(tmp_path):
    schedule_path = tmp_path / "schedules" / "2026.parquet"
    schedule_path.parent.mkdir(parents=True)
    pl.DataFrame(
        {
            "season": [2026],
            "week": [1],
            "gameday": ["2026-09-09"],
            "gametime": ["20:20"],
            "away_team": ["NE"],
            "home_team": ["SEA"],
            "location": ["Home"],
            "spread_line": [None],
            "total_line": [44.5],
        }
    ).write_parquet(schedule_path)

    try:
        export_week_lines_from_schedule(2026, 1, data_root=tmp_path)
    except ValueError as exc:
        assert "Missing spread_line" in str(exc)
    else:
        raise AssertionError("Expected missing spread_line to fail")
