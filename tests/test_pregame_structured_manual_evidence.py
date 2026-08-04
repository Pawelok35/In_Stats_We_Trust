from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from pregame.candidate_registry import CandidateRegistryService
from pregame.contracts import (
    CandidateRecord,
    InjuryObservationPayload,
    MarketSnapshot,
    PublicBettingObservationPayload,
    RosterObservationPayload,
    StructuredManualEvidenceRecord,
    WeatherObservationPayload,
)
from pregame.events import (
    ExecutableStatus,
    MarketQualityStatus,
    MarketType,
    PregameEventType,
    SnapshotKind,
    StructuredManualEvidenceCategory,
)
from pregame.jsonl_store import JsonlPregameEventStore
from pregame.manual_evidence import (
    StructuredManualEvidenceError,
    StructuredManualEvidenceRegistryService,
    structured_manual_evidence_event_id,
)
from pregame.market_history import MarketSnapshotHistoryService
from pregame.store import AppendStatus, InMemoryPregameEventStore

GAME_ID = "2026_w01_BUF_at_HOU"
OTHER_GAME_ID = "2026_w01_NE_at_SEA"
NOW = datetime(2026, 9, 8, 18, tzinfo=timezone.utc)


def candidate(*, game_id: str = GAME_ID, candidate_id: str = "candidate-1") -> CandidateRecord:
    return CandidateRecord(
        candidate_id=candidate_id,
        game_id=game_id,
        season=2026,
        week=1,
        away="BUF",
        home="HOU",
        status="MODEL_CANDIDATE",
        created_at_utc=NOW,
        model_variant="variant_m",
        selected_team="BUF",
        model_tag="VALUE PLAY",
        production_eligible=True,
    )


def snapshot(*, snapshot_id: str = "snapshot-1", game_id: str = GAME_ID) -> MarketSnapshot:
    return MarketSnapshot(
        snapshot_id=snapshot_id,
        game_id=game_id,
        snapshot_kind=SnapshotKind.CURRENT,
        captured_at_utc=NOW,
        book="Book A",
        source="test",
        market_type=MarketType.SPREAD,
        quality_status=MarketQualityStatus.MARKET_GRADE,
        executable_status=ExecutableStatus.CONFIRMED,
        selected_side="BUF",
        spread=-1.5,
        spread_price=-110,
    )


def service(store):
    candidates = CandidateRegistryService(store)
    markets = MarketSnapshotHistoryService(store)
    return (
        StructuredManualEvidenceRegistryService(
            store=store, candidates=candidates, market_history=markets
        ),
        candidates,
        markets,
    )


def observation(
    *,
    observation_id: str = "injury-1",
    category: StructuredManualEvidenceCategory = StructuredManualEvidenceCategory.INJURY,
    payload=None,
    game_id: str = GAME_ID,
    source_name: str = "Official Team",
    observed_at_utc: datetime = NOW,
    recorded_at_utc: datetime = NOW,
    effective_at_utc: datetime | None = None,
    candidate_id: str | None = None,
    supersedes_observation_id: str | None = None,
) -> StructuredManualEvidenceRecord:
    payload = payload or InjuryObservationPayload(
        team="BUF", player_name="Player One", report_status="QUESTIONABLE"
    )
    return StructuredManualEvidenceRecord(
        observation_id=observation_id,
        game_id=game_id,
        category=category,
        source_name=source_name,
        source_type="OFFICIAL",
        source_reference="source:1",
        observed_at_utc=observed_at_utc,
        recorded_at_utc=recorded_at_utc,
        effective_at_utc=effective_at_utc,
        candidate_id=candidate_id,
        supersedes_observation_id=supersedes_observation_id,
        payload=payload,
    )


def test_valid_category_observations_project_factual_fields():
    store = InMemoryPregameEventStore()
    registry, _, _ = service(store)
    cases = [
        observation(),
        observation(
            observation_id="roster-1",
            category=StructuredManualEvidenceCategory.ROSTER,
            effective_at_utc=NOW,
            payload=RosterObservationPayload(
                team="BUF", player_name="Player Two", transaction_type="ACTIVATED"
            ),
        ),
        observation(
            observation_id="weather-1",
            category=StructuredManualEvidenceCategory.WEATHER,
            payload=WeatherObservationPayload(
                venue="NRG Stadium", forecast_valid_for_utc=NOW, indoor=True
            ),
        ),
        observation(
            observation_id="public-1",
            category=StructuredManualEvidenceCategory.PUBLIC_BETTING,
            payload=PublicBettingObservationPayload(
                provider_scope="US",
                market_type=MarketType.SPREAD,
                market_scope="FULL_GAME",
                selected_side="BUF",
                tickets_percentage=72.0,
            ),
        ),
    ]

    for item in cases:
        assert registry.record(observation=item).append_result.status == AppendStatus.APPENDED

    state = registry.record(observation=cases[-1]).projected_game
    assert len(state.structured_manual_evidence) == 4
    assert len(state.active_structured_manual_evidence) == 4
    assert state.structured_manual_evidence[0].payload.player_name == "Player One"
    public = next(
        item for item in state.structured_manual_evidence if item.observation_id == "public-1"
    )
    assert public.payload.tickets_percentage == 72.0


@pytest.mark.parametrize("value", [-0.1, 100.1, math.nan, math.inf, "72%"])
def test_public_percentages_fail_closed(value):
    with pytest.raises((ValidationError, ValueError)):
        PublicBettingObservationPayload(
            provider_scope="US",
            market_type=MarketType.SPREAD,
            market_scope="FULL_GAME",
            selected_side="BUF",
            tickets_percentage=value,
        )


@pytest.mark.parametrize("value", [math.nan, math.inf])
def test_weather_non_finite_values_fail_closed(value):
    with pytest.raises(ValidationError):
        WeatherObservationPayload(venue="NRG", forecast_valid_for_utc=NOW, wind_speed=value)


@pytest.mark.parametrize(
    "field,value",
    [
        ("source_name", ""),
        ("source_type", ""),
        ("source_reference", ""),
        ("observed_at_utc", None),
        ("recorded_at_utc", None),
    ],
)
def test_required_provenance_fails_closed(field, value):
    values = observation().model_dump()
    values[field] = value
    with pytest.raises(ValidationError):
        StructuredManualEvidenceRecord.model_validate(values)


def test_category_timestamp_and_fact_only_validation():
    with pytest.raises(ValidationError):
        StructuredManualEvidenceRecord.model_validate(
            {**observation().model_dump(), "category": "NOT_SUPPORTED"}
        )
    with pytest.raises(ValidationError):
        StructuredManualEvidenceRecord.model_validate(
            {**observation().model_dump(), "observed_at_utc": datetime(2026, 9, 8, 18)}
        )
    with pytest.raises(ValidationError):
        StructuredManualEvidenceRecord.model_validate(
            {
                **observation().model_dump(),
                "observed_at_utc": datetime(2026, 9, 8, 19, tzinfo=timezone(timedelta(hours=1))),
            }
        )
    with pytest.raises(ValidationError):
        InjuryObservationPayload(
            team="BUF", player_name="Player One", report_status="QUESTIONABLE", blocking="YES"
        )
    with pytest.raises(ValidationError):
        PublicBettingObservationPayload(
            provider_scope="US",
            market_type=MarketType.SPREAD,
            market_scope="FULL_GAME",
            selected_side="BUF",
            tickets_percentage=70,
            public_bias="YES",
        )


def test_candidate_and_market_snapshot_links_are_explicit_only():
    store = InMemoryPregameEventStore()
    registry, candidates, markets = service(store)
    item = candidate()
    assert candidates.record_candidate(item, recorded_at_utc=NOW).status == AppendStatus.APPENDED
    assert (
        registry.record(
            observation=observation(candidate_id=item.candidate_id)
        ).append_result.status
        == AppendStatus.APPENDED
    )
    with pytest.raises(StructuredManualEvidenceError, match="candidate_id was not found"):
        registry.record(
            observation=observation(observation_id="unknown-candidate", candidate_id="missing")
        )
    other_candidate = candidate(game_id=OTHER_GAME_ID, candidate_id="candidate-other")
    assert (
        candidates.record_candidate(other_candidate, recorded_at_utc=NOW).status
        == AppendStatus.APPENDED
    )
    with pytest.raises(StructuredManualEvidenceError, match="another game"):
        registry.record(
            observation=observation(
                observation_id="other-game-candidate", candidate_id=other_candidate.candidate_id
            )
        )

    market = snapshot()
    assert markets.record_snapshot(market, recorded_at_utc=NOW).status == AppendStatus.APPENDED
    public = observation(
        observation_id="linked-public",
        category=StructuredManualEvidenceCategory.PUBLIC_BETTING,
        payload=PublicBettingObservationPayload(
            provider_scope="US",
            market_type=MarketType.SPREAD,
            market_scope="FULL_GAME",
            selected_side="BUF",
            tickets_percentage=70,
            market_snapshot_id=market.snapshot_id,
        ),
    )
    assert registry.record(observation=public).append_result.status == AppendStatus.APPENDED
    with pytest.raises(StructuredManualEvidenceError, match="market_type mismatch"):
        registry.record(
            observation=observation(
                observation_id="market-type-mismatch",
                category=StructuredManualEvidenceCategory.PUBLIC_BETTING,
                payload=PublicBettingObservationPayload(
                    provider_scope="US",
                    market_type=MarketType.TOTAL,
                    market_scope="FULL_GAME",
                    selected_side="BUF",
                    tickets_percentage=70,
                    market_snapshot_id=market.snapshot_id,
                ),
            )
        )
    assert (
        registry.record(
            observation=observation(
                observation_id="unlinked-public",
                category=StructuredManualEvidenceCategory.PUBLIC_BETTING,
                payload=PublicBettingObservationPayload(
                    provider_scope="US",
                    market_type=MarketType.SPREAD,
                    market_scope="FULL_GAME",
                    selected_side="BUF",
                    tickets_percentage=70,
                ),
            )
        ).append_result.status
        == AppendStatus.APPENDED
    )


def test_idempotency_conflict_supersession_and_source_coexistence():
    store = InMemoryPregameEventStore()
    registry, _, _ = service(store)
    first = observation(observed_at_utc=NOW, recorded_at_utc=NOW)
    assert registry.record(observation=first).append_result.status == AppendStatus.APPENDED
    rerun = registry.record(observation=first)
    assert rerun.append_result.status == AppendStatus.ALREADY_EXISTS
    assert len(store.list_events(GAME_ID)) == 1

    conflict = observation(
        payload=InjuryObservationPayload(team="BUF", player_name="Player One", report_status="OUT")
    )
    assert registry.record(observation=conflict).append_result.status == AppendStatus.CONFLICT
    assert len(store.list_events(GAME_ID)) == 1

    replacement = observation(
        observation_id="injury-2",
        supersedes_observation_id="injury-1",
        observed_at_utc=NOW + timedelta(minutes=5),
        recorded_at_utc=NOW + timedelta(minutes=5),
        payload=InjuryObservationPayload(team="BUF", player_name="Player One", report_status="OUT"),
    )
    state = registry.record(observation=replacement).projected_game
    assert state.superseded_structured_manual_evidence_ids == ("injury-1",)
    assert [item.observation_id for item in state.active_structured_manual_evidence] == ["injury-2"]
    assert state.latest_structured_manual_evidence_by_source_subject[0].observation_id == "injury-2"

    other_source = observation(
        observation_id="injury-other-source",
        source_name="League",
        observed_at_utc=NOW + timedelta(minutes=6),
        recorded_at_utc=NOW + timedelta(minutes=6),
    )
    state = registry.record(observation=other_source).projected_game
    assert {item.observation_id for item in state.active_structured_manual_evidence} == {
        "injury-2",
        "injury-other-source",
    }
    assert len(state.latest_structured_manual_evidence_by_source_subject) == 2


def test_invalid_supersession_and_jsonl_restart(tmp_path):
    path = tmp_path / "events.jsonl"
    store = JsonlPregameEventStore(path)
    registry, _, _ = service(store)
    with pytest.raises(StructuredManualEvidenceError, match="was not found"):
        registry.record(observation=observation(supersedes_observation_id="missing"))

    first = observation()
    registry.record(observation=first)
    with pytest.raises(StructuredManualEvidenceError, match="crosses sources"):
        registry.record(
            observation=observation(
                observation_id="bad-source",
                source_name="League",
                supersedes_observation_id="injury-1",
            )
        )
    with pytest.raises(StructuredManualEvidenceError, match="crosses subjects"):
        registry.record(
            observation=observation(
                observation_id="bad-subject",
                supersedes_observation_id="injury-1",
                payload=InjuryObservationPayload(
                    team="BUF", player_name="Different Player", report_status="OUT"
                ),
            )
        )
    second = observation(
        observation_id="injury-2",
        supersedes_observation_id="injury-1",
        observed_at_utc=NOW + timedelta(minutes=1),
        recorded_at_utc=NOW + timedelta(minutes=1),
    )
    registry.record(observation=second)
    restarted = JsonlPregameEventStore(path)
    state = registry.record(observation=second).projected_game
    assert restarted.duplicate_event_ids == ()
    assert state.superseded_structured_manual_evidence_ids == ("injury-1",)
    assert structured_manual_evidence_event_id("injury-2") == "structured-manual-evidence:injury-2"


def test_cross_category_supersession_and_multiple_subjects_are_preserved():
    store = InMemoryPregameEventStore()
    registry, _, _ = service(store)
    registry.record(observation=observation())
    with pytest.raises(StructuredManualEvidenceError, match="crosses categories"):
        registry.record(
            observation=observation(
                observation_id="wrong-category",
                category=StructuredManualEvidenceCategory.ROSTER,
                effective_at_utc=NOW,
                supersedes_observation_id="injury-1",
                payload=RosterObservationPayload(
                    team="BUF", player_name="Player One", transaction_type="ACTIVATED"
                ),
            )
        )
    registry.record(
        observation=observation(
            observation_id="injury-player-two",
            payload=InjuryObservationPayload(
                team="BUF", player_name="Player Two", report_status="QUESTIONABLE"
            ),
        )
    )
    state = registry.record(observation=observation()).projected_game
    assert {item.subject_key for item in state.active_structured_manual_evidence} == {
        "INJURY|BUF|Player One",
        "INJURY|BUF|Player Two",
    }


def test_legacy_manual_events_remain_pass_through():
    store = InMemoryPregameEventStore()
    registry, _, _ = service(store)
    from pregame.contracts import PregameEvent

    store.append(
        PregameEvent(
            event_id="legacy",
            game_id=GAME_ID,
            event_type=PregameEventType.INJURY_UPDATED,
            created_at_utc=NOW,
            effective_at_utc=NOW,
            source="legacy",
            payload={"status": "DNP"},
        )
    )
    state = registry.record(observation=observation()).projected_game
    assert [item.observation_id for item in state.structured_manual_evidence] == ["injury-1"]
