import polars as pl
import pytest

from utils.contracts import get_contract, list_contracts, validate_df


def test_validate_df_accepts_valid_payload():
    df = pl.DataFrame(
        {
            "season": [2025, 2025],
            "week": [8, 8],
            "game_id": ["G1", "G1"],
            "play_id": [1, 2],
            "posteam": ["AAA", "AAA"],
            "defteam": ["BBB", "BBB"],
            "drive": [1, 1],
            "epa": [0.5, -0.3],
            "success": [1.0, 0.0],
        }
    )

    validated = validate_df(df, "L1")
    assert validated is df


def test_validate_df_missing_required_column():
    df = pl.DataFrame(
        {
            "season": [2025],
            "week": [8],
            "game_id": ["G1"],
            "play_id": [1],
            "posteam": ["AAA"],
            "defteam": ["BBB"],
            # missing drive
            "epa": [0.1],
            "success": [1.0],
        }
    )

    with pytest.raises(ValueError, match="missing required columns.*drive"):
        validate_df(df, "L1")


def test_validate_df_detects_dtype_mismatch():
    df = pl.DataFrame(
        {
            "season": [2025],
            "week": [8],
            "game_id": ["G1"],
            "play_id": ["not-an-int"],
            "posteam": ["AAA"],
            "defteam": ["BBB"],
            "drive": [1],
            "epa": [0.5],
            "success": [1.0],
        }
    )

    with pytest.raises(ValueError, match="column 'play_id'.*expected Int64"):
        validate_df(df, "L1")


def test_get_contract_and_list_contracts():
    available = list_contracts()
    assert {"L1", "L2", "L3", "L4_CORE12", "L4_POWERSCORE", "PICK_OUTPUT"}.issubset(set(available))

    spec = get_contract("L2")
    assert spec.keys == ("season", "week", "game_id", "play_id")
    assert any(col.name == "TEAM" for col in spec.columns)


def test_validate_l4_powerscore_contract():
    df = pl.DataFrame(
        {
            "season": [2025],
            "week": [8],
            "team": ["BAL"],
            "power_score": [0.42],
        }
    )

    assert validate_df(df, "L4_POWERSCORE") is df


def test_validate_pick_output_contract_detects_missing_field():
    df = pl.DataFrame(
        {
            "season": [2025],
            "week": [8],
            "home": ["BAL"],
            "away": ["MIA"],
            "tag": ["GOY"],
            "model_winner": ["BAL"],
            "confidence": [82.0],
            "model_version": ["variant_j"],
            "commit_sha": ["abc123"],
            "config_sha256": ["def456"],
            "data_cutoff": ["2025_w8"],
            # missing handicap
        }
    )

    with pytest.raises(ValueError, match="missing required columns.*handicap"):
        validate_df(df, "PICK_OUTPUT")
