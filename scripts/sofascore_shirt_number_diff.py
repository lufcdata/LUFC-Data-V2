#!/usr/bin/env python3
"""Build zero-write Leeds match shirt-number operations from audited SofaScore lineups.

The destination contract is the existing `player_match_shirt_numbers` table. Provider
player IDs are resolved through the LUFC-scoped identity package before an operation is
proposed. No primary-key allocation, SQL generation, database access or write occurs.
"""

from __future__ import annotations

from typing import Any, Mapping


class ShirtNumberDiffError(RuntimeError):
    """Raised when a shirt-number population cannot be proposed safely."""


def _require_int(value: Any, label: str) -> int:
    if not isinstance(value, int):
        raise ShirtNumberDiffError(f"{label} must be an integer")
    return value


def _resolved_leeds_player(identity_package: Mapping[str, Any], provider_id: int) -> int:
    group = identity_package.get("leeds_players")
    if not isinstance(group, Mapping) or not isinstance(group.get("resolutions"), list):
        raise ShirtNumberDiffError("identity package has no Leeds player resolution population")
    matches = [
        row for row in group["resolutions"]
        if isinstance(row, Mapping)
        and row.get("entity_scope") == "leeds_player"
        and row.get("provider_id") == provider_id
    ]
    if len(matches) != 1:
        raise ShirtNumberDiffError(
            f"expected exactly one Leeds player identity for provider_id={provider_id}; found {len(matches)}"
        )
    return _require_int(matches[0].get("canonical_id"), "canonical Leeds player ID")


def _lineup_population(source_bundle: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    leeds_is_home = source_bundle.get("leeds_is_home")
    if not isinstance(leeds_is_home, bool):
        raise ShirtNumberDiffError("source bundle has no Leeds home/away identity")
    lineups = source_bundle.get("lineups")
    if not isinstance(lineups, Mapping):
        raise ShirtNumberDiffError("source bundle has no lineup population")
    side_name = "home" if leeds_is_home else "away"
    side = lineups.get(side_name)
    if not isinstance(side, Mapping):
        raise ShirtNumberDiffError("source bundle has no Leeds lineup side")
    starters = side.get("starters")
    bench = side.get("bench")
    if not isinstance(starters, list) or not isinstance(bench, list):
        raise ShirtNumberDiffError("Leeds starter/bench populations are missing")
    rows = [row for row in starters + bench if isinstance(row, Mapping)]
    if len(starters) != 11 or len(rows) != 20:
        raise ShirtNumberDiffError(
            f"Leeds shirt-number population must be XI 11 / squad 20; found XI {len(starters)} / squad {len(rows)}"
        )
    return rows


def build_shirt_number_operations(
    *,
    source_bundle: Mapping[str, Any],
    identity_package: Mapping[str, Any],
    canonical_match_id: int,
) -> dict[str, Any]:
    """Return 20 canonical shirt-number INSERT proposals; never allocate row IDs."""
    match_id = _require_int(canonical_match_id, "canonical match ID")
    rows = _lineup_population(source_bundle)
    operations: list[dict[str, Any]] = []
    provider_ids: set[int] = set()
    canonical_ids: set[int] = set()
    shirt_numbers: set[int] = set()

    for row in rows:
        provider_id = _require_int(row.get("sofascore_player_id"), "lineup provider player ID")
        shirt_number = row.get("shirt_number")
        if not isinstance(shirt_number, int):
            shirt_number = row.get("jersey_number")
        shirt_number = _require_int(shirt_number, "shirt number")
        if shirt_number <= 0:
            raise ShirtNumberDiffError("shirt number must be positive")
        player_id = _resolved_leeds_player(identity_package, provider_id)

        if provider_id in provider_ids:
            raise ShirtNumberDiffError(f"duplicate Leeds provider player ID {provider_id}")
        if player_id in canonical_ids:
            raise ShirtNumberDiffError(f"duplicate canonical Leeds player ID {player_id}")
        if shirt_number in shirt_numbers:
            raise ShirtNumberDiffError(f"duplicate Leeds shirt number {shirt_number}")
        provider_ids.add(provider_id)
        canonical_ids.add(player_id)
        shirt_numbers.add(shirt_number)

        operations.append(
            {
                "table": "player_match_shirt_numbers",
                "action": "INSERT",
                "key": {"match_id": match_id, "player_id": player_id},
                "values": {
                    "shirt_number": shirt_number,
                    # Existing column is nullable. Provider provenance belongs in the
                    # ingestion provenance layer, not a fabricated historical source row.
                    "source_row_id": None,
                },
            }
        )

    return {
        "status": "PASS",
        "canonical_match_id": match_id,
        "operation_count": len(operations),
        "operations": operations,
        "primary_key_allocation_performed": False,
        "provider_ids_written_to_canonical_ids": False,
        "database_writes": 0,
        "sql_generated": False,
        "promotion_performed": False,
    }
