from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from pregame.candidate_registry import CandidateRegistryService
from pregame.model_output_adapter import MatchupBatchPickOutputAdapter, ModelOutputImportError
from pregame.projector import project_game
from pregame.store import InMemoryPregameEventStore
from scripts import matchup_batch


def _install_current_writer_fixture(monkeypatch) -> None:
    def fake_run(*args, **kwargs):
        return SimpleNamespace(
            text="analysis",
            projection=SimpleNamespace(
                tag="GOY",
                model_winner="BAL",
                market_winner="BAL",
                confidence=82.0,
                adv_model=7.0,
                adv_market=3.5,
                edge_vs_line=3.5,
                winner_line=-3.5,
            ),
        )

    monkeypatch.setattr(matchup_batch.matchup_analyzer, "run", fake_run)


def _write_current_writer_config(tmp_path: Path) -> tuple[Path, Path]:
    report = tmp_path / "data" / "reports" / "comparisons" / "2025_w2" / "BAL_vs_MIA.md"
    report.parent.mkdir(parents=True)
    report.write_text("# BAL vs MIA\n", encoding="utf-8")
    config = tmp_path / "week2_lines.yaml"
    config.write_text(
        f"""
matchups:
  - home: BAL
    away: MIA
    spread: -3.5
    total: 44.5
    price: -110
    quote_id: TEST_QUOTE_001
    book: TEST_BOOK
    decision_ts_utc: "2025-09-10T18:00:00Z"
    report: {report}
""",
        encoding="utf-8",
    )
    tag_config = tmp_path / "variant_m.yaml"
    tag_config.write_text("GOY: {}\n", encoding="utf-8")
    return config, tag_config


def _run_current_writer(tmp_path: Path, monkeypatch, *, unsafe_bypass: bool = False) -> dict:
    _install_current_writer_fixture(monkeypatch)
    config, tag_config = _write_current_writer_config(tmp_path)
    picks_dir = tmp_path / ("unsafe_picks" if unsafe_bypass else "picks")
    matchup_batch.run_batch(
        config_path=config,
        output_dir=None,
        default_window=None,
        strict=True,
        combined_output=None,
        picks_dir=picks_dir,
        tag_config=tag_config,
        enforce_preflight=not unsafe_bypass,
        unsafe_test_only_bypass=unsafe_bypass,
    )
    path = picks_dir / "2025" / "week_02.jsonl"
    return {"path": path, "record": json.loads(path.read_text(encoding="utf-8"))}


def _adapter_and_store():
    store = InMemoryPregameEventStore()
    registry = CandidateRegistryService(store)
    return store, registry, MatchupBatchPickOutputAdapter(registry)


def _recorded_at(record: dict) -> datetime:
    return datetime.fromisoformat(record["generated_at"].replace("Z", "+00:00"))


def test_current_writer_output_flows_to_active_candidate_registry_and_projector(
    tmp_path, monkeypatch
):
    writer = _run_current_writer(tmp_path, monkeypatch)
    record = writer["record"]
    store, registry, adapter = _adapter_and_store()

    assert record["preflight"]["status"] == "PASS"
    assert record["preflight"]["production_eligible"] is True
    assert "warnings" not in record
    assert "reason_codes" not in record

    result = adapter.import_jsonl(
        writer["path"],
        season=2025,
        week=2,
        model_variant="variant_m",
        recorded_at_utc=_recorded_at(record),
        source_ref="current-matchup-batch-fixture",
    )
    candidate = registry.get_candidate(result.candidate_ids[0])
    projected = project_game(store, "2025_w02_MIA_at_BAL")

    assert candidate.season == 2025
    assert candidate.week == 2
    assert candidate.game_id == "2025_w02_MIA_at_BAL"
    assert candidate.selected_team == record["model_winner"]
    assert candidate.model_tag == record["tag"]
    assert candidate.confidence == record["confidence"]
    assert candidate.edge_vs_line == record["edge_vs_line"]
    assert candidate.model_margin == record["model_margin"]
    assert candidate.market_margin_at_scan == record["market_margin"]
    assert candidate.spread_at_scan == record["handicap"]
    assert candidate.price_at_scan == record["price"]
    assert candidate.model_variant == record["model_version"]
    assert candidate.production_eligible is True
    assert candidate.source_metadata["preflight"] == record["preflight"]
    assert (
        store.get_event(f"candidate-record:{candidate.candidate_id}").event_type.value
        == "MODEL_CANDIDATE_CREATED"
    )
    assert projected.current_decision_level.value == "MODEL_CANDIDATE"
    assert projected.research_approved is False
    assert projected.operator_decision is None

    retry = adapter.import_jsonl(
        writer["path"],
        season=2025,
        week=2,
        model_variant="variant_m",
        recorded_at_utc=_recorded_at(record),
        source_ref="current-matchup-batch-fixture",
    )
    assert retry.appended_count == 0
    assert retry.already_exists_count == 1


def test_current_writer_unsafe_bypass_flows_to_blocked_candidate_and_projector(
    tmp_path, monkeypatch
):
    writer = _run_current_writer(tmp_path, monkeypatch, unsafe_bypass=True)
    record = writer["record"]
    store, registry, adapter = _adapter_and_store()

    assert record["preflight"]["status"] == "BYPASSED_UNSAFE"
    assert record["preflight"]["production_eligible"] is False

    result = adapter.import_jsonl(
        writer["path"],
        season=2025,
        week=2,
        model_variant="variant_m",
        recorded_at_utc=_recorded_at(record),
    )
    candidate = registry.get_candidate(result.candidate_ids[0])
    projected = project_game(store, "2025_w02_MIA_at_BAL")

    assert candidate.status.value == "BLOCKED"
    assert candidate.production_eligible is False
    assert "BYPASSED_UNSAFE" in candidate.warnings
    assert (
        store.get_event(f"candidate-record:{candidate.candidate_id}").event_type.value
        == "MODEL_CANDIDATE_BLOCKED"
    )
    assert projected.candidate_status.value == "BLOCKED"
    assert projected.current_decision_level is None
    assert projected.operator_decision is None


def test_legacy_record_without_preflight_blocks_whole_file_before_append(tmp_path, monkeypatch):
    writer = _run_current_writer(tmp_path, monkeypatch)
    valid = writer["record"]
    legacy = dict(valid)
    legacy.pop("preflight")
    source = tmp_path / "legacy-plus-valid.jsonl"
    source.write_text(
        f"{json.dumps(valid)}\n{json.dumps(legacy)}\n",
        encoding="utf-8",
    )
    store, _, adapter = _adapter_and_store()

    with pytest.raises(ModelOutputImportError, match="preflight"):
        adapter.import_jsonl(
            source,
            season=2025,
            week=2,
            model_variant="variant_m",
            recorded_at_utc=_recorded_at(valid),
        )
    assert store.list_all_events() == []


def test_current_writer_schema_drift_guard_requires_nested_preflight_contract(
    tmp_path, monkeypatch
):
    writer = _run_current_writer(tmp_path, monkeypatch)
    record = writer["record"]

    assert {
        "season",
        "week",
        "home",
        "away",
        "tag",
        "model_winner",
        "confidence",
        "model_margin",
        "market_margin",
        "edge_vs_line",
        "handicap",
        "price",
        "model_version",
        "generated_at",
        "preflight",
    }.issubset(record)
    assert {"status", "production_eligible", "bypass_used"}.issubset(record["preflight"])
