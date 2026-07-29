import json

import polars as pl
import pytest

from metrics.backtest import (
    backtest_picks,
    confidence_bucket,
    format_summary_table,
    load_manual_results,
    load_picks,
    load_results,
    summarize,
    validate_pick_records,
)


def test_backtest_grades_ats_results_and_roi():
    picks = [
        {
            "season": 2025,
            "week": 2,
            "home": "BAL",
            "away": "MIA",
            "tag": "GOY",
            "model_winner": "BAL",
            "confidence": 82,
            "handicap": -3.5,
        },
        {
            "season": 2025,
            "week": 2,
            "home": "CIN",
            "away": "JAX",
            "tag": "GOY",
            "model_winner": "JAX",
            "confidence": 71,
            "handicap": 2.5,
        },
        {
            "season": 2025,
            "week": 2,
            "home": "GB",
            "away": "WAS",
            "tag": "GOM",
            "model_winner": "GB",
            "confidence": 64,
            "handicap": -7.0,
        },
    ]
    results = {
        (2, "BAL", "MIA"): {"home_score": 24, "away_score": 17},
        (2, "CIN", "JAX"): {"home_score": 21, "away_score": 24},
        (2, "GB", "WAS"): {"home_score": 20, "away_score": 13},
    }

    rows = backtest_picks(picks, results)

    assert [row["outcome"] for row in rows] == ["win", "win", "push"]
    summary = summarize(rows, group_by="tag")
    goy = next(row for row in summary if row["tag"] == "GOY")
    assert goy["wins"] == 2
    assert goy["losses"] == 0
    assert goy["win_rate"] == 1.0
    assert goy["profit_units"] > 1.8

    table = format_summary_table(summary)
    assert "GOY" in table
    assert "ROI" in table


def test_backtest_loads_jsonl_inputs(tmp_path):
    picks_dir = tmp_path / "picks" / "2025"
    picks_dir.mkdir(parents=True)
    pick_path = picks_dir / "week_02.jsonl"
    pick_path.write_text(
        json.dumps(
            {
                "season": 2025,
                "week": 2,
                "home": "BAL",
                "away": "MIA",
                "tag": "GOY",
                "model_winner": "BAL",
                "confidence": 82,
                "handicap": -3.5,
            }
        )
        + "\n",
        encoding="utf-8",
    )

    results_path = tmp_path / "manual_results.jsonl"
    results_path.write_text(
        json.dumps(
            {
                "season": 2025,
                "week": 2,
                "home_team": "BAL",
                "away_team": "MIA",
                "home_score": 24,
                "away_score": 17,
            }
        )
        + "\n",
        encoding="utf-8",
    )

    assert len(load_picks(tmp_path / "picks", 2025, from_week=2, to_week=2)) == 1
    assert load_manual_results(results_path, season=2025)[(2, "BAL", "MIA")]["home_score"] == 24


def test_confidence_bucket_handles_missing_values():
    assert confidence_bucket(84.5) == "80-90"
    assert confidence_bucket(None) == "unknown"


def test_load_results_uses_schedule_scores_without_manual_jsonl(tmp_path):
    schedule_path = tmp_path / "schedules" / "2025.parquet"
    schedule_path.parent.mkdir(parents=True)
    pl.DataFrame(
        {
            "season": [2025],
            "game_type": ["REG"],
            "week": [2],
            "home_team": ["BAL"],
            "away_team": ["MIA"],
            "home_score": [24],
            "away_score": [17],
        }
    ).write_parquet(schedule_path)

    results = load_results(tmp_path, 2025)

    assert results[(2, "BAL", "MIA")] == {"home_score": 24, "away_score": 17}


def test_validate_pick_records_rejects_missing_required_field():
    records = [
        {
            "season": 2025,
            "week": 2,
            "home": "BAL",
            "away": "MIA",
            "tag": "GOY",
            "model_winner": "BAL",
            "confidence": 82,
        }
    ]

    with pytest.raises(ValueError, match="PICK_OUTPUT.*handicap"):
        validate_pick_records(records)
