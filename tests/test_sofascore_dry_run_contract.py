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


def _complete_side(
    *,
    first_id: int,
    captain_name: str,
    formation: str,
) -> dict:
    players = []
    for index in range(11):
        provider_id = first_id + index
        player = {
            "id": provider_id,
            "name": captain_name if index == 0 else f"Starter {provider_id}",
            "position": "M" if index == 0 else "D",
        }
        players.append(
            {
                "player": player,
                "captain": index == 0,
                "substitute": False,
                "shirtNumber": index + 1,
                "position": "D" if index == 0 else "M",
            }
        )
    for index in range(5):
        provider_id = first_id + 100 + index
        players.append(
            {
                "player": {"id": provider_id, "name": f"Bench {provider_id}", "position": "F"},
                "substitute": True,
                "shirtNumber": index + 20,
                "position": "F",
            }
        )
    return {"formation": formation, "players": players}


def _complete_lineups() -> dict:
    return {
        "confirmed": True,
        "home": _complete_side(first_id=1000, captain_name="Lewis Dunk", formation="4-2-3-1"),
        "away": _complete_side(first_id=2000, captain_name="Ethan Ampadu", formation="4-3-3"),
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


def test_unknown_competition_blocks_instead_of_silently_becoming_non_league():
    with pytest.raises(contract.ContractError, match="not classified"):
        contract.league_position_requirement(_event("Future New Competition"))


def test_missing_competition_blocks():
    with pytest.raises(contract.ContractError, match="not classified"):
        contract.league_position_requirement({})


def test_bbc_attendance_can_fill_missing_sofascore_attendance_with_provenance():
    result = contract.attendance_candidate(
        None,
        secondary_attendance=31661,
        secondary_source="BBC",
    )

    assert result == {
        "status": "SECONDARY_SOURCE_FACT",
        "attendance": 31661,
        "source": "BBC",
    }


def test_attendance_is_never_inferred_when_sources_are_missing():
    result = contract.attendance_candidate(None)

    assert result["status"] == "UNAVAILABLE"
    assert result["attendance"] is None


def test_secondary_attendance_requires_source_attribution():
    with pytest.raises(contract.ContractError, match="no source attribution"):
        contract.attendance_candidate(None, secondary_attendance=31661)


def test_brighton_formation_crosscheck_agrees_between_sofascore_and_bbc():
    result = contract.validate_formation_crosscheck(
        "4-2-3-1",
        secondary_formation="4-2-3-1",
        secondary_source="BBC",
    )

    assert result["status"] == "VALIDATED"
    assert result["formation"] == "4-2-3-1"
    assert result["crosscheck_source"] == "BBC"


def test_leeds_formation_crosscheck_agrees_between_sofascore_and_bbc():
    result = contract.validate_formation_crosscheck(
        "3-5-2",
        secondary_formation="3-5-2",
        secondary_source="BBC",
    )

    assert result["status"] == "VALIDATED"
    assert result["formation"] == "3-5-2"


def test_formation_conflict_blocks_instead_of_overwriting_primary_source():
    with pytest.raises(contract.ContractError, match="formation conflict"):
        contract.validate_formation_crosscheck(
            "3-5-2",
            secondary_formation="4-3-3",
            secondary_source="BBC",
        )


def test_motm_is_explicitly_not_automated_from_sofascore():
    result = contract.motm_automation_policy()

    assert result["status"] == "NOT_AUTOMATED"
    assert result["canonical_field"] == "motm_player_id"


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


def test_confirmed_lineups_summarize_both_sides_without_assigning_lufc_ids():
    result = contract.summarize_lineups(_complete_lineups())

    assert result["confirmed"] is True
    assert result["database_writes"] == 0
    assert result["canonical_lufc_ids_assigned"] is False
    assert result["home"]["starter_count"] == 11
    assert result["home"]["bench_count"] == 5
    assert result["home"]["captain"]["name"] == "Lewis Dunk"
    assert result["away"]["starter_count"] == 11
    assert result["away"]["captain"]["name"] == "Ethan Ampadu"


def test_match_position_and_profile_position_remain_separate():
    result = contract.summarize_lineup_side(_complete_lineups(), "away")
    captain = result["captain"]

    assert captain["match_position"] == "D"
    assert captain["profile_position"] == "M"


def test_unconfirmed_lineups_block_dry_run():
    lineups = _complete_lineups()
    lineups["confirmed"] = False

    with pytest.raises(contract.ContractError, match="not confirmed"):
        contract.summarize_lineups(lineups)


def test_lineup_with_fewer_than_11_starters_blocks_dry_run():
    lineups = _complete_lineups()
    lineups["away"]["players"][10]["substitute"] = True

    with pytest.raises(contract.ContractError, match="exactly 11 starters"):
        contract.summarize_lineup_side(lineups, "away")


def test_duplicate_provider_player_id_blocks_dry_run():
    lineups = _complete_lineups()
    lineups["away"]["players"][1]["player"]["id"] = lineups["away"]["players"][0]["player"]["id"]

    with pytest.raises(contract.ContractError, match="duplicate SofaScore player IDs"):
        contract.summarize_lineup_side(lineups, "away")
