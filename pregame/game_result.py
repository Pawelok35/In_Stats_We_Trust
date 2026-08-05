"""Central immutable registration of authoritative final game results."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from pydantic import ValidationError

from pregame.contracts import AuthoritativeGameResult, PregameEvent
from pregame.events import PregameEventType
from pregame.projector import ProjectionError, project_game
from pregame.store import AppendStatus, PregameEventStore


def game_result_event_id(game_id: str) -> str:
    """Return the deterministic authoritative result event ID for one game."""

    if not isinstance(game_id, str) or not game_id.strip():
        raise ValueError("game_id must be a non-empty string")
    return f"game-result:{game_id}"


@dataclass(frozen=True)
class AuthoritativeGameResultRegistrationResult:
    """Explicit outcome of one append-only authoritative result registration."""

    game_id: str
    event_id: str | None
    appended: bool
    projected_game: object | None
    readiness_failure_codes: tuple[str, ...] = ()


@dataclass(frozen=True)
class _GameCreationAuthority:
    event_id: str
    season: int
    week: int
    home_team: str
    away_team: str
    kickoff_utc: datetime
    neutral_site: bool | None


class AuthoritativeGameResultService:
    """Append one FINAL home/away result derived from exactly one GAME_CREATED event."""

    def __init__(self, *, store: PregameEventStore) -> None:
        self._store = store

    def record(
        self,
        *,
        game_id: str,
        home_score: int,
        away_score: int,
        source: str,
        source_reference: str,
        source_finalized_at_utc: datetime,
        observed_at_utc: datetime,
        overtime: bool | None = None,
    ) -> AuthoritativeGameResultRegistrationResult:
        """Record one final result without settling any execution or ledger state."""

        try:
            event_id = game_result_event_id(game_id)
        except ValueError:
            return self._failed(game_id, None, "GAME_ID_INVALID")

        authority, failure = self._find_game_creation_authority(game_id)
        if failure is not None:
            return self._failed(game_id, event_id, failure)
        assert authority is not None

        try:
            result = AuthoritativeGameResult(
                result_event_id=event_id,
                game_id=game_id,
                game_created_event_id=authority.event_id,
                home_team=authority.home_team,
                away_team=authority.away_team,
                season=authority.season,
                week=authority.week,
                kickoff_utc=authority.kickoff_utc,
                neutral_site=authority.neutral_site,
                home_score=home_score,
                away_score=away_score,
                overtime=overtime,
                source=source,
                source_reference=source_reference,
                source_finalized_at_utc=source_finalized_at_utc,
                observed_at_utc=observed_at_utc,
            )
        except ValidationError:
            return self._failed(game_id, event_id, "INVALID_AUTHORITATIVE_RESULT")

        append = self._store.append(
            PregameEvent(
                event_id=event_id,
                game_id=game_id,
                event_type=PregameEventType.AUTHORITATIVE_GAME_RESULT_RECORDED,
                created_at_utc=result.observed_at_utc,
                effective_at_utc=result.source_finalized_at_utc,
                source="authoritative_game_result",
                idempotency_key=event_id,
                payload=result.to_json_dict(),
            )
        )
        if append.status == AppendStatus.CONFLICT:
            return self._failed(game_id, event_id, "AUTHORITATIVE_RESULT_EVENT_CONFLICT")
        try:
            projected = project_game(self._store, game_id)
        except ProjectionError:
            return self._failed(game_id, event_id, "AUTHORITATIVE_RESULT_PROJECTOR_FAILURE")
        return AuthoritativeGameResultRegistrationResult(
            game_id=game_id,
            event_id=event_id,
            appended=append.status == AppendStatus.APPENDED,
            projected_game=projected,
        )

    def _find_game_creation_authority(
        self, game_id: str
    ) -> tuple[_GameCreationAuthority | None, str | None]:
        creation_events = [
            event
            for event in self._store.list_events(game_id)
            if event.event_type == PregameEventType.GAME_CREATED
        ]
        if not creation_events:
            return None, "GAME_CREATED_NOT_FOUND"
        if len(creation_events) != 1:
            return None, "GAME_CREATED_AMBIGUOUS"
        event = creation_events[0]
        try:
            return self._parse_game_creation(event), None
        except ValueError as exc:
            return None, str(exc)

    @staticmethod
    def _parse_game_creation(event: PregameEvent) -> _GameCreationAuthority:
        payload = event.payload
        if event.game_id != payload.get("game_id", event.game_id):
            raise ValueError("GAME_CREATED_IDENTITY_INVALID")
        required = ("season", "week", "home_team", "away_team", "kickoff_utc")
        if any(field not in payload for field in required):
            raise ValueError("GAME_CREATED_REQUIRED_FIELD_MISSING")
        season, week = payload["season"], payload["week"]
        if isinstance(season, bool) or not isinstance(season, int):
            raise ValueError("GAME_CREATED_SEASON_INVALID")
        if isinstance(week, bool) or not isinstance(week, int):
            raise ValueError("GAME_CREATED_WEEK_INVALID")
        home_team, away_team = payload["home_team"], payload["away_team"]
        if not isinstance(home_team, str) or not home_team.strip():
            raise ValueError("GAME_CREATED_HOME_TEAM_INVALID")
        if not isinstance(away_team, str) or not away_team.strip():
            raise ValueError("GAME_CREATED_AWAY_TEAM_INVALID")
        if home_team == away_team:
            raise ValueError("GAME_CREATED_TEAMS_IDENTICAL")
        kickoff_utc = AuthoritativeGameResultService._parse_kickoff(payload["kickoff_utc"])
        neutral_site = payload.get("neutral_site")
        if neutral_site is not None and not isinstance(neutral_site, bool):
            raise ValueError("GAME_CREATED_NEUTRAL_SITE_INVALID")
        return _GameCreationAuthority(
            event_id=event.event_id,
            season=season,
            week=week,
            home_team=home_team,
            away_team=away_team,
            kickoff_utc=kickoff_utc,
            neutral_site=neutral_site,
        )

    @staticmethod
    def _parse_kickoff(value: Any) -> datetime:
        if isinstance(value, datetime):
            parsed = value
        elif isinstance(value, str):
            try:
                parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError as exc:
                raise ValueError("GAME_CREATED_KICKOFF_INVALID") from exc
        else:
            raise ValueError("GAME_CREATED_KICKOFF_INVALID")
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise ValueError("GAME_CREATED_KICKOFF_INVALID")
        return parsed.astimezone(timezone.utc)

    @staticmethod
    def _failed(
        game_id: object,
        event_id: str | None,
        code: str,
    ) -> AuthoritativeGameResultRegistrationResult:
        return AuthoritativeGameResultRegistrationResult(
            game_id=game_id if isinstance(game_id, str) else "",
            event_id=event_id,
            appended=False,
            projected_game=None,
            readiness_failure_codes=(code,),
        )
