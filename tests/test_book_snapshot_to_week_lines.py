from scripts.book_snapshot_to_week_lines import build_lines


def test_build_lines_preserves_schedule_context_from_existing_lines():
    snapshot = {
        "book_snapshot": {
            "season": 2026,
            "week": 1,
            "book": "TEST_BOOK",
            "captured_at_utc": "2026-07-26T12:00:00Z",
        },
        "games": [
            {
                "away": "SF",
                "home": "LA",
                "home_spread": -3.5,
                "home_spread_price": -110,
                "total_over": 48.5,
            }
        ],
    }
    existing = {
        "matchups": [
            {
                "away": "SF",
                "home": "LA",
                "prime_time": True,
                "neutral_site": True,
            }
        ]
    }

    matchup = build_lines(snapshot, existing_lines=existing)["matchups"][0]

    assert matchup["prime_time"] is True
    assert matchup["neutral_site"] is True


def test_explicit_snapshot_context_overrides_existing_lines():
    snapshot = {
        "book_snapshot": {"season": 2026, "week": 1},
        "games": [
            {
                "away": "SF",
                "home": "LA",
                "home_spread": -3.0,
                "total_over": 48.5,
                "prime_time": False,
                "neutral_site": False,
            }
        ],
    }
    existing = {
        "matchups": [
            {
                "away": "SF",
                "home": "LA",
                "prime_time": True,
                "neutral_site": True,
            }
        ]
    }

    matchup = build_lines(snapshot, existing_lines=existing)["matchups"][0]

    assert matchup["prime_time"] is False
    assert matchup["neutral_site"] is False
