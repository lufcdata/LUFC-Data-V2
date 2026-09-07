#!/usr/bin/env python3
"""Build a zero-write opposition-manager proposal against the Gold relational model.

The Gold model is `managerial_assignments` -> `managerial_assignment_people`. This
adapter deliberately does not invent a `managerial_assignment_id`: that primary key has
no database default and must be allocated transactionally by the eventual promotion
layer. Instead, the proposal is keyed by the canonical match and carries the already
resolved `managerial_people` identity for the linked person row.
"""

from __future__ import annotations

from typing import Any, Mapping


class OppositionManagerDiffError(RuntimeError):
    """Raised when an opposition-manager assignment cannot be proposed safely."""


def _require_int(value: Any, label: str) -> int:
    if not isinstance(value, int):
        raise OppositionManagerDiffError(f"{label} must be an integer")
    return value


def _require_text(value: Any, label: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise OppositionManagerDiffError(f"{label} is required")
    return text


def _opposition_manager_id(identity_package: Mapping[str, Any], provider_id: int) -> int:
    resolution = identity_package.get("opposition_manager")
    if not isinstance(resolution, Mapping):
        raise OppositionManagerDiffError("identity package has no opposition_manager resolution")
    if resolution.get("entity_scope") != "opposition_manager":
        raise OppositionManagerDiffError("opposition manager identity has the wrong entity scope")
    if resolution.get("canonical_namespace") != "managerial_people.managerial_person_id":
        raise OppositionManagerDiffError("opposition manager identity has the wrong canonical namespace")
    if resolution.get("provider_id") != provider_id:
        raise OppositionManagerDiffError("opposition manager provider ID does not match evidence")
    return _require_int(resolution.get("canonical_id"), "canonical opposition managerial person ID")


def build_opposition_manager_assignment_proposal(
    *,
    evidence_bundle: Mapping[str, Any],
    identity_package: Mapping[str, Any],
    canonical_match_id: int,
    leeds_is_home: bool,
    canonical_name: str,
    nationality_display: str | None = None,
) -> dict[str, Any]:
    """Return a Gold-compatible relational proposal without allocating generated IDs."""
    match_id = _require_int(canonical_match_id, "canonical match ID")
    if not isinstance(leeds_is_home, bool):
        raise OppositionManagerDiffError("leeds_is_home must be boolean")
    if evidence_bundle.get("status") != "PASS":
        raise OppositionManagerDiffError("evidence bundle is not PASS")

    validations = evidence_bundle.get("validations")
    if not isinstance(validations, Mapping):
        raise OppositionManagerDiffError("evidence bundle has no validations")
    managers = validations.get("managers")
    if not isinstance(managers, Mapping) or managers.get("status") != "PASS":
        raise OppositionManagerDiffError("manager evidence is not PASS")

    opposition_side = "away" if leeds_is_home else "home"
    provider_id = _require_int(
        managers.get(f"{opposition_side}_manager_provider_id"),
        "opposition manager provider ID",
    )
    person_id = _opposition_manager_id(identity_package, provider_id)
    name = _require_text(canonical_name, "opposition manager canonical name")
    nationality = str(nationality_display or "").strip() or None

    assignment = {
        "table": "managerial_assignments",
        "action": "INSERT",
        # Match is the authoritative natural key: production enforces UNIQUE(match_id).
        "key": {"match_id": match_id},
        "values": {
            "authority_type": "individual",
            "managerial_committee_id": None,
            "assignment_certainty": "confirmed",
            "raw_source": name,
            "canonical_source_name": name,
            "nationality_display": nationality,
            "provenance_status": "forensically_validated",
            "provenance_note": "SofaScore manager identity resolved to Gold managerial_people; raw provider evidence retained by ingestion provenance",
        },
        "deferred_primary_key": {
            "column": "managerial_assignment_id",
            "allocation": "TRANSACTIONAL_AT_PROMOTION",
            "reason": "column is NOT NULL with no database default; never guess from match_id or max(id)+1 in the dry-run diff",
        },
    }
    person_link = {
        "table": "managerial_assignment_people",
        "action": "INSERT_AFTER_PARENT_KEY_ALLOCATION",
        "key": {
            "managerial_assignment_id": "<FROM_PARENT_INSERT>",
            "managerial_person_id": person_id,
        },
        "values": {
            "member_role": "manager",
            "role_certainty": "confirmed",
            "provenance_note": "Resolved SofaScore opposition manager identity",
        },
    }

    return {
        "status": "PASS",
        "canonical_match_id": match_id,
        "opposition_manager_provider_id": provider_id,
        "managerial_person_id": person_id,
        "authority_type": "individual",
        "operations": [assignment, person_link],
        "operation_count": 2,
        "primary_key_allocation_performed": False,
        "requires_transactional_parent_key_allocation": True,
        "gold_model": "managerial_assignments -> managerial_assignment_people",
        "database_writes": 0,
        "sql_generated": False,
        "promotion_performed": False,
    }
