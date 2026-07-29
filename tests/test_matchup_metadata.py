import json
from types import SimpleNamespace

from scripts import matchup_batch


def test_matchup_batch_writes_pick_metadata(tmp_path, monkeypatch):
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

    tag_config = tmp_path / "variant_j.yaml"
    tag_config.write_text("GOY: {}\n", encoding="utf-8")

    def fake_run(*args, **kwargs):
        return SimpleNamespace(
            text="analysis",
            projection=SimpleNamespace(
                tag="GOY",
                model_winner="BAL",
                market_winner="BAL",
                confidence=82.0,
                adv_model=7.0,
                adv_market=3.5,
                edge_vs_line=3.5,
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
        tag_config=tag_config,
    )

    record = json.loads((picks_dir / "2025" / "week_02.jsonl").read_text(encoding="utf-8"))
    assert record["model_version"] == "variant_j"
    assert record["data_cutoff"] == "2025_w2"
    assert record["commit_sha"]
    assert record["config_sha256"]
    assert "config_hashes" in record
