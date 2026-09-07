#!/usr/bin/env python3
"""Pure identity-resolution helpers for SofaScore ingestion dry runs.

This module contains no network or database access. It validates provider-namespaced
identity mappings before any canonical LUFC IDs can be attached to a proposed diff.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Iterable

PROVIDER = "sofascore"
ALLOWED_ENTITY_TYPES = {"team", "player", "manager", "match", "venue", "referee"}


class IdentityContractError(RuntimeError):
    """Raised when an external identity cannot be resolved safely and uniquely."""


def _normalise_mapping_row(row: dict[str, Any]) -> tuple[str, str, int, int]:
    provider = str(row.get("provider") or "").strip().casefold()
    entity_type = str(row.get("entity_type") or "").strip().casefold()
    provider_id = row.get("provider_id")
    canonical_id = row.get("canonical_id")

    if provider != PROVIDER:
        raise IdentityContractError(f"unsupported provider mapping: {provider or '<missing>'}")
    if entity_type not in ALLOWED_ENTITY_TYPES:
        raise IdentityContractError(f"unsupported entity type: {entity_type or '<missing>'}")
    if not isinstance(provider_id, int):
        raise IdentityContractError("mapping provider_id must be an integer")
    if not isinstance(canonical_id, int):
        raise IdentityContractError("mapping canonical_id must be an integer")

    return provider, entity_type, provider_id, canonical_id


def validate_mapping_population(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Reject duplicate/conflicting provider identities before resolution.

    A SofaScore provider identity may resolve to exactly one canonical LUFC identity.
    Canonical IDs remain a separate namespace; this function never rewrites source IDs.
    """
    normalised = [_normalise_mapping_row(row) for row in rows]
    provider_keys = [(provider, entity_type, provider_id) for provider, entity_type, provider_id, _ in normalised]
    duplicate_keys = [key for key, count in Counter(provider_keys).items() if count > 1]
    if duplicate_keys:
        raise IdentityContractError(f"duplicate provider identity mappings: {duplicate_keys}")

    return {
        "status": "PASS",
        "mapping_count": len(normalised),
        "provider": PROVIDER,
        "canonical_namespace_kept_separate": True,
    }


def resolve_external_id(
    rows: Iterable[dict[str, Any]],
    *,
    entity_type: str,
    provider_id: int,
) -> dict[str, Any]:
    """Resolve one SofaScore identity to exactly one LUFC canonical identity."""
    if entity_type.casefold() not in ALLOWED_ENTITY_TYPES:
        raise IdentityContractError(f"unsupported entity type: {entity_type}")
    if not isinstance(provider_id, int):
        raise IdentityContractError("provider_id must be an integer")

    normalised = [_normalise_mapping_row(row) for row in rows]
    matches = [
        canonical_id
        for provider, mapped_type, mapped_provider_id, canonical_id in normalised
        if provider == PROVIDER
        and mapped_type == entity_type.casefold()
        and mapped_provider_id == provider_id
    ]

    if not matches:
        raise IdentityContractError(
            f"unresolved SofaScore {entity_type} identity: provider_id={provider_id}"
        )
    if len(matches) != 1:
        raise IdentityContractError(
            f"ambiguous SofaScore {entity_type} identity: provider_id={provider_id}, matches={matches}"
        )

    return {
        "status": "RESOLVED",
        "provider": PROVIDER,
        "entity_type": entity_type.casefold(),
        "provider_id": provider_id,
        "canonical_id": matches[0],
    }


def require_all_provider_ids_resolved(
    rows: Iterable[dict[str, Any]],
    *,
    entity_type: str,
    provider_ids: Iterable[int],
) -> dict[str, Any]:
    """Require every provider ID in a source population to resolve before promotion."""
    ids = list(provider_ids)
    if any(not isinstance(provider_id, int) for provider_id in ids):
        raise IdentityContractError("provider ID population contains a non-integer value")

    unique_ids = list(dict.fromkeys(ids))
    resolutions = [
        resolve_external_id(rows, entity_type=entity_type, provider_id=provider_id)
        for provider_id in unique_ids
    ]

    canonical_ids = [result["canonical_id"] for result in resolutions]
    if len(canonical_ids) != len(set(canonical_ids)):
        raise IdentityContractError(
            f"multiple SofaScore {entity_type} IDs resolve to the same canonical ID"
        )

    return {
        "status": "PASS",
        "entity_type": entity_type.casefold(),
        "provider_id_count": len(unique_ids),
        "resolved_count": len(resolutions),
        "resolutions": resolutions,
        "canonical_namespace_kept_separate": True,
    }


def proposed_identity_package(
    *,
    event_id: int,
    home_team_id: int,
    away_team_id: int,
    player_ids: Iterable[int],
    manager_ids: Iterable[int],
    mappings: Iterable[dict[str, Any]],
) -> dict[str, Any]:
    """Resolve the minimum identity populations needed by a match dry run.

    This remains a proposal only: it performs no database writes and carries both
    provider and canonical identities side by side for auditability.
    """
    mapping_rows = list(mappings)
    validate_mapping_population(mapping_rows)

    return {
        "status": "PASS",
        "match": resolve_external_id(mapping_rows, entity_type="match", provider_id=event_id),
        "teams": require_all_provider_ids_resolved(
            mapping_rows,
            entity_type="team",
            provider_ids=[home_team_id, away_team_id],
        ),
        "players": require_all_provider_ids_resolved(
            mapping_rows,
            entity_type="player",
            provider_ids=player_ids,
        ),
        "managers": require_all_provider_ids_resolved(
            mapping_rows,
            entity_type="manager",
            provider_ids=manager_ids,
        ),
        "database_writes": 0,
        "provider_ids_preserved": True,
        "canonical_ids_assigned_only_via_mapping": True,
    }
