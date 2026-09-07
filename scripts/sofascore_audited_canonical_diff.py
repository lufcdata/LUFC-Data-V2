#!/usr/bin/env python3
"""Compose audited canonical adapters into one zero-write LUFC proposal.

This layer closes only schema gaps whose live production contracts have been audited.
It does not weaken or hide unresolved gaps. Shirt numbers are routed to the existing
match-shirt table. Opposition managerial authority is routed through the Gold relational
model with its parent key explicitly deferred to the eventual promotion transaction.
Designed-but-not-deployed destinations may contribute exact blocked rows, but their
schema gaps remain blocking until deployment is separately approved and verified.
"""

from __future__ import annotations

from typing import Any, Mapping

from sofascore_opposition_captain_diff import build_opposition_captain_proposal
from sofascore_opposition_goal_diff import build_opposition_goal_proposal
from sofascore_opposition_manager_diff import build_opposition_manager_assignment_proposal
from sofascore_shirt_number_diff import build_shirt_number_operations
from sofascore_source_canonical_diff import build_source_canonical_diff


class AuditedCanonicalDiffError(RuntimeError):
    """Raised when audited canonical composition cannot be completed safely."""


def _require_int(value: Any, label: str) -> int:
    if not isinstance(value, int):
        raise AuditedCanonicalDiffError(f"{label} must be an integer")
    return value


def _require_text(value: Any, label: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise AuditedCanonicalDiffError(f"{label} is required")
    return text


def build_audited_canonical_diff(
    *,
    raw_payloads: Mapping[str, Any],
    source_bundle: Mapping[str, Any],
    evidence_bundle: Mapping[str, Any],
    identity_package: Mapping[str, Any],
    canonical_context: Mapping[str, Any],
    leeds_team_provider_id: int,
) -> dict[str, Any]:
    """Return one composed source-derived diff; still never execute promotion."""
    base = build_source_canonical_diff(
        raw_payloads=raw_payloads,
        source_bundle=source_bundle,
        evidence_bundle=evidence_bundle,
        identity_package=identity_package,
        canonical_context=canonical_context,
        leeds_team_provider_id=leeds_team_provider_id,
    )
    if base.get("database_writes") != 0 or base.get("promotion_performed") is not False:
        raise AuditedCanonicalDiffError("base canonical diff violated zero-write contract")

    match_id = _require_int(base.get("canonical_match_id"), "canonical match ID")
    leeds_is_home = source_bundle.get("leeds_is_home")
    if not isinstance(leeds_is_home, bool):
        raise AuditedCanonicalDiffError("source bundle has no Leeds home/away identity")

    shirts = build_shirt_number_operations(
        source_bundle=source_bundle,
        identity_package=identity_package,
        canonical_match_id=match_id,
    )
    manager = build_opposition_manager_assignment_proposal(
        evidence_bundle=evidence_bundle,
        identity_package=identity_package,
        canonical_match_id=match_id,
        leeds_is_home=leeds_is_home,
        canonical_name=_require_text(
            canonical_context.get("opposition_manager_canonical_name"),
            "opposition manager canonical name",
        ),
        nationality_display=canonical_context.get("opposition_manager_nationality_display"),
    )
    staged_events = source_bundle.get("staged_events")
    if not isinstance(staged_events, Mapping):
        raise AuditedCanonicalDiffError("source bundle has no staged-event population")
    opposition_goals = build_opposition_goal_proposal(
        canonical_match_id=match_id,
        staged_events=staged_events,
    )
    opposition_captain = build_opposition_captain_proposal(
        canonical_match_id=match_id,
        source_bundle=source_bundle,
        evidence_bundle=evidence_bundle,
    )

    operations = list(base.get("operations") or [])
    operations.extend(shirts["operations"])
    operations.extend(manager["operations"])
    # These are explicit BLOCKED operations: carrying them in the diff makes the
    # missing destinations inspectable without pretending they have been deployed.
    operations.extend(opposition_goals["operations"])
    operations.extend(opposition_captain["operations"])

    # Remove exactly the gap now satisfied by the audited Gold manager adapter. The
    # structured-opposition-goals and opposition-captain gaps deliberately remain because
    # their destinations are designed/preserved but not deployed.
    base_gaps = base.get("schema_gaps")
    if not isinstance(base_gaps, list):
        raise AuditedCanonicalDiffError("base canonical diff has no schema-gap population")
    manager_gaps = [
        gap for gap in base_gaps
        if isinstance(gap, Mapping)
        and gap.get("domain") == "match"
        and gap.get("field") == "opposition manager"
    ]
    if len(manager_gaps) != 1:
        raise AuditedCanonicalDiffError(
            f"expected exactly one opposition-manager schema gap; found {len(manager_gaps)}"
        )
    opposition_goal_gaps = [
        gap for gap in base_gaps
        if isinstance(gap, Mapping) and gap.get("field") == "structured opposition goals"
    ]
    if len(opposition_goal_gaps) != 1:
        raise AuditedCanonicalDiffError(
            f"expected exactly one structured-opposition-goals schema gap; found {len(opposition_goal_gaps)}"
        )
    captain_gaps = [
        gap for gap in base_gaps
        if isinstance(gap, Mapping) and gap.get("field") == "opposition captain"
    ]
    if len(captain_gaps) != 1:
        raise AuditedCanonicalDiffError(
            f"expected exactly one opposition-captain schema gap; found {len(captain_gaps)}"
        )
    if opposition_goals.get("status") != "SCHEMA_GAP" or opposition_goals.get("destination_deployed") is not False:
        raise AuditedCanonicalDiffError("opposition-goal adapter must remain schema-blocked before deployment")
    if opposition_captain.get("status") != "SCHEMA_GAP" or opposition_captain.get("destination_deployed") is not False:
        raise AuditedCanonicalDiffError("opposition-captain adapter must remain schema-blocked before deployment")

    remaining_gaps = [gap for gap in base_gaps if gap not in manager_gaps]

    return {
        **base,
        "status": "BLOCKED" if remaining_gaps else "PASS",
        "operations": operations,
        "operation_count": len(operations),
        "schema_gaps": remaining_gaps,
        "schema_gap_count": len(remaining_gaps),
        "shirt_number_adapter": {
            "status": shirts["status"],
            "operation_count": shirts["operation_count"],
        },
        "opposition_manager_adapter": {
            "status": manager["status"],
            "managerial_person_id": manager["managerial_person_id"],
            "operation_count": manager["operation_count"],
            "requires_transactional_parent_key_allocation": manager[
                "requires_transactional_parent_key_allocation"
            ],
        },
        "opposition_goal_adapter": {
            "status": opposition_goals["status"],
            "canonical_destination": opposition_goals["canonical_destination"],
            "destination_deployed": opposition_goals["destination_deployed"],
            "opposition_goal_count": opposition_goals["opposition_goal_count"],
            "operation_count": opposition_goals["operation_count"],
            "blocker": opposition_goals["blocker"],
        },
        "opposition_captain_adapter": {
            "status": opposition_captain["status"],
            "canonical_destination": opposition_captain["canonical_destination"],
            "destination_deployed": opposition_captain["destination_deployed"],
            "captain_name_raw": opposition_captain["captain_name_raw"],
            "provider_player_id": opposition_captain["provider_player_id"],
            "operation_count": opposition_captain["operation_count"],
            "blocker": opposition_captain["blocker"],
        },
        "audited_composition": True,
        "database_writes": 0,
        "sql_generated": False,
        "promotion_performed": False,
    }
