from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"


def _load(name: str):
    path = SCRIPTS_DIR / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_load("sofascore_dry_run_contract")
_load("sofascore_staged_events")
source_dry_run = _load("sofascore_source_derived_dry_run")


def _player(player_id: int, name: str = "Player"):
    return {"id": player_id, "name": name, "position": "M"}


def _lineup_entries(start: int, captain_id: int):
    ids = [captain_id] + [start + i for i in range(19) if start + i != captain_id]
    ids = ids[:20]
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


def test_brighton_source_payloads_derive_reconciliation_and_staged_population():
    substitutions = [
        {"id": 9, "incidentType": "substitution", "time": 61, "isHome": False, "playerOut": _player(929132), "playerIn": _player(1106242)},
        {"id": 10, "incidentType": "substitution", "time": 62, "isHome": False, "playerOut": _player(999002), "playerIn": _player(1056093)},
        {"id": 13, "incidentType": "substitution", "time": 73, "isHome": False, "playerOut": _player(871886), "playerIn": _player(1111117)},
        {"id": 14, "incidentType": "substitution", "time": 73, "isHome": False, "playerOut": _player(983572), "playerIn": _player(996672)},
        {"id": 15, "incidentType": "substitution", "time": 77, "isHome": True, "playerOut": _player(995493), "playerIn": _player(1444898)},
        {"id": 16, "incidentType": "substitution", "time": 78, "isHome": True, "playerOut": _player(851505), "playerIn": _player(1200006)},
        {"id": 19, "incidentType": "substitution", "time": 90, "addedTime": 3, "isHome": True, "playerOut": _player(997152), "playerIn": _player(847094)},
    ]
    goals = [
        {"id": 6, "incidentType": "goal", "time": 15, "isHome": False, "player": _player(929132), "assist1": _player(871886), "homeScore": 0, "awayScore": 1},
        {"id": 12, "incidentType": "goal", "time": 71, "isHome": True, "player": _player(1405212), "assist1": _player(997152), "homeScore": 1, "awayScore": 1},
    ]
    cards = [
        {"id": 5, "incidentType": "card", "incidentClass": "yellow", "time": 6, "isHome": False, "player": _player(929132)},
        {"id": 7, "incidentType": "card", "incidentClass": "yellow", "time": 38, "isHome": True, "player": _player(1234567)},
        {"id": 8, "incidentType": "card", "incidentClass": "yellow", "time": 49, "isHome": True, "player": _player(997152)},
        {"id": 11, "incidentType": "card", "incidentClass": "yellow", "time": 64, "isHome": False, "player": _player(983572)},
        {"id": 17, "incidentType": "card", "incidentClass": "yellow", "time": 85, "isHome": False, "player": _player(1111117)},
        {"id": 18, "incidentType": "card", "incidentClass": "yellow", "time": 88, "isHome": True, "player": _player(1444898)},
    ]
    incidents = goals + substitutions + cards

    shots = [
        {"id": 8272133, "time": 15, "timeSeconds": 900, "isHome": False, "player": _player(929132), "goalkeeper": _player(994363), "shotType": "goal"},
        {"id": 8273596, "time": 71, "timeSeconds": 4260, "isHome": True, "player": _player(1405212), "goalkeeper": _player(980643), "shotType": "goal"},
    ]
    shots.extend({"id": 9000000 + i, "time": 20 + i, "timeSeconds": 1200 + i, "isHome": True, "player": _player(2000000 + i), "shotType": "miss"} for i in range(19))
    shots.extend({"id": 9100000 + i, "time": 30 + i, "timeSeconds": 1800 + i, "isHome": False, "player": _player(3000000 + i), "shotType": "miss"} for i in range(9))

    raw = {
        "event": {
            "id": 16363258,
            "homeTeam": {"id": 30},
            "awayTeam": {"id": 34},
            "homeScore": {"current": 1, "period1": 0},
            "awayScore": {"current": 1, "period1": 1},
        },
        "lineups": {
            "confirmed": True,
            "home": {"formation": "4-2-3-1", "players": _lineup_entries(4000000, 115365)},
            "away": {"formation": "3-5-2", "players": _lineup_entries(5000000, 847097)},
        },
        "incidents": {"incidents": incidents},
        "statistics": {
            "statistics": [
                {"period": "ALL", "groups": [{"statisticsItems": [_stat("Total shots", 20, 10), _stat("Yellow cards", 3, 3)]}]}
            ]
        },
        "shotmap": {"shotmap": shots},
        "average_positions": {"substitutions": substitutions},
    }

    result = source_dry_run.build_source_derived_dry_run(raw_payloads=raw, leeds_team_provider_id=34)

    assert result["status"] == "PASS"
    assert result["sofascore_event_id"] == 16363258
    assert result["leeds_is_home"] is False
    assert result["lineups"]["home"]["formation"] == "4-2-3-1"
    assert result["lineups"]["away"]["formation"] == "3-5-2"
    assert result["reconciliation"]["goals"]["final_score"] == {"home": 1, "away": 1}
    assert result["reconciliation"]["goals"]["half_time_score"] == {"home": 0, "away": 1}
    assert result["reconciliation"]["substitutions"]["substitution_count"] == 7
    assert result["reconciliation"]["cards"]["yellow_cards"] == {"home": 3, "away": 3}
    assert result["reconciliation"]["shots"]["shots"] == {"home": 20, "away": 10}
    assert result["staged_events"]["event_count"] == 45
    assert result["database_writes"] == 0
    assert result["canonical_lufc_ids_assigned"] is False
    assert result["promotion_performed"] is False


def test_source_derived_bundle_fails_if_leeds_is_not_a_fixture_team():
    raw = {
        "event": {"id": 1, "homeTeam": {"id": 30}, "awayTeam": {"id": 31}},
        "lineups": {}, "incidents": {}, "statistics": {}, "shotmap": {}, "average_positions": {},
    }
    with pytest.raises(source_dry_run.SourceDerivedDryRunError, match="not one of the event teams"):
        source_dry_run.build_source_derived_dry_run(raw_payloads=raw, leeds_team_provider_id=34)
