"""Operator-layer contracts for the NFL 2026 pregame decision system."""

from pregame.contracts import (
    CandidateRecord,
    MarketSnapshot,
    OperatorDecision,
    PregameEvent,
    PregameGameRecord,
)
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
from pregame.jsonl_store import EventStoreCorruptionError, JsonlPregameEventStore
from pregame.projector import PregameGameProjector, ProjectionError, project_events, project_game
from pregame.store import AppendResult, AppendStatus, InMemoryPregameEventStore, PregameEventStore

__all__ = [
    "AppendResult",
    "AppendStatus",
    "CandidateRecord",
    "CandidateStatus",
    "DecisionLevel",
    "ExecutableStatus",
    "EventStoreCorruptionError",
    "InMemoryPregameEventStore",
    "JsonlPregameEventStore",
    "MarketQualityStatus",
    "MarketSnapshot",
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
    "project_events",
    "project_game",
]
