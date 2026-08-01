from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from pregame.candidate_registry import CandidateRegistryService
from pregame.contracts import CandidateRecord, FinalQuotePolicy, MarketSnapshot
from pregame.events import (
    CandidateStatus,
    ExecutableStatus,
    FinalQuoteGateReason,
    FinalQuoteGateStatus,
    MarketQualityStatus,
    MarketType,
    SnapshotKind,
)
from pregame.final_quote_gate import (
    FinalQuoteGateError,
    FinalQuoteGateService,
    evaluate_final_quote,
)
from pregame.market_history import MarketSnapshotHistoryService
from pregame.projector import project_game
from pregame.store import AppendStatus, InMemoryPregameEventStore

GAME_ID = "2026_w01_BUF_at_HOU"


def utc_at(hour: int, minute: int = 0) -> datetime:
    return datetime(2026, 9, 10, hour, minute, tzinfo=timezone.utc)


def candidate(**changes) -> CandidateRecord:
    payload = dict(
        candidate_id="candidate-1",
        game_id=GAME_ID,
        season=2026,
        week=1,
        status=CandidateStatus.MODEL_CANDIDATE,
        created_at_utc=utc_at(18),
        model_generated_at_utc=utc_at(18),
        model_variant="variant_m",
        selected_team="BUF",
        model_tag="VALUE PLAY",
        production_eligible=True,
        spread_at_scan=-2.5,
        price_at_scan=-110,
    )
    payload.update(changes)
    return CandidateRecord(**payload)


def snapshot(**changes) -> MarketSnapshot:
    payload = dict(
        snapshot_id="final-1",
        game_id=GAME_ID,
        snapshot_kind=SnapshotKind.FINAL,
        captured_at_utc=utc_at(19),
        book="BOOK_A",
        source="book_feed",
        market_type=MarketType.SPREAD,
        quality_status=MarketQualityStatus.MARKET_GRADE,
        executable_status=ExecutableStatus.CONFIRMED,
        selected_side="BUF",
        spread=-2.5,
        spread_price=-110,
    )
    payload.update(changes)
    return MarketSnapshot(**payload)


def policy(**changes) -> FinalQuotePolicy:
    payload = dict(
        policy_id="policy-1",
        source="operator_policy",
        selected_team="BUF",
        market_type=MarketType.SPREAD,
        minimum_acceptable_spread=-3.0,
        minimum_acceptable_price=-110,
        max_quote_age_seconds=300,
        allowed_quality_statuses=(MarketQualityStatus.MARKET_GRADE,),
        allowed_executable_statuses=(ExecutableStatus.CONFIRMED,),
        allowed_books=("BOOK_A",),
        key_numbers=(3.0, 7.0, 10.0, 14.0),
        reject_key_number_loss=True,
        created_at_utc=utc_at(18),
    )
    payload.update(changes)
    return FinalQuotePolicy(**payload)


def evaluate(**changes):
    item = candidate(**changes.pop("candidate", {}))
    quote = snapshot(**changes.pop("snapshot", {}))
    limits = policy(**changes.pop("policy", {}))
    evaluated_at = changes.pop("evaluated_at", utc_at(19, 5))
    return evaluate_final_quote(item, quote, limits, evaluated_at_utc=evaluated_at, **changes)


def test_valid_quote_has_only_technical_valid_status():
    result = evaluate()

    assert result.passed is True
    assert result.primary_status == FinalQuoteGateStatus.FINAL_QUOTE_VALID
    assert result.primary_reason is None
    assert result.reason_codes == ()
    assert result.quote_age_seconds == 300


@pytest.mark.parametrize(
    ("snapshot_changes", "reason"),
    [
        ({"snapshot_kind": SnapshotKind.CURRENT}, FinalQuoteGateReason.SNAPSHOT_NOT_FINAL),
        ({"selected_side": None}, FinalQuoteGateReason.SELECTED_SIDE_MISSING),
        ({"selected_side": "HOU"}, FinalQuoteGateReason.SELECTED_SIDE_MISMATCH),
        ({"market_type": MarketType.TOTAL}, FinalQuoteGateReason.WRONG_MARKET_TYPE),
        ({"spread": None}, FinalQuoteGateReason.SPREAD_MISSING),
        ({"spread_price": None}, FinalQuoteGateReason.PRICE_MISSING),
        (
            {"quality_status": MarketQualityStatus.DISPLAYED_UNVERIFIED},
            FinalQuoteGateReason.MARKET_QUALITY_REJECTED,
        ),
        (
            {"executable_status": ExecutableStatus.DISPLAYED_ONLY},
            FinalQuoteGateReason.EXECUTABLE_STATUS_REJECTED,
        ),
        ({"book": "BOOK_B"}, FinalQuoteGateReason.BOOK_REJECTED),
    ],
)
def test_snapshot_checks_return_structured_block_reasons(snapshot_changes, reason):
    result = evaluate(snapshot=snapshot_changes)

    assert result.passed is False
    assert result.primary_status == FinalQuoteGateStatus.FINAL_QUOTE_BLOCKED
    assert reason in result.reason_codes


def test_freshness_boundary_passes_and_future_or_stale_quotes_block():
    assert evaluate(evaluated_at=utc_at(19, 5)).passed is True

    stale = evaluate(
        evaluated_at=utc_at(
            19,
            5,
        )
        + timedelta(seconds=1)
    )
    assert FinalQuoteGateReason.FINAL_QUOTE_STALE in stale.reason_codes
    fractional_stale = evaluate(evaluated_at=utc_at(19, 5) + timedelta(microseconds=1))
    assert FinalQuoteGateReason.FINAL_QUOTE_STALE in fractional_stale.reason_codes
    future = evaluate(snapshot={"captured_at_utc": utc_at(19, 6)})
    assert FinalQuoteGateReason.QUOTE_TIMESTAMP_IN_FUTURE in future.reason_codes


def test_frontiers_use_selected_team_numeric_perspective_and_american_odds():
    acceptable = evaluate(
        snapshot={"spread": -3.0, "spread_price": -110},
        policy={"reject_key_number_loss": False},
    )
    rejected = evaluate(
        snapshot={"spread": -3.5, "spread_price": -115},
        policy={"reject_key_number_loss": False},
    )

    assert acceptable.passed is True
    assert FinalQuoteGateReason.FINAL_QUOTE_OUTSIDE_FRONTIER in rejected.reason_codes
    assert FinalQuoteGateReason.FINAL_PRICE_REJECTED in rejected.reason_codes


def test_no_chase_is_explicit_and_key_number_loss_can_warn_or_block():
    blocked = evaluate(
        candidate={"spread_at_scan": -2.5},
        snapshot={"spread": -3.0},
        policy={"minimum_acceptable_spread": -3.0, "no_chase_minimum_spread": -2.5},
    )
    warned = evaluate(
        candidate={"spread_at_scan": 3.5},
        snapshot={"spread": 3.0},
        policy={"reject_key_number_loss": False},
    )

    assert FinalQuoteGateReason.NO_CHASE_BLOCK in blocked.reason_codes
    assert FinalQuoteGateReason.KEY_NUMBER_LOST in blocked.reason_codes
    assert blocked.crossed_or_lost_key_numbers == (3.0,)
    assert warned.passed is True
    assert warned.crossed_or_lost_key_numbers == (3.0,)
    assert warned.warnings == ("key_number_loss_allowed_by_policy:3",)


def test_candidate_and_policy_checks_are_deterministic_and_complete():
    result = evaluate(
        candidate={"status": CandidateStatus.BLOCKED, "production_eligible": False},
        policy={
            "selected_team": "HOU",
            "market_type": MarketType.TOTAL,
            "minimum_acceptable_price": None,
        },
        latest_candidate_id="candidate-2",
    )

    assert result.primary_reason == FinalQuoteGateReason.POLICY_SELECTED_TEAM_MISMATCH
    assert set(result.reason_codes) >= {
        FinalQuoteGateReason.POLICY_SELECTED_TEAM_MISMATCH,
        FinalQuoteGateReason.POLICY_MARKET_MISMATCH,
        FinalQuoteGateReason.POLICY_INCOMPLETE,
        FinalQuoteGateReason.CANDIDATE_BLOCKED,
        FinalQuoteGateReason.CANDIDATE_NOT_PRODUCTION_ELIGIBLE,
        FinalQuoteGateReason.CANDIDATE_NOT_LATEST,
    }


def test_service_uses_explicit_ids_preserves_book_and_records_idempotently():
    store = InMemoryPregameEventStore()
    registry = CandidateRegistryService(store)
    history = MarketSnapshotHistoryService(store)
    item = candidate()
    quote = snapshot()
    registry.record_candidate(item, recorded_at_utc=utc_at(18))
    history.record_snapshot(quote, recorded_at_utc=utc_at(19))
    service = FinalQuoteGateService(registry, history, store)

    result, first = service.evaluate_and_record(
        candidate_id=item.candidate_id,
        final_snapshot_id=quote.snapshot_id,
        policy=policy(),
        evaluated_at_utc=utc_at(19, 5),
        recorded_at_utc=utc_at(19, 6),
    )
    repeated, second = service.evaluate_and_record(
        candidate_id=item.candidate_id,
        final_snapshot_id=quote.snapshot_id,
        policy=policy(),
        evaluated_at_utc=utc_at(19, 5),
        recorded_at_utc=utc_at(19, 6),
    )
    projected = project_game(store, GAME_ID)

    assert first.status == AppendStatus.APPENDED
    assert second.status == AppendStatus.ALREADY_EXISTS
    assert repeated.evaluation_id == result.evaluation_id
    assert projected.final_quote_gate_passed is True
    assert projected.final_quote_gate_status == FinalQuoteGateStatus.FINAL_QUOTE_VALID
    assert projected.current_decision_level.value == "MODEL_CANDIDATE"


def test_service_blocks_stale_candidate_and_snapshot_versions_without_autoselection():
    store = InMemoryPregameEventStore()
    registry = CandidateRegistryService(store)
    history = MarketSnapshotHistoryService(store)
    first_candidate = candidate(candidate_id="candidate-1")
    latest_candidate = candidate(candidate_id="candidate-2", model_generated_at_utc=utc_at(18, 30))
    old_quote = snapshot(snapshot_id="final-old", captured_at_utc=utc_at(19))
    latest_quote = snapshot(snapshot_id="final-new", captured_at_utc=utc_at(19, 1))
    for item in (first_candidate, latest_candidate):
        registry.record_candidate(item, recorded_at_utc=item.created_at_utc)
    for quote in (old_quote, latest_quote):
        history.record_snapshot(quote, recorded_at_utc=utc_at(19, 2))

    result = FinalQuoteGateService(registry, history, store).evaluate(
        candidate_id="candidate-1",
        final_snapshot_id="final-old",
        policy=policy(),
        evaluated_at_utc=utc_at(19, 5),
    )

    assert FinalQuoteGateReason.CANDIDATE_NOT_LATEST in result.reason_codes
    assert FinalQuoteGateReason.FINAL_SNAPSHOT_NOT_LATEST_FOR_BOOK in result.reason_codes


def test_service_missing_explicit_records_raises_dedicated_domain_error():
    service = FinalQuoteGateService(
        CandidateRegistryService(InMemoryPregameEventStore()),
        MarketSnapshotHistoryService(InMemoryPregameEventStore()),
        InMemoryPregameEventStore(),
    )
    with pytest.raises(FinalQuoteGateError, match="Candidate not found"):
        service.evaluate(
            candidate_id="missing",
            final_snapshot_id="also-missing",
            policy=policy(),
            evaluated_at_utc=utc_at(19),
        )


def test_contradictory_preserved_preflight_metadata_is_a_domain_error():
    with pytest.raises(FinalQuoteGateError, match="conflicts"):
        evaluate(candidate={"source_metadata": {"preflight": {"production_eligible": False}}})
