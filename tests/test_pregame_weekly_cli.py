from __future__ import annotations

import json
from datetime import timedelta

from pregame.closing_quote_link import ClosingQuoteLinkService
from pregame.game_result import AuthoritativeGameResultService
from pregame.jsonl_store import JsonlPregameEventStore
from pregame.market_history import MarketSnapshotHistoryService
from pregame.projector import project_game
from pregame.wager_execution import ManifestBackedWagerExecutionService
from pregame.wager_execution_clv import WagerExecutionClvService
from pregame.wager_execution_settlement import WagerExecutionSettlementService
from pregame.weekly_cli import WeeklyOperator, main
from tests.test_pregame_closing_quote_link import _closing
from tests.test_pregame_manifest_backed_final_quote_gate import NOW
from tests.test_pregame_wager_execution import _approved, _execution_values


def test_weekly_operator_persists_games_status_and_report(tmp_path):
    operator = WeeklyOperator(root=tmp_path / "ledger", season=2026, week=1)
    game = {
        "game_id": "2026_w01_BUF_at_HOU",
        "season": 2026,
        "week": 1,
        "away_team": "BUF",
        "home_team": "HOU",
        "kickoff_utc": "2026-09-10T18:00:00Z",
        "source": "TEST_SCHEDULE",
    }
    assert operator.import_games([game])[0]["status"] == "APPENDED"
    assert operator.import_games([game])[0]["status"] == "ALREADY_EXISTS"

    status = operator.status()
    assert status["games"][0]["game_id"] == game["game_id"]
    assert status["games"][0]["game_registered"]
    assert status["games"][0]["next_action"] == "import-candidates"

    report = operator.report()
    assert (tmp_path / "ledger" / "reports" / "2026" / "week_01.json").exists()
    assert (tmp_path / "ledger" / "reports" / "2026" / "week_01.md").exists()
    assert report["status"]["games"]

    restarted = WeeklyOperator(root=tmp_path / "ledger", season=2026, week=1)
    assert restarted.status() == status


def test_weekly_cli_init_and_status_are_machine_readable(tmp_path, capsys):
    root = tmp_path / "ledger"
    assert main(["--root", str(root), "--season", "2026", "--week", "1", "init-week"]) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["status"] == "READY"
    assert main(["--root", str(root), "--season", "2026", "--week", "1", "status"]) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["games"] == []


def test_week_1_simulation_runs_full_central_chain_and_restarts(tmp_path):
    store, candidate, gate = _approved(tmp_path)
    execution = ManifestBackedWagerExecutionService(store=store).record(
        **_execution_values(candidate, gate)
    )
    assert execution.appended
    closing = _closing(candidate, gate, spread=-3.5, spread_price=-105)
    assert (
        MarketSnapshotHistoryService(store)
        .record_snapshot(closing, recorded_at_utc=closing.captured_at_utc)
        .status.value
        == "APPENDED"
    )
    assert (
        ClosingQuoteLinkService(store=store)
        .record(
            execution_id="execution-1",
            closing_snapshot_id=closing.snapshot_id,
            linked_at_utc=NOW + timedelta(minutes=31),
        )
        .appended
    )
    state = project_game(store, candidate.game_id)
    finalized = state.kickoff_utc + timedelta(hours=3)
    assert (
        AuthoritativeGameResultService(store=store)
        .record(
            game_id=candidate.game_id,
            home_score=17,
            away_score=24,
            source="SIMULATION_FIXTURE_ONLY",
            source_reference="fixture:2026-week-01",
            source_finalized_at_utc=finalized,
            observed_at_utc=finalized + timedelta(minutes=1),
        )
        .appended
    )
    assert (
        WagerExecutionSettlementService(store=store)
        .record(execution_id="execution-1", settled_at_utc=finalized + timedelta(minutes=2))
        .appended
    )
    assert (
        WagerExecutionClvService(store=store)
        .record(execution_id="execution-1", calculated_at_utc=finalized + timedelta(minutes=3))
        .appended
    )
    state = project_game(store, candidate.game_id)
    assert state.settlement_outcome_for_execution("execution-1") == "WIN"
    assert state.clv_for_execution("execution-1").line_clv_points == "1.500000"

    path = tmp_path / "week-1-events.jsonl"
    durable = JsonlPregameEventStore(path)
    for event in store.list_all_events():
        assert durable.append(event).status.value == "APPENDED"
    restarted = project_game(durable, candidate.game_id)
    assert restarted.to_json_dict() == state.to_json_dict()
