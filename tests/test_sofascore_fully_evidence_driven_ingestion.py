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
_load("sofascore_ingestion_run_package")
_load("sofascore_dry_run_contract")
_load("sofascore_staged_events")
_load("sofascore_source_derived_dry_run")
_load("sofascore_evidence_validations")
orchestrator = _load("sofascore_source_driven_ingestion_package")


def _player(player_id: int):
    return {"id": player_id, "name": f"P{player_id}", "position": "M"}


def _lineup(start: int, captain_id: int, bench_ids: tuple[int, ...] = ()):
    starters = [captain_id]
    candidate = start
    while len(starters) < 11:
        if candidate != captain_id:
            starters.append(candidate)
        candidate += 1
    bench = list(bench_ids)
    while len(bench) < 9:
        if candidate not in starters and candidate not in bench:
            bench.append(candidate)
        candidate += 1
    ids = starters + bench[:9]
    return [
        {
            "player": _player(player_id),
            "substitute": index >= 11,
            "captain": player_id == captain_id,
            "shirtNumber": index + 1,
            "position": "M",
        }
        for index, player_id in enumerate(ids)
    ]


def _stat(name: str, home: int, away: int):
    return {"name": name, "homeValue": home, "awayValue": away}


def _raw_brighton():
    substitutions = [
        {"id": 9, "incidentType": "substitution", "time": 61, "isHome": False, "playerOut": _player(929132), "playerIn": _player(1106242)},
        {"id": 10, "incidentType": "substitution", "time": 62, "isHome": False, "playerOut": _player(999002), "playerIn": _player(1056093)},
        {"id": 13, "incidentType": "substitution", "time": 73, "isHome": False, "playerOut": _player(871886), "playerIn": _player(1111117)},
        {"id": 14, "incidentType": "substitution", "time": 73, "isHome": False, "playerOut": _player(983572), "playerIn": _player(996672)},
        {"id": 15, "incidentType": "substitution", "time": 77, "isHome": True, "playerOut": _player(995493), "playerIn": _player(1444898)},
        {"id": 16, "incidentType": "substitution", "time": 78, "isHome": True, "playerOut": _player(851505), "playerIn": _player(1200006)},
        {"id": 19, "incidentType": "substitution", "time": 90, "addedTime": 3, "isHome": True, "playerOut": _player(997152), "playerIn": _player(847094)},
    ]
    incidents = [
        {"id": 6, "incidentType": "goal", "time": 15, "isHome": False, "player": _player(929132), "assist1": _player(871886), "homeScore": 0, "awayScore": 1},
        {"id": 12, "incidentType": "goal", "time": 71, "isHome": True, "player": _player(1405212), "assist1": _player(997152), "homeScore": 1, "awayScore": 1},
        *substitutions,
        {"id": 5, "incidentType": "card", "incidentClass": "yellow", "time": 6, "isHome": False, "player": _player(929132)},
        {"id": 7, "incidentType": "card", "incidentClass": "yellow", "time": 38, "isHome": True, "player": _player(4001)},
        {"id": 8, "incidentType": "card", "incidentClass": "yellow", "time": 49, "isHome": True, "player": _player(997152)},
        {"id": 11, "incidentType": "card", "incidentClass": "yellow", "time": 64, "isHome": False, "player": _player(983572)},
        {"id": 17, "incidentType": "card", "incidentClass": "yellow", "time": 85, "isHome": False, "player": _player(1111117)},
        {"id": 18, "incidentType": "card", "incidentClass": "yellow", "time": 88, "isHome": True, "player": _player(1444898)},
    ]
    shots = [
        {"id": 8272133, "time": 15, "timeSeconds": 900, "isHome": False, "player": _player(929132), "goalkeeper": _player(994363), "shotType": "goal"},
        {"id": 8273596, "time": 71, "timeSeconds": 4260, "isHome": True, "player": _player(1405212), "goalkeeper": _player(980643), "shotType": "goal"},
    ]
    shots.extend({"id": 9000000 + i, "time": 20 + i, "timeSeconds": 1200 + i, "isHome": True, "player": _player(2000000 + i), "shotType": "miss"} for i in range(19))
    shots.extend({"id": 9100000 + i, "time": 30 + i, "timeSeconds": 1800 + i, "isHome": False, "player": _player(3000000 + i), "shotType": "miss"} for i in range(9))

    return {
        "event": {
            "id": 16363258,
            "status": {"type": "finished"},
            "homeTeam": {"id": 30},
            "awayTeam": {"id": 34},
            "homeScore": {"current": 1, "period1": 0},
            "awayScore": {"current": 1, "period1": 1},
            "tournament": {"name": "Premier League"},
            "roundInfo": {"round": 3},
            "attendance": None,
            "spectators": None,
        },
        "lineups": {
            "confirmed": True,
            "home": {"formation": "4-2-3-1", "players": _lineup(4000000, 115365, (1444898, 1200006, 847094))},
            "away": {"formation": "3-5-2", "players": _lineup(5000000, 847097, (1106242, 1056093, 1111117, 996672))},
        },
        "incidents": {"incidents": incidents},
        "managers": {
            "homeManager": {"id": 788529, "name": "Fabian Hurzeler"},
            "awayManager": {"id": 265307, "name": "Daniel Farke"},
        },
        "statistics": {"statistics": [{"period": "ALL", "groups": [{"statisticsItems": [_stat("Total shots", 20, 10), _stat("Yellow cards", 3, 3)]}]}]},
        "shotmap": {"shotmap": shots},
        "average_positions": {"substitutions": substitutions},
        "standings": {"standings": [{"rows": [
            {"team": {"id": 34}, "position": 9, "matches": 3, "points": 5},
            {"team": {"id": 30}, "position": 10, "matches": 3, "points": 4},
        ]}]},
    }


def _secondary():
    return {
        "attendance": {"value": 31661, "source": "BBC Sport"},
        "formations": {
            "home": {"value": "4-2-3-1", "source": "BBC Sport"},
            "away": {"value": "3-5-2", "source": "BBC Sport"},
        },
    }


def test_brighton_package_derives_every_non_identity_gate_from_evidence():
    result = orchestrator.build_fully_evidence_driven_ingestion_package(
        run_id="brighton-fully-evidence-driven",
        importer_git_sha="804b9b4213c2eb1f389b200bd169005e77c29334",
        raw_payloads=_raw_brighton(),
        leeds_team_provider_id=34,
        identity_package={"match": {"provider_id": 16363258, "canonical_id": 4857}},
        identity_mapping_validation={"status": "RESOLVED"},
        secondary_evidence=_secondary(),
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
            "promotion_performed": False,
        },
    )

    package = result["package"]
    validations = package["validations"]
    assert validations["fixture"]["sofascore_event_id"] == 16363258
    assert validations["captains"]["home_captain_provider_id"] == 115365
    assert validations["captains"]["away_captain_provider_id"] == 847097
    assert validations["managers"]["home_manager_provider_id"] == 788529
    assert validations["managers"]["away_manager_provider_id"] == 265307
    assert validations["formations"]["status"] == "VALIDATED"
    assert validations["attendance"]["attendance"] == 31661
    assert validations["attendance"]["source"] == "BBC Sport"
    assert validations["league_position"]["position"] == 9
    assert validations["shots"]["shots"] == {"home": 20, "away": 10}
    assert validations["substitutions"]["substitution_count"] == 7
    assert validations["appearance_population"]["home_appearance_count"] == 14
    assert validations["appearance_population"]["away_appearance_count"] == 15
    assert validations["identity_mapping"]["status"] == "RESOLVED"
    assert package["promotion_gate"]["status"] == "BLOCKED"
    assert result["database_writes"] == 0
    assert result["canonical_promotion_performed"] is False


def test_fully_evidence_driven_ready_state_remains_zero_write():
    result = orchestrator.build_fully_evidence_driven_ingestion_package(
        run_id="brighton-fully-evidence-driven-ready",
        importer_git_sha="804b9b4213c2eb1f389b200bd169005e77c29334",
        raw_payloads=_raw_brighton(),
        leeds_team_provider_id=34,
        identity_package={"match": {"provider_id": 16363258, "canonical_id": 4857}},
        identity_mapping_validation={"status": "RESOLVED"},
        secondary_evidence=_secondary(),
        canonical_diff={
            "status": "PASS",
            "sofascore_event_id": 16363258,
            "schema_gap_count": 0,
            "schema_gaps": [],
            "database_writes": 0,
            "promotion_performed": False,
        },
        backup={"status": "VERIFIED"},
        rollback_manifest={"status": "READY"},
    )

    assert result["status"] == "READY_FOR_PROMOTION"
    assert result["package"]["promotion_gate"]["passed_validation_count"] == 16
    assert result["package"]["database_writes"] == 0
    assert result["package"]["canonical_promotion_performed"] is False
