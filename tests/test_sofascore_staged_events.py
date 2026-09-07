from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "sofascore_staged_events.py"
SPEC = importlib.util.spec_from_file_location("sofascore_staged_events", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
staged = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = staged
SPEC.loader.exec_module(staged)


def _player(player_id: int):
    return {"id": player_id}


def test_brighton_population_preserves_opposition_goal_and_substitutions_as_schema_gaps():
    incidents = [
        {"id": 7, "incidentType": "substitution", "time": 90, "addedTime": 3, "isHome": True, "playerOut": _player(997152), "playerIn": _player(847094)},
        {"id": 6, "incidentType": "substitution", "time": 78, "isHome": True, "playerOut": _player(851505), "playerIn": _player(1200006)},
        {"id": 5, "incidentType": "substitution", "time": 77, "isHome": True, "playerOut": _player(995493), "playerIn": _player(1444898)},
        {"id": 4, "incidentType": "goal", "time": 71, "isHome": True, "player": _player(1405212), "assist1": _player(997152)},
        {"id": 3, "incidentType": "substitution", "time": 73, "isHome": False, "playerOut": _player(983572), "playerIn": _player(996672)},
        {"id": 2, "incidentType": "substitution", "time": 61, "isHome": False, "playerOut": _player(929132), "playerIn": _player(1106242)},
        {"id": 1, "incidentType": "goal", "time": 15, "isHome": False, "player": _player(929132), "assist1": _player(871886)},
    ]
    shots = [
        {"id": 8272133, "time": 15, "timeSeconds": 900, "isHome": False, "player": _player(929132), "goalkeeper": _player(994363), "shotType": "goal", "xg": 0.9023},
        {"id": 8273596, "time": 71, "timeSeconds": 4260, "isHome": True, "player": _player(1405212), "goalkeeper": _player(980643), "shotType": "goal", "xg": 0.15069},
    ]

    result = staged.build_staged_event_population(
        incidents=incidents,
        shots=shots,
        leeds_is_home=False,
        home_team_provider_id=30,
        away_team_provider_id=34,
    )

    assert result["status"] == "PASS"
    assert result["event_count"] == 9
    assert result["database_writes"] == 0
    assert result["promotion_performed"] is False

    bogle_goal = next(event for event in result["events"] if event["event_kind"] == "goal" and event["provider_player_id"] == 929132)
    assert bogle_goal["team_side"] == "LEEDS"
    assert bogle_goal["canonical_destination"] == "goals"
    assert bogle_goal["promotion_status"] == "ELIGIBLE"
    assert bogle_goal["provider_secondary_player_id"] == 871886

    vusk_goal = next(event for event in result["events"] if event["event_kind"] == "goal" and event["provider_player_id"] == 1405212)
    assert vusk_goal["team_side"] == "OPPONENT"
    assert vusk_goal["canonical_destination"] is None
    assert vusk_goal["promotion_status"] == "SCHEMA_GAP"
    assert vusk_goal["event_json"]["assist1"]["id"] == 997152

    brighton_subs = [event for event in result["events"] if event["event_kind"] == "substitution" and event["team_side"] == "OPPONENT"]
    assert len(brighton_subs) == 3
    assert all(event["promotion_status"] == "SCHEMA_GAP" for event in brighton_subs)


def test_incidents_are_chronological_not_source_array_order():
    result = staged.stage_incidents(
        [
            {"id": 2, "incidentType": "goal", "time": 71, "isHome": True, "player": _player(1405212)},
            {"id": 1, "incidentType": "goal", "time": 15, "isHome": False, "player": _player(929132)},
        ],
        leeds_is_home=False,
        home_team_provider_id=30,
        away_team_provider_id=34,
    )

    assert [event["minute_base"] for event in result] == [15, 71]
    assert [event["sequence_index"] for event in result] == [1, 2]


def test_stoppage_minute_is_preserved_from_added_time():
    result = staged.stage_incidents(
        [{"id": 8, "incidentType": "substitution", "time": 90, "addedTime": 3, "isHome": True, "playerOut": _player(1), "playerIn": _player(2)}],
        leeds_is_home=False,
        home_team_provider_id=30,
        away_team_provider_id=34,
    )

    assert result[0]["minute_base"] == 90
    assert result[0]["stoppage_minute"] == 3


def test_shot_source_object_is_preserved_without_inventing_big_chance_flag():
    source = {
        "id": 8272133,
        "time": 15,
        "timeSeconds": 900,
        "isHome": False,
        "player": _player(929132),
        "goalkeeper": _player(994363),
        "shotType": "goal",
        "situation": "corner",
        "bodyPart": "right-foot",
        "xg": 0.9023,
        "xgot": 0.9953,
    }
    result = staged.stage_shotmap(
        [source],
        leeds_is_home=False,
        home_team_provider_id=30,
        away_team_provider_id=34,
    )

    assert result[0]["event_json"] == source
    assert "bigChance" not in result[0]["event_json"]
    assert result[0]["provider_event_id"] == 8272133
    assert result[0]["promotion_status"] == "SCHEMA_GAP"


def test_missing_is_home_fails_closed():
    with pytest.raises(staged.StagedEventError, match="isHome"):
        staged.stage_incidents(
            [{"id": 1, "incidentType": "goal", "time": 15, "player": _player(929132)}],
            leeds_is_home=False,
            home_team_provider_id=30,
            away_team_provider_id=34,
        )
