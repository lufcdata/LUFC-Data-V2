#!/usr/bin/env python3
"""Build one zero-write ingestion package directly from captured SofaScore payloads.

This orchestration layer makes source-derived reconciliation and staged-event results
authoritative for their gates. Callers may supply the remaining externally validated
gates (fixture identity, managers, formations, attendance, league position, identity
mapping, etc.), but they cannot override source-derived lineup/event populations.

No network or database access is performed here.
"""

from __future__ import annotations

from typing import Any, Mapping

from sofascore_ingestion_run_package import build_ingestion_run_package
from sofascore_source_derived_dry_run import build_source_derived_dry_run


class SourceDrivenPackageError(RuntimeError):
    """Raised when a source-driven package cannot be assembled safely."""


SOURCE_DERIVED_VALIDATION_GATES = (
    "lineups",
    "goals",
    "scores",
    "substitutions",
    "cards",
    "shots",
)


def _require_zero_write_source_bundle(bundle: Mapping[str, Any]) -> None:
    if bundle.get("database_writes") != 0:
        raise SourceDrivenPackageError("source-derived bundle reports database writes")
    if bundle.get("canonical_lufc_ids_assigned") is not False:
        raise SourceDrivenPackageError("source-derived bundle reports canonical LUFC IDs")
    if bundle.get("promotion_performed") is not False:
        raise SourceDrivenPackageError("source-derived bundle reports promotion")


def _require_zero_write_canonical_diff(canonical_diff: Mapping[str, Any]) -> None:
    if canonical_diff.get("database_writes") != 0:
        raise SourceDrivenPackageError("canonical diff reports database writes")
    if canonical_diff.get("promotion_performed") not in {None, False}:
        raise SourceDrivenPackageError("canonical diff reports promotion")


def build_source_driven_ingestion_package(
    *,
    run_id: str,
    importer_git_sha: str,
    raw_payloads: Mapping[str, Any],
    leeds_team_provider_id: int,
    identity_package: Mapping[str, Any],
    canonical_diff: Mapping[str, Any],
    external_validations: Mapping[str, Any],
    backup: Mapping[str, Any] | None = None,
    rollback_manifest: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Derive source populations, merge non-overridable validations, then package them."""
    source_bundle = build_source_derived_dry_run(
        raw_payloads=raw_payloads,
        leeds_team_provider_id=leeds_team_provider_id,
    )
    _require_zero_write_source_bundle(source_bundle)
    _require_zero_write_canonical_diff(canonical_diff)

    source_event_id = source_bundle.get("sofascore_event_id")
    if not isinstance(source_event_id, int):
        raise SourceDrivenPackageError("source-derived bundle has no numeric SofaScore event ID")

    validations = dict(external_validations)
    source_validations = source_bundle.get("validations")
    if not isinstance(source_validations, Mapping):
        raise SourceDrivenPackageError("source-derived bundle has no validations")

    # Source-derived populations always win over caller-supplied claims. This prevents
    # a stale/manual PASS from masking a contradiction in the captured payloads.
    for gate_name in SOURCE_DERIVED_VALIDATION_GATES:
        value = source_validations.get(gate_name)
        if not isinstance(value, Mapping):
            raise SourceDrivenPackageError(
                f"source-derived validation is missing: {gate_name}"
            )
        validations[gate_name] = dict(value)

    package = build_ingestion_run_package(
        run_id=run_id,
        sofascore_event_id=source_event_id,
        importer_git_sha=importer_git_sha,
        raw_payloads=raw_payloads,
        identity_package=identity_package,
        reconciliation=source_bundle["reconciliation"],
        staged_events=source_bundle["staged_events"],
        canonical_diff=canonical_diff,
        validations=validations,
        backup=backup,
        rollback_manifest=rollback_manifest,
    )

    return {
        "status": package["promotion_gate"]["status"],
        "source_derived": source_bundle,
        "package": package,
        "database_writes": 0,
        "canonical_promotion_performed": False,
    }
