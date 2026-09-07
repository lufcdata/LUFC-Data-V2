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
evidence = _load("sofascore_evidence_validations")


def _player(player_id: int):
    return {"id": player_id, "name": f"P{player_id}", "position": "M"}


def _lineup(start: int, captain_id: int):
    ids = [captain_id] + [start + i for i in range(40) if start + i != captain_id]
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


def _brighton_raw():
    return {
        "event": {
            "id": 16363258,
            "status": {"type": "finished"},
            "homeTeam": {"id": 30},
            "awayTeam": {"id": 34},
            "tournament": {"name": "Premier League"},
            "roundInfo": {"round": 3},
            "attendance": None,
            "spectators": None,
        },
        "lineups": {
            "confirmed": True,
            "home": {"formation": "4-2-3-1", "players": _lineup(4000000, 115365)},
            "away": {"formation": "3-5-2", "players": _lineup(5000000, 847097)},
        },
        "managers": {
            "homeManager": {"id": 788529, "name": "Fabian Hurzeler"},
            "awayManager": {"id": 265307, "name": "Daniel Farke"},
        },
        "standings": {
            "standings": [
                {
                    "rows": [
                        {"team": {"id": 34}, "position": 9, "matches": 3, "points": 5},
                        {"team": {"id": 30}, "position": 10, "matches": 3, "points": 4},
                    ]
                }
            ]
        },
    }


def _secondary():
    return {
        "attendance": {"value": 31661, "source": "BBC Sport"},
        "formations": {
            "home": {"value": "4-2-3-1", "source": "BBC Sport"},
            "away": {"value": "3-5-2", "source": "BBC Sport"},
        },
    }


def test_brighton_external_gates_are_derived_from_captured_evidence():
    result = evidence.build_evidence_validations(
        raw_payloads=_brighton_raw(),
        leeds_team_provider_id=34,
        secondary_evidence=_secondary(),
    )

    validations = result["validations"]
    assert result["status"] == "PASS"
    assert validations["fixture"]["sofascore_event_id"] == 16363258
    assert validations["fixture"]["leeds_is_home"] is False
    assert validations["captains"]["home_captain_provider_id"] == 115365
    assert validations["captains"]["away_captain_provider_id"] == 847097
    assert validations["managers"]["home_manager_provider_id"] == 788529
    assert validations["managers"]["away_manager_provider_id"] == 265307
    assert validations["formations"]["status"] == "VALIDATED"
    assert validations["formations"]["home"]["formation"] == "4-2-3-1"
    assert validations["formations"]["away"]["formation"] == "3-5-2"
    assert validations["attendance"] == {
        "status": "SECONDARY_SOURCE_FACT",
        "attendance": 31661,
        "source": "BBC Sport",
    }
    assert validations["league_position"]["position"] == 9
    assert validations["league_position"]["round"] == 3
    assert validations["league_position"]["played"] == 3
    assert validations["league_position"]["points"] == 5
    assert result["database_writes"] == 0
    assert result["canonical_lufc_ids_assigned"] is False
    assert result["promotion_performed"] is False


def test_league_position_rejects_pre_round_snapshot():
    raw = _brighton_raw()
    raw["standings"]["standings"][0]["rows"][0]["matches"] = 2
    with pytest.raises(evidence.EvidenceValidationError, match="not completed round 3"):
        evidence.build_evidence_validations(
            raw_payloads=raw,
            leeds_team_provider_id=34,
            secondary_evidence=_secondary(),
        )


def test_formation_disagreement_fails_closed():
    secondary = _secondary()
    secondary["formations"]["away"]["value"] = "4-3-3"
    with pytest.raises(Exception, match="formation conflict"):
        evidence.build_evidence_validations(
            raw_payloads=_brighton_raw(),
            leeds_team_provider_id=34,
            secondary_evidence=secondary,
        )


def test_attendance_requires_approved_source_when_sofascore_is_blank():
    secondary = _secondary()
    secondary["attendance"]["source"] = ""
    with pytest.raises(Exception, match="secondary attendance has no source attribution"):
        evidence.build_evidence_validations(
            raw_payloads=_brighton_raw(),
            leeds_team_provider_id=34,
            secondary_evidence=secondary,
        )


def test_non_league_fixture_skips_standings_lookup():
    raw = _brighton_raw()
    raw["event"]["tournament"]["name"] = "FA Cup"
    raw.pop("standings")
    result = evidence.build_evidence_validations(
        raw_payloads=raw,
        leeds_team_provider_id=34,
        secondary_evidence=_secondary(),
    )
    assert result["validations"]["league_position"]["status"] == "NOT_APPLICABLE"
