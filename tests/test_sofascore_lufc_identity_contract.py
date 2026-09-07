from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "sofascore_lufc_identity_contract.py"
SPEC = importlib.util.spec_from_file_location("sofascore_lufc_identity_contract", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
identity = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = identity
SPEC.loader.exec_module(identity)


def _mapping(scope: str, provider_id: int, canonical_id: int):
    return {
        "provider": "sofascore",
        "entity_scope": scope,
        "provider_id": provider_id,
        "canonical_id": canonical_id,
        "canonical_namespace": identity.CANONICAL_NAMESPACES[scope],
    }


def _brighton_scoped_mappings():
    return [
        _mapping("match", 16363258, 4857),
        _mapping("opponent_club", 30, 75),
        _mapping("leeds_player", 929132, 877),
        _mapping("leeds_player", 871886, 878),
        _mapping("leeds_manager", 265307, 49),
        _mapping("opposition_manager", 788529, 822),
    ]


def test_brighton_identity_package_does_not_map_leeds_into_opponent_clubs():
    package = identity.proposed_lufc_identity_package(
        event_id=16363258,
        home_team_provider_id=30,
        away_team_provider_id=34,
        leeds_team_provider_id=34,
        leeds_player_provider_ids=[929132, 871886],
        leeds_manager_provider_id=265307,
        opposition_manager_provider_id=788529,
        mappings=_brighton_scoped_mappings(),
    )

    assert package["status"] == "PASS"
    assert package["leeds_team"]["provider_id"] == 34
    assert package["leeds_team"]["canonical_mapping"] == "NOT_APPLICABLE"
    assert package["opponent_club"]["provider_id"] == 30
    assert package["opponent_club"]["canonical_id"] == 75
    assert package["opponent_club"]["canonical_namespace"] == "clubs.club_id"


def test_opposition_manager_and_leeds_manager_use_different_canonical_namespaces():
    package = identity.proposed_lufc_identity_package(
        event_id=16363258,
        home_team_provider_id=30,
        away_team_provider_id=34,
        leeds_team_provider_id=34,
        leeds_player_provider_ids=[929132, 871886],
        leeds_manager_provider_id=265307,
        opposition_manager_provider_id=788529,
        mappings=_brighton_scoped_mappings(),
    )

    assert package["leeds_manager"]["canonical_id"] == 49
    assert package["leeds_manager"]["canonical_namespace"] == "managers.manager_id"
    assert package["opposition_manager"]["canonical_id"] == 822
    assert package["opposition_manager"]["canonical_namespace"] == "managerial_people.managerial_person_id"


def test_opposition_players_are_never_resolved_into_leeds_players():
    package = identity.proposed_lufc_identity_package(
        event_id=16363258,
        home_team_provider_id=30,
        away_team_provider_id=34,
        leeds_team_provider_id=34,
        leeds_player_provider_ids=[929132, 871886],
        leeds_manager_provider_id=265307,
        opposition_manager_provider_id=788529,
        mappings=_brighton_scoped_mappings(),
    )

    assert package["leeds_players"]["resolved_count"] == 2
    assert package["opposition_players"]["status"] == "NOT_APPLICABLE"
    assert package["opposition_players"]["canonical_mapping"] == "NOT_APPLICABLE"
    assert package["database_writes"] == 0
    assert package["canonical_promotion_performed"] is False


def test_wrong_namespace_for_opposition_manager_fails_closed():
    mappings = _brighton_scoped_mappings()
    mappings[-1] = {
        "provider": "sofascore",
        "entity_scope": "opposition_manager",
        "provider_id": 788529,
        "canonical_id": 822,
        "canonical_namespace": "managers.manager_id",
    }

    with pytest.raises(identity.LufcIdentityContractError, match="wrong canonical namespace"):
        identity.validate_scoped_mapping_population(mappings)


def test_missing_opponent_club_mapping_blocks_package():
    mappings = [
        row for row in _brighton_scoped_mappings()
        if row["entity_scope"] != "opponent_club"
    ]

    with pytest.raises(identity.LufcIdentityContractError, match="unresolved SofaScore opponent_club"):
        identity.proposed_lufc_identity_package(
            event_id=16363258,
            home_team_provider_id=30,
            away_team_provider_id=34,
            leeds_team_provider_id=34,
            leeds_player_provider_ids=[929132, 871886],
            leeds_manager_provider_id=265307,
            opposition_manager_provider_id=788529,
            mappings=mappings,
        )
