from __future__ import annotations

from datetime import timedelta

from pregame.candidate_registry import CandidateRegistryService
from pregame.contracts import FinalQuotePolicy, MarketSnapshot
from pregame.events import ExecutableStatus, MarketQualityStatus, MarketType, SnapshotKind
from pregame.final_quote_gate import FinalQuoteGateService
from pregame.manifest_backed_final_quote_gate import ManifestBackedFinalQuoteGateService
from pregame.market_history import MarketSnapshotHistoryService
from pregame.projector import project_game
from pregame.store import AppendStatus, InMemoryPregameEventStore
from tests.test_pregame_manifest_backed_variant_b_refresh import (
    FIXTURES,
    NOW,
    RULES,
    manifest,
    refresh,
    register_manifest,
    setup,
)
from tests.test_pregame_manifest_backed_variant_b_refresh import (
    run as run_refresh,
)


class CountingGate:
    def __init__(self, inner: FinalQuoteGateService) -> None:
        self.inner = inner
        self.calls = 0

    def evaluate_and_record(self, **kwargs):
        self.calls += 1
        return self.inner.evaluate_and_record(**kwargs)


def final_snapshot(value, snapshot_id="final-1", captured_at=NOW + timedelta(minutes=3)):
    return MarketSnapshot(
        snapshot_id=snapshot_id,
        game_id=value.game_id,
        snapshot_kind=SnapshotKind.FINAL,
        captured_at_utc=captured_at,
        book="BOOK",
        source="DIRECT_SPORTSBOOK",
        market_type=MarketType.SPREAD,
        quality_status=MarketQualityStatus.MARKET_GRADE,
        executable_status=ExecutableStatus.CONFIRMED,
        selected_side=value.selected_team,
        spread=value.spread_at_scan,
        spread_price=value.price_at_scan,
    )


def policy(value):
    return FinalQuotePolicy(
        policy_id="final-policy",
        source="test",
        selected_team=value.selected_team,
        market_type=MarketType.SPREAD,
        minimum_acceptable_spread=value.spread_at_scan,
        minimum_acceptable_price=value.price_at_scan,
        max_quote_age_seconds=600,
        allowed_quality_statuses=(MarketQualityStatus.MARKET_GRADE,),
        allowed_executable_statuses=(ExecutableStatus.CONFIRMED,),
        allowed_books=("BOOK",),
        created_at_utc=NOW,
    )


def ready_service(tmp_path):
    store = InMemoryPregameEventStore()
    value, lineage, central = setup(store)
    item = manifest(value)
    register_manifest(lineage, item)
    audit = run_refresh(
        refresh(store, value, central),
        value,
        item,
        tmp_path,
        build_timestamp_utc=NOW + timedelta(minutes=1),
        recorded_at_utc=NOW + timedelta(minutes=2),
    ).audit_result
    assert audit is not None
    build_id = audit.orchestration_result.build_id
    assert build_id is not None
    markets = MarketSnapshotHistoryService(store)
    quote = final_snapshot(value)
    assert (
        markets.record_snapshot(quote, recorded_at_utc=quote.captured_at_utc).status
        == AppendStatus.APPENDED
    )
    base_gate = FinalQuoteGateService(CandidateRegistryService(store), markets, store)
    gate = CountingGate(base_gate)
    wrapper = ManifestBackedFinalQuoteGateService(
        store=store,
        candidates=CandidateRegistryService(store),
        market_history=markets,
        final_quote_gate=gate,
    )
    return store, value, item, quote, build_id, gate, wrapper


def evaluate(wrapper, value, item, quote, build_id):
    return wrapper.evaluate(
        candidate_id=value.candidate_id,
        audit_build_id=build_id,
        manifest_id=item.manifest_id,
        final_snapshot_id=quote.snapshot_id,
        policy=policy(value),
        evaluated_at_utc=NOW + timedelta(minutes=4),
        recorded_at_utc=NOW + timedelta(minutes=5),
    )


def test_manifest_backed_final_quote_gate_records_lineage_and_is_idempotent(tmp_path):
    store, value, item, quote, build_id, gate, wrapper = ready_service(tmp_path)

    first = evaluate(wrapper, value, item, quote, build_id)
    second = evaluate(wrapper, value, item, quote, build_id)

    assert first.lineage_ready and second.lineage_ready
    assert gate.calls == 2
    assert first.gate_result is not None and second.gate_result is not None
    assert first.gate_result.evaluation_id == second.gate_result.evaluation_id
    assert first.gate_result.research_lineage.audit_build_id == build_id
    assert first.gate_result.research_lineage.manifest_id == item.manifest_id
    assert len(store.list_events(value.game_id)) == len(
        set(event.event_id for event in store.list_events(value.game_id))
    )
    state = project_game(store, value.game_id)
    assert len(state.final_quote_gate_results) == 1
    assert (
        state.final_quote_gate_by_evaluation_id[0].evaluation_id == first.gate_result.evaluation_id
    )
    assert state.structured_variant_b_successful_audit_by_build_id[0].build_id == build_id


def test_different_lineage_changes_evaluation_identity_without_auto_selecting_old_audit(tmp_path):
    store, value, item, quote, build_a, gate, wrapper = ready_service(tmp_path)
    first = evaluate(wrapper, value, item, quote, build_a)
    assert first.gate_result is not None

    # A later successful audit must be explicitly selected and needs a later explicit quote.
    from pregame.central_variant_b_audit import CentralSingleGameVariantBAuditService
    from pregame.manifest_backed_variant_b_refresh import ManifestBackedVariantBAuditRefreshService

    second_audit = (
        ManifestBackedVariantBAuditRefreshService(
            store=store,
            candidates=CandidateRegistryService(store),
            central_audit=CentralSingleGameVariantBAuditService(
                candidates=CandidateRegistryService(store),
                market_history=MarketSnapshotHistoryService(store),
                store=store,
            ),
        )
        .run(
            candidate_id=value.candidate_id,
            model_generation_snapshot_id="quote-1",
            evidence_path=FIXTURES / "evidence.json",
            manifest_id=item.manifest_id,
            rules_path=RULES,
            build_timestamp_utc=NOW + timedelta(minutes=6),
            output_path=tmp_path / "audit-b.json",
            recorded_at_utc=NOW + timedelta(minutes=7),
        )
        .audit_result
    )
    assert second_audit is not None
    build_b = second_audit.orchestration_result.build_id
    assert build_b and build_b != build_a
    later_quote = final_snapshot(value, "final-2", NOW + timedelta(minutes=8))
    MarketSnapshotHistoryService(store).record_snapshot(
        later_quote, recorded_at_utc=later_quote.captured_at_utc
    )
    second = wrapper.evaluate(
        candidate_id=value.candidate_id,
        audit_build_id=build_b,
        manifest_id=item.manifest_id,
        final_snapshot_id=later_quote.snapshot_id,
        policy=policy(value),
        evaluated_at_utc=NOW + timedelta(minutes=9),
        recorded_at_utc=NOW + timedelta(minutes=10),
    )
    assert second.gate_result is not None
    assert second.gate_result.evaluation_id != first.gate_result.evaluation_id
    stale = evaluate(wrapper, value, item, quote, build_a)
    assert stale.readiness_failure_codes == ("AUDIT_NOT_LATEST_SUCCESSFUL",)


def test_readiness_failures_do_not_call_gate(tmp_path):
    _store, value, item, quote, build_id, gate, wrapper = ready_service(tmp_path)
    missing = wrapper.evaluate(
        candidate_id="missing",
        audit_build_id=build_id,
        manifest_id=item.manifest_id,
        final_snapshot_id=quote.snapshot_id,
        policy=policy(value),
        evaluated_at_utc=NOW + timedelta(minutes=4),
        recorded_at_utc=NOW + timedelta(minutes=5),
    )
    mismatch = wrapper.evaluate(
        candidate_id=value.candidate_id,
        audit_build_id=build_id,
        manifest_id="manifest:missing",
        final_snapshot_id=quote.snapshot_id,
        policy=policy(value),
        evaluated_at_utc=NOW + timedelta(minutes=4),
        recorded_at_utc=NOW + timedelta(minutes=5),
    )
    assert missing.readiness_failure_codes == ("CANDIDATE_NOT_FOUND",)
    assert mismatch.readiness_failure_codes == ("MANIFEST_NOT_FOUND",)
    assert gate.calls == 0
