from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"


def _load(name: str):
    path = SCRIPTS_DIR / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# The run-package module imports the promotion gate by its script-level module name,
# so load that dependency first just as the existing script tests do.
_load("sofascore_promotion_gate")
run_package = _load("sofascore_ingestion_run_package")


def _identity_package():
    return {
        "match": {"provider_id": 16363258, "canonical_id": 4857},
        "teams": {"resolutions": []},
        "players": {"resolutions": []},
        "managers": {"resolutions": []},
    }


def _validations():
    return {
        name: {"status": "PASS"}
        for name in (
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
        )
    }


def test_brighton_run_package_is_fail_closed_while_schema_gaps_and_backup_remain():
    package = run_package.build_ingestion_run_package(
        run_id="brighton-2026-09-05-dry-run",
        sofascore_event_id=16363258,
        importer_git_sha="55296514fa48667279d12d76dda2e74b5ad06e29",
        raw_payloads={
            "event": {"id": 16363258, "status": {"type": "finished"}},
            "lineups": {"confirmed": True, "home": {"formation": "4-2-3-1"}, "away": {"formation": "3-5-2"}},
            "incidents": {"incidents": [{"incidentType": "goal", "time": 15}, {"incidentType": "goal", "time": 71}]},
            "managers": {"homeManager": {"id": 788529}, "awayManager": {"id": 265307}},
            "statistics": {"statistics": [{"period": "ALL"}]},
            "average_positions": {"substitutions": [1, 2, 3, 4, 5, 6, 7]},
            "shotmap": {"shotmap": list(range(30))},
            "standings": {"leeds": {"position": 9, "matches": 3, "points": 5}},
        },
        identity_package=_identity_package(),
        reconciliation={"status": "PASS", "goals": 2, "substitutions": 7, "shots": 30},
        canonical_diff={
            "status": "BLOCKED",
            "sofascore_event_id": 16363258,
            "schema_gap_count": 2,
            "schema_gaps": [
                {"status": "SCHEMA_GAP", "field": "structured opposition goals"},
                {"status": "SCHEMA_GAP", "field": "opposition captain"},
            ],
            "database_writes": 0,
        },
        validations=_validations(),
    )

    assert package["sofascore_event_id"] == 16363258
    assert package["raw_manifest"]["shotmap"]["sha256"]
    assert package["raw_manifest_sha256"]
    assert package["package_sha256"]
    assert package["promotion_gate"]["status"] == "BLOCKED"
    assert "validation not passed: canonical_diff (BLOCKED)" in package["blockers"]
    assert "verified pre-import backup required" in package["blockers"]
    assert "rollback manifest required" in package["blockers"]
    assert package["database_writes"] == 0
    assert package["canonical_promotion_performed"] is False
    run_package.require_zero_write_package(package)


def test_raw_payload_fingerprint_changes_when_evidence_changes():
    common = dict(
        run_id="brighton-fingerprint-test",
        sofascore_event_id=16363258,
        importer_git_sha="abc123",
        identity_package=_identity_package(),
        reconciliation={"status": "PASS"},
        canonical_diff={"status": "PASS", "sofascore_event_id": 16363258, "schema_gap_count": 0, "schema_gaps": []},
        validations=_validations(),
        backup={"status": "VERIFIED"},
        rollback_manifest={"status": "READY"},
    )
    first = run_package.build_ingestion_run_package(raw_payloads={"event": {"id": 16363258, "score": "1-1"}}, **common)
    second = run_package.build_ingestion_run_package(raw_payloads={"event": {"id": 16363258, "score": "2-1"}}, **common)

    assert first["raw_manifest_sha256"] != second["raw_manifest_sha256"]
    assert first["package_sha256"] != second["package_sha256"]
    assert first["promotion_gate"]["status"] == "READY_FOR_PROMOTION"
    assert first["database_writes"] == 0
