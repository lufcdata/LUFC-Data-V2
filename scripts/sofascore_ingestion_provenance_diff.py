#!/usr/bin/env python3
"""Build zero-write proposals for ingestion provenance that is not yet deployed.

This adapter gives audited source facts an explicit operational destination without
pretending the private ingestion schema exists in production. It must remain fail-closed
until that schema is separately reviewed, migrated and verified outside production.
"""

from __future__ import annotations

from typing import Any, Mapping


class IngestionProvenanceDiffError(RuntimeError):
    """Raised when source provenance cannot be represented safely."""


def _require_int(value: Any, label: str) -> int:
    if not isinstance(value, int):
        raise IngestionProvenanceDiffError(f"{label} must be an integer")
    return value


def _require_text(value: Any, label: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise IngestionProvenanceDiffError(f"{label} is required")
    return text


def build_ingestion_provenance_proposal(
    *,
    canonical_match_id: int,
    source_bundle: Mapping[str, Any],
    evidence_bundle: Mapping[str, Any],
) -> dict[str, Any]:
    """Preserve provider fixture identity and attendance provenance as blocked rows."""
    match_id = _require_int(canonical_match_id, "canonical match ID")
    if source_bundle.get("database_writes") != 0 or source_bundle.get("promotion_performed") is not False:
        raise IngestionProvenanceDiffError("source bundle is not zero-write")
    if evidence_bundle.get("database_writes") != 0 or evidence_bundle.get("promotion_performed") is not False:
        raise IngestionProvenanceDiffError("evidence bundle is not zero-write")

    source_event_id = _require_int(source_bundle.get("sofascore_event_id"), "SofaScore event ID")
    evidence_event_id = _require_int(evidence_bundle.get("sofascore_event_id"), "evidence SofaScore event ID")
    if source_event_id != evidence_event_id:
        raise IngestionProvenanceDiffError(
            f"SofaScore event identity mismatch: source={source_event_id}, evidence={evidence_event_id}"
        )

    validations = evidence_bundle.get("validations")
    if not isinstance(validations, Mapping):
        raise IngestionProvenanceDiffError("evidence bundle has no validations")
    attendance = validations.get("attendance")
    if not isinstance(attendance, Mapping) or attendance.get("status") not in {
        "SECONDARY_SOURCE_FACT",
        "SOURCE_FACT",
    }:
        raise IngestionProvenanceDiffError("attendance evidence is not an approved source fact")

    attendance_value = _require_int(attendance.get("attendance"), "attendance")
    if attendance_value <= 0:
        raise IngestionProvenanceDiffError("attendance must be positive")
    attendance_source = _require_text(attendance.get("source"), "attendance source")
    authority = "SECONDARY" if attendance.get("status") == "SECONDARY_SOURCE_FACT" else "PRIMARY"

    operations = [
        {
            "table": "ingestion.runs",
            "action": "INSERT_AFTER_SCHEMA_DEPLOYMENT",
            "key": {
                "provider": "sofascore",
                "provider_event_id": str(source_event_id),
                "canonical_match_id": match_id,
            },
            "values": {
                "provider": "sofascore",
                "provider_event_id": str(source_event_id),
                "canonical_match_id": match_id,
                "status": "BLOCKED",
                "database_writes": 0,
            },
            "provider_id_written_to_canonical_id": False,
            "canonical_primary_key_allocated": False,
        },
        {
            "table": "ingestion.field_provenance",
            "action": "INSERT_AFTER_SCHEMA_DEPLOYMENT",
            "key": {
                "domain": "fixture",
                "record_key": f"matches.match_id={match_id}",
                "field_name": "attendance",
            },
            "values": {
                "domain": "fixture",
                "record_key": f"matches.match_id={match_id}",
                "field_name": "attendance",
                "value_json": attendance_value,
                "source_provider": attendance_source,
                "authority": authority,
                "validation_status": "VALIDATED",
                "resolution_note": "Attendance retained with field-level source attribution; stadium capacity is not an attendance source.",
            },
            "canonical_primary_key_allocated": False,
        },
    ]

    return {
        "status": "SCHEMA_GAP",
        "destination_deployed": False,
        "provider_event_id": source_event_id,
        "canonical_match_id": match_id,
        "attendance": attendance_value,
        "attendance_source": attendance_source,
        "attendance_authority": authority,
        "operations": operations,
        "operation_count": len(operations),
        "blockers": [
            "private ingestion schema is designed but not deployed",
            "SofaScore external event identity must remain provider-namespaced",
            "attendance field provenance must exist before canonical promotion",
        ],
        "database_writes": 0,
        "sql_generated": False,
        "promotion_performed": False,
    }
