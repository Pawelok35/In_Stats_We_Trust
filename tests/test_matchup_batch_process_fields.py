from scripts.matchup_batch import build_process_fields


def test_build_process_fields_keeps_only_filled_review_fields():
    fields = build_process_fields(
        {
            "argument_against": "Injury news could invalidate the trench edge.",
            "market_move_notes": "Do not chase above -3.",
            "injury_role_notes": "",
            "weather_notes": None,
            "closing_line": -2.5,
        }
    )

    assert fields == {
        "argument_against": "Injury news could invalidate the trench edge.",
        "market_move_notes": "Do not chase above -3.",
        "closing_line": -2.5,
    }


def test_build_process_fields_ignores_todo_placeholders():
    fields = build_process_fields(
        {
            "argument_against": "TODO: write the strongest case against this pick",
            "market_move_notes": "TODO: compare open/current/key numbers",
        }
    )

    assert fields == {}
