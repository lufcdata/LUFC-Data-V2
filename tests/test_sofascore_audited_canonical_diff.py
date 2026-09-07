from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
TESTS_DIR = Path(__file__).resolve().parent


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
    }


def _source_bundle_with_goals():
    source = fixtures._source_bundle()
    # The audited Brighton integration fixture must contain the actual opposition
    # captain population rather than relying on captain evidence alone.
    source["lineups"]["home"]["starters"] = [
        {
            "sofascore_player_id": 115365,
            "name": "Lewis Dunk",
            "shirt_number": 5,
            "jersey_number": 5,
            "substitute": False,
            "captain": True,
        }
    ]
    staged = source["staged_events"]
    staged["database_writes"] = 0
    staged["promotion_performed"] = False
    staged["events"] = [
        {
            "provider": "sofascore",
            "provider_event_id": 1,
            "event_kind": "goal",
            "team_side": "LEEDS",
            "provider_team_id": 34,
            "provider_player_id": 929132,
            "provider_secondary_player_id": 871886,
            "minute_base": 15,
            "stoppage_minute": 0,
            "period": None,
            "event_json": {
                "incidentType": "goal",
                "time": 15,
                "isHome": False,
                "player": {"id": 929132, "name": "Jayden Bogle"},
                "assist1": {"id": 871886, "name": "Ao Tanaka"},
            },
        },
        *staged["events"],
        {
            "provider": "sofascore",
            "provider_event_id": 2,
            "event_kind": "goal",
            "team_side": "OPPONENT",
            "provider_team_id": 30,
            "provider_player_id": 1405212,
            "provider_secondary_player_id": 997152,
            "minute_base": 71,
            "stoppage_minute": 0,
            "period": None,
            "event_json": {
                "incidentType": "goal",
                "time": 71,
                "isHome": True,
                "player": {"id": 1405212, "name": "Luka Vušković"},
                "assist1": {"id": 997152, "name": "Maxim De Cuyper"},
            },
        },
    ]
    return source


def _build():
    return audited.build_audited_canonical_diff(
        raw_payloads=fixtures._raw_payloads(),
        source_bundle=_source_bundle_with_goals(),
        evidence_bundle=fixtures._evidence_bundle(),
        identity_package=fixtures._identity_package(),
        canonical_context=_canonical_context(),
        leeds_team_provider_id=34,
    )


def test_brighton_composition_adds_twenty_shirts_and_gold_manager_route():
    result = _build()

    shirts = [row for row in result["operations"] if row["table"] == "player_match_shirt_numbers"]
    assignments = [row for row in result["operations"] if row["table"] == "managerial_assignments"]
    people = [row for row in result["operations"] if row["table"] == "managerial_assignment_people"]

    assert len(shirts) == 20
    assert len(assignments) == 1
    assert len(people) == 1
    assert assignments[0]["key"] == {"match_id": 4857}
    assert assignments[0]["values"]["canonical_source_name"] == "Fabian Hürzeler"
    assert people[0]["key"]["managerial_person_id"] == 822
    assert result["shirt_number_adapter"] == {"status": "PASS", "operation_count": 20}
    assert result["opposition_manager_adapter"]["status"] == "PASS"
    assert result["opposition_manager_adapter"]["managerial_person_id"] == 822
    assert result["opposition_manager_adapter"]["requires_transactional_parent_key_allocation"] is True


def test_brighton_diff_carries_exact_vuskovic_row_without_closing_schema_gap():
    result = _build()
    rows = [row for row in result["operations"] if row["table"] == "opposition_goals"]

    assert len(rows) == 1
    row = rows[0]
    assert row["action"] == "INSERT_AFTER_SCHEMA_DEPLOYMENT"
    assert row["key"] == {"match_id": 4857, "opposition_goal_number_in_match": 1}
    assert row["values"]["sequence_in_match"] == 2
    assert row["values"]["scorer_name_raw"] == "Luka Vušković"
    assert row["values"]["assist_name_raw"] == "Maxim De Cuyper"
    assert row["values"]["minute_raw"] == "71"
    assert row["values"]["score_leeds_after"] == 1
    assert row["values"]["score_opponent_after"] == 1
    assert row["values"]["game_state_before"] == "Leading +1"
    assert row["provider_evidence"]["provider_player_id"] == 1405212
    assert result["opposition_goal_adapter"]["status"] == "SCHEMA_GAP"
    assert result["opposition_goal_adapter"]["destination_deployed"] is False
    assert result["opposition_goal_adapter"]["opposition_goal_count"] == 1


def test_brighton_diff_carries_lewis_dunk_without_namespace_contamination():
    result = _build()
    rows = [row for row in result["operations"] if row["table"] == "opposition_captains"]

    assert len(rows) == 1
    row = rows[0]
    assert row["action"] == "INSERT_AFTER_SCHEMA_DEPLOYMENT"
    assert row["key"] == {"match_id": 4857}
    assert row["values"] == {"match_id": 4857, "captain_name_raw": "Lewis Dunk"}
    assert row["provider_evidence"]["provider_player_id"] == 115365
    assert row["canonical_opposition_player_id"] is None
    assert row["provider_id_written_to_canonical_id"] is False
    assert result["opposition_captain_adapter"]["status"] == "SCHEMA_GAP"
    assert result["opposition_captain_adapter"]["destination_deployed"] is False
    assert result["opposition_captain_adapter"]["captain_name_raw"] == "Lewis Dunk"
    assert result["opposition_captain_adapter"]["provider_player_id"] == 115365


def test_opposition_manager_gap_is_closed_but_other_real_gaps_remain_blocking():
    result = _build()
    fields = {gap["field"] for gap in result["schema_gaps"]}

    assert "opposition manager" not in fields
    assert "structured opposition goals" in fields
    assert "opposition captain" in fields
    assert "attendance provenance" in fields
    assert "SofaScore external event identity" in fields
    assert "exact tactical formation slots" in fields
    assert result["status"] == "BLOCKED"


def test_composed_diff_remains_strictly_zero_write():
    result = _build()
    assert result["audited_composition"] is True
    assert result["database_writes"] == 0
    assert result["sql_generated"] is False
    assert result["promotion_performed"] is False
