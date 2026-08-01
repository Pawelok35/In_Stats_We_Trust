"""Operator-layer contracts for the NFL 2026 pregame decision system."""

from pregame.candidate_registry import (
    CandidateRegistryError,
    CandidateRegistryService,
    candidate_record_event_id,
)
from pregame.contracts import (
    CandidateRecord,
    FinalQuoteGateResult,
    FinalQuotePolicy,
    MarketSnapshot,
    OperatorDecision,
    PregameEvent,
    PregameGameRecord,
)
from pregame.events import (
    CandidateStatus,
    DecisionLevel,
    ExecutableStatus,
    FinalQuoteGateReason,
    FinalQuoteGateStatus,
    MarketQualityStatus,
    MarketType,
    OperatorVerdict,
    PregameEventType,
    SnapshotKind,
)
from pregame.final_quote_gate import (
    FinalQuoteGateError,
    FinalQuoteGateService,
    evaluate_final_quote,
    final_quote_evaluation_id,
    final_quote_gate_event_id,
)
from pregame.jsonl_store import EventStoreCorruptionError, JsonlPregameEventStore
from pregame.market_history import (
    MarketSnapshotHistoryError,
    MarketSnapshotHistoryService,
    market_snapshot_event_id,
)
from pregame.model_output_adapter import (
    CandidateImportResult,
    MatchupBatchPickOutputAdapter,
    ModelOutputImportError,
    candidate_id_for_scan,
    model_scan_id,
)
from pregame.projector import PregameGameProjector, ProjectionError, project_events, project_game
from pregame.store import AppendResult, AppendStatus, InMemoryPregameEventStore, PregameEventStore

__all__ = [
    "AppendResult",
    "AppendStatus",
    "CandidateRecord",
    "CandidateImportResult",
    "CandidateRegistryError",
    "CandidateRegistryService",
    "CandidateStatus",
    "DecisionLevel",
    "ExecutableStatus",
    "FinalQuoteGateError",
    "FinalQuoteGateReason",
    "FinalQuoteGateResult",
    "FinalQuoteGateService",
    "FinalQuoteGateStatus",
    "FinalQuotePolicy",
    "EventStoreCorruptionError",
    "InMemoryPregameEventStore",
    "MatchupBatchPickOutputAdapter",
    "JsonlPregameEventStore",
    "MarketQualityStatus",
    "MarketSnapshot",
    "MarketSnapshotHistoryError",
    "MarketSnapshotHistoryService",
    "MarketType",
    "OperatorDecision",
    "OperatorVerdict",
    "PregameEvent",
    "PregameGameProjector",
    "PregameGameRecord",
    "PregameEventStore",
    "PregameEventType",
    "SnapshotKind",
    "ProjectionError",
    "ModelOutputImportError",
    "candidate_id_for_scan",
    "candidate_record_event_id",
    "model_scan_id",
    "project_events",
    "project_game",
    "market_snapshot_event_id",
    "evaluate_final_quote",
    "final_quote_evaluation_id",
    "final_quote_gate_event_id",
]
