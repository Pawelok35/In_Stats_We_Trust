from __future__ import annotations

import pandas as pd
import pytest

from live_scenario import batch
from live_scenario.batch import (
    BatchGameInput,
    BatchValidationError,
    block_options,
    build_entries,
    completeness,
    games_for_block,
    generate_batch_post,
    parse_score,
)
from live_scenario.week_games import WeekGame


def _game(index: int, *, time: str = "13:00") -> WeekGame:
    away = f"A{index:02d}"
    home = f"H{index:02d}"
    return WeekGame(
        game_id=f"2026_01_{away}_{home}",
        season=2026,
        week=1,
        away=away,
        home=home,
        game_date="2026-09-13",
        game_time=time,
        neutral_site=False,
        spread_line=-1.5,
        spread_source="test_schedule",
        spread_status="AVAILABLE",
        schedule_source="test",
        schedule_timestamp_utc="2026-08-01T00:00:00+00:00",
        model_status="NO MODEL PICK",
        model_tag=None,
        model_selected_team=None,
        model_edge=None,
        model_margin=None,
    )


def _ten_entries() -> list[BatchGameInput]:
    return [BatchGameInput(game=_game(index)) for index in range(10)]


def test_batch_block_lists_all_games_without_duplicates():
    games = [_game(index) for index in range(10)]

    assert block_options(games) == ["2026-09-13 13:00"]
    block_games = games_for_block(games, "2026-09-13 13:00")
    assert len(block_games) == 10
    assert len({game.game_id for game in block_games}) == 10


def test_batch_completeness_counts_ready_not_halftime_and_excluded():
    entries = _ten_entries()
    for entry in entries[:7]:
        entry.q1_away, entry.q1_home = "7", "3"
        entry.q2_away, entry.q2_home = "10", "7"
        entry.status = "READY"
    entries[7].status = "NOT_AT_HALFTIME"
    entries[8].status = "NOT_AT_HALFTIME"
    entries[9].status = "EXCLUDED"

    assert completeness(entries).to_dict() == {
        "total": 10,
        "ready": 7,
        "included": 0,
        "not_at_halftime": 2,
        "excluded": 1,
        "errors": 0,
        "unclassified": 0,
    }


def test_strict_batch_generates_only_ready_sections_in_deterministic_order(monkeypatch):
    entries = _ten_entries()
    for entry in entries[:7]:
        entry.q1_away, entry.q1_home = "7", "3"
        entry.q2_away, entry.q2_home = "10", "7"
        entry.status = "READY"
    entries[7].status = "NOT_AT_HALFTIME"
    entries[8].status = "NOT_AT_HALFTIME"
    entries[9].status = "EXCLUDED"

    monkeypatch.setattr(
        batch,
        "_report_for_entry",
        lambda entry, validation, historical_rows, **kwargs: f"report {entry.game_id}",
    )
    result = generate_batch_post(
        entries,
        pd.DataFrame(),
        season=2026,
        week=1,
        block="2026-09-13 13:00",
        data_cutoff_utc="2026-09-13T18:00:00Z",
    )

    assert result.included_game_ids == tuple(entry.game_id for entry in entries[:7])
    assert len(result.omitted_game_ids) == 3
    assert result.text.count("report 2026_01_") == 7


def test_batch_section_matches_existing_single_game_formatter():
    entry = BatchGameInput(
        game=_game(0),
        q1_away="7",
        q1_home="3",
        q2_away="10",
        q2_home="7",
        status="READY",
    )
    rows = pd.read_parquet("data/live_scenario/processed/team_game_scenario_rows.parquet")

    single_validation = batch.validate_entry(entry)
    single_post = batch._report_for_entry(
        entry,
        single_validation,
        rows,
        data_cutoff_utc="2026-08-06T18:00:00Z",
        generated_at_utc="2026-08-06T18:00:00Z",
        tie_policy="TIE_AS_LOSS",
    )
    result = generate_batch_post(
        [entry],
        rows,
        season=2026,
        week=1,
        block="2026-09-13 13:00",
        data_cutoff_utc="2026-08-06T18:00:00Z",
        generated_at_utc="2026-08-06T18:00:00Z",
    )

    assert single_post in result.text
    assert result.included_game_ids == (entry.game_id,)


def test_unclassified_game_blocks_strict_batch_and_names_game(monkeypatch):
    entries = _ten_entries()
    entries[0].status = ""
    for entry in entries[1:]:
        entry.status = "NOT_AT_HALFTIME"

    monkeypatch.setattr(batch, "_report_for_entry", lambda *args, **kwargs: "unused")
    with pytest.raises(BatchValidationError) as exc_info:
        generate_batch_post(
            entries,
            pd.DataFrame(),
            season=2026,
            week=1,
            block="2026-09-13 13:00",
            data_cutoff_utc="2026-09-13T18:00:00Z",
        )

    assert entries[0].game_id in str(exc_info.value)


def test_invalid_ready_score_is_error_and_partial_mode_omits_it(monkeypatch):
    entries = _ten_entries()[:2]
    entries[0].status = "READY"
    entries[0].q1_away = "bad"
    entries[0].q1_home = "3"
    entries[0].q2_away = "7"
    entries[0].q2_home = "7"
    entries[1].status = "NOT_AT_HALFTIME"

    monkeypatch.setattr(batch, "_report_for_entry", lambda *args, **kwargs: "unused")
    result = generate_batch_post(
        entries,
        pd.DataFrame(),
        season=2026,
        week=1,
        block="2026-09-13 13:00",
        data_cutoff_utc="2026-09-13T18:00:00Z",
        allow_partial=True,
    )

    assert result.partial is True
    assert result.included_game_ids == ()
    assert result.omitted_game_ids == (entries[0].game_id, entries[1].game_id)


def test_refresh_preserves_operator_fields_by_game_id():
    original = _game(1)
    edited = BatchGameInput(
        game=original,
        q1_away="10",
        q1_home="3",
        q2_away="7",
        q2_home="7",
        spread_away="+1.5",
        status="READY",
    )
    refreshed = _game(1)

    entries = build_entries([refreshed], previous={original.game_id: edited})

    assert entries[0].q1_away == "10"
    assert entries[0].q2_home == "7"
    assert entries[0].spread_away == "+1.5"
    assert entries[0].status == "READY"


def test_parse_score_accepts_operator_formats_and_rejects_invalid_values():
    assert parse_score("7-3") == (7, 3)
    assert parse_score("7:3") == (7, 3)
    with pytest.raises(ValueError):
        parse_score("7")


def test_batch_uses_one_selected_locale_and_one_final_disclaimer(monkeypatch):
    entry = _ten_entries()[0]
    entry.status = "READY"
    entry.q1_away, entry.q1_home = "10", "3"
    entry.q2_away, entry.q2_home = "7", "7"
    monkeypatch.setattr(batch, "_report_for_entry", lambda *args, **kwargs: "GAME SECTION")

    result = generate_batch_post(
        [entry],
        pd.DataFrame(),
        season=2026,
        week=1,
        block="2026-09-13 13:00",
        data_cutoff_utc="2026-09-13T18:00:00Z",
        locale="en-US",
    )

    assert "NFL HALFTIME SCENARIOS — WEEK 1" in result.text
    assert "Historical context only — not an automatic live decision." in result.text
    assert result.text.count("Historical context only") == 1
