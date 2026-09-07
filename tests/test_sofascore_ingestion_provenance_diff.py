from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
path = SCRIPTS_DIR / "sofascore_ingestion_provenance_diff.py"
spec = importlib.util.spec_from_file_location("sofascore_ingestion_provenance_diff", path)
assert spec is not None and spec.loader is not None
provenance_diff = importlib.util.module_from_spec(spec)
sys.modules["sofascore_ingestion_provenance_diff"] = provenance_diff
spec.loader.exec_module(provenance_diff)


def _source():
    return {
        "sofascore_event_id": 16363258,
        "database_writes": 0,
        "promotion_performed": False,
    }


def _evidence():
    return {
        "sofascore_event_id": 16363258,
        "validations": {
            "attendance": {
                "status": "SECONDARY_SOURCE_FACT",
                "attendance": 31661,
                "source": "BBC Sport",
            }
        },
        "database_writes": 0,
        "promotion_performed": False,
    }


def test_brighton_external_event_and_attendance_provenance_are_preserved_without_deployment():
    result = provenance_diff.build_ingestion_provenance_proposal(
        canonical_match_id=4857,
        source_bundle=_source(),
        evidence_bundle=_evidence(),
    )

    assert result["status"] == "SCHEMA_GAP"
    assert result["destination_deployed"] is False
    assert result["provider_event_id"] == 16363258
    assert result["canonical_match_id"] == 4857
    assert result["attendance"] == 31661
    assert result["attendance_source"] == "BBC Sport"
    assert result["attendance_authority"] == "SECONDARY"
    assert result["operation_count"] == 2
    assert result["database_writes"] == 0
    assert result["sql_generated"] is False
    assert result["promotion_performed"] is False

    run = result["operations"][0]
    assert run["table"] == "ingestion.runs"
    assert run["action"] == "INSERT_AFTER_SCHEMA_DEPLOYMENT"
    assert run["key"] == {
        "provider": "sofascore",
        "provider_event_id": "16363258",
        "canonical_match_id": 4857,
    }
    assert run["provider_id_written_to_canonical_id"] is False
    assert run["canonical_primary_key_allocated"] is False

    field = result["operations"][1]
    assert field["table"] == "ingestion.field_provenance"
    assert field["values"]["field_name"] == "attendance"
    assert field["values"]["value_json"] == 31661
    assert field["values"]["source_provider"] == "BBC Sport"
    assert field["values"]["authority"] == "SECONDARY"


def test_provider_event_identity_mismatch_fails_closed():
    evidence = _evidence()
    evidence["sofascore_event_id"] = 999
    try:
        provenance_diff.build_ingestion_provenance_proposal(
            canonical_match_id=4857,
            source_bundle=_source(),
            evidence_bundle=evidence,
        )
    except provenance_diff.IngestionProvenanceDiffError as exc:
        assert "event identity mismatch" in str(exc)
    else:
        raise AssertionError("mismatched provider event identity must fail closed")


def test_attendance_requires_approved_source_attribution():
    evidence = _evidence()
    evidence["validations"]["attendance"]["source"] = ""
    try:
        provenance_diff.build_ingestion_provenance_proposal(
            canonical_match_id=4857,
            source_bundle=_source(),
            evidence_bundle=evidence,
        )
    except provenance_diff.IngestionProvenanceDiffError as exc:
        assert "attendance source is required" in str(exc)
    else:
        raise AssertionError("unattributed attendance must fail closed")


def test_provider_id_never_becomes_canonical_match_id():
    result = provenance_diff.build_ingestion_provenance_proposal(
        canonical_match_id=4857,
        source_bundle=_source(),
        evidence_bundle=_evidence(),
    )
    run = result["operations"][0]
    assert run["values"]["canonical_match_id"] == 4857
    assert run["values"]["provider_event_id"] == "16363258"
    assert run["values"]["canonical_match_id"] != int(run["values"]["provider_event_id"])
