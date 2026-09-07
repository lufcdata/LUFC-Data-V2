#!/usr/bin/env python3
"""Assemble one immutable, zero-write post-match ingestion run package.

The package is the hand-off boundary between collection/validation and any future
promotion machinery. It contains source payload fingerprints, identity resolution,
reconciliation results, staged events, proposed canonical changes, schema gaps and
the master gate result. This module has no network or database access and performs
no writes.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

from sofascore_promotion_gate import evaluate_promotion_gate


class IngestionRunPackageError(RuntimeError):
    """Raised when a dry-run package is incomplete or internally inconsistent."""


def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _require_text(value: Any, label: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise IngestionRunPackageError(f"{label} is required")
    return text


def _require_int(value: Any, label: str) -> int:
    if not isinstance(value, int):
        raise IngestionRunPackageError(f"{label} must be an integer")
    return value


def _validate_staged_events(staged_events: Mapping[str, Any]) -> None:
    events = staged_events.get("events")
    if not isinstance(events, list):
        raise IngestionRunPackageError("staged event population must contain an events list")
    if staged_events.get("event_count") != len(events):
        raise IngestionRunPackageError("staged event_count does not match staged events list")
    if staged_events.get("database_writes") != 0:
        raise IngestionRunPackageError("staged event population reports database writes")
    if staged_events.get("promotion_performed") is not False:
        raise IngestionRunPackageError("staged event population reports promotion")


def build_ingestion_run_package(
    *,
    run_id: str,
    sofascore_event_id: int,
    importer_git_sha: str,
    raw_payloads: Mapping[str, Any],
    identity_package: Mapping[str, Any],
    reconciliation: Mapping[str, Any],
    staged_events: Mapping[str, Any],
    canonical_diff: Mapping[str, Any],
    validations: Mapping[str, Any],
    backup: Mapping[str, Any] | None = None,
    rollback_manifest: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Return one deterministic audit package; never write to canonical storage."""
    run_id = _require_text(run_id, "run ID")
    event_id = _require_int(sofascore_event_id, "SofaScore event ID")
    git_sha = _require_text(importer_git_sha, "importer Git SHA")

    if not raw_payloads:
        raise IngestionRunPackageError("at least one raw payload is required")

    identity_match = identity_package.get("match")
    if not isinstance(identity_match, Mapping) or identity_match.get("provider_id") != event_id:
        raise IngestionRunPackageError("identity package does not resolve the requested SofaScore event")

    diff_event_id = canonical_diff.get("sofascore_event_id")
    if diff_event_id != event_id:
        raise IngestionRunPackageError("canonical diff SofaScore event ID does not match run event")

    _validate_staged_events(staged_events)

    raw_manifest = {
        name: {
            "sha256": _sha256(payload),
            "byte_length": len(_canonical_json(payload)),
        }
        for name, payload in sorted(raw_payloads.items())
    }
    raw_manifest_sha256 = _sha256(raw_manifest)
    staged_events_sha256 = _sha256(staged_events)

    gate_validations = dict(validations)
    gate_validations["raw_provenance"] = {
        "status": "PASS",
        "payload_count": len(raw_manifest),
        "manifest_sha256": raw_manifest_sha256,
    }
    # Staged events are an auditable integrity validation carried in the package.
    # They are not one of the 15 canonical promotion gates, but retaining the PASS
    # result here prevents a source-derived validation from disappearing at hand-off.
    gate_validations["staged_events"] = {
        "status": "PASS",
        "event_count": staged_events.get("event_count"),
        "schema_gap_event_count": staged_events.get("schema_gap_event_count"),
        "eligible_event_count": staged_events.get("eligible_event_count"),
        "sha256": staged_events_sha256,
    }
    gate_validations["canonical_diff"] = {
        "status": "PASS" if canonical_diff.get("status") == "PASS" else "BLOCKED",
        "schema_gap_count": canonical_diff.get("schema_gap_count"),
    }

    gate = evaluate_promotion_gate(
        gate_validations,
        backup=backup,
        rollback_manifest=rollback_manifest,
    )

    blockers = list(gate.get("blockers") or [])
    schema_gaps = list(canonical_diff.get("schema_gaps") or [])

    package_core = {
        "run_id": run_id,
        "provider": "sofascore",
        "sofascore_event_id": event_id,
        "importer_git_sha": git_sha,
        "raw_manifest": raw_manifest,
        "raw_manifest_sha256": raw_manifest_sha256,
        "identity_package": identity_package,
        "reconciliation": reconciliation,
        "staged_events": staged_events,
        "staged_events_sha256": staged_events_sha256,
        "canonical_diff": canonical_diff,
        "validations": gate_validations,
        "promotion_gate": gate,
        "schema_gaps": schema_gaps,
        "blockers": blockers,
        "database_writes": 0,
        "canonical_promotion_performed": False,
    }
    package_core["package_sha256"] = _sha256(package_core)
    return package_core


def require_zero_write_package(package: Mapping[str, Any]) -> None:
    """Fail if a purported dry-run package claims any write/promotion occurred."""
    if package.get("database_writes") != 0:
        raise IngestionRunPackageError("dry-run package reports database writes")
    if package.get("canonical_promotion_performed") is not False:
        raise IngestionRunPackageError("dry-run package reports canonical promotion")
