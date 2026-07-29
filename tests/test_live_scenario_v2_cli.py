import json
import subprocess
import sys

import pandas as pd
import pytest

from scripts.live_scenario_v2 import parse_quarter_score


def _write_history(path):
    rows = pd.DataFrame(
        [
            {
                "game_id": "g1",
                "season": 2020,
                "team": "BUF",
                "q1_result": "WIN",
                "q2_result": "WIN",
                "after_q1_margin": 3,
                "after_q2_margin": 7,
                "final_state": "WIN",
            },
            {
                "game_id": "g2",
                "season": 2021,
                "team": "BUF",
                "q1_result": "WIN",
                "q2_result": "WIN",
                "after_q1_margin": 3,
                "after_q2_margin": 7,
                "final_state": "LOSS",
            },
            {
                "game_id": "g3",
                "season": 2022,
                "team": "KC",
                "q1_result": "WIN",
                "q2_result": "WIN",
                "after_q1_margin": 3,
                "after_q2_margin": 7,
                "final_state": "WIN",
            },
            {
                "game_id": "g4",
                "season": 2023,
                "team": "MIA",
                "q1_result": "WIN",
                "q2_result": "WIN",
                "after_q1_margin": 3,
                "after_q2_margin": 7,
                "final_state": "WIN",
            },
            {
                "game_id": "g5",
                "season": 2020,
                "team": "HOU",
                "q1_result": "LOSS",
                "q2_result": "LOSS",
                "after_q1_margin": -3,
                "after_q2_margin": -7,
                "final_state": "LOSS",
            },
            {
                "game_id": "g6",
                "season": 2021,
                "team": "HOU",
                "q1_result": "LOSS",
                "q2_result": "LOSS",
                "after_q1_margin": -3,
                "after_q2_margin": -7,
                "final_state": "WIN",
            },
            {
                "game_id": "g7",
                "season": 2024,
                "team": "BUF",
                "q1_result": "WIN",
                "q2_result": "WIN",
                "after_q1_margin": 3,
                "after_q2_margin": 10,
                "final_state": "WIN",
            },
        ]
    )
    rows.to_csv(path, index=False)


def test_parse_quarter_score_accepts_dash_and_colon():
    assert parse_quarter_score("7-3") == (7, 3)
    assert parse_quarter_score("10:7") == (10, 7)
    with pytest.raises(Exception, match="Quarter score"):
        parse_quarter_score("7/3")


def test_live_scenario_v2_cli_writes_report_json(tmp_path):
    history_path = tmp_path / "history.csv"
    output_path = tmp_path / "report.json"
    _write_history(history_path)

    result = subprocess.run(
        [
            sys.executable,
            "scripts/live_scenario_v2.py",
            "--team-a",
            "BUF",
            "--opponent",
            "HOU",
            "--q1",
            "7-3",
            "--q2",
            "10-7",
            "--historical-rows",
            str(history_path),
            "--data-cutoff-utc",
            "2026-09-10T00:00:00Z",
            "--generated-at-utc",
            "2026-09-10T00:01:00Z",
            "--team-a-live-decimal",
            "1.8",
            "--opponent-live-decimal",
            "2.2",
            "--team-a-closing-spread",
            "-3",
            "--team-a-role",
            "FAVORITE",
            "--spread-source",
            "PREGAME_COM",
            "--spread-captured-at-utc",
            "2026-09-09T18:00:00Z",
            "--spread-quality",
            "displayed_unverified",
            "--output",
            str(output_path),
        ],
        cwd=".",
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    stdout_payload = json.loads(result.stdout)
    file_payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert stdout_payload == file_payload
    assert stdout_payload["schema_version"] == "live_scenario.v2"
    assert stdout_payload["current_state"]["team_a_quarter_result_path"] == "WIN-WIN"
    assert stdout_payload["current_state"]["opponent_quarter_result_path"] == "LOSS-LOSS"
    assert stdout_payload["current_state"]["team_a_cumulative_state_path"] == "LEAD-LEAD"
    assert stdout_payload["current_state"]["opponent_cumulative_state_path"] == "TRAIL-TRAIL"
    assert stdout_payload["current_state"]["team_a_path"] == "WIN-WIN"
    assert stdout_payload["current_state"]["opponent_path"] == "LOSS-LOSS"
    assert stdout_payload["current_state"]["margin_bucket"] == "LEADING_1_TO_7"
    assert stdout_payload["league_baseline"]["sample_size"] == 4
    assert stdout_payload["team_a_history"]["sample_size"] == 2
    assert stdout_payload["opponent_recovery_history"]["sample_size"] == 2
    assert stdout_payload["pregame_spread_context"] == {
        "team_a_closing_spread": -3.0,
        "opponent_closing_spread": 3.0,
        "team_a_role": "FAVORITE",
        "exact_spread": 3.0,
        "spread_bucket": "FAV_2-3",
        "spread_source": "PREGAME_COM",
        "spread_captured_at_utc": "2026-09-09T18:00:00Z",
        "spread_quality": "DISPLAYED_UNVERIFIED",
    }
    assert stdout_payload["market_comparison"]["primary_probability_source"] == "league_baseline"
    assert stdout_payload["market_comparison"]["tie_policy"] == "TIE_AS_LOSS"
    assert stdout_payload["market_comparison"]["edge_vs_market_pp"] == 20.0


def test_live_scenario_v2_cli_legacy_compatibility_mode(tmp_path):
    history_path = tmp_path / "history.csv"
    _write_history(history_path)

    result = subprocess.run(
        [
            sys.executable,
            "scripts/live_scenario_v2.py",
            "--team-a",
            "BUF",
            "--opponent",
            "HOU",
            "--q1",
            "7-3",
            "--q2",
            "10-7",
            "--historical-rows",
            str(history_path),
            "--data-cutoff-utc",
            "2026-09-10T00:00:00Z",
            "--legacy-compatibility-mode",
        ],
        cwd=".",
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    compatibility = payload["legacy_compatibility"]
    assert compatibility["identical_results_required"] is False
    assert compatibility["legacy_path_only"]["filters_applied"] == ["path"]
    assert compatibility["legacy_path_only"]["filters_not_applied"] == ["margin_bucket"]
    assert compatibility["legacy_path_only"]["sample_size"] == 5
    assert compatibility["v2_path_margin"]["filters_applied"] == [
        "cumulative_state_path",
        "margin_bucket",
    ]
    assert compatibility["v2_path_margin"]["quarter_result_path"] == "WIN-WIN"
    assert compatibility["v2_path_margin"]["cumulative_state_path"] == "LEAD-LEAD"
    assert compatibility["v2_path_margin"]["sample_size"] == 4
    assert compatibility["sample_size_delta"] == 1
