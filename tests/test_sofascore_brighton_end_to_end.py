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
staged = _load("sofascore_staged_events")


def _player(player_id: int):
    return {"id": player_id}


def _validations():
    return {
        name: {"status": "PASS"}
        for name in (
            "fixture", "lineups", "captains", "managers", "goals", "scores",
            "substitutions", "cards", "shots", "formations", "attendance",
            "league_position", "identity_mapping",
        )
    }


def test_brighton_verified_populations_flow_through_one_zero_write_package():
    # Verified Brighton reference facts. Canonical IDs below are deliberately synthetic
    # test identities except for the candidate match ID; provider IDs remain namespaced.
    incidents = [
        {"id": 19, "incidentType": "substitution", "time": 90, "addedTime": 3, "isHome": True, "playerOut": _player(997152), "playerIn": _player(847094)},
        {"id": 18, "incidentType": "card", "time": 88, "isHome": True, "player": _player(1444898)},
        {"id": 17, "incidentType": "card", "time": 85, "isHome": False, "player": _player(1111117)},
        {"id": 16, "incidentType": "substitution", "time": 78, "isHome": True, "playerOut": _player(851505), "playerIn": _player(1200006)},
        {"id": 15, "incidentType": "substitution", "time": 77, "isHome": True, "playerOut": _player(995493), "playerIn": _player(1444898)},
        {"id": 14, "incidentType": "substitution", "time": 73, "isHome": False, "playerOut": _player(983572), "playerIn": _player(996672)},
        {"id": 13, "incidentType": "substitution", "time": 73, "isHome": False, "playerOut": _player(871886), "playerIn": _player(1111117)},
        {"id": 12, "incidentType": "goal", "time": 71, "isHome": True, "player": _player(1405212), "assist1": _player(997152), "homeScore": 1, "awayScore": 1},
        {"id": 11, "incidentType": "card", "time": 64, "isHome": False, "player": _player(983572)},
        {"id": 10, "incidentType": "substitution", "time": 62, "isHome": False, "playerOut": _player(999002), "playerIn": _player(1056093)},
        {"id": 9, "incidentType": "substitution", "time": 61, "isHome": False, "playerOut": _player(929132), "playerIn": _player(1106242)},
        {"id": 8, "incidentType": "card", "time": 49, "isHome": True, "player": _player(997152)},
        {"id": 7, "incidentType": "card", "time": 38, "isHome": True, "player": _player(1234567)},
        {"id": 6, "incidentType": "goal", "time": 15, "isHome": False, "player": _player(929132), "assist1": _player(871886), "homeScore": 0, "awayScore": 1},
        {"id": 5, "incidentType": "card", "time": 6, "isHome": False, "player": _player(929132)},
    ]

    # Preserve the verified 20-10 shot population. The two goals carry the known rich facts;
    # the remaining 28 synthetic rows exist only to lock population completeness/counting.
    shots = [
        {"id": 8272133, "time": 15, "timeSeconds": 900, "isHome": False, "player": _player(929132), "goalkeeper": _player(994363), "shotType": "goal", "situation": "corner", "bodyPart": "right-foot", "xg": 0.9023, "xgot": 0.9953},
        {"id": 8273596, "time": 71, "timeSeconds": 4260, "isHome": True, "player": _player(1405212), "goalkeeper": _player(980643), "shotType": "goal", "situation": "corner", "bodyPart": "head", "xg": 0.15069, "xgot": 0.20484},
    ]
    shots.extend(
        {"id": 9000000 + i, "time": 20 + i, "timeSeconds": (20 + i) * 60, "isHome": True, "player": _player(2000000 + i), "shotType": "miss"}
        for i in range(19)
    )
    shots.extend(
        {"id": 9100000 + i, "time": 30 + i, "timeSeconds": (30 + i) * 60, "isHome": False, "player": _player(3000000 + i), "shotType": "miss"}
        for i in range(9)
    )

    staged_population = staged.build_staged_event_population(
        incidents=incidents,
        shots=shots,
        leeds_is_home=False,
        home_team_provider_id=30,
        away_team_provider_id=34,
    )

    assert staged_population["incident_event_count"] == 15
    assert staged_population["shot_event_count"] == 30
    assert staged_population["event_count"] == 45
    assert len([e for e in staged_population["events"] if e["event_kind"] == "goal"]) == 2
    assert len([e for e in staged_population["events"] if e["event_kind"] == "substitution"]) == 7
    assert len([e for e in staged_population["events"] if e["event_kind"] == "card"]) == 6
    assert len([e for e in staged_population["events"] if e["event_kind"] == "shot" and e["team_side"] == "OPPONENT"]) == 20
    assert len([e for e in staged_population["events"] if e["event_kind"] == "shot" and e["team_side"] == "LEEDS"]) == 10

    package = run_package.build_ingestion_run_package(
        run_id="brighton-2026-09-05-end-to-end-dry-run",
        sofascore_event_id=16363258,
        importer_git_sha="4a7417d33dc8884f364ca8b4ea7163791b8cd9af",
        raw_payloads={
            "event": {"id": 16363258, "status": {"type": "finished"}, "homeScore": {"current": 1, "period1": 0}, "awayScore": {"current": 1, "period1": 1}, "roundInfo": {"round": 3}, "time": {"injuryTime1": 1, "injuryTime2": 4}},
            "lineups": {"confirmed": True, "home": {"formation": "4-2-3-1", "captain": 115365, "squad_count": 20}, "away": {"formation": "3-5-2", "captain": 847097, "squad_count": 20}},
            "incidents": {"incidents": incidents},
            "managers": {"homeManager": {"id": 788529}, "awayManager": {"id": 265307}},
            "statistics": {"ALL": {"total_shots": {"home": 20, "away": 10}, "yellow_cards": {"home": 3, "away": 3}}},
            "average_positions": {"substitution_count": 7},
            "shotmap": {"shotmap": shots},
            "standings": {"leeds": {"position": 9, "matches": 3, "points": 5}},
            "attendance_secondary": {"attendance": 31661, "source": "BBC Sport"},
        },
        identity_package={
            "match": {"provider_id": 16363258, "canonical_id": 4857},
            "teams": {"resolutions": [{"provider_id": 30, "canonical_id": 10030}, {"provider_id": 34, "canonical_id": 10034}]},
            "players": {"resolutions": []},
            "managers": {"resolutions": [{"provider_id": 788529, "canonical_id": 20001}, {"provider_id": 265307, "canonical_id": 20002}]},
        },
        reconciliation={
            "status": "PASS",
            "goal_count": 2,
            "substitution_count": 7,
            "yellow_cards": {"home": 3, "away": 3},
            "shots": {"home": 20, "away": 10},
            "half_time_score": {"home": 0, "away": 1},
            "final_score": {"home": 1, "away": 1},
        },
        staged_events=staged_population,
        canonical_diff={
            "status": "BLOCKED",
            "sofascore_event_id": 16363258,
            "schema_gap_count": 4,
            "schema_gaps": [
                {"status": "SCHEMA_GAP", "field": "structured opposition goals"},
                {"status": "SCHEMA_GAP", "field": "opposition substitutions"},
                {"status": "SCHEMA_GAP", "field": "opposition captain"},
                {"status": "SCHEMA_GAP", "field": "rich shot events"},
            ],
            "database_writes": 0,
        },
        validations=_validations(),
    )

    assert package["staged_events"]["event_count"] == 45
    assert package["staged_events_sha256"]
    assert package["validations"]["staged_events"]["status"] == "PASS"
    assert package["promotion_gate"]["status"] == "BLOCKED"
    assert package["schema_gaps"] == package["canonical_diff"]["schema_gaps"]
    assert "verified pre-import backup required" in package["blockers"]
    assert "rollback manifest required" in package["blockers"]
    assert package["database_writes"] == 0
    assert package["canonical_promotion_performed"] is False
    run_package.require_zero_write_package(package)
