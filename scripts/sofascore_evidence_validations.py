#!/usr/bin/env python3
"""Derive non-population ingestion gates from captured source evidence.

This module keeps fixture identity, captain, manager, formation, attendance and
league-position validation source-backed and zero-write. It accepts already-captured
SofaScore payloads plus optional explicitly attributed secondary evidence. It does
not resolve LUFC canonical identities and performs no database writes.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from sofascore_dry_run_contract import (
    attendance_candidate,
    league_position_requirement,
    summarize_lineups,
    validate_formation_crosscheck,
)


class EvidenceValidationError(RuntimeError):
    """Raised when captured evidence cannot satisfy a mandatory validation gate."""


def _require_mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise EvidenceValidationError(f"{label} is missing or invalid")
    return value


def _require_int(value: Any, label: str) -> int:
    if not isinstance(value, int):
        raise EvidenceValidationError(f"{label} must be an integer")
    return value


def _team_id(event: Mapping[str, Any], side: str) -> int:
    team = _require_mapping(event.get(f"{side}Team"), f"event.{side}Team")
    return _require_int(team.get("id"), f"event.{side}Team.id")


def validate_fixture(event: Mapping[str, Any], *, leeds_team_provider_id: int) -> dict[str, Any]:
    event_id = _require_int(event.get("id"), "event.id")
    home_id = _team_id(event, "home")
    away_id = _team_id(event, "away")
    if leeds_team_provider_id not in {home_id, away_id}:
        raise EvidenceValidationError("Leeds provider team ID is not one of the fixture teams")

    status = _require_mapping(event.get("status"), "event.status")
    status_type = str(status.get("type") or "").strip().casefold()
    description = str(status.get("description") or "").strip().casefold()
    if status_type != "finished" and description not in {"finished", "after extra time", "after penalties"}:
        raise EvidenceValidationError("fixture is not finished")

    return {
        "status": "PASS",
        "provider": "sofascore",
        "sofascore_event_id": event_id,
        "home_team_provider_id": home_id,
        "away_team_provider_id": away_id,
        "leeds_is_home": home_id == leeds_team_provider_id,
    }


def validate_captains(lineups: Mapping[str, Any]) -> dict[str, Any]:
    summary = summarize_lineups(dict(lineups))
    return {
        "status": "PASS",
        "provider": "sofascore",
        "home_captain_provider_id": summary["home"]["captain"]["sofascore_player_id"],
        "away_captain_provider_id": summary["away"]["captain"]["sofascore_player_id"],
    }


def _manager_id(managers: Mapping[str, Any], key: str) -> int:
    manager = _require_mapping(managers.get(key), f"managers.{key}")
    return _require_int(manager.get("id"), f"managers.{key}.id")


def validate_managers(managers: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "status": "PASS",
        "provider": "sofascore",
        "home_manager_provider_id": _manager_id(managers, "homeManager"),
        "away_manager_provider_id": _manager_id(managers, "awayManager"),
    }


def _secondary_side(
    secondary_evidence: Mapping[str, Any] | None,
    side: str,
) -> tuple[str | None, str | None]:
    if secondary_evidence is None:
        return None, None
    formations = secondary_evidence.get("formations")
    if not isinstance(formations, Mapping):
        return None, None
    side_evidence = formations.get(side)
    if not isinstance(side_evidence, Mapping):
        return None, None
    value = side_evidence.get("value")
    source = side_evidence.get("source")
    return (
        str(value).strip() if isinstance(value, str) else None,
        str(source).strip() if isinstance(source, str) else None,
    )


def validate_formations(
    lineups: Mapping[str, Any],
    *,
    secondary_evidence: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    summary = summarize_lineups(dict(lineups))
    home_secondary, home_source = _secondary_side(secondary_evidence, "home")
    away_secondary, away_source = _secondary_side(secondary_evidence, "away")
    home = validate_formation_crosscheck(
        summary["home"]["formation"],
        secondary_formation=home_secondary,
        secondary_source=home_source,
    )
    away = validate_formation_crosscheck(
        summary["away"]["formation"],
        secondary_formation=away_secondary,
        secondary_source=away_source,
    )
    status = "VALIDATED" if home["status"] == away["status"] == "VALIDATED" else "SOURCE_FACT"
    return {"status": status, "home": home, "away": away}


def _event_attendance(event: Mapping[str, Any]) -> int | None:
    for key in ("attendance", "spectators"):
        value = event.get(key)
        if isinstance(value, int) and value > 0:
            return value
    return None


def validate_attendance(
    event: Mapping[str, Any],
    *,
    secondary_evidence: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    secondary_value = None
    secondary_source = None
    if secondary_evidence is not None:
        evidence = secondary_evidence.get("attendance")
        if isinstance(evidence, Mapping):
            secondary_value = evidence.get("value")
            source = evidence.get("source")
            secondary_source = str(source).strip() if isinstance(source, str) else None
    result = attendance_candidate(
        _event_attendance(event),
        secondary_attendance=secondary_value,
        secondary_source=secondary_source,
    )
    if result["status"] == "UNAVAILABLE":
        raise EvidenceValidationError("attendance is unavailable from approved evidence")
    return result


def _walk_mappings(value: Any) -> Iterable[Mapping[str, Any]]:
    if isinstance(value, Mapping):
        yield value
        for child in value.values():
            yield from _walk_mappings(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_mappings(child)


def _standings_candidates(
    standings: Mapping[str, Any],
    *,
    leeds_team_provider_id: int,
) -> list[Mapping[str, Any]]:
    matches: list[Mapping[str, Any]] = []
    for row in _walk_mappings(standings):
        team = row.get("team")
        if not isinstance(team, Mapping) or team.get("id") != leeds_team_provider_id:
            continue
        if isinstance(row.get("position"), int):
            matches.append(row)
    return matches


def validate_league_position(
    event: Mapping[str, Any],
    standings: Mapping[str, Any] | None,
    *,
    leeds_team_provider_id: int,
) -> dict[str, Any]:
    requirement = league_position_requirement(dict(event))
    if requirement["status"] == "NOT_APPLICABLE":
        return requirement

    if not isinstance(standings, Mapping):
        raise EvidenceValidationError("league fixture requires captured post-match standings")

    round_info = _require_mapping(event.get("roundInfo"), "event.roundInfo")
    round_number = _require_int(round_info.get("round"), "event.roundInfo.round")
    candidates = _standings_candidates(standings, leeds_team_provider_id=leeds_team_provider_id)
    if len(candidates) != 1:
        raise EvidenceValidationError(
            f"expected exactly one Leeds standings row; found {len(candidates)}"
        )
    row = candidates[0]
    played = row.get("matches") if isinstance(row.get("matches"), int) else row.get("played")
    if played != round_number:
        raise EvidenceValidationError(
            f"standings snapshot is not completed round {round_number}: Leeds played={played!r}"
        )
    position = _require_int(row.get("position"), "standings Leeds position")
    points = row.get("points")
    return {
        "status": "PASS",
        "provider": "sofascore",
        "position": position,
        "round": round_number,
        "played": played,
        "points": points if isinstance(points, int) else None,
    }


def build_evidence_validations(
    *,
    raw_payloads: Mapping[str, Any],
    leeds_team_provider_id: int,
    secondary_evidence: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    event = _require_mapping(raw_payloads.get("event"), "raw_payloads.event")
    lineups = _require_mapping(raw_payloads.get("lineups"), "raw_payloads.lineups")
    managers = _require_mapping(raw_payloads.get("managers"), "raw_payloads.managers")
    standings = raw_payloads.get("standings")

    validations = {
        "fixture": validate_fixture(event, leeds_team_provider_id=leeds_team_provider_id),
        "captains": validate_captains(lineups),
        "managers": validate_managers(managers),
        "formations": validate_formations(lineups, secondary_evidence=secondary_evidence),
        "attendance": validate_attendance(event, secondary_evidence=secondary_evidence),
        "league_position": validate_league_position(
            event,
            standings if isinstance(standings, Mapping) else None,
            leeds_team_provider_id=leeds_team_provider_id,
        ),
    }
    return {
        "status": "PASS",
        "validations": validations,
        "database_writes": 0,
        "canonical_lufc_ids_assigned": False,
        "promotion_performed": False,
    }
