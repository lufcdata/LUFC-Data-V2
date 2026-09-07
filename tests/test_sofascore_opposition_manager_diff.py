from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "sofascore_opposition_manager_diff.py"
SPEC = importlib.util.spec_from_file_location("sofascore_opposition_manager_diff", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
manager_diff = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = manager_diff
SPEC.loader.exec_module(manager_diff)


def _evidence_bundle():
    return {
        "status": "PASS",
        "validations": {
            "managers": {
                "status": "PASS",
                "home_manager_provider_id": 788529,
                "away_manager_provider_id": 265307,
            }
        },
    }


def _identity_package():
    return {
        "opposition_manager": {
            "status": "RESOLVED",
            "provider": "sofascore",
            "entity_scope": "opposition_manager",
            "provider_id": 788529,
            "canonical_id": 822,
            "canonical_namespace": "managerial_people.managerial_person_id",
        }
    }


def test_brighton_manager_routes_to_gold_relational_model_without_guessing_assignment_id():
    result = manager_diff.build_opposition_manager_assignment_proposal(
        evidence_bundle=_evidence_bundle(),
        identity_package=_identity_package(),
        canonical_match_id=4857,
        leeds_is_home=False,
        canonical_name="Fabian Hürzeler",
        nationality_display="🇩🇪",
    )

    assert result["status"] == "PASS"
    assert result["managerial_person_id"] == 822
    assert result["authority_type"] == "individual"
    assert result["operation_count"] == 2
    assert result["primary_key_allocation_performed"] is False
    assert result["requires_transactional_parent_key_allocation"] is True
    assert result["database_writes"] == 0
    assert result["promotion_performed"] is False

    assignment, person = result["operations"]
    assert assignment["table"] == "managerial_assignments"
    assert assignment["key"] == {"match_id": 4857}
    assert "managerial_assignment_id" not in assignment["key"]
    assert assignment["values"]["authority_type"] == "individual"
    assert assignment["values"]["canonical_source_name"] == "Fabian Hürzeler"
    assert assignment["values"]["nationality_display"] == "🇩🇪"
    assert assignment["deferred_primary_key"]["allocation"] == "TRANSACTIONAL_AT_PROMOTION"

    assert person["table"] == "managerial_assignment_people"
    assert person["key"]["managerial_assignment_id"] == "<FROM_PARENT_INSERT>"
    assert person["key"]["managerial_person_id"] == 822
    assert person["values"]["member_role"] == "manager"


def test_provider_identity_mismatch_fails_closed():
    identities = _identity_package()
    identities["opposition_manager"]["provider_id"] = 999
    with pytest.raises(manager_diff.OppositionManagerDiffError, match="provider ID does not match"):
        manager_diff.build_opposition_manager_assignment_proposal(
            evidence_bundle=_evidence_bundle(),
            identity_package=identities,
            canonical_match_id=4857,
            leeds_is_home=False,
            canonical_name="Fabian Hürzeler",
        )


def test_wrong_canonical_namespace_fails_closed():
    identities = _identity_package()
    identities["opposition_manager"]["canonical_namespace"] = "managers.manager_id"
    with pytest.raises(manager_diff.OppositionManagerDiffError, match="wrong canonical namespace"):
        manager_diff.build_opposition_manager_assignment_proposal(
            evidence_bundle=_evidence_bundle(),
            identity_package=identities,
            canonical_match_id=4857,
            leeds_is_home=False,
            canonical_name="Fabian Hürzeler",
        )


def test_non_pass_manager_evidence_fails_closed():
    evidence = _evidence_bundle()
    evidence["validations"]["managers"]["status"] = "BLOCKED"
    with pytest.raises(manager_diff.OppositionManagerDiffError, match="manager evidence is not PASS"):
        manager_diff.build_opposition_manager_assignment_proposal(
            evidence_bundle=evidence,
            identity_package=_identity_package(),
            canonical_match_id=4857,
            leeds_is_home=False,
            canonical_name="Fabian Hürzeler",
        )
