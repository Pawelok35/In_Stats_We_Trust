from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from pregame.contracts import CandidateRecord, MarketSnapshot, OperatorDecision, PregameEvent
from pregame.events import (
    CandidateStatus,
    DecisionLevel,
    ExecutableStatus,
    MarketQualityStatus,
    MarketType,
    OperatorVerdict,
    PregameEventType,
    SnapshotKind,
)


def utc_now() -> datetime:
    return datetime(2026, 9, 8, 18, 0, tzinfo=timezone.utc)


def naive_now() -> datetime:
    return datetime(2026, 9, 8, 18, 0)


def test_pregame_event_accepts_valid_event_and_serializes_stably():
    event = PregameEvent(
        event_id="evt_001",
        game_id="2026_w01_BUF_at_HOU",
        event_type=PregameEventType.MODEL_CANDIDATE_CREATED,
        created_at_utc=utc_now(),
        effective_at_utc=utc_now(),
        source="unit_test",
        payload={"edge_vs_line": 4.88, "reason_codes": ["MODEL_EDGE"]},
    )

    payload = event.to_json_dict()

    assert payload["event_type"] == "MODEL_CANDIDATE_CREATED"
    assert payload["created_at_utc"] == "2026-09-08T18:00:00Z"
    assert payload["payload"]["reason_codes"] == ["MODEL_EDGE"]


@pytest.mark.parametrize("field", ["event_id", "game_id"])
def test_pregame_event_rejects_missing_identity(field: str):
    kwargs = {
        "event_id": "evt_001",
        "game_id": "2026_w01_BUF_at_HOU",
        "event_type": PregameEventType.GAME_CREATED,
        "created_at_utc": utc_now(),
        "effective_at_utc": utc_now(),
        "source": "unit_test",
        "payload": {},
    }
    kwargs[field] = ""

    with pytest.raises(ValidationError, match=field):
        PregameEvent(**kwargs)


def test_pregame_event_rejects_naive_timestamp():
    with pytest.raises(ValidationError, match="created_at_utc"):
        PregameEvent(
            event_id="evt_001",
            game_id="2026_w01_BUF_at_HOU",
            event_type=PregameEventType.GAME_CREATED,
            created_at_utc=naive_now(),
            effective_at_utc=utc_now(),
            source="unit_test",
            payload={},
        )


def test_pregame_event_rejects_non_json_payload():
    with pytest.raises(ValidationError, match="JSON-compatible"):
        PregameEvent(
            event_id="evt_001",
            game_id="2026_w01_BUF_at_HOU",
            event_type=PregameEventType.GAME_CREATED,
            created_at_utc=utc_now(),
            effective_at_utc=utc_now(),
            source="unit_test",
            payload={"bad": object()},
        )


def test_market_snapshot_accepts_spread_snapshot_and_keeps_statuses_separate():
    snapshot = MarketSnapshot(
        snapshot_id="snap_001",
        game_id="2026_w01_BUF_at_HOU",
        snapshot_kind=SnapshotKind.INITIAL,
        captured_at_utc=utc_now(),
        book="PREGAME_COM",
        source="screen_extract",
        market_type=MarketType.SPREAD,
        quality_status=MarketQualityStatus.DISPLAYED_UNVERIFIED,
        executable_status=ExecutableStatus.DISPLAYED_ONLY,
        selected_side="BUF",
        spread=-1.5,
        spread_price=-102,
    )

    payload = snapshot.to_json_dict()

    assert payload["snapshot_kind"] == "INITIAL"
    assert payload["market_type"] == "SPREAD"
    assert payload["quality_status"] == "DISPLAYED_UNVERIFIED"
    assert payload["executable_status"] == "DISPLAYED_ONLY"
    assert payload["spread"] == -1.5


def test_market_snapshot_accepts_total_snapshot_without_spread_or_moneyline():
    snapshot = MarketSnapshot(
        snapshot_id="snap_total_001",
        game_id="2026_w01_BUF_at_HOU",
        snapshot_kind=SnapshotKind.CURRENT,
        captured_at_utc=utc_now(),
        book="PREGAME_COM",
        source="screen_extract",
        market_type=MarketType.TOTAL,
        quality_status=MarketQualityStatus.DISPLAYED_UNVERIFIED,
        executable_status=ExecutableStatus.UNVERIFIED,
        total=44.5,
        total_price=-110,
    )

    assert snapshot.spread is None
    assert snapshot.moneyline is None
    assert snapshot.total == 44.5


def test_market_snapshot_allows_missing_price_when_quality_marks_missing_price():
    snapshot = MarketSnapshot(
        snapshot_id="snap_missing_price",
        game_id="2026_w01_BUF_at_HOU",
        snapshot_kind=SnapshotKind.CURRENT,
        captured_at_utc=utc_now(),
        book="PREGAME_COM",
        source="screen_extract",
        market_type=MarketType.SPREAD,
        quality_status=MarketQualityStatus.MISSING_PRICE,
        executable_status=ExecutableStatus.UNKNOWN,
        selected_side="BUF",
        spread=-1.5,
    )

    assert snapshot.spread_price is None
    assert snapshot.quality_status == MarketQualityStatus.MISSING_PRICE
    assert snapshot.executable_status == ExecutableStatus.UNKNOWN


def test_market_snapshot_rejects_naive_captured_timestamp():
    with pytest.raises(ValidationError, match="captured_at_utc"):
        MarketSnapshot(
            snapshot_id="snap_001",
            game_id="2026_w01_BUF_at_HOU",
            snapshot_kind=SnapshotKind.INITIAL,
            captured_at_utc=naive_now(),
            book="PREGAME_COM",
            source="screen_extract",
            market_type=MarketType.SPREAD,
            quality_status=MarketQualityStatus.DISPLAYED_UNVERIFIED,
            executable_status=ExecutableStatus.DISPLAYED_ONLY,
        )


def test_candidate_record_accepts_model_candidate_with_optional_missing_metrics():
    candidate = CandidateRecord(
        candidate_id="cand_001",
        game_id="2026_w01_BUF_at_HOU",
        season=2026,
        week=1,
        away="BUF",
        home="HOU",
        status=CandidateStatus.MODEL_CANDIDATE,
        created_at_utc=utc_now(),
        model_variant="variant_m",
        selected_team="BUF",
        model_tag="VALUE PLAY",
        production_eligible=False,
        warnings=["week_1_limited_current_form"],
        reason_codes=["MODEL_EDGE"],
    )

    payload = candidate.to_json_dict()

    assert payload["status"] == "MODEL_CANDIDATE"
    assert payload["production_eligible"] is False
    assert payload["confidence"] is None
    assert payload["warnings"] == ["week_1_limited_current_form"]
    assert payload["reason_codes"] == ["MODEL_EDGE"]


@pytest.mark.parametrize("field", ["game_id", "selected_team", "away", "home"])
def test_candidate_record_rejects_missing_required_text(field: str):
    kwargs = {
        "candidate_id": "cand_001",
        "game_id": "2026_w01_BUF_at_HOU",
        "season": 2026,
        "week": 1,
        "away": "BUF",
        "home": "HOU",
        "status": CandidateStatus.MODEL_CANDIDATE,
        "created_at_utc": utc_now(),
        "model_variant": "variant_m",
        "selected_team": "BUF",
        "model_tag": "VALUE PLAY",
        "production_eligible": True,
    }
    kwargs[field] = ""

    with pytest.raises(ValidationError, match=field):
        CandidateRecord(**kwargs)


def test_candidate_record_rejects_naive_model_generated_timestamp():
    with pytest.raises(ValidationError, match="model_generated_at_utc"):
        CandidateRecord(
            candidate_id="cand_001",
            game_id="2026_w01_BUF_at_HOU",
            season=2026,
            week=1,
            away="BUF",
            home="HOU",
            status=CandidateStatus.MODEL_CANDIDATE,
            created_at_utc=utc_now(),
            model_variant="variant_m",
            selected_team="BUF",
            model_tag="VALUE PLAY",
            production_eligible=True,
            model_generated_at_utc=naive_now(),
        )


def test_candidate_record_rejects_identical_home_and_away_teams():
    with pytest.raises(ValidationError, match="home and away must be different"):
        CandidateRecord(
            candidate_id="cand_001",
            game_id="2026_w01_BUF_at_BUF",
            season=2026,
            week=1,
            away="BUF",
            home="BUF",
            status=CandidateStatus.MODEL_CANDIDATE,
            created_at_utc=utc_now(),
            model_variant="variant_m",
            selected_team="BUF",
            model_tag="VALUE PLAY",
            production_eligible=True,
        )


@pytest.mark.parametrize(
    "verdict",
    [OperatorVerdict.WAIT, OperatorVerdict.PASS, OperatorVerdict.REJECTED_PRICE],
)
def test_operator_decision_accepts_basic_verdicts(verdict: OperatorVerdict):
    decision = OperatorDecision(
        decision_id=f"decision_{verdict.value.lower()}",
        game_id="2026_w01_BUF_at_HOU",
        verdict=verdict,
        decided_at_utc=utc_now(),
        operator="daniel",
        reason_codes=[verdict.value],
    )

    payload = decision.to_json_dict()

    assert payload["verdict"] == verdict.value
    assert payload["reason_codes"] == [verdict.value]
    assert payload["spread"] is None


def test_operator_decision_rejects_missing_operator():
    with pytest.raises(ValidationError, match="operator"):
        OperatorDecision(
            decision_id="decision_001",
            game_id="2026_w01_BUF_at_HOU",
            verdict=OperatorVerdict.WAIT,
            decided_at_utc=utc_now(),
            operator="",
            reason_codes=["WAIT_FOR_MARKET"],
        )


def test_operator_decision_rejects_naive_timestamp():
    with pytest.raises(ValidationError, match="decided_at_utc"):
        OperatorDecision(
            decision_id="decision_001",
            game_id="2026_w01_BUF_at_HOU",
            verdict=OperatorVerdict.WAIT,
            decided_at_utc=naive_now(),
            operator="daniel",
            reason_codes=["WAIT_FOR_MARKET"],
        )


def test_operator_decision_requires_reason_codes():
    with pytest.raises(ValidationError, match="reason_codes"):
        OperatorDecision(
            decision_id="decision_001",
            game_id="2026_w01_BUF_at_HOU",
            verdict=OperatorVerdict.WAIT,
            decided_at_utc=utc_now(),
            operator="daniel",
            reason_codes=[],
        )


def test_enum_values_are_stable_and_decision_levels_are_not_verdicts():
    assert PregameEventType.FINAL_QUOTE_CAPTURED.value == "FINAL_QUOTE_CAPTURED"
    assert CandidateStatus.WATCHLIST.value == "WATCHLIST"
    assert DecisionLevel.MODEL_CANDIDATE.value == "MODEL_CANDIDATE"
    assert DecisionLevel.RESEARCH_APPROVED.value == "RESEARCH_APPROVED"
    assert DecisionLevel.FINAL_OPERATOR_PICK.value == "FINAL_OPERATOR_PICK"
    assert OperatorVerdict.APPROVED.value == "APPROVED"
    assert OperatorVerdict.WAIT.value == "WAIT"

    decision_level_values = {item.value for item in DecisionLevel}
    verdict_values = {item.value for item in OperatorVerdict}

    assert "FINAL_OPERATOR_PICK" in decision_level_values
    assert "FINAL_OPERATOR_PICK" not in verdict_values
    assert "APPROVED" in verdict_values
    assert "APPROVED" not in decision_level_values
