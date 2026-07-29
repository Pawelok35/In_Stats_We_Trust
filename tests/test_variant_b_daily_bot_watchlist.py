from pathlib import Path

from scripts.variant_b_daily_bot_gui import (
    is_watchlist_record,
    week_generated_artifact_paths,
)


def test_neutral_record_at_or_above_edge_threshold_is_on_watchlist():
    assert is_watchlist_record({"tag": "NEUTRAL", "edge_vs_line": 2.0})
    assert is_watchlist_record({"tag": "neutral", "edge_vs_line": -3.25})


def test_action_or_other_tags_are_not_on_watchlist():
    assert not is_watchlist_record({"tag": "VALUE PLAY", "edge_vs_line": 4.0})
    assert not is_watchlist_record({"tag": "NO BET", "edge_vs_line": 4.0})


def test_small_missing_or_invalid_edge_is_not_on_watchlist():
    assert not is_watchlist_record({"tag": "NEUTRAL", "edge_vs_line": 1.99})
    assert not is_watchlist_record({"tag": "NEUTRAL"})
    assert not is_watchlist_record({"tag": "NEUTRAL", "edge_vs_line": "invalid"})


def test_week_reset_paths_exclude_manual_evidence():
    paths = week_generated_artifact_paths(Path("repo"), 2026, 1, "variant_m")
    rendered = {path.as_posix() for path in paths}

    assert not any("book_snapshots" in path for path in rendered)
    assert not any("market_quotes" in path for path in rendered)
    assert not any("gpt_snapshots" in path for path in rendered)
    assert not any("closing_snapshots" in path for path in rendered)
