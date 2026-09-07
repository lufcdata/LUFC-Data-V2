from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
TESTS_DIR = Path(__file__).resolve().parent
IMPORTER_GIT_SHA = "b61f7b8d6ee2d33e5237e7d2bb1641f510c52b34"


def _load_path(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _load_script(name: str):
    return _load_path(name, SCRIPTS_DIR / f"{name}.py")


_load_script("sofascore_canonical_diff")
_load_script("sofascore_canonical_match_enrichment")
_load_script("sofascore_goal_semantics")
_load_script("sofascore_source_canonical_diff")
_load_script("sofascore_shirt_number_diff")
_load_script("sofascore_opposition_manager_diff")
_load_script("sofascore_opposition_goal_diff")
_load_script("sofascore_opposition_captain_diff")
_load_script("sofascore_ingestion_provenance_diff")
audited = _load_script("sofascore_audited_canonical_diff")
fixtures = _load_path(
    "source_diff_fixture_helpers",
    TESTS_DIR / "test_sofascore_source_canonical_diff.py",
)


def _canonical_context():
    return {
        "season_id": 101,
        "competition_id": 12,
        "competition_name_id": 12,
        "manager_spell_id": 57,
        "opposition_manager_canonical_name": "Fabian Hürzeler",
        "opposition_manager_nationality_display": "🇩🇪",
        "candidate_match_id": 4857,
        "opponent_club_id": 75,
        "league_position_after_match": 9,
    }


def _source():
    source = fixtures._source_bundle()
    source["lineups"]["home"]["starters"] = [
        {
            "sofascore_player_id": 115365,
            "name": "Lewis Dunk",
            "shirt_number": 5,
            "jersey_number": 5,
            "substitute": False,
        },
        {
            "sofascore_player_id": 1405212,
            "name": "Luka Vušković",
            "shirt_number": 44,
            "jersey_number": 44,
            "substitute": False,
        },
    ]
    source["staged_events"] = {
        "database_writes": 0,
        "promotion_performed": False,
        "events": [
            {
                "event_kind": "goal",
                "team_side": "LEEDS",
                "provider_player_id": 929132,
                "minute_raw": "15'",
                "minute_base": 15,
                "stoppage_minute": None,
                "period": "1ST",
                "event_json": {
                    "player": {"id": 929132, "name": "Jayden Bogle"},
                    "assist1": {"id": 871886, "name": "Ao Tanaka"},
                    "isHome": False,
                    "incidentType": "goal",
                },
            },
            {
                "event_kind": "goal",
                "team_side": "OPPONENT",
                "provider_player_id": 1405212,
                "minute_raw": "71'",
                "minute_base": 71,
                "stoppage_minute": None,
                "period": "2ND",
                "event_json": {
                    "player": {"id": 1405212, "name": "Luka Vušković"},
                    "assist1": {"id": 997152, "name": "Maxim De Cuyper"},
                    "isHome": True,
                    "incidentType": "goal",
                },
            },
        ],
    }
    return source


def _evidence():
    return fixtures._evidence_bundle()


def _identity():
    return fixtures._identity_package()


def _build():
    return audited.build_audited_canonical_diff(
        raw_payloads=fixtures._raw_payloads(),
        source_bundle=_source(),
        evidence_bundle=_evidence(),
        identity_package=_identity(),
        canonical_context=_canonical_context(),
        leeds_team_provider_id=34,
        importer_git_sha=IMPORTER_GIT_SHA,
    )


def test_audited_diff_adds_twenty_shirt_rows_and_gold_manager_relationship():
    result = _build()
    assert result["audited_composition"] is True
    assert result["status"] == "BLOCKED"
    assert result["shirt_number_adapter"] == {"status": "PASS", "operation_count": 20}
    assert result["opposition_manager_adapter"] == {
        "status": "PASS",
        "managerial_person_id": 822,
        "operation_count": 2,
        "requires_transactional_parent_key_allocation": True,
    }

    shirts = [op for op in result["operations"] if op["table"] == "player_match_shirt_numbers"]
    assert len(shirts) == 20
    assert all(op["key"]["match_id"] == 4857 for op in shirts)
    assert all("player_match_shirt_number_id" not in op["values"] for op in shirts)
    assert all(op["values"]["source_row_id"] is None for op in shirts)

    assignment = next(op for op in result["operations"] if op["table"] == "managerial_assignments")
    assert assignment["key"] == {"match_id": 4857}
    assert assignment["values"]["authority_type"] == "individual"
    assert assignment["values"]["canonical_source_name"] == "Fabian Hürzeler"
    assert "managerial_assignment_id" not in assignment["values"]
    assert assignment["deferred_primary_key"] == {
        "column": "managerial_assignment_id",
        "allocation": "TRANSACTIONAL_AT_PROMOTION",
        "reason": "column is NOT NULL with no database default; never guess from match_id or max(id)+1 in the dry-run diff",
    }

    link = next(op for op in result["operations"] if op["table"] == "managerial_assignment_people")
    assert link["action"] == "INSERT_AFTER_PARENT_KEY_ALLOCATION"
    assert link["key"]["managerial_assignment_id"] == "<FROM_PARENT_INSERT>"
    assert link["key"]["managerial_person_id"] == 822


def test_only_audited_manager_schema_gap_is_removed():
    result = _build()
    fields = {gap["field"] for gap in result["schema_gaps"]}
    assert "opposition manager" not in fields
    assert "structured opposition goals" in fields
    assert "opposition captain" in fields
    assert "attendance provenance" in fields
    assert "SofaScore external event identity" in fields
    assert "exact tactical formation slots" in fields
    assert result["schema_gap_count"] == len(result["schema_gaps"])


def test_blocked_opposition_goal_row_is_carried_without_closing_schema_gap():
    result = _build()
    rows = [op for op in result["operations"] if op["table"] == "opposition_goals"]
    assert len(rows) == 1
    row = rows[0]
    assert row["action"] == "INSERT_AFTER_SCHEMA_DEPLOYMENT"
    assert row["key"] == {"match_id": 4857, "opposition_goal_number_in_match": 1}
    assert row["values"]["sequence_in_match"] == 2
    assert row["values"]["scorer_name_raw"] == "Luka Vušković"
    assert row["values"]["assist_name_raw"] == "Maxim De Cuyper"
    assert row["values"]["minute_normalised"] == 71
    assert row["values"]["score_leeds_after"] == 1
    assert row["values"]["score_opponent_after"] == 1
    assert row["values"]["game_state_before"] == "Leading +1"
    assert row["provider_evidence"]["provider_player_id"] == 1405212
    assert result["opposition_goal_adapter"]["status"] == "SCHEMA_GAP"
    assert result["opposition_goal_adapter"]["destination_deployed"] is False
    assert result["opposition_goal_adapter"]["opposition_goal_count"] == 1
    assert result["opposition_goal_adapter"]["operation_count"] == 1


def test_blocked_opposition_captain_row_is_carried_without_namespace_contamination():
    result = _build()
    rows = [op for op in result["operations"] if op["table"] == "opposition_captains"]
    assert len(rows) == 1
    row = rows[0]
    assert row["action"] == "INSERT_AFTER_SCHEMA_DEPLOYMENT"
    assert row["key"] == {"match_id": 4857}
    assert row["values"]["captain_name_raw"] == "Lewis Dunk"
    assert row["provider_evidence"]["provider_player_id"] == 115365
    assert row["canonical_opposition_player_id"] is None
    assert row["provider_id_written_to_canonical_id"] is False
    assert result["opposition_captain_adapter"]["status"] == "SCHEMA_GAP"
    assert result["opposition_captain_adapter"]["destination_deployed"] is False
    assert result["opposition_captain_adapter"]["captain_name_raw"] == "Lewis Dunk"
    assert result["opposition_captain_adapter"]["provider_player_id"] == 115365
    assert result["opposition_captain_adapter"]["operation_count"] == 1


def test_blocked_ingestion_provenance_rows_are_carried_with_deferred_parent_identity():
    result = _build()
    runs = [op for op in result["operations"] if op["table"] == "ingestion.runs"]
    fields = [op for op in result["operations"] if op["table"] == "ingestion.field_provenance"]
    assert len(runs) == 1
    assert len(fields) == 1

    run = runs[0]
    assert run["key"] == {
        "provider": "sofascore",
        "provider_event_id": "16363258",
        "importer_git_sha": IMPORTER_GIT_SHA,
    }
    assert run["values"]["canonical_match_id"] == 4857
    assert run["deferred_primary_key"]["column"] == "ingestion_run_id"
    assert run["canonical_primary_key_allocated"] is False

    field = fields[0]
    assert field["action"] == "INSERT_AFTER_PARENT_KEY_ALLOCATION_AND_SCHEMA_DEPLOYMENT"
    assert field["values"]["ingestion_run_id"] == "<FROM_PARENT_INSERT>"
    assert field["values"]["field_name"] == "attendance"
    assert field["values"]["value_json"] == 31661
    assert field["values"]["source_provider"] == "BBC Sport"
    assert field["values"]["authority"] == "SECONDARY"

    assert result["ingestion_provenance_adapter"]["importer_git_sha"] == IMPORTER_GIT_SHA
    gap_fields = {gap["field"] for gap in result["schema_gaps"]}
    assert "attendance provenance" in gap_fields
    assert "SofaScore external event identity" in gap_fields


def test_composed_diff_never_executes_database_writes():
    result = _build()
    assert result["database_writes"] == 0
    assert result["sql_generated"] is False
    assert result["promotion_performed"] is False
