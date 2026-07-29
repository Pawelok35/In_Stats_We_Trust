from scripts.variant_b_audit import has_model_generation_quote, is_market_grade


def test_unknown_timestamp_does_not_satisfy_model_generation_quote():
    assert not has_model_generation_quote(
        {
            "model_generation_spread_selected_team": -3.5,
            "model_generation_price": -110,
            "model_generation_quote_timestamp_utc": "UNKNOWN",
        }
    )


def test_market_grade_requires_a_real_timestamp_and_confirmed_status():
    record = {
        "book": "DraftKings",
        "quote_timestamp_utc": "UNKNOWN",
        "executable_status": "CONFIRMED_AT_BOOK",
        "source_type": "DIRECT_BOOK",
    }
    assert not is_market_grade(record)
    record["quote_timestamp_utc"] = "2026-09-08T18:42:00Z"
    assert is_market_grade(record)
