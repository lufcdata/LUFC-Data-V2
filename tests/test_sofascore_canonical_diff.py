from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "sofascore_canonical_diff.py"
SPEC = importlib.util.spec_from_file_location("sofascore_canonical_diff", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
canonical_diff = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = canonical_diff
SPEC.loader.exec_module(canonical_diff)


def _resolution(entity_type: str, provider_id: int, canonical_id: int) -> dict:
    return {
        "status": "RESOLVED",
        "provider": "sofascore",
        "entity_type": entity_type,
        "provider_id": provider_id,
        "canonical_id": canonical_id,
    }


def _identity_package() -> dict:
    player_provider_ids = [
        980643,
        827681,
        282229,
        1118177,
        929132,
        889861,
        847097,
        871886,
        834308,
        372344,
        865523,
        886930,
        973431,
        355528,
        803185,
        190161,
        906075,
        866191,
        828639,
        1146148,
        115365,
    ]
    return {
        "status": "PASS",
        "match": _resolution("match", 16363258, 4857),
        "teams": {
            "resolutions": [
                _resolution("team", 30, 130),
                _resolution("team", 34, 999),
            ]
        },
        "players": {
            "resolutions": [
                _resolution("player", provider_id, 10000 + index)
                for index, provider_id in enumerate(player_provider_ids)
            ]
        },
        "managers": {
            "resolutions": [
                _resolution("manager", 265307, 49),
                _resolution("manager", 788529, 9001),
            ]
        },
    }


def _fixture() -> dict:
    return {
        "event_id": 16363258,
        "home_team_provider_id": 30,
        "away_team_provider_id": 34,
        "home_score": 1,
        "away_score": 1,
        "match_date": "2026-09-05",
        "stadium": "American Express Stadium",
        "attendance": 31661,
        "referee": "Stuart Attwell",
        "kickoff_time": "15:00",
        "round": "3",
        "leeds_formation": "3-5-2",
    }


def _leeds_players() -> list[dict]:
    starters = [
        980643,
        827681,
        282229,
        1118177,
        929132,
        889861,
        847097,
        871886,
        834308,
        372344,
        865523,
    ]
    bench = [886930, 973431, 355528, 803185, 190161, 906075, 866191, 828639, 1146148]
    rows = [
        {
            "provider_player_id": provider_id,
            "started": True,
            "substitute": False,
            "source_slot": f"XI{index}",
        }
        for index, provider_id in enumerate(starters, start=1)
    ]
    rows.extend(
        {
            "provider_player_id": provider_id,
            "started": False,
            "substitute": True,
            "source_slot": f"SUB{index}",
        }
        for index, provider_id in enumerate(bench, start=1)
    )
    return rows


def _kwargs() -> dict:
    return {
        "fixture": _fixture(),
        "identity_package": _identity_package(),
        "leeds_team_provider_id": 34,
        "leeds_manager_provider_id": 265307,
        "leeds_captain_provider_id": 847097,
        "leeds_players": _leeds_players(),
        "leeds_substitutions": [
            {"player_out": 929132, "player_in": 886930, "minute": "61"},
            {"player_out": 865523, "player_in": 973431, "minute": "62"},
            {"player_out": 871886, "player_in": 355528, "minute": "73"},
            {"player_out": 372344, "player_in": 803185, "minute": "73"},
        ],
        "leeds_goals": [
            {
                "provider_event_id": 8272133,
                "provider_player_id": 929132,
                "scorer_name": "Jayden Bogle",
                "minute_raw": "15'",
                "minute_normalised": 15,
                "assist_provider_player_id": 871886,
                "assist_name": "Ao Tanaka",
                "is_own_goal": False,
                "goal_type": "regular",
                "location": "0.8,53.4",
                "body_part": "right-foot",
                "goal_state": "Scored",
                "game_state": "D-W",
            }
        ],
        "opposition_goals": [
            {
                "provider_event_id": 8273596,
                "provider_player_id": 1405212,
                "scorer_name": "Luka Vuskovic",
                "minute_raw": "71'",
            }
        ],
        "opposition_manager_provider_id": 788529,
        "opposition_captain_provider_id": 115365,
        "attendance_source": "BBC",
    }


def test_brighton_diff_is_read_only_and_blocks_on_explicit_schema_gaps():
    result = canonical_diff.build_proposed_canonical_diff(**_kwargs())

    assert result["status"] == "BLOCKED"
    assert result["sofascore_event_id"] == 16363258
    assert result["canonical_match_id"] == 4857
    assert result["database_writes"] == 0
    assert result["sql_generated"] is False
    assert result["promotion_performed"] is False
    assert result["schema_gap_count"] >= 5


def test_brighton_match_operation_is_leeds_away_draw_with_bbc_attendance():
    result = canonical_diff.build_proposed_canonical_diff(**_kwargs())
    match_operation = next(row for row in result["operations"] if row["table"] == "matches")

    assert match_operation["action"] == "INSERT"
    assert match_operation["key"] == {"match_id": 4857}
    assert match_operation["values"]["venue_type"] == "A"
    assert match_operation["values"]["leeds_score"] == 1
    assert match_operation["values"]["opponent_score"] == 1
    assert match_operation["values"]["result"] == "D"
    assert match_operation["values"]["attendance"] == 31661
    assert match_operation["values"]["formation"] == "3-5-2"


def test_brighton_diff_proposes_exactly_20_player_match_rows():
    result = canonical_diff.build_proposed_canonical_diff(**_kwargs())
    player_rows = [row for row in result["operations"] if row["table"] == "player_matches"]

    assert len(player_rows) == 20
    assert sum(row["values"]["started"] is True for row in player_rows) == 11
    assert sum(row["values"]["substitute"] is True for row in player_rows) == 9


def test_jayden_bogle_goal_uses_mapped_lufc_player_and_preserves_provider_event_key():
    result = canonical_diff.build_proposed_canonical_diff(**_kwargs())
    goal = next(row for row in result["operations"] if row["table"] == "goals")

    assert goal["key"]["provider_event_id"] == 8272133
    assert goal["values"]["scorer_name_raw"] == "Jayden Bogle"
    assert goal["values"]["minute_normalised"] == 15
    assert goal["values"]["body_part"] == "right-foot"
    assert isinstance(goal["values"]["leeds_player_id"], int)
    assert goal["values"]["leeds_player_id"] != 929132


def test_structured_opposition_goal_is_not_silently_forced_into_leeds_goals_schema():
    result = canonical_diff.build_proposed_canonical_diff(**_kwargs())

    assert any(
        gap["field"] == "structured opposition goals"
        and gap["status"] == "SCHEMA_GAP"
        for gap in result["schema_gaps"]
    )


def test_provider_event_id_never_becomes_canonical_match_id():
    result = canonical_diff.build_proposed_canonical_diff(**_kwargs())

    assert result["canonical_match_id"] == 4857
    assert result["sofascore_event_id"] == 16363258
    assert result["canonical_match_id"] != result["sofascore_event_id"]


def test_incomplete_leeds_squad_blocks_diff():
    kwargs = _kwargs()
    kwargs["leeds_players"] = _leeds_players()[:-1]

    with pytest.raises(canonical_diff.CanonicalDiffError, match="20 players"):
        canonical_diff.build_proposed_canonical_diff(**kwargs)


def test_unresolved_captain_identity_blocks_diff():
    kwargs = _kwargs()
    kwargs["leeds_captain_provider_id"] = 999999999

    with pytest.raises(canonical_diff.CanonicalDiffError, match="exactly one player identity"):
        canonical_diff.build_proposed_canonical_diff(**kwargs)
