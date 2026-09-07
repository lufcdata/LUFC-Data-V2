from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "sofascore_dry_run_contract.py"
SPEC = importlib.util.spec_from_file_location("sofascore_dry_run_contract", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
contract = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = contract
SPEC.loader.exec_module(contract)


def _event(competition: str) -> dict:
    return {"tournament": {"name": competition}}


def _lineups() -> dict:
    return {
        "home": {
            "players": [
                {
                    "player": {"id": 1001, "name": "Lewis Dunk"},
                    "captain": True,
                    "substitute": False,
                    "shirtNumber": 5,
                    "position": "D",
                },
                {
                    "player": {"id": 1002, "name": "Brighton Player"},
                    "substitute": False,
                },
            ]
        },
        "away": {
            "players": [
                {
                    "player": {"id": 2001, "name": "Ethan Ampadu"},
                    "captain": True,
                    "substitute": False,
                    "shirtNumber": 4,
                    "position": "M",
                },
                {
                    "player": {"id": 2002, "name": "Leeds Player"},
                    "substitute": False,
                },
            ]
        },
    }


def test_premier_league_requires_post_match_league_position_lookup():
    result = contract.league_position_requirement(_event("Premier League"))

    assert result["status"] == "REQUIRED"


def test_league_cup_does_not_trigger_league_position_lookup():
    result = contract.league_position_requirement(_event("EFL Cup"))

    assert result["status"] == "NOT_APPLICABLE"


def test_fa_cup_does_not_trigger_league_position_lookup():
    result = contract.league_position_requirement(_event("FA Cup"))

    assert result["status"] == "NOT_APPLICABLE"


def test_brighton_and_leeds_captains_come_from_match_lineup_entries():
    lineups = _lineups()

    home = contract.extract_captain(lineups, "home")
    away = contract.extract_captain(lineups, "away")

    assert home["name"] == "Lewis Dunk"
    assert home["sofascore_player_id"] == 1001
    assert away["name"] == "Ethan Ampadu"
    assert away["sofascore_player_id"] == 2001
    assert away["shirt_number"] == 4


def test_zero_captains_blocks_promotion():
    lineups = _lineups()
    lineups["away"]["players"][0].pop("captain")

    with pytest.raises(contract.ContractError, match="exactly one captain"):
        contract.extract_captain(lineups, "away")


def test_captain_marked_as_substitute_blocks_promotion():
    lineups = _lineups()
    lineups["away"]["players"][0]["substitute"] = True

    with pytest.raises(contract.ContractError, match="marked as a substitute"):
        contract.extract_captain(lineups, "away")
