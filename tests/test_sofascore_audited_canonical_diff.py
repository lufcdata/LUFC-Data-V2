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


def _build():
    return audited.build_audited_canonical_diff(
        raw_payloads=fixtures._raw_payloads(),
        source_bundle=fixtures._source_bundle(),
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
