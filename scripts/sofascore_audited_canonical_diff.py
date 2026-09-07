#!/usr/bin/env python3
"""Compose audited canonical adapters into one zero-write LUFC proposal.

This layer closes only schema gaps whose live production contracts have been audited.
It does not weaken or hide unresolved gaps. Shirt numbers are routed to the existing
match-shirt table. Opposition managerial authority is routed through the Gold relational
model with its parent key explicitly deferred to the eventual promotion transaction.
"""

from __future__ import annotations

from typing import Any, Mapping

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

    operations = list(base.get("operations") or [])
    operations.extend(shirts["operations"])
    operations.extend(manager["operations"])

    # Remove exactly the gap now satisfied by the audited Gold manager adapter. No
    # other schema gap may disappear as a side effect of composition.
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
        "audited_composition": True,
        "database_writes": 0,
        "sql_generated": False,
        "promotion_performed": False,
    }
