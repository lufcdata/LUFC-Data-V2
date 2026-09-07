#!/usr/bin/env python3
"""Fail-closed promotion gate for post-match ingestion proposals.

This module has no network or database access and performs no writes. It combines
already-validated dry-run results into one auditable promotion decision. A fixture
is never READY while a mandatory validation is absent, failed, unresolved, or while
the verified pre-import backup / rollback manifest is missing.
"""

from __future__ import annotations

from typing import Any, Mapping

REQUIRED_VALIDATION_GATES = (
    "fixture",
    "lineups",
    "captains",
    "managers",
    "goals",
    "scores",
    "substitutions",
    "cards",
    "shots",
    "formations",
    "attendance",
    "league_position",
    "identity_mapping",
    "raw_provenance",
    "canonical_diff",
)

PASS_STATUSES = {"PASS", "VALIDATED", "RESOLVED", "SOURCE_FACT", "SECONDARY_SOURCE_FACT", "NOT_APPLICABLE"}


class PromotionGateError(RuntimeError):
    """Raised when a promotion proposal is malformed or unsafe."""


def _status(value: Any) -> str:
    if isinstance(value, str):
        return value.strip().upper()
    if isinstance(value, Mapping):
        return str(value.get("status") or "").strip().upper()
    return ""


def _gate_passes(value: Any) -> bool:
    return _status(value) in PASS_STATUSES


def evaluate_promotion_gate(
    validations: Mapping[str, Any],
    *,
    backup: Mapping[str, Any] | None = None,
    rollback_manifest: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Return one deterministic READY/BLOCKED decision without writing anything."""
    missing = [name for name in REQUIRED_VALIDATION_GATES if name not in validations]
    failed = [
        name
        for name in REQUIRED_VALIDATION_GATES
        if name in validations and not _gate_passes(validations[name])
    ]

    backup_status = _status(backup)
    backup_verified = backup_status in {"PASS", "VERIFIED"}
    rollback_status = _status(rollback_manifest)
    rollback_ready = rollback_status in {"PASS", "READY", "VERIFIED"}

    blockers: list[str] = []
    blockers.extend(f"missing validation: {name}" for name in missing)
    blockers.extend(
        f"validation not passed: {name} ({_status(validations[name]) or 'MISSING_STATUS'})"
        for name in failed
    )
    if not backup_verified:
        blockers.append("verified pre-import backup required")
    if not rollback_ready:
        blockers.append("rollback manifest required")

    status = "READY_FOR_PROMOTION" if not blockers else "BLOCKED"
    return {
        "status": status,
        "validation_gate_count": len(REQUIRED_VALIDATION_GATES),
        "passed_validation_count": len(REQUIRED_VALIDATION_GATES) - len(missing) - len(failed),
        "backup": "VERIFIED" if backup_verified else "REQUIRED",
        "rollback_manifest": "READY" if rollback_ready else "REQUIRED",
        "blocker_count": len(blockers),
        "blockers": blockers,
        "database_writes": 0,
        "promotion_performed": False,
    }


def require_ready_for_promotion(result: Mapping[str, Any]) -> None:
    """Raise unless a previously evaluated proposal is explicitly ready."""
    if _status(result) != "READY_FOR_PROMOTION":
        blockers = result.get("blockers") if isinstance(result, Mapping) else None
        raise PromotionGateError(f"promotion blocked: {blockers or 'unresolved gate'}")
