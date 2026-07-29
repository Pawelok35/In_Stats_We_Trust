import json

import polars as pl

from scripts.freeze_prospective_picks import freeze_picks
from scripts.update_prospective_ytd_report import update_ytd


def _write_jsonl(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(record) + "\n" for record in records),
        encoding="utf-8",
    )


def test_update_ytd_refreshes_settlements_and_summary(tmp_path):
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
                "market": "spread",
                "line": -3.5,
                "price": -110,
                "book": "testbook",
                "decision_ts_utc": "2026-09-10T15:00:00Z",
                "model_version": "variant_m",
                "commit_sha": "abc123",
                "code_is_dirty": False,
            }
        ],
    )
    freeze_picks(
        source_path=source,
        output_root=tmp_path / "ledger",
        operator="test",
        frozen_at="2026-09-10T15:01:00Z",
    )
    schedule = tmp_path / "data" / "schedules" / "2026.parquet"
    schedule.parent.mkdir(parents=True)
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
    ).write_parquet(schedule)

    report, rows = update_ytd(
        season=2026,
        ledger_root=tmp_path / "ledger",
        data_root=tmp_path / "data",
    )

    text = report.read_text(encoding="utf-8")
    assert len(rows) == 1
    assert rows[0]["settled"] == 1
    assert rows[0]["wins"] == 1
    assert "Prospective Edge YTD Report - 2026" in text
    assert "W-L-P: 1-0-0" in text
