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
    importer_git_sha: str,
) -> dict[str, Any]:
    """Preserve provider fixture identity and attendance provenance as blocked rows."""
    match_id = _require_int(canonical_match_id, "canonical match ID")
    git_sha = _require_text(importer_git_sha, "importer Git SHA")
    if len(git_sha) != 40 or any(char not in "0123456789abcdef" for char in git_sha.lower()):
        raise IngestionProvenanceDiffError("importer Git SHA must be a 40-character hexadecimal commit SHA")

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
    if not isinstance(attendance, Mapping):
        raise IngestionProvenanceDiffError("attendance evidence is missing")

    attendance_status = attendance.get("status")
    if attendance_status not in {"SECONDARY_SOURCE_FACT", "SOURCE_FACT", "NOT_PUBLISHED"}:
        raise IngestionProvenanceDiffError("attendance evidence is not resolved")
    if attendance.get("blocking") is True:
        raise IngestionProvenanceDiffError("attendance evidence remains blocking")

    attendance_source = _require_text(attendance.get("source"), "attendance source")
    if attendance_status == "NOT_PUBLISHED":
        if attendance.get("attendance") is not None:
            raise IngestionProvenanceDiffError("verified unpublished attendance must have a null value")
        attendance_value = None
        authority = "VERIFIED_ABSENCE"
        validation_status = "NOT_PUBLISHED"
        resolution_note = (
            "Approved source was successfully checked and did not publish an attendance figure; "
            "canonical attendance remains NULL and may be enriched later if a verified value appears."
        )
    else:
        attendance_value = _require_int(attendance.get("attendance"), "attendance")
        if attendance_value <= 0:
            raise IngestionProvenanceDiffError("attendance must be positive")
        authority = "SECONDARY" if attendance_status == "SECONDARY_SOURCE_FACT" else "PRIMARY"
        validation_status = "VALIDATED"
        resolution_note = (
            "Attendance retained with field-level source attribution; stadium capacity is not an attendance source."
        )

    operations = [
        {
            "table": "ingestion.runs",
            "action": "INSERT_AFTER_SCHEMA_DEPLOYMENT",
            "key": {
                "provider": "sofascore",
                "provider_event_id": str(source_event_id),
                "importer_git_sha": git_sha,
            },
            "values": {
                "provider": "sofascore",
                "provider_event_id": str(source_event_id),
                "canonical_match_id": match_id,
                "status": "BLOCKED",
                "importer_git_sha": git_sha,
                "database_writes": 0,
            },
            "deferred_primary_key": {
                "column": "ingestion_run_id",
                "allocation": "UUID_AT_INSERT_AFTER_SCHEMA_DEPLOYMENT",
                "reason": "ingestion.runs requires a UUID primary key; the zero-write proposal never fabricates operational IDs",
            },
            "provider_id_written_to_canonical_id": False,
            "canonical_primary_key_allocated": False,
        },
        {
            "table": "ingestion.field_provenance",
            "action": "INSERT_AFTER_PARENT_KEY_ALLOCATION_AND_SCHEMA_DEPLOYMENT",
            "key": {
                "ingestion_run_id": "<FROM_PARENT_INSERT>",
                "domain": "fixture",
                "record_key": f"matches.match_id={match_id}",
                "field_name": "attendance",
            },
            "values": {
                "ingestion_run_id": "<FROM_PARENT_INSERT>",
                "domain": "fixture",
                "record_key": f"matches.match_id={match_id}",
                "field_name": "attendance",
                "value_json": attendance_value,
                "source_provider": attendance_source,
                "authority": authority,
                "validation_status": validation_status,
                "resolution_note": resolution_note,
            },
            "deferred_parent_key": {
                "column": "ingestion_run_id",
                "from_operation": "ingestion.runs",
                "allocation": "FROM_PARENT_INSERT",
            },
            "canonical_primary_key_allocated": False,
        },
    ]

    return {
        "status": "SCHEMA_GAP",
        "destination_deployed": False,
        "provider_event_id": source_event_id,
        "canonical_match_id": match_id,
        "importer_git_sha": git_sha,
        "attendance": attendance_value,
        "attendance_status": attendance_status,
        "attendance_source": attendance_source,
        "attendance_authority": authority,
        "operations": operations,
        "operation_count": len(operations),
        "blockers": [
            "private ingestion schema is designed but not deployed",
            "ingestion run UUID must be allocated transactionally after schema deployment",
            "SofaScore external event identity must remain provider-namespaced",
            "attendance field provenance must reference its parent ingestion run before canonical promotion",
        ],
        "database_writes": 0,
        "sql_generated": False,
        "promotion_performed": False,
    }
