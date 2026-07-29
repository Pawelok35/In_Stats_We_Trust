import json

from scripts.freeze_prospective_picks import freeze_picks


def _write_jsonl(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(record) + "\n" for record in records),
        encoding="utf-8",
    )


def test_freeze_picks_writes_append_only_qualified_ledger(tmp_path):
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
            }
        ],
    )

    ledger, manifest, appended, qualified = freeze_picks(
        source_path=source,
        output_root=tmp_path / "ledger",
        operator="test",
        frozen_at="2026-09-10T15:01:00Z",
    )
    _, _, appended_again, qualified_again = freeze_picks(
        source_path=source,
        output_root=tmp_path / "ledger",
        operator="test",
        frozen_at="2026-09-10T15:01:00Z",
    )

    lines = ledger.read_text(encoding="utf-8").splitlines()
    payload = json.loads(lines[0])
    manifest_payload = json.loads(manifest.read_text(encoding="utf-8"))

    assert appended == 1
    assert appended_again == 0
    assert qualified == 1
    assert qualified_again == 1
    assert len(lines) == 1
    assert payload["proof_qualified"] is True
    assert payload["process_snapshot"]["fair_line"] == 1.5
    assert payload["process_snapshot"]["edge_vs_line"] == 5.0
    assert payload["process_snapshot"]["has_argument_against"] is True
    assert payload["record_hash"]
    assert manifest_payload["records_appended"] == 0
    assert manifest_payload["proof_qualified_seen"] == 1


def test_freeze_picks_marks_missing_timestamp_as_not_qualified(tmp_path):
    source = tmp_path / "picks" / "2026" / "week_03.jsonl"
    _write_jsonl(
        source,
        [
            {
                "season": 2026,
                "week": 3,
                "home": "DAL",
                "away": "NYG",
                "tag": "GOW",
                "model_winner": "DAL",
                "confidence": 77,
                "handicap": -2.5,
            }
        ],
    )

    ledger, _, _, qualified = freeze_picks(
        source_path=source,
        output_root=tmp_path / "ledger",
        operator="test",
        frozen_at="2026-09-17T15:01:00Z",
    )

    payload = json.loads(ledger.read_text(encoding="utf-8").splitlines()[0])

    assert qualified == 0
    assert payload["proof_qualified"] is False
    assert payload["process_snapshot"]["has_fair_line"] is False
    assert any("missing proof fields" in reason for reason in payload["disqualification_reasons"])
    assert any("missing model_margin" in warning for warning in payload["integrity_warnings"])
