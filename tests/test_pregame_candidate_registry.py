from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from pregame.candidate_registry import CandidateRegistryError, CandidateRegistryService
from pregame.contracts import CandidateRecord, PregameEvent
from pregame.events import CandidateStatus, PregameEventType
from pregame.jsonl_store import JsonlPregameEventStore
from pregame.model_output_adapter import (
    MatchupBatchPickOutputAdapter,
    ModelOutputImportError,
    candidate_id_for_scan,
)
from pregame.projector import project_game
from pregame.store import InMemoryPregameEventStore


def utc_at(hour: int, minute: int = 0) -> datetime:
    return datetime(2026, 9, 8, hour, minute, tzinfo=timezone.utc)


def output_row(
    *,
    home: str = "HOU",
    away: str = "BUF",
    selected_team: str = "BUF",
    tag: str = "VALUE PLAY",
    edge: float = 4.88,
    handicap: float = -1.5,
    production_eligible: bool = True,
    preflight_status: str = "PASS",
    generated_at: str | None = "2026-09-08T18:00:00Z",
    model_version: str = "variant_m",
) -> dict:
    row = {
        "season": 2026,
        "week": 1,
        "home": home,
        "away": away,
        "tag": tag,
        "model_winner": selected_team,
        "confidence": 72.5,
        "model_margin": 4.25,
        "market_margin": -1.5,
        "edge_vs_line": edge,
        "handicap": handicap,
        "price": -110,
        "model_version": model_version,
        "preflight": {
            "status": preflight_status,
            "production_eligible": production_eligible,
            "bypass_used": preflight_status == "BYPASSED_UNSAFE",
        },
    }
    if generated_at is not None:
        row["generated_at"] = generated_at
    return row


def write_rows(tmp_path, rows: list[dict], *, name: str = "picks.jsonl"):
    path = tmp_path / name
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
    return path


def adapter_for(store):
    registry = CandidateRegistryService(store)
    return registry, MatchupBatchPickOutputAdapter(registry)


def test_real_pick_output_mapping_and_tag_preservation(tmp_path):
    registry, adapter = adapter_for(InMemoryPregameEventStore())
    path = write_rows(tmp_path, [output_row(tag="GOY")])

    result = adapter.import_jsonl(
        path,
        season=2026,
        week=1,
        model_variant="variant_m",
        recorded_at_utc=utc_at(19),
        source_ref="data/picks_variant_m/2026/week_01.jsonl",
    )
    candidate = registry.get_candidate(result.candidate_ids[0])

    assert candidate.game_id == "2026_w01_BUF_at_HOU"
    assert candidate.away == "BUF"
    assert candidate.home == "HOU"
    assert candidate.selected_team == "BUF"
    assert candidate.model_tag == "GOY"
    assert candidate.confidence == 72.5
    assert candidate.edge_vs_line == 4.88
    assert candidate.spread_at_scan == -1.5
    assert candidate.price_at_scan == -110
    assert candidate.production_eligible is True
    assert candidate.status == CandidateStatus.MODEL_CANDIDATE
    assert candidate.source_ref == "data/picks_variant_m/2026/week_01.jsonl"
    assert candidate.source_record_number == 1
    assert candidate.source_metadata["away"] == candidate.away
    assert candidate.source_metadata["home"] == candidate.home


def test_adapter_preserves_home_team_when_selected_team_is_home(tmp_path):
    registry, adapter = adapter_for(InMemoryPregameEventStore())
    result = adapter.import_jsonl(
        write_rows(
            tmp_path,
            [output_row(home="JAX", away="CLE", selected_team="JAX")],
        ),
        season=2026,
        week=1,
        model_variant="variant_m",
        recorded_at_utc=utc_at(19),
    )

    candidate = registry.get_candidate(result.candidate_ids[0])

    assert candidate.away == "CLE"
    assert candidate.home == "JAX"
    assert candidate.selected_team == "JAX"


@pytest.mark.parametrize(
    ("field", "value"),
    [("home", None), ("away", None), ("home", ""), ("away", "   ")],
)
def test_adapter_rejects_missing_or_empty_authoritative_matchup_team(field, value, tmp_path):
    _, adapter = adapter_for(InMemoryPregameEventStore())
    row = output_row()
    if value is None:
        del row[field]
    else:
        row[field] = value

    with pytest.raises(ModelOutputImportError):
        adapter.import_jsonl(
            write_rows(tmp_path, [row]),
            season=2026,
            week=1,
            model_variant="variant_m",
            recorded_at_utc=utc_at(19),
        )


def test_adapter_does_not_recover_missing_team_from_game_id(tmp_path):
    _, adapter = adapter_for(InMemoryPregameEventStore())
    row = output_row()
    row["game_id"] = "2026_w01_BUF_at_HOU"
    del row["home"]

    with pytest.raises(ModelOutputImportError, match="missing required source fields: home"):
        adapter.import_jsonl(
            write_rows(tmp_path, [row]),
            season=2026,
            week=1,
            model_variant="variant_m",
            recorded_at_utc=utc_at(19),
        )


@pytest.mark.parametrize("tag", ["GOY", "GOM", "GOW", "VALUE PLAY"])
def test_tags_are_preserved_without_reclassification(tag, tmp_path):
    registry, adapter = adapter_for(InMemoryPregameEventStore())
    result = adapter.import_jsonl(
        write_rows(tmp_path, [output_row(tag=tag)]),
        season=2026,
        week=1,
        model_variant="variant_m",
        recorded_at_utc=utc_at(19),
    )
    assert registry.get_candidate(result.candidate_ids[0]).model_tag == tag


def test_production_status_mapping_and_projector_integration(tmp_path):
    store = InMemoryPregameEventStore()
    store.append(
        PregameEvent(
            event_id="game",
            game_id="2026_w01_BUF_at_HOU",
            event_type=PregameEventType.GAME_CREATED,
            created_at_utc=utc_at(17),
            effective_at_utc=utc_at(17),
            source="test",
            payload={"season": 2026, "week": 1, "away_team": "BUF", "home_team": "HOU"},
        )
    )
    registry, adapter = adapter_for(store)
    result = adapter.import_jsonl(
        write_rows(tmp_path, [output_row()]),
        season=2026,
        week=1,
        model_variant="variant_m",
        recorded_at_utc=utc_at(19),
    )
    event = store.get_event(f"candidate-record:{result.candidate_ids[0]}")
    record = project_game(store, "2026_w01_BUF_at_HOU")

    assert event.event_type == PregameEventType.MODEL_CANDIDATE_CREATED
    assert record.candidate.status == CandidateStatus.MODEL_CANDIDATE
    assert record.current_decision_level.value == "MODEL_CANDIDATE"

    blocked_store = InMemoryPregameEventStore()
    blocked_registry, blocked_adapter = adapter_for(blocked_store)
    blocked = blocked_adapter.import_jsonl(
        write_rows(
            tmp_path,
            [output_row(production_eligible=False, preflight_status="BYPASSED_UNSAFE")],
            name="blocked.jsonl",
        ),
        season=2026,
        week=1,
        model_variant="variant_m",
        recorded_at_utc=utc_at(19),
    )
    blocked_event = blocked_store.get_event(f"candidate-record:{blocked.candidate_ids[0]}")
    blocked_record = project_game(blocked_store, "2026_w01_BUF_at_HOU")

    assert blocked_event.event_type == PregameEventType.MODEL_CANDIDATE_BLOCKED
    assert blocked_record.candidate_status == CandidateStatus.BLOCKED
    assert blocked_record.current_decision_level is None
    assert "BYPASSED_UNSAFE" in blocked_record.candidate.warnings


def test_missing_production_eligible_is_import_error_before_append(tmp_path):
    store = InMemoryPregameEventStore()
    _, adapter = adapter_for(store)
    row = output_row()
    del row["preflight"]["production_eligible"]

    with pytest.raises(ModelOutputImportError, match="production_eligible"):
        adapter.import_jsonl(
            write_rows(tmp_path, [row]),
            season=2026,
            week=1,
            model_variant="variant_m",
            recorded_at_utc=utc_at(19),
        )
    assert store.list_all_events() == []


def test_scan_and_candidate_ids_are_deterministic_across_whitespace_and_order(tmp_path):
    rows = [
        output_row(home="HOU", away="BUF", selected_team="BUF"),
        output_row(home="LV", away="MIA", selected_team="MIA", edge=2.1),
    ]
    first = write_rows(tmp_path, rows, name="first.jsonl")
    second = tmp_path / "second.jsonl"
    second.write_text(
        "\n".join(json.dumps(row, separators=(", ", ": ")) for row in reversed(rows)) + "\n",
        encoding="utf-8",
    )
    registry, adapter = adapter_for(InMemoryPregameEventStore())
    first_result = adapter.import_jsonl(
        first, season=2026, week=1, model_variant="variant_m", recorded_at_utc=utc_at(19)
    )
    second_result = adapter.import_jsonl(
        second, season=2026, week=1, model_variant="variant_m", recorded_at_utc=utc_at(20)
    )

    assert first_result.scan_id == second_result.scan_id
    assert first_result.candidate_ids == second_result.candidate_ids
    assert second_result.appended_count == 0
    assert second_result.already_exists_count == 2
    assert (
        candidate_id_for_scan(
            first_result.scan_id,
            game_id="2026_w01_BUF_at_HOU",
            selected_team="BUF",
            model_variant="variant_m",
        )
        in first_result.candidate_ids
    )


def test_changed_model_value_creates_new_scan_and_keeps_history(tmp_path):
    registry, adapter = adapter_for(InMemoryPregameEventStore())
    first = adapter.import_jsonl(
        write_rows(tmp_path, [output_row(edge=4.0)], name="one.jsonl"),
        season=2026,
        week=1,
        model_variant="variant_m",
        recorded_at_utc=utc_at(19),
    )
    second = adapter.import_jsonl(
        write_rows(tmp_path, [output_row(edge=5.0)], name="two.jsonl"),
        season=2026,
        week=1,
        model_variant="variant_m",
        recorded_at_utc=utc_at(20),
    )

    assert first.scan_id != second.scan_id
    assert first.candidate_ids != second.candidate_ids
    assert len(registry.list_candidates(2026, 1, game_id="2026_w01_BUF_at_HOU")) == 2
    assert (
        registry.get_latest_candidate("2026_w01_BUF_at_HOU", model_variant="variant_m").edge_vs_line
        == 5.0
    )


def test_duplicate_source_key_malformed_late_line_and_preflight_conflict_append_nothing(tmp_path):
    store = InMemoryPregameEventStore()
    _, adapter = adapter_for(store)
    duplicate = [output_row(), output_row(edge=5.0)]
    with pytest.raises(ModelOutputImportError, match="duplicate source candidate"):
        adapter.import_jsonl(
            write_rows(tmp_path, duplicate),
            season=2026,
            week=1,
            model_variant="variant_m",
            recorded_at_utc=utc_at(19),
        )
    assert store.list_all_events() == []

    malformed = tmp_path / "malformed.jsonl"
    malformed.write_text(json.dumps(output_row()) + "\nnot-json\n", encoding="utf-8")
    with pytest.raises(ModelOutputImportError, match="line 2: invalid JSON"):
        adapter.import_jsonl(
            malformed, season=2026, week=1, model_variant="variant_m", recorded_at_utc=utc_at(19)
        )
    assert store.list_all_events() == []


def test_queries_filters_variants_unknown_timestamp_and_jsonl_restart(tmp_path):
    path = tmp_path / "events.jsonl"
    registry, adapter = adapter_for(JsonlPregameEventStore(path))
    rows = [
        output_row(home="HOU", away="BUF", selected_team="BUF", generated_at=None),
        output_row(home="LV", away="MIA", selected_team="MIA", production_eligible=False),
    ]
    result = adapter.import_jsonl(
        write_rows(tmp_path, rows),
        season=2026,
        week=1,
        model_variant="variant_m",
        recorded_at_utc=utc_at(19),
    )
    other = adapter.import_jsonl(
        write_rows(tmp_path, [output_row(model_version="variant_d_balanced")], name="other.jsonl"),
        season=2026,
        week=1,
        model_variant="variant_d_balanced",
        recorded_at_utc=utc_at(20),
    )
    restarted = CandidateRegistryService(JsonlPregameEventStore(path))

    candidates = restarted.list_candidates(2026, 1, model_variant="variant_m")
    assert len(candidates) == 2
    assert candidates[0].source_sha256 == result.source_sha256
    unknown_timestamp_candidate = next(
        candidate for candidate in candidates if candidate.game_id == "2026_w01_BUF_at_HOU"
    )
    assert "MODEL_GENERATED_AT_UNKNOWN" in unknown_timestamp_candidate.warnings
    assert len(restarted.list_candidates(2026, 1, status=CandidateStatus.BLOCKED)) == 1
    assert len(restarted.list_candidates(2026, 1, model_variant="variant_d_balanced")) == 1
    assert (
        other.candidate_ids[0]
        == restarted.get_latest_candidate(
            "2026_w01_BUF_at_HOU", model_variant="variant_d_balanced"
        ).candidate_id
    )


def test_invalid_direct_candidate_event_and_defensive_query_copies():
    store = InMemoryPregameEventStore()
    registry = CandidateRegistryService(store)
    candidate = CandidateRecord(
        candidate_id="candidate_1",
        game_id="2026_w01_BUF_at_HOU",
        season=2026,
        week=1,
        away="BUF",
        home="HOU",
        status=CandidateStatus.MODEL_CANDIDATE,
        created_at_utc=utc_at(19),
        model_variant="variant_m",
        selected_team="BUF",
        model_tag="GOY",
        production_eligible=True,
    )
    store.append(
        PregameEvent(
            event_id="candidate-record:candidate_1",
            game_id="wrong_game",
            event_type=PregameEventType.MODEL_CANDIDATE_CREATED,
            created_at_utc=utc_at(19),
            effective_at_utc=utc_at(19),
            source="test",
            payload=candidate.to_json_dict(),
        )
    )
    with pytest.raises(CandidateRegistryError, match="payload game_id"):
        registry.list_candidates(2026, 1)

    store = InMemoryPregameEventStore()
    registry = CandidateRegistryService(store)
    registry.record_candidate(candidate, recorded_at_utc=utc_at(19))
    returned = registry.list_candidates(2026, 1)[0]
    returned.warnings.append("MUTATED")
    assert registry.get_candidate("candidate_1").warnings == []


def test_list_all_events_is_deterministic_and_defensive_for_both_backends(tmp_path):
    for store in (InMemoryPregameEventStore(), JsonlPregameEventStore(tmp_path / "events.jsonl")):
        later = PregameEvent(
            event_id="later",
            game_id="g2",
            event_type=PregameEventType.RESEARCH_STARTED,
            created_at_utc=utc_at(20),
            effective_at_utc=utc_at(20),
            source="test",
        )
        early = PregameEvent(
            event_id="early",
            game_id="g1",
            event_type=PregameEventType.RESEARCH_STARTED,
            created_at_utc=utc_at(18),
            effective_at_utc=utc_at(18),
            source="test",
        )
        store.append(later)
        store.append(early)
        events = store.list_all_events()
        assert [event.event_id for event in events] == ["early", "later"]
        events[0].payload["mutated"] = True
        assert store.get_event("early").payload == {}
