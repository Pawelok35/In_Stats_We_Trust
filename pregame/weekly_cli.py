"""One restartable operator entry point for a persistent pregame week ledger.

Inputs are JSON arrays supplied with ``--input``. The CLI deliberately does not
invent missing authorities: commands report per-record failures and continue.
"""

# ruff: noqa: E501

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from pregame.candidate_registry import CandidateRegistryService
from pregame.central_variant_b_audit import CentralSingleGameVariantBAuditService
from pregame.closing_quote_link import ClosingQuoteLinkService
from pregame.contracts import (
    CandidateRecord,
    MarketSnapshot,
    PregameEvent,
    VariantBEvidenceLineageManifestRecord,
)
from pregame.events import MarketType, OperatorVerdict, PregameEventType
from pregame.evidence_lineage import VariantBEvidenceLineageRegistryService
from pregame.game_result import AuthoritativeGameResultService
from pregame.jsonl_store import JsonlPregameEventStore
from pregame.manifest_backed_operator_decision import ManifestBackedOperatorDecisionService
from pregame.manifest_backed_variant_b_refresh import ManifestBackedVariantBAuditRefreshService
from pregame.market_history import MarketSnapshotHistoryService
from pregame.projector import project_game
from pregame.wager_execution import ManifestBackedWagerExecutionService
from pregame.wager_execution_clv import WagerExecutionClvService
from pregame.wager_execution_settlement import WagerExecutionSettlementService


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _parse_utc(value: Any, *, default: datetime | None = None) -> datetime:
    if value is None:
        if default is None:
            raise ValueError("UTC timestamp is required")
        return default
    if not isinstance(value, str):
        raise ValueError("UTC timestamp must be an ISO string")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise ValueError("UTC timestamp must include a literal UTC offset")
    return parsed.astimezone(timezone.utc)


def _json_input(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if isinstance(value, dict):
        value = value.get("records", value.get("items", []))
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        raise ValueError("input JSON must be an array of objects or {records: [...]}")
    return value


def _event_time(item: dict[str, Any], key: str = "recorded_at_utc") -> datetime:
    return _parse_utc(item.get(key), default=_utc_now())


class WeeklyOperator:
    def __init__(self, *, root: Path, season: int, week: int) -> None:
        self.root = root
        self.season = season
        self.week = week
        self.events_path = root / "events" / str(season) / f"week_{week:02d}.jsonl"
        self.events_path.parent.mkdir(parents=True, exist_ok=True)
        self.store = JsonlPregameEventStore(self.events_path)
        self.candidates = CandidateRegistryService(self.store)
        self.markets = MarketSnapshotHistoryService(self.store)

    def init_week(self) -> dict[str, Any]:
        return {
            "status": "READY",
            "season": self.season,
            "week": self.week,
            "event_store": str(self.events_path),
            "events": len(self.store.list_all_events()),
        }

    def import_games(self, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        output = []
        for item in records:
            game_id = _text(item, "game_id")
            event_id = f"game-created:{game_id}"
            created = _event_time(item)
            payload = {
                "season": _strict_int(item, "season", self.season),
                "week": _strict_int(item, "week", self.week),
                "away_team": _text(item, "away_team"),
                "home_team": _text(item, "home_team"),
                "kickoff_utc": _parse_utc(item.get("kickoff_utc")).isoformat(),
                "neutral_site": item.get("neutral_site"),
            }
            for key in ("venue", "game_type"):
                if key in item:
                    payload[key] = item[key]
            result = self.store.append(
                PregameEvent(
                    event_id=event_id,
                    game_id=game_id,
                    event_type=PregameEventType.GAME_CREATED,
                    created_at_utc=created,
                    effective_at_utc=created,
                    source=item.get("source", "operator_schedule"),
                    idempotency_key=event_id,
                    payload=payload,
                )
            )
            output.append(_result(item, result.status.value, result.message))
        return output

    def import_candidates(self, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        output = []
        for item in records:
            try:
                candidate = CandidateRecord.model_validate(item)
                result = self.candidates.record_candidate(
                    candidate, recorded_at_utc=_event_time(item)
                )
                output.append(_result(item, result.status.value, result.message))
            except (ValidationError, ValueError) as exc:
                output.append(_result(item, "BLOCKED", str(exc)))
        return output

    def import_market_snapshots(self, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        output = []
        for item in records:
            try:
                snapshot = MarketSnapshot.model_validate(item)
                result = self.markets.record_snapshot(snapshot, recorded_at_utc=_event_time(item))
                output.append(_result(item, result.status.value, result.message))
            except (ValidationError, ValueError) as exc:
                output.append(_result(item, "BLOCKED", str(exc)))
        return output

    def build_audits(self, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        service = ManifestBackedVariantBAuditRefreshService(
            store=self.store,
            candidates=self.candidates,
            central_audit=CentralSingleGameVariantBAuditService(
                candidates=self.candidates,
                market_history=self.markets,
                store=self.store,
            ),
        )
        output = []
        for item in records:
            try:
                result = service.run(
                    candidate_id=_text(item, "candidate_id"),
                    model_generation_snapshot_id=_text(item, "model_generation_snapshot_id"),
                    evidence_path=Path(_text(item, "evidence_path")),
                    manifest_id=_text(item, "manifest_id"),
                    rules_path=Path(_text(item, "rules_path")),
                    build_timestamp_utc=_parse_utc(item.get("build_timestamp_utc")),
                    output_path=Path(_text(item, "output_path")),
                    recorded_at_utc=_parse_utc(item.get("recorded_at_utc")),
                )
                output.append(
                    _result(
                        item,
                        "COMPLETED" if result.audit_result else "BLOCKED",
                        result.error,
                    )
                )
            except (ValidationError, ValueError, OSError) as exc:
                output.append(_result(item, "BLOCKED", str(exc)))
        return output

    def register_lineage(self, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        service = VariantBEvidenceLineageRegistryService(
            store=self.store, candidates=self.candidates
        )
        output = []
        for item in records:
            try:
                manifest = VariantBEvidenceLineageManifestRecord.model_validate(item["manifest"])
                result = service.record(
                    manifest=manifest, evidence_path=Path(_text(item, "evidence_path"))
                )
                output.append(
                    _result(
                        item,
                        result.append_result.status.value,
                        result.append_result.message,
                    )
                )
            except (ValidationError, ValueError, OSError) as exc:
                output.append(_result(item, "BLOCKED", str(exc)))
        return output

    def register_decisions(self, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        service = ManifestBackedOperatorDecisionService(
            store=self.store, candidates=self.candidates, market_history=self.markets
        )
        output = []
        for item in records:
            try:
                result = service.record(
                    decision_id=_text(item, "decision_id"),
                    candidate_id=_text(item, "candidate_id"),
                    gate_evaluation_id=_text(item, "gate_evaluation_id"),
                    verdict=OperatorVerdict(_text(item, "verdict")),
                    stake_units=item.get("stake_units"),
                    operator_id=_text(item, "operator_id"),
                    reason_codes=tuple(item.get("reason_codes", ())),
                    decision_at_utc=_parse_utc(item.get("decision_at_utc")),
                    recorded_at_utc=_parse_utc(item.get("recorded_at_utc")),
                    supersedes_decision_id=item.get("supersedes_decision_id"),
                    operator_display_name=item.get("operator_display_name"),
                    notes=item.get("notes"),
                )
                output.append(
                    _result(
                        item, _status_from_result(result), ";".join(result.readiness_failure_codes)
                    )
                )
            except (ValidationError, ValueError) as exc:
                output.append(_result(item, "BLOCKED", str(exc)))
        return output

    def record_executions(self, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        service = ManifestBackedWagerExecutionService(store=self.store)
        output = []
        for item in records:
            try:
                result = service.record(
                    execution_id=_text(item, "execution_id"),
                    decision_id=_text(item, "decision_id"),
                    market_type=MarketType(item["market_type"]),
                    selected_side=_text(item, "selected_side"),
                    spread=item["spread"],
                    price=item["price"],
                    book=_text(item, "book"),
                    stake_units=item["stake_units"],
                    executed_at_utc=_parse_utc(item.get("executed_at_utc")),
                    recorded_at_utc=_parse_utc(item.get("recorded_at_utc")),
                    external_ticket_id=item.get("external_ticket_id"),
                )
                output.append(
                    _result(
                        item, _status_from_result(result), ";".join(result.readiness_failure_codes)
                    )
                )
            except (ValidationError, ValueError, KeyError) as exc:
                output.append(_result(item, "BLOCKED", str(exc)))
        return output

    def link_closing(self, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        service = ClosingQuoteLinkService(store=self.store)
        output = []
        for item in records:
            result = service.record(
                execution_id=_text(item, "execution_id"),
                closing_snapshot_id=_text(item, "closing_snapshot_id"),
                linked_at_utc=_parse_utc(item.get("linked_at_utc")),
            )
            output.append(
                _result(item, _status_from_result(result), ";".join(result.readiness_failure_codes))
            )
        return output

    def import_results(self, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        service = AuthoritativeGameResultService(store=self.store)
        output = []
        for item in records:
            try:
                result = service.record(
                    game_id=_text(item, "game_id"),
                    home_score=item["home_score"],
                    away_score=item["away_score"],
                    source=_text(item, "source"),
                    source_reference=_text(item, "source_reference"),
                    source_finalized_at_utc=_parse_utc(item.get("source_finalized_at_utc")),
                    observed_at_utc=_parse_utc(item.get("observed_at_utc")),
                    overtime=item.get("overtime"),
                )
                output.append(
                    _result(
                        item, _status_from_result(result), ";".join(result.readiness_failure_codes)
                    )
                )
            except (ValidationError, ValueError, KeyError) as exc:
                output.append(_result(item, "BLOCKED", str(exc)))
        return output

    def settle_ready(self) -> list[dict[str, Any]]:
        service = WagerExecutionSettlementService(store=self.store)
        output = []
        for state in self._states():
            for execution in state.wager_execution_history:
                if state.has_execution_settlement(execution.execution_id):
                    continue
                result = service.record(
                    execution_id=execution.execution_id, settled_at_utc=_utc_now()
                )
                output.append(
                    _result(
                        {"execution_id": execution.execution_id},
                        _status_from_result(result),
                        ";".join(result.readiness_failure_codes),
                    )
                )
        return output

    def calculate_clv_ready(self) -> list[dict[str, Any]]:
        service = WagerExecutionClvService(store=self.store)
        output = []
        for state in self._states():
            for execution in state.wager_execution_history:
                if state.has_execution_clv(execution.execution_id):
                    continue
                result = service.record(
                    execution_id=execution.execution_id, calculated_at_utc=_utc_now()
                )
                output.append(
                    _result(
                        {"execution_id": execution.execution_id},
                        _status_from_result(result),
                        ";".join(result.readiness_failure_codes),
                    )
                )
        return output

    def status(self) -> dict[str, Any]:
        rows = []
        for state in self._states():
            rows.append(
                {
                    "game_id": state.game_id,
                    "game_registered": bool(state.away_team and state.home_team),
                    "candidate": (
                        state.candidate_status.value if state.candidate_status else "NOT_STARTED"
                    ),
                    "audit": (
                        "COMPLETED"
                        if state.latest_successful_structured_variant_b_audit
                        else "PENDING_INPUT"
                    ),
                    "decision": (
                        "COMPLETED"
                        if state.active_structured_operator_decision
                        else "PENDING_INPUT"
                    ),
                    "executions": len(state.wager_execution_history),
                    "closing": len(state.closing_quote_link_history),
                    "result": "COMPLETED" if state.authoritative_game_result else "PENDING_INPUT",
                    "settlements": len(state.wager_execution_settlement_history),
                    "clv": len(state.wager_execution_clv_history),
                    "next_action": _next_action(state),
                }
            )
        return {
            "season": self.season,
            "week": self.week,
            "event_store": str(self.events_path),
            "games": rows,
        }

    def report(self) -> dict[str, Any]:
        status = self.status()
        executions = []
        for state in self._states():
            for item in state.wager_execution_history:
                settlement = state.settlement_for_execution(item.execution_id)
                clv = state.clv_for_execution(item.execution_id)
                executions.append(
                    {
                        "game_id": state.game_id,
                        "execution_id": item.execution_id,
                        "outcome": None if settlement is None else settlement.outcome,
                        "risk_units": None if settlement is None else settlement.risk_units,
                        "net_profit_units": (
                            None if settlement is None else settlement.net_profit_units
                        ),
                        "settlement_status": "COMPLETED" if settlement else "PENDING",
                        "line_clv_points": None if clv is None else clv.line_clv_points,
                        "price_clv_probability": None if clv is None else clv.price_clv_probability,
                        "clv_status": "COMPLETED" if clv else "PENDING",
                    }
                )
        report = {
            "status": status,
            "executions": executions,
            "methodology": {"clv": "OPERATOR_DESIGNATED_SAME_BOOK_SPREAD_CLV_V1"},
        }
        report_path = self.root / "reports" / str(self.season) / f"week_{self.week:02d}.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
        markdown = self.root / "reports" / str(self.season) / f"week_{self.week:02d}.md"
        lines = [
            f"# Pregame Week {self.season} Week {self.week}",
            "",
            f"Event store: `{self.events_path}`",
            "",
            "## Game Status",
        ]
        for row in status["games"]:
            lines.append(
                f"- `{row['game_id']}`: result={row['result']}, settlement={row['settlements']}, clv={row['clv']}, next={row['next_action']}"
            )
        lines.extend(["", "## Executions"])
        for row in executions:
            lines.append(
                f"- `{row['execution_id']}` `{row['outcome'] or 'PENDING'}` net={row['net_profit_units'] or 'PENDING'} line_clv={row['line_clv_points'] or 'PENDING'}"
            )
        markdown.write_text("\n".join(lines) + "\n", encoding="utf-8")
        report["report_json"] = str(report_path)
        report["report_markdown"] = str(markdown)
        return report

    def _states(self):
        ids = sorted({event.game_id for event in self.store.list_all_events()})
        return [
            state for game_id in ids if (state := project_game(self.store, game_id)) is not None
        ]


def _text(item: dict[str, Any], key: str) -> str:
    value = item.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be a non-empty string")
    return value


def _strict_int(item: dict[str, Any], key: str, default: int) -> int:
    value = item.get(key, default)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{key} must be an integer")
    return value


def _result(item: dict[str, Any], status: str, message: str | None) -> dict[str, Any]:
    row = {
        "id": item.get("game_id", item.get("execution_id", item.get("candidate_id"))),
        "status": status,
    }
    if message:
        row["message"] = message
    return row


def _status_from_result(result: Any) -> str:
    if result.readiness_failure_codes:
        return "BLOCKED"
    return "COMPLETED" if result.appended else "READY"


def _next_action(state: Any) -> str:
    if not state.candidate:
        return "import-candidates"
    if not state.latest_successful_structured_variant_b_audit:
        return "build-audits"
    if not state.active_structured_operator_decision:
        return "register-decisions"
    if not state.wager_execution_history:
        return "record-executions"
    if not state.closing_quote_link_history:
        return "link-closing"
    if not state.authoritative_game_result:
        return "import-results"
    if not state.wager_execution_settlement_history:
        return "settle-ready"
    if not state.wager_execution_clv_history:
        return "calculate-clv-ready"
    return "COMPLETED"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="NFL 2026 persistent pregame operator workflow")
    parser.add_argument("--season", type=int, required=True)
    parser.add_argument("--week", type=int, required=True)
    parser.add_argument("--root", type=Path, default=Path("data/pregame"))
    parser.add_argument("--input", type=Path)
    parser.add_argument(
        "command",
        choices=(
            "init-week",
            "import-games",
            "import-candidates",
            "import-market-snapshots",
            "build-audits",
            "register-lineage",
            "register-decisions",
            "record-executions",
            "link-closing",
            "import-results",
            "settle-ready",
            "calculate-clv-ready",
            "status",
            "report",
            "run-ready",
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.season <= 0 or args.week <= 0:
        print("season and week must be positive", file=sys.stderr)
        return 2
    operator = WeeklyOperator(root=args.root, season=args.season, week=args.week)
    try:
        if args.command == "init-week":
            result = operator.init_week()
        elif args.command == "status":
            result = operator.status()
        elif args.command == "report":
            result = operator.report()
        elif args.command == "settle-ready":
            result = {"results": operator.settle_ready()}
        elif args.command == "calculate-clv-ready":
            result = {"results": operator.calculate_clv_ready()}
        elif args.command == "run-ready":
            result = {
                "settlement": operator.settle_ready(),
                "clv": operator.calculate_clv_ready(),
                "status": operator.status(),
            }
        else:
            if args.input is None:
                raise ValueError(f"{args.command} requires --input JSON")
            records = _json_input(args.input)
            handler = {
                "import-games": operator.import_games,
                "import-candidates": operator.import_candidates,
                "import-market-snapshots": operator.import_market_snapshots,
                "build-audits": operator.build_audits,
                "register-lineage": operator.register_lineage,
                "register-decisions": operator.register_decisions,
                "record-executions": operator.record_executions,
                "link-closing": operator.link_closing,
                "import-results": operator.import_results,
            }[args.command]
            result = {"results": handler(records)}
        print(json.dumps(result, indent=2, default=str))
        return 1 if _contains_blocked(result) else 0
    except Exception as exc:
        print(f"SYSTEM_ERROR: {exc}", file=sys.stderr)
        return 2


def _contains_blocked(value: Any) -> bool:
    if isinstance(value, dict):
        return any(_contains_blocked(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_blocked(item) for item in value)
    return value == "BLOCKED" or value == "CONFLICT"


if __name__ == "__main__":
    raise SystemExit(main())
