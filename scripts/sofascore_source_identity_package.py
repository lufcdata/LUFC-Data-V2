#!/usr/bin/env python3
"""Derive the LUFC-scoped identity package directly from captured SofaScore evidence.

This module removes manual assembly of provider identity populations. It extracts only
identities that have approved LUFC canonical destinations: the fixture, opponent club,
Leeds matchday players, Leeds manager and opposition manager. Opposition players are
intentionally excluded from canonical resolution.

No network/database access and no writes occur here.
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from sofascore_dry_run_contract import summarize_lineups
from sofascore_lufc_identity_contract import proposed_lufc_identity_package


class SourceIdentityPackageError(RuntimeError):
    """Raised when captured source evidence cannot define the scoped identity population."""


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise SourceIdentityPackageError(f"{label} is missing or invalid")
    return value


def _integer(value: Any, label: str) -> int:
    if not isinstance(value, int):
        raise SourceIdentityPackageError(f"{label} must be an integer")
    return value


def _team_id(event: Mapping[str, Any], side: str) -> int:
    team = _mapping(event.get(f"{side}Team"), f"event.{side}Team")
    return _integer(team.get("id"), f"event.{side}Team.id")


def _manager_id(managers: Mapping[str, Any], side: str) -> int:
    key = f"{side}Manager"
    manager = _mapping(managers.get(key), f"managers.{key}")
    return _integer(manager.get("id"), f"managers.{key}.id")


def _leeds_player_ids(lineup_summary: Mapping[str, Any], side: str) -> list[int]:
    side_summary = _mapping(lineup_summary.get(side), f"lineup_summary.{side}")
    rows = []
    for bucket in ("starters", "bench"):
        values = side_summary.get(bucket)
        if not isinstance(values, list):
            raise SourceIdentityPackageError(f"lineup_summary.{side}.{bucket} is missing")
        rows.extend(values)
    ids = [
        _integer(_mapping(row, "lineup player").get("sofascore_player_id"), "lineup player ID")
        for row in rows
    ]
    if len(ids) != 20:
        raise SourceIdentityPackageError(f"Leeds matchday identity population must contain 20 players; found {len(ids)}")
    if len(ids) != len(set(ids)):
        raise SourceIdentityPackageError("Leeds lineup contains duplicate provider player IDs")
    return ids


def build_source_identity_package(
    *,
    raw_payloads: Mapping[str, Any],
    leeds_team_provider_id: int,
    mappings: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    """Extract source identities then resolve them through the LUFC-scoped mapping contract."""
    event = _mapping(raw_payloads.get("event"), "raw_payloads.event")
    lineups = _mapping(raw_payloads.get("lineups"), "raw_payloads.lineups")
    managers = _mapping(raw_payloads.get("managers"), "raw_payloads.managers")

    event_id = _integer(event.get("id"), "event.id")
    home_team_id = _team_id(event, "home")
    away_team_id = _team_id(event, "away")
    if leeds_team_provider_id not in {home_team_id, away_team_id}:
        raise SourceIdentityPackageError("Leeds provider team ID is not one of the fixture teams")

    leeds_side = "home" if home_team_id == leeds_team_provider_id else "away"
    opposition_side = "away" if leeds_side == "home" else "home"
    lineup_summary = summarize_lineups(dict(lineups))
    leeds_player_provider_ids = _leeds_player_ids(lineup_summary, leeds_side)
    leeds_manager_provider_id = _manager_id(managers, leeds_side)
    opposition_manager_provider_id = _manager_id(managers, opposition_side)

    package = proposed_lufc_identity_package(
        event_id=event_id,
        home_team_provider_id=home_team_id,
        away_team_provider_id=away_team_id,
        leeds_team_provider_id=leeds_team_provider_id,
        leeds_player_provider_ids=leeds_player_provider_ids,
        leeds_manager_provider_id=leeds_manager_provider_id,
        opposition_manager_provider_id=opposition_manager_provider_id,
        mappings=mappings,
    )

    return {
        "status": "PASS",
        "provider": "sofascore",
        "sofascore_event_id": event_id,
        "leeds_side": leeds_side,
        "opposition_side": opposition_side,
        "source_population": {
            "home_team_provider_id": home_team_id,
            "away_team_provider_id": away_team_id,
            "leeds_team_provider_id": leeds_team_provider_id,
            "leeds_player_provider_ids": leeds_player_provider_ids,
            "leeds_manager_provider_id": leeds_manager_provider_id,
            "opposition_manager_provider_id": opposition_manager_provider_id,
        },
        "identity_package": package,
        "identity_mapping_validation": {
            "status": "RESOLVED",
            "provider": "sofascore",
            "scope": "LUFC_SCOPED",
            "resolved_leeds_player_count": len(leeds_player_provider_ids),
            "opposition_players": "NOT_APPLICABLE",
        },
        "database_writes": 0,
        "canonical_promotion_performed": False,
    }
