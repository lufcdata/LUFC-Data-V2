#!/usr/bin/env python3
"""Build a zero-write proposal for an opposition captain source fact.

Production currently has a Leeds captain field but no deployed audited canonical
destination for opposition captains or opposition-player identities. Preserve the
source fact without forcing a SofaScore player ID into the Leeds `players` namespace.
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence


class OppositionCaptainDiffError(RuntimeError):
    """Raised when opposition-captain evidence cannot be preserved safely."""


def _require_int(value: Any, label: str) -> int:
    if not isinstance(value, int):
        raise OppositionCaptainDiffError(f"{label} must be an integer")
    return value


def build_opposition_captain_proposal(
    *,
    canonical_match_id: int,
    source_bundle: Mapping[str, Any],
    evidence_bundle: Mapping[str, Any],
) -> dict[str, Any]:
    """Preserve the exact opposition captain while leaving promotion blocked."""
    match_id = _require_int(canonical_match_id, "canonical match ID")
    if source_bundle.get("database_writes") != 0 or source_bundle.get("promotion_performed") is not False:
        raise OppositionCaptainDiffError("source bundle is not zero-write")
    if evidence_bundle.get("database_writes") != 0 or evidence_bundle.get("promotion_performed") is not False:
        raise OppositionCaptainDiffError("evidence bundle is not zero-write")

    leeds_is_home = source_bundle.get("leeds_is_home")
    if not isinstance(leeds_is_home, bool):
        raise OppositionCaptainDiffError("source bundle has no Leeds home/away identity")
    opposition_side = "away" if leeds_is_home else "home"

    validations = evidence_bundle.get("validations")
    if not isinstance(validations, Mapping):
        raise OppositionCaptainDiffError("evidence bundle has no validations")
    captains = validations.get("captains")
    if not isinstance(captains, Mapping) or captains.get("status") != "PASS":
        raise OppositionCaptainDiffError("captain evidence is not PASS")
    provider_id = _require_int(
        captains.get(f"{opposition_side}_captain_provider_id"),
        "opposition captain provider ID",
    )

    lineups = source_bundle.get("lineups")
    if not isinstance(lineups, Mapping):
        raise OppositionCaptainDiffError("source bundle has no lineups")
    opposition_lineup = lineups.get(opposition_side)
    if not isinstance(opposition_lineup, Mapping):
        raise OppositionCaptainDiffError("source bundle has no opposition lineup")

    candidates: list[Mapping[str, Any]] = []
    for population in ("starters", "bench"):
        rows = opposition_lineup.get(population) or []
        if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
            raise OppositionCaptainDiffError(f"opposition {population} population is invalid")
        candidates.extend(row for row in rows if isinstance(row, Mapping))
    matches = [row for row in candidates if row.get("sofascore_player_id") == provider_id]
    if len(matches) != 1:
        raise OppositionCaptainDiffError(
            f"opposition captain provider ID {provider_id} matched {len(matches)} lineup rows"
        )
    name = str(matches[0].get("name") or "").strip()
    if not name:
        raise OppositionCaptainDiffError("opposition captain source name is missing")

    operation = {
        "table": "opposition_captains",
        "action": "INSERT_AFTER_PARENT_KEY_ALLOCATION_AND_SCHEMA_DEPLOYMENT",
        "key": {"match_id": match_id},
        "values": {
            "match_id": match_id,
            "captain_name_raw": name,
            "ingestion_run_id": "<FROM_PARENT_INSERT>",
        },
        "deferred_parent_key": {
            "column": "ingestion_run_id",
            "from_operation": "ingestion.runs",
            "allocation": "FROM_PARENT_INSERT",
        },
        "provider_evidence": {
            "provider": "sofascore",
            "provider_player_id": provider_id,
            "provider_team_id": source_bundle.get(
                "away_team_provider_id" if leeds_is_home else "home_team_provider_id"
            ),
        },
        "canonical_opposition_player_id": None,
        "provider_id_written_to_canonical_id": False,
        "canonical_primary_key_allocated": False,
    }

    return {
        "status": "SCHEMA_GAP",
        "canonical_destination": "opposition_captains",
        "destination_deployed": False,
        "canonical_match_id": match_id,
        "captain_name_raw": name,
        "provider_player_id": provider_id,
        "operations": [operation],
        "operation_count": 1,
        "blocker": "opposition captain destination and parent ingestion run are not deployed",
        "database_writes": 0,
        "sql_generated": False,
        "promotion_performed": False,
    }
