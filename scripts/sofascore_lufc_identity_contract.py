#!/usr/bin/env python3
"""LUFC-scoped external identity contract for SofaScore ingestion.

The canonical database does not use one universal namespace for every football entity:
- `players` contains Leeds players, not opposition players.
- `clubs` contains opponents, not Leeds United itself.
- `managers` contains Leeds managers, while opposition managers use `managerial_people`.

This module makes those scopes explicit so provider IDs cannot be forced into the wrong
canonical population. It performs no network/database access and no writes.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Iterable, Mapping

PROVIDER = "sofascore"
CANONICAL_NAMESPACES = {
    "match": "matches.match_id",
    "opponent_club": "clubs.club_id",
    "leeds_player": "players.player_id",
    "leeds_manager": "managers.manager_id",
    "opposition_manager": "managerial_people.managerial_person_id",
}


class LufcIdentityContractError(RuntimeError):
    """Raised when a provider identity would cross or ambiguously resolve namespaces."""


def _normalise_row(row: Mapping[str, Any]) -> tuple[str, str, int, int, str]:
    provider = str(row.get("provider") or "").strip().casefold()
    entity_scope = str(row.get("entity_scope") or "").strip().casefold()
    provider_id = row.get("provider_id")
    canonical_id = row.get("canonical_id")
    canonical_namespace = str(row.get("canonical_namespace") or "").strip()

    if provider != PROVIDER:
        raise LufcIdentityContractError(f"unsupported provider: {provider or '<missing>'}")
    if entity_scope not in CANONICAL_NAMESPACES:
        raise LufcIdentityContractError(
            f"unsupported LUFC identity scope: {entity_scope or '<missing>'}"
        )
    expected_namespace = CANONICAL_NAMESPACES[entity_scope]
    if canonical_namespace != expected_namespace:
        raise LufcIdentityContractError(
            f"wrong canonical namespace for {entity_scope}: "
            f"{canonical_namespace or '<missing>'} != {expected_namespace}"
        )
    if not isinstance(provider_id, int):
        raise LufcIdentityContractError("provider_id must be an integer")
    if not isinstance(canonical_id, int):
        raise LufcIdentityContractError("canonical_id must be an integer")
    return provider, entity_scope, provider_id, canonical_id, canonical_namespace


def validate_scoped_mapping_population(rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    normalised = [_normalise_row(row) for row in rows]
    provider_keys = [(provider, scope, provider_id) for provider, scope, provider_id, _, _ in normalised]
    duplicates = [key for key, count in Counter(provider_keys).items() if count > 1]
    if duplicates:
        raise LufcIdentityContractError(f"duplicate scoped provider mappings: {duplicates}")

    canonical_keys = [(scope, canonical_id) for _, scope, _, canonical_id, _ in normalised]
    canonical_duplicates = [key for key, count in Counter(canonical_keys).items() if count > 1]
    if canonical_duplicates:
        raise LufcIdentityContractError(
            f"multiple provider IDs resolve to the same scoped canonical identity: {canonical_duplicates}"
        )

    return {
        "status": "PASS",
        "provider": PROVIDER,
        "mapping_count": len(normalised),
        "canonical_namespaces": dict(CANONICAL_NAMESPACES),
        "database_writes": 0,
    }


def resolve_scoped_external_id(
    rows: Iterable[Mapping[str, Any]],
    *,
    entity_scope: str,
    provider_id: int,
) -> dict[str, Any]:
    scope = entity_scope.strip().casefold()
    if scope not in CANONICAL_NAMESPACES:
        raise LufcIdentityContractError(f"unsupported LUFC identity scope: {entity_scope}")
    if not isinstance(provider_id, int):
        raise LufcIdentityContractError("provider_id must be an integer")

    matches = []
    for row in rows:
        provider, mapped_scope, mapped_provider_id, canonical_id, canonical_namespace = _normalise_row(row)
        if provider == PROVIDER and mapped_scope == scope and mapped_provider_id == provider_id:
            matches.append((canonical_id, canonical_namespace))

    if not matches:
        raise LufcIdentityContractError(
            f"unresolved SofaScore {scope} identity: provider_id={provider_id}"
        )
    if len(matches) != 1:
        raise LufcIdentityContractError(
            f"ambiguous SofaScore {scope} identity: provider_id={provider_id}"
        )

    canonical_id, canonical_namespace = matches[0]
    return {
        "status": "RESOLVED",
        "provider": PROVIDER,
        "entity_scope": scope,
        "provider_id": provider_id,
        "canonical_id": canonical_id,
        "canonical_namespace": canonical_namespace,
    }


def _resolve_population(
    rows: list[Mapping[str, Any]],
    *,
    entity_scope: str,
    provider_ids: Iterable[int],
) -> dict[str, Any]:
    ids = list(dict.fromkeys(provider_ids))
    if any(not isinstance(provider_id, int) for provider_id in ids):
        raise LufcIdentityContractError("provider ID population contains a non-integer value")
    resolutions = [
        resolve_scoped_external_id(rows, entity_scope=entity_scope, provider_id=provider_id)
        for provider_id in ids
    ]
    return {
        "status": "PASS",
        "entity_scope": entity_scope,
        "provider_id_count": len(ids),
        "resolved_count": len(resolutions),
        "resolutions": resolutions,
    }


def proposed_lufc_identity_package(
    *,
    event_id: int,
    home_team_provider_id: int,
    away_team_provider_id: int,
    leeds_team_provider_id: int,
    leeds_player_provider_ids: Iterable[int],
    leeds_manager_provider_id: int,
    opposition_manager_provider_id: int,
    mappings: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    """Resolve only provider identities that have real LUFC canonical destinations.

    Leeds United's provider team ID is validated as fixture identity but is NOT mapped
    to `clubs`, because `clubs` is the opponent population. Opposition players are not
    resolved to `players`; they remain provider/staged identities until an approved
    opposition-player model exists.
    """
    mapping_rows = list(mappings)
    validate_scoped_mapping_population(mapping_rows)

    if leeds_team_provider_id not in {home_team_provider_id, away_team_provider_id}:
        raise LufcIdentityContractError("Leeds provider team ID is not one of the fixture teams")
    opponent_team_provider_id = (
        away_team_provider_id
        if home_team_provider_id == leeds_team_provider_id
        else home_team_provider_id
    )

    return {
        "status": "PASS",
        "provider": PROVIDER,
        "match": resolve_scoped_external_id(
            mapping_rows, entity_scope="match", provider_id=event_id
        ),
        "leeds_team": {
            "status": "VALIDATED_PROVIDER_IDENTITY",
            "provider": PROVIDER,
            "provider_id": leeds_team_provider_id,
            "canonical_mapping": "NOT_APPLICABLE",
            "reason": "Leeds United is not represented in the opponent clubs population",
        },
        "opponent_club": resolve_scoped_external_id(
            mapping_rows,
            entity_scope="opponent_club",
            provider_id=opponent_team_provider_id,
        ),
        "leeds_players": _resolve_population(
            mapping_rows,
            entity_scope="leeds_player",
            provider_ids=leeds_player_provider_ids,
        ),
        "leeds_manager": resolve_scoped_external_id(
            mapping_rows,
            entity_scope="leeds_manager",
            provider_id=leeds_manager_provider_id,
        ),
        "opposition_manager": resolve_scoped_external_id(
            mapping_rows,
            entity_scope="opposition_manager",
            provider_id=opposition_manager_provider_id,
        ),
        "opposition_players": {
            "status": "NOT_APPLICABLE",
            "canonical_mapping": "NOT_APPLICABLE",
            "reason": "opposition players must not be inserted into Leeds players",
        },
        "database_writes": 0,
        "provider_ids_preserved": True,
        "canonical_namespace_separation_enforced": True,
        "canonical_promotion_performed": False,
    }
