from __future__ import annotations

import importlib.util
import sys
from datetime import datetime, timezone
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


_load("sofascore_canonical_diff")
_load("sofascore_canonical_match_enrichment")
_load("sofascore_goal_semantics")
source_diff = _load("sofascore_source_canonical_diff")


LEEDS_IDS = [
    980643, 827681, 282229, 1118177, 929132, 889861, 847097, 871886, 834308, 372344,
    865523, 886930, 973431, 355528, 803185, 190161, 906075, 866191, 828639, 1146148,
]
LEEDS_USED_SUB_IDS = [886930, 973431, 355528, 803185]
LEEDS_APPEARANCE_IDS = LEEDS_IDS[:11] + LEEDS_USED_SUB_IDS


def _resolution(scope: str, provider_id: int, canonical_id: int):
    namespaces = {
        "match": "matches.match_id",
        "opponent_club": "clubs.club_id",
        "leeds_player": "players.player_id",
        "leeds_manager": "managers.manager_id",
        "opposition_manager": "managerial_people.managerial_person_id",
    }
    return {
        "status": "RESOLVED",
        "provider": "sofascore",
        "entity_scope": scope,
        "provider_id": provider_id,
        "canonical_id": canonical_id,
        "canonical_namespace": namespaces[scope],
    }


def _identity_package():
    production = {929132: 877, 871886: 878, 847097: 866}
    return {
        "status": "PASS",
        "match": _resolution("match", 16363258, 4857),
        "leeds_team": {
            "status": "VALIDATED_PROVIDER_IDENTITY",
            "provider": "sofascore",
            "provider_id": 34,
            "canonical_mapping": "NOT_APPLICABLE",
        },
        "opponent_club": _resolution("opponent_club", 30, 75),
        "leeds_players": {
            "status": "PASS",
            "resolutions": [
                _resolution("leeds_player", provider_id, production.get(provider_id, 10000 + index))
                for index, provider_id in enumerate(LEEDS_IDS)
            ],
        },
        "leeds_manager": _resolution("leeds_manager", 265307, 49),
        "opposition_manager": _resolution("opposition_manager", 788529, 822),
        "opposition_players": {"status": "NOT_APPLICABLE", "canonical_mapping": "NOT_APPLICABLE"},
    }


def _lineup_summary_rows(ids, start_shirt):
    return [
        {
            "sofascore_player_id": provider_id,
            "name": f"P{provider_id}",
            "shirt_number": start_shirt + index,
            "jersey_number": start_shirt + index,
            "substitute": index >= 11,
        }
        for index, provider_id in enumerate(ids)
    ]


def _source_bundle():
    rows = _lineup_summary_rows(LEEDS_IDS, 1)
    return {
        "status": "PASS",
        "sofascore_event_id": 16363258,
        "home_team_provider_id": 30,
        "away_team_provider_id": 34,
        "leeds_team_provider_id": 34,
        "leeds_is_home": False,
        "lineups": {
            "home": {"formation": "4-2-3-1", "starters": [], "bench": []},
            "away": {
                "formation": "3-5-2",
                "starters": rows[:11],
                "bench": rows[11:],
            },
        },
        "appearance_population": {
            "away": {
                "status": "PASS",
                "starter_ids": LEEDS_IDS[:11],
                "used_substitute_ids": LEEDS_USED_SUB_IDS,
                "unused_bench_ids": LEEDS_IDS[15:],
                "appearance_ids": LEEDS_APPEARANCE_IDS,
                "starter_count": 11,
                "used_substitute_count": 4,
                "unused_bench_count": 5,
                "appearance_count": 15,
            }
        },
        "reconciliation": {
            "goals": {
                "status": "PASS",
                "goal_count": 2,
                "half_time_score": {"home": 0, "away": 1},
                "final_score": {"home": 1, "away": 1},
                "chronology": [
                    {"time": 15, "added_time": 0, "is_home": False, "sofascore_player_id": 929132, "home_score": 0, "away_score": 1},
                    {"time": 71, "added_time": 0, "is_home": True, "sofascore_player_id": 1405212, "home_score": 1, "away_score": 1},
                ],
            }
        },
        "staged_events": {
            "events": [
                {"event_kind": "substitution", "team_side": "LEEDS", "provider_player_id": 929132, "provider_secondary_player_id": 886930, "minute_base": 61, "stoppage_minute": 0},
                {"event_kind": "substitution", "team_side": "LEEDS", "provider_player_id": 865523, "provider_secondary_player_id": 973431, "minute_base": 62, "stoppage_minute": 0},
                {"event_kind": "substitution", "team_side": "LEEDS", "provider_player_id": 871886, "provider_secondary_player_id": 355528, "minute_base": 73, "stoppage_minute": 0},
                {"event_kind": "substitution", "team_side": "LEEDS", "provider_player_id": 372344, "provider_secondary_player_id": 803185, "minute_base": 73, "stoppage_minute": 0},
            ]
        },
        "database_writes": 0,
        "promotion_performed": False,
    }


def _evidence_bundle():
    return {
        "status": "PASS",
        "sofascore_event_id": 16363258,
        "validations": {
            "attendance": {"status": "SECONDARY_SOURCE_FACT", "attendance": 31661, "source": "BBC Sport"},
            "formations": {
                "status": "VALIDATED",
                "home": {"status": "VALIDATED", "formation": "4-2-3-1", "source": "sofascore"},
                "away": {"status": "VALIDATED", "formation": "3-5-2", "source": "sofascore"},
            },
            "league_position": {"status": "PASS", "position": 9, "round": 3, "played": 3, "points": 5},
            "managers": {"status": "PASS", "home_manager_provider_id": 788529, "away_manager_provider_id": 265307},
            "captains": {"status": "PASS", "home_captain_provider_id": 115365, "away_captain_provider_id": 847097},
        },
        "database_writes": 0,
        "promotion_performed": False,
    }


def _raw_payloads():
    start = int(datetime(2026, 9, 5, 14, 0, tzinfo=timezone.utc).timestamp())
    return {
        "event": {
            "id": 16363258,
            "startTimestamp": start,
            "homeTeam": {"id": 30, "name": "Brighton & Hove Albion"},
            "awayTeam": {"id": 34, "name": "Leeds United"},
            "homeScore": {"current": 1, "period1": 0},
            "awayScore": {"current": 1, "period1": 1},
            "roundInfo": {"round": 3},
            "venue": {"stadium": {"name": "American Express Stadium"}, "name": "American Express Stadium"},
            "referee": {"id": 52597, "name": "Stuart Attwell"},
        },
        "incidents": {
            "incidents": [
                {"id": 2, "incidentType": "goal", "time": 71, "isHome": True, "player": {"id": 1405212, "name": "Luka Vušković"}, "assist1": {"id": 997152, "name": "Maxim De Cuyper"}, "homeScore": 1, "awayScore": 1},
                {"id": 1, "incidentType": "goal", "time": 15, "isHome": False, "player": {"id": 929132, "name": "Jayden Bogle"}, "assist1": {"id": 871886, "name": "Ao Tanaka"}, "homeScore": 0, "awayScore": 1},
            ]
        },
        "shotmap": {
            "shotmap": [
                {"id": 8272133, "time": 15, "isHome": False, "player": {"id": 929132}, "shotType": "goal", "bodyPart": "right-foot", "situation": "corner"},
                {"id": 8273596, "time": 71, "isHome": True, "player": {"id": 1405212}, "shotType": "goal", "bodyPart": "head", "situation": "corner"},
            ]
        },
    }


def test_brighton_source_adapter_builds_real_scoped_zero_write_diff():
    result = source_diff.build_source_canonical_diff(
        raw_payloads=_raw_payloads(),
        source_bundle=_source_bundle(),
        evidence_bundle=_evidence_bundle(),
        identity_package=_identity_package(),
        canonical_context={"season_id": 101, "competition_id": 12, "competition_name_id": 12, "manager_spell_id": 57},
        leeds_team_provider_id=34,
    )

    assert result["source_derived"] is True
    assert result["status"] == "BLOCKED"
    assert result["canonical_match_id"] == 4857
    assert result["sofascore_event_id"] == 16363258
    assert result["database_writes"] == 0
    assert result["promotion_performed"] is False

    match = next(row for row in result["operations"] if row["table"] == "matches")
    assert match["values"]["match_date"] == "2026-09-05"
    assert match["values"]["kickoff_time"] == "15:00"
    assert match["values"]["opponent_id"] == 75
    assert match["values"]["stadium"] == "American Express Stadium"
    assert match["values"]["referee"] == "Stuart Attwell"
    assert match["values"]["season_id"] == 101
    assert match["values"]["competition_id"] == 12
    assert match["values"]["manager_spell_id"] == 57
    assert match["values"]["half_time_leeds_score"] == 1
    assert match["values"]["half_time_opponent_score"] == 0
    assert match["values"]["first_goal"] == "Scored"
    assert match["values"]["league_position_after_match"] == 9
    assert match["values"]["attendance"] == 31661
    assert match["values"]["formation"] == "3-5-2"

    player_rows = [row for row in result["operations"] if row["table"] == "player_matches"]
    assert len(player_rows) == 15
    assert sum(1 for row in player_rows if row["values"]["started"]) == 11
    assert sum(1 for row in player_rows if row["values"]["substitute"]) == 4
    proposed_provider_ids = {row["provider_evidence"]["provider_player_id"] for row in player_rows}
    assert proposed_provider_ids == set(LEEDS_APPEARANCE_IDS)
    assert proposed_provider_ids.isdisjoint(set(LEEDS_IDS[15:]))


def test_bogle_goal_semantics_are_derived_from_full_match_chronology():
    result = source_diff.build_source_canonical_diff(
        raw_payloads=_raw_payloads(),
        source_bundle=_source_bundle(),
        evidence_bundle=_evidence_bundle(),
        identity_package=_identity_package(),
        canonical_context={"season_id": 101, "competition_id": 12, "competition_name_id": 12, "manager_spell_id": 57},
        leeds_team_provider_id=34,
    )
    goal = next(row for row in result["operations"] if row["table"] == "goals")

    assert goal["key"]["provider_event_id"] == 8272133
    assert goal["values"]["leeds_player_id"] == 877
    assert goal["values"]["assist_player_id"] == 878
    assert goal["values"]["minute_raw"] == "15"
    assert goal["values"]["minute_normalised"] == 15
    assert goal["values"]["game_state"] == "Level"
    assert goal["values"]["goal_state"] == "1st Goal"
    assert goal["values"]["goal_type"] is None
    assert goal["values"]["location"] is None
    assert goal["values"]["body_part"] is None


def test_source_adapter_routes_four_leeds_substitutions_but_not_brighton_goal():
    result = source_diff.build_source_canonical_diff(
        raw_payloads=_raw_payloads(),
        source_bundle=_source_bundle(),
        evidence_bundle=_evidence_bundle(),
        identity_package=_identity_package(),
        canonical_context={"season_id": 101, "competition_id": 12, "competition_name_id": 12, "manager_spell_id": 57},
        leeds_team_provider_id=34,
    )

    substitutions = [row for row in result["operations"] if row["table"] == "match_substitutions"]
    canonical_goals = [row for row in result["operations"] if row["table"] == "goals"]
    assert len(substitutions) == 4
    assert len(canonical_goals) == 1
    assert any(gap["field"] == "structured opposition goals" for gap in result["schema_gaps"])
