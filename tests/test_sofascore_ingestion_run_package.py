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
            "appearance_population",
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


def _staged_events():
    return {
        "status": "PASS",
        "event_count": 4,
        "incident_event_count": 2,
        "shot_event_count": 2,
        "schema_gap_event_count": 2,
        "eligible_event_count": 2,
        "events": [
            {"event_kind": "goal", "team_side": "LEEDS", "provider_player_id": 929132, "minute_base": 15, "promotion_status": "ELIGIBLE", "canonical_destination": "goals"},
            {"event_kind": "goal", "team_side": "OPPONENT", "provider_player_id": 1405212, "minute_base": 71, "promotion_status": "SCHEMA_GAP", "canonical_destination": None},
            {"event_kind": "shot", "team_side": "LEEDS", "provider_player_id": 929132, "minute_base": 15, "promotion_status": "SCHEMA_GAP", "canonical_destination": None},
            {"event_kind": "shot", "team_side": "OPPONENT", "provider_player_id": 1405212, "minute_base": 71, "promotion_status": "SCHEMA_GAP", "canonical_destination": None},
        ],
        "database_writes": 0,
        "promotion_performed": False,
    }


def test_brighton_run_package_contains_staged_population_and_remains_fail_closed():
    package = run_package.build_ingestion_run_package(
        run_id="brighton-2026-09-05-dry-run",
        sofascore_event_id=16363258,
        importer_git_sha="6549d1f622ac3c42846b48f267c49882662ab9b4",
        raw_payloads={
            "event": {"id": 16363258, "status": {"type": "finished"}},
            "lineups": {"confirmed": True, "home": {"formation": "4-2-3-1"}, "away": {"formation": "3-5-2"}},
            "incidents": {"incidents": [{"incidentType": "goal", "time": 15}, {"incidentType": "goal", "time": 71}]},
            "shotmap": {"shotmap": [{"id": 8272133}, {"id": 8273596}]},
        },
        identity_package=_identity_package(),
        reconciliation={"status": "PASS", "goals": 2, "substitutions": 7, "shots": 30},
        staged_events=_staged_events(),
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
    assert package["staged_events"]["event_count"] == 4
    assert package["staged_events"]["events"][1]["team_side"] == "OPPONENT"
    assert package["staged_events_sha256"]
    assert package["raw_manifest_sha256"]
    assert package["package_sha256"]
    assert package["promotion_gate"]["status"] == "BLOCKED"
    assert "validation not passed: canonical_diff (BLOCKED)" in package["blockers"]
    assert "verified pre-import backup required" in package["blockers"]
    assert "rollback manifest required" in package["blockers"]
    assert package["database_writes"] == 0
    assert package["canonical_promotion_performed"] is False
    run_package.require_zero_write_package(package)


def test_staged_population_is_part_of_package_fingerprint():
    common = dict(
        run_id="brighton-fingerprint-test",
        sofascore_event_id=16363258,
        importer_git_sha="abc123",
        raw_payloads={"event": {"id": 16363258, "score": "1-1"}},
        identity_package=_identity_package(),
        reconciliation={"status": "PASS"},
        canonical_diff={"status": "PASS", "sofascore_event_id": 16363258, "schema_gap_count": 0, "schema_gaps": []},
        validations=_validations(),
        backup={"status": "VERIFIED"},
        rollback_manifest={"status": "READY"},
    )
    first_staged = _staged_events()
    second_staged = _staged_events()
    second_staged["events"] = [dict(event) for event in second_staged["events"]]
    second_staged["events"][0]["minute_base"] = 16

    first = run_package.build_ingestion_run_package(staged_events=first_staged, **common)
    second = run_package.build_ingestion_run_package(staged_events=second_staged, **common)

    assert first["staged_events_sha256"] != second["staged_events_sha256"]
    assert first["package_sha256"] != second["package_sha256"]
    assert first["promotion_gate"]["status"] == "READY_FOR_PROMOTION"


def test_staged_population_cannot_claim_database_writes():
    staged = _staged_events()
    staged["database_writes"] = 1

    try:
        run_package.build_ingestion_run_package(
            run_id="brighton-invalid-staging",
            sofascore_event_id=16363258,
            importer_git_sha="abc123",
            raw_payloads={"event": {"id": 16363258}},
            identity_package=_identity_package(),
            reconciliation={"status": "PASS"},
            staged_events=staged,
            canonical_diff={"status": "PASS", "sofascore_event_id": 16363258, "schema_gap_count": 0, "schema_gaps": []},
            validations=_validations(),
        )
    except run_package.IngestionRunPackageError as exc:
        assert "reports database writes" in str(exc)
    else:
        raise AssertionError("expected staged population write claim to fail closed")
