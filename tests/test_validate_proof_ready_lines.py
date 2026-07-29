import yaml

from scripts.validate_proof_ready_lines import validate_file


def _write_yaml(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def test_validate_proof_ready_lines_accepts_complete_matchup(tmp_path):
    config = tmp_path / "week1_lines.yaml"
    _write_yaml(
        config,
        {
            "season": 2026,
            "week": 1,
            "matchups": [
                {
                    "home": "BAL",
                    "away": "CLE",
                    "spread": -3.5,
                    "total": 44.5,
                    "book": "testbook",
                    "price": -110,
                    "decision_ts_utc": "2026-09-10T15:00:00Z",
                }
            ],
        },
    )

    report, output = validate_file(config, tmp_path / "report.md")

    assert report["proof_ready"] is True
    assert report["proof_ready_matchups"] == 1
    assert report["issues"] == []
    assert "Proof-ready week: True" in output.read_text(encoding="utf-8")


def test_validate_proof_ready_lines_reports_missing_proof_fields(tmp_path):
    config = tmp_path / "week1_lines.yaml"
    _write_yaml(
        config,
        {
            "season": 2026,
            "week": 1,
            "matchups": [
                {
                    "home": "BAL",
                    "away": "CLE",
                    "spread": -3.5,
                    "total": 44.5,
                }
            ],
        },
    )

    report, output = validate_file(config, tmp_path / "report.md")

    assert report["proof_ready"] is False
    assert report["not_ready_matchups"] == 1
    assert {issue["field"] for issue in report["issues"]} >= {
        "book",
        "price",
        "decision_ts_utc",
    }
    text = output.read_text(encoding="utf-8")
    assert "Proof-ready week: False" in text
    assert "`book`" in text
