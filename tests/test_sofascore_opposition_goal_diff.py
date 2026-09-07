from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "sofascore_opposition_goal_diff.py"
SPEC = importlib.util.spec_from_file_location("sofascore_opposition_goal_diff", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mod
SPEC.loader.exec_module(mod)


def _goal(side, minute, player, *, assist=None, provider_player_id=None):
    event_json = {"player": {"name": player}}
    if assist:
        event_json["assist1"] = {"name": assist}
    return {
        "provider": "sofascore",
        "provider_event_id": None,
        "event_kind": "goal",
        "team_side": side,
        "provider_team_id": 34 if side == "LEEDS" else 30,
        "provider_player_id": provider_player_id,
        "provider_secondary_player_id": None,
        "minute_base": minute,
        "stoppage_minute": None,
        "period": "second" if minute > 45 else "first",
        "event_json": event_json,
    }


def test_brighton_vuskovic_goal_is_exactly_proposed_but_remains_schema_blocked():
    staged = {
        "database_writes": 0,
        "promotion_performed": False,
        "events": [
            _goal("LEEDS", 15, "Jayden Bogle", assist="Ao Tanaka", provider_player_id=929132),
            _goal("OPPONENT", 71, "Luka Vušković", assist="Maxim De Cuyper", provider_player_id=1405212),
        ],
    }

    result = mod.build_opposition_goal_proposal(canonical_match_id=4857, staged_events=staged)

    assert result["status"] == "SCHEMA_GAP"
    assert result["destination_deployed"] is False
    assert result["opposition_goal_count"] == 1
    assert result["database_writes"] == 0
    assert result["promotion_performed"] is False

    op = result["operations"][0]
    assert op["table"] == "opposition_goals"
    assert op["action"] == "INSERT_AFTER_PARENT_KEY_ALLOCATION_AND_SCHEMA_DEPLOYMENT"
    assert op["key"] == {"match_id": 4857, "opposition_goal_number_in_match": 1}
    assert op["values"]["sequence_in_match"] == 2
    assert op["values"]["scorer_name_raw"] == "Luka Vušković"
    assert op["values"]["assist_name_raw"] == "Maxim De Cuyper"
    assert op["values"]["minute_raw"] == "71"
    assert op["values"]["score_leeds_after"] == 1
    assert op["values"]["score_opponent_after"] == 1
    assert op["values"]["game_state_before"] == "Leading +1"
    assert op["values"]["ingestion_run_id"] == "<FROM_PARENT_INSERT>"
    assert op["deferred_parent_key"] == {
        "column": "ingestion_run_id",
        "from_operation": "ingestion.runs",
        "allocation": "FROM_PARENT_INSERT",
    }
    assert op["provider_evidence"]["provider_player_id"] == 1405212
    assert "opposition_goal_id" not in op["values"]
    assert "leeds_player_id" not in op["values"]


def test_stoppage_time_is_preserved_explicitly():
    staged = {
        "database_writes": 0,
        "promotion_performed": False,
        "events": [
            {
                **_goal("OPPONENT", 90, "Example Scorer"),
                "stoppage_minute": 3,
            }
        ],
    }
    result = mod.build_opposition_goal_proposal(canonical_match_id=9999, staged_events=staged)
    values = result["operations"][0]["values"]
    assert values["minute_raw"] == "90+3"
    assert values["minute_normalised"] == 90
    assert values["stoppage_minute"] == 3
    assert values["game_state_before"] == "Level"


def test_missing_scorer_fails_closed():
    goal = _goal("OPPONENT", 71, "Luka Vušković")
    goal["event_json"]["player"] = {}
    staged = {"database_writes": 0, "promotion_performed": False, "events": [goal]}
    with pytest.raises(mod.OppositionGoalDiffError, match="scorer name is missing"):
        mod.build_opposition_goal_proposal(canonical_match_id=4857, staged_events=staged)


def test_non_zero_write_staging_fails_closed():
    staged = {"database_writes": 1, "promotion_performed": False, "events": []}
    with pytest.raises(mod.OppositionGoalDiffError, match="not zero-write"):
        mod.build_opposition_goal_proposal(canonical_match_id=4857, staged_events=staged)
