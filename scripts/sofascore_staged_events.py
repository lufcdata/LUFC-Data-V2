#!/usr/bin/env python3
"""Build lossless staged SofaScore event envelopes without database writes.

Staged events preserve structured source facts that are either awaiting canonical
promotion or have no approved canonical LUFC destination yet. Provider identifiers
remain namespaced and source payload fragments are retained verbatim in event_json.
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping


class StagedEventError(RuntimeError):
    """Raised when a source event cannot be staged deterministically."""


def _require_int(value: Any, label: str) -> int:
    if not isinstance(value, int):
        raise StagedEventError(f"{label} must be an integer")
    return value


def _optional_int(value: Any, label: str) -> int | None:
    if value is None:
        return None
    return _require_int(value, label)


def _event_time(row: Mapping[str, Any]) -> tuple[int, int, str | None]:
    minute = _require_int(row.get("time"), "event time")
    added = _optional_int(row.get("addedTime"), "event added time") or 0
    period = row.get("incidentClass") or row.get("period")
    period_text = str(period) if period is not None else None
    return minute, added, period_text


def _team_side(row: Mapping[str, Any], *, leeds_is_home: bool) -> str:
    is_home = row.get("isHome")
    if not isinstance(is_home, bool):
        raise StagedEventError("event isHome must be boolean")
    return "LEEDS" if is_home == leeds_is_home else "OPPONENT"


def _provider_player_id(row: Mapping[str, Any], key: str = "player") -> int | None:
    player = row.get(key)
    if player is None:
        return None
    if not isinstance(player, Mapping):
        raise StagedEventError(f"event {key} must be an object when present")
    return _optional_int(player.get("id"), f"event {key} provider ID")


def _envelope(
    *,
    event_kind: str,
    team_side: str,
    provider_team_id: int,
    provider_player_id: int | None,
    provider_secondary_player_id: int | None,
    minute_base: int,
    stoppage_minute: int,
    period: str | None,
    sequence_index: int,
    event_json: Mapping[str, Any],
    provider_event_id: int | None = None,
    canonical_destination: str | None = None,
    promotion_status: str = "STAGED",
) -> dict[str, Any]:
    return {
        "provider": "sofascore",
        "provider_event_id": provider_event_id,
        "event_kind": event_kind,
        "team_side": team_side,
        "provider_team_id": provider_team_id,
        "provider_player_id": provider_player_id,
        "provider_secondary_player_id": provider_secondary_player_id,
        "minute_base": minute_base,
        "stoppage_minute": stoppage_minute,
        "period": period,
        "sequence_index": sequence_index,
        "event_json": dict(event_json),
        "canonical_destination": canonical_destination,
        "promotion_status": promotion_status,
    }


def stage_incidents(
    incidents: Iterable[Mapping[str, Any]],
    *,
    leeds_is_home: bool,
    home_team_provider_id: int,
    away_team_provider_id: int,
) -> list[dict[str, Any]]:
    """Normalise incident records chronologically into staging envelopes."""
    rows = list(incidents)
    chronological = sorted(
        rows,
        key=lambda row: (
            _require_int(row.get("time"), "incident time"),
            _optional_int(row.get("addedTime"), "incident added time") or 0,
        ),
    )
    staged: list[dict[str, Any]] = []
    for index, row in enumerate(chronological, start=1):
        minute, added, period = _event_time(row)
        side = _team_side(row, leeds_is_home=leeds_is_home)
        team_provider_id = home_team_provider_id if row.get("isHome") is True else away_team_provider_id
        incident_type = str(row.get("incidentType") or "other").strip().casefold()
        if incident_type == "goal":
            kind = "goal"
            secondary = _provider_player_id(row, "assist1") or _provider_player_id(row, "assist")
        elif incident_type == "substitution":
            kind = "substitution"
            secondary = _provider_player_id(row, "playerIn")
        elif incident_type in {"card", "yellow", "red"}:
            kind = "card"
            secondary = None
        else:
            kind = incident_type or "other"
            secondary = None

        primary = (
            _provider_player_id(row, "player")
            or _provider_player_id(row, "playerOut")
        )
        canonical_destination = None
        promotion_status = "STAGED"
        if side == "LEEDS" and kind == "goal":
            canonical_destination = "goals"
            promotion_status = "ELIGIBLE"
        elif side == "LEEDS" and kind == "substitution":
            canonical_destination = "match_substitutions"
            promotion_status = "ELIGIBLE"
        elif side == "OPPONENT" and kind in {"goal", "substitution"}:
            promotion_status = "SCHEMA_GAP"

        staged.append(
            _envelope(
                event_kind=kind,
                team_side=side,
                provider_team_id=team_provider_id,
                provider_player_id=primary,
                provider_secondary_player_id=secondary,
                minute_base=minute,
                stoppage_minute=added,
                period=period,
                sequence_index=index,
                event_json=row,
                provider_event_id=_optional_int(row.get("id"), "incident provider event ID"),
                canonical_destination=canonical_destination,
                promotion_status=promotion_status,
            )
        )
    return staged


def stage_shotmap(
    shots: Iterable[Mapping[str, Any]],
    *,
    leeds_is_home: bool,
    home_team_provider_id: int,
    away_team_provider_id: int,
    sequence_start: int = 1,
) -> list[dict[str, Any]]:
    """Preserve every rich shot record as a staged shot event."""
    rows = list(shots)
    chronological = sorted(
        rows,
        key=lambda row: (
            _require_int(row.get("time"), "shot time"),
            _optional_int(row.get("timeSeconds"), "shot timeSeconds") or 0,
            _optional_int(row.get("id"), "shot provider ID") or 0,
        ),
    )
    staged: list[dict[str, Any]] = []
    for offset, row in enumerate(chronological):
        minute = _require_int(row.get("time"), "shot time")
        side = _team_side(row, leeds_is_home=leeds_is_home)
        team_provider_id = home_team_provider_id if row.get("isHome") is True else away_team_provider_id
        staged.append(
            _envelope(
                event_kind="shot",
                team_side=side,
                provider_team_id=team_provider_id,
                provider_player_id=_provider_player_id(row, "player"),
                provider_secondary_player_id=_provider_player_id(row, "goalkeeper"),
                minute_base=minute,
                stoppage_minute=0,
                period=str(row.get("period")) if row.get("period") is not None else None,
                sequence_index=sequence_start + offset,
                event_json=row,
                provider_event_id=_optional_int(row.get("id"), "shot provider ID"),
                canonical_destination=None,
                promotion_status="SCHEMA_GAP",
            )
        )
    return staged


def build_staged_event_population(
    *,
    incidents: Iterable[Mapping[str, Any]],
    shots: Iterable[Mapping[str, Any]],
    leeds_is_home: bool,
    home_team_provider_id: int,
    away_team_provider_id: int,
) -> dict[str, Any]:
    """Return one complete staged-event population for a dry run."""
    incident_events = stage_incidents(
        incidents,
        leeds_is_home=leeds_is_home,
        home_team_provider_id=home_team_provider_id,
        away_team_provider_id=away_team_provider_id,
    )
    shot_events = stage_shotmap(
        shots,
        leeds_is_home=leeds_is_home,
        home_team_provider_id=home_team_provider_id,
        away_team_provider_id=away_team_provider_id,
        sequence_start=len(incident_events) + 1,
    )
    events = incident_events + shot_events
    return {
        "status": "PASS",
        "event_count": len(events),
        "incident_event_count": len(incident_events),
        "shot_event_count": len(shot_events),
        "schema_gap_event_count": sum(event["promotion_status"] == "SCHEMA_GAP" for event in events),
        "eligible_event_count": sum(event["promotion_status"] == "ELIGIBLE" for event in events),
        "events": events,
        "database_writes": 0,
        "promotion_performed": False,
    }
