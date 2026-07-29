import json

import polars as pl

from scripts.freeze_prospective_picks import freeze_picks
from scripts.settle_prospective_ledger import settle


def _write_jsonl(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(record) + "\n" for record in records),
        encoding="utf-8",
    )


def _write_schedule(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    pl.DataFrame(
        {
            "season": [2026],
            "game_type": ["REG"],
            "week": [2],
            "home_team": ["BAL"],
            "away_team": ["CLE"],
            "home_score": [24],
            "away_score": [17],
        }
    ).write_parquet(path)


def test_settle_scores_only_proof_qualified_records(tmp_path):
    source = tmp_path / "picks" / "2026" / "week_02.jsonl"
    _write_jsonl(
        source,
        [
            {
                "season": 2026,
                "week": 2,
                "home": "BAL",
                "away": "CLE",
                "tag": "GOM",
                "model_winner": "BAL",
                "confidence": 82,
                "handicap": -3.5,
                "model_margin": 1.5,
                "market_margin": -3.5,
                "edge_vs_line": 5.0,
                "argument_against": "Market may be pricing a better injury report than our inputs.",
                "market": "spread",
                "line": -3.5,
                "price": -110,
                "book": "testbook",
                "decision_ts_utc": "2026-09-10T15:00:00Z",
                "model_version": "variant_m",
                "commit_sha": "abc123",
                "code_is_dirty": False,
            },
            {
                "season": 2026,
                "week": 2,
                "home": "BAL",
                "away": "CLE",
                "tag": "GOM",
                "model_winner": "CLE",
                "confidence": 70,
                "handicap": 3.5,
            },
        ],
    )
    ledger, _, _, _ = freeze_picks(
        source_path=source,
        output_root=tmp_path / "ledger",
        operator="test",
        frozen_at="2026-09-10T15:01:00Z",
    )
    _write_schedule(tmp_path / "data" / "schedules" / "2026.parquet")

    report, summary = settle(ledger, tmp_path / "data", None)

    assert summary["records"] == 2
    assert summary["proof_qualified"] == 1
    assert summary["not_qualified"] == 1
    assert summary["wins"] == 1
    assert summary["profit_units"] > 0.9
    report_text = report.read_text(encoding="utf-8")
    assert "not_qualified" in report_text
    assert "complete_pre_kick" in report_text
    assert "| 2 | CLE @ BAL | GOM | True | win | +0.91u | 3.5 |" in report_text
    assert "| -3.5 | 1.5 | 5.0 |  | complete_pre_kick |" in report_text
