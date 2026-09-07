from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "sofascore_goal_semantics.py"
SPEC = importlib.util.spec_from_file_location("sofascore_goal_semantics", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
goals = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = goals
SPEC.loader.exec_module(goals)


def test_brighton_bogle_goal_is_first_goal_from_level_not_synthetic_transition_label():
    result = goals.derive_leeds_goal_semantics(
        chronology=[
            {"time": 15, "added_time": 0, "is_home": False, "sofascore_player_id": 929132, "home_score": 0, "away_score": 1},
            {"time": 71, "added_time": 0, "is_home": True, "sofascore_player_id": 1405212, "home_score": 1, "away_score": 1},
        ],
        leeds_is_home=False,
        final_home_score=1,
        final_away_score=1,
    )

    assert len(result) == 1
    assert result[0]["provider_player_id"] == 929132
    assert result[0]["game_state"] == "Level"
    assert result[0]["goal_state"] == "1st Goal"
    assert result[0]["pre_goal_score"] == {"leeds": 0, "opponent": 0}
    assert result[0]["post_goal_score"] == {"leeds": 1, "opponent": 0}


def test_equaliser_uses_pre_goal_trailing_state():
    result = goals.derive_leeds_goal_semantics(
        chronology=[
            {"time": 10, "is_home": True, "sofascore_player_id": 1, "home_score": 1, "away_score": 0},
            {"time": 74, "is_home": False, "sofascore_player_id": 2, "home_score": 1, "away_score": 1},
        ],
        leeds_is_home=False,
        final_home_score=1,
        final_away_score=1,
    )

    assert result[0]["game_state"] == "Trailing -1"
    assert result[0]["goal_state"] == "Equaliser"


def test_decisive_final_goal_in_one_goal_win_is_winner_from_level():
    result = goals.derive_leeds_goal_semantics(
        chronology=[
            {"time": 4, "is_home": True, "sofascore_player_id": 10, "home_score": 1, "away_score": 0},
            {"time": 9, "is_home": False, "sofascore_player_id": 20, "home_score": 1, "away_score": 1},
            {"time": 13, "is_home": False, "sofascore_player_id": 30, "home_score": 1, "away_score": 2},
        ],
        leeds_is_home=False,
        final_home_score=1,
        final_away_score=2,
    )

    assert result[0]["goal_state"] == "Equaliser"
    assert result[0]["game_state"] == "Trailing -1"
    assert result[1]["goal_state"] == "Winner"
    assert result[1]["game_state"] == "Level"


def test_non_special_leeds_goal_uses_match_goal_ordinal_not_leeds_goal_count():
    result = goals.derive_leeds_goal_semantics(
        chronology=[
            {"time": 5, "is_home": True, "home_score": 1, "away_score": 0},
            {"time": 25, "is_home": True, "home_score": 2, "away_score": 0},
            {"time": 63, "is_home": False, "sofascore_player_id": 40, "home_score": 2, "away_score": 1},
            {"time": 77, "is_home": False, "sofascore_player_id": 41, "home_score": 2, "away_score": 2},
            {"time": 85, "is_home": False, "sofascore_player_id": 42, "home_score": 2, "away_score": 3},
        ],
        leeds_is_home=False,
        final_home_score=2,
        final_away_score=3,
    )

    assert result[0]["goal_state"] == "3rd Goal"
    assert result[0]["game_state"] == "Trailing -2"
    assert result[1]["goal_state"] == "Equaliser"
    assert result[1]["game_state"] == "Trailing -1"
    assert result[2]["goal_state"] == "Winner"
    assert result[2]["game_state"] == "Level"


def test_invalid_score_transition_fails_closed():
    with pytest.raises(goals.GoalSemanticsError, match="invalid goal transition"):
        goals.derive_leeds_goal_semantics(
            chronology=[{"time": 15, "is_home": False, "home_score": 0, "away_score": 2}],
            leeds_is_home=False,
            final_home_score=0,
            final_away_score=2,
        )
