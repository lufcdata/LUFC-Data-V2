from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "sofascore_identity_contract.py"
SPEC = importlib.util.spec_from_file_location("sofascore_identity_contract", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
identity = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = identity
SPEC.loader.exec_module(identity)


def _mapping(entity_type: str, provider_id: int, canonical_id: int) -> dict:
    return {
        "provider": "sofascore",
        "entity_type": entity_type,
        "provider_id": provider_id,
        "canonical_id": canonical_id,
    }


def _brighton_reference_mappings() -> list[dict]:
    return [
        _mapping("match", 16363258, 4857),
        _mapping("team", 30, 9990),
        _mapping("team", 34, 9991),
        _mapping("manager", 788529, 7001),
        _mapping("manager", 265307, 7002),
        _mapping("player", 929132, 8001),
        _mapping("player", 871886, 8002),
        _mapping("player", 1405212, 8003),
        _mapping("player", 997152, 8004),
    ]


def test_brighton_match_identity_resolves_without_reusing_provider_id():
    result = identity.resolve_external_id(
        _brighton_reference_mappings(),
        entity_type="match",
        provider_id=16363258,
    )

    assert result["status"] == "RESOLVED"
    assert result["provider_id"] == 16363258
    assert result["canonical_id"] == 4857


def test_leeds_sofascore_team_id_resolves_through_mapping_layer():
    result = identity.resolve_external_id(
        _brighton_reference_mappings(),
        entity_type="team",
        provider_id=34,
    )

    assert result["provider"] == "sofascore"
    assert result["provider_id"] == 34
    assert result["canonical_id"] == 9991


def test_daniel_farke_provider_manager_id_resolves_through_mapping_layer():
    result = identity.resolve_external_id(
        _brighton_reference_mappings(),
        entity_type="manager",
        provider_id=265307,
    )

    assert result["provider_id"] == 265307
    assert result["canonical_id"] == 7002


def test_unresolved_provider_identity_blocks_promotion():
    with pytest.raises(identity.IdentityContractError, match="unresolved SofaScore player identity"):
        identity.resolve_external_id(
            _brighton_reference_mappings(),
            entity_type="player",
            provider_id=980643,
        )


def test_duplicate_provider_mapping_blocks_even_when_canonical_id_matches():
    mappings = _brighton_reference_mappings()
    mappings.append(_mapping("team", 34, 9991))

    with pytest.raises(identity.IdentityContractError, match="duplicate provider identity mappings"):
        identity.validate_mapping_population(mappings)


def test_duplicate_provider_mapping_blocks_when_canonical_ids_conflict():
    mappings = _brighton_reference_mappings()
    mappings.append(_mapping("team", 34, 123456))

    with pytest.raises(identity.IdentityContractError, match="duplicate provider identity mappings"):
        identity.validate_mapping_population(mappings)


def test_two_provider_players_cannot_collapse_to_one_canonical_player():
    mappings = [
        _mapping("player", 929132, 8001),
        _mapping("player", 871886, 8001),
    ]

    with pytest.raises(identity.IdentityContractError, match="same canonical ID"):
        identity.require_all_provider_ids_resolved(
            mappings,
            entity_type="player",
            provider_ids=[929132, 871886],
        )


def test_brighton_reference_identity_package_is_zero_write_and_auditable():
    result = identity.proposed_identity_package(
        event_id=16363258,
        home_team_id=30,
        away_team_id=34,
        player_ids=[929132, 871886, 1405212, 997152],
        manager_ids=[788529, 265307],
        mappings=_brighton_reference_mappings(),
    )

    assert result["status"] == "PASS"
    assert result["database_writes"] == 0
    assert result["provider_ids_preserved"] is True
    assert result["canonical_ids_assigned_only_via_mapping"] is True
    assert result["teams"]["resolved_count"] == 2
    assert result["players"]["resolved_count"] == 4
    assert result["managers"]["resolved_count"] == 2


def test_identity_package_blocks_if_one_player_is_unresolved():
    with pytest.raises(identity.IdentityContractError, match="unresolved SofaScore player identity"):
        identity.proposed_identity_package(
            event_id=16363258,
            home_team_id=30,
            away_team_id=34,
            player_ids=[929132, 980643],
            manager_ids=[788529, 265307],
            mappings=_brighton_reference_mappings(),
        )
