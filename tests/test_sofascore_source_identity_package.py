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
identity_contract = _load("sofascore_lufc_identity_contract")
source_identity = _load("sofascore_source_identity_package")


def _entry(player_id: int, *, substitute: bool, captain: bool = False):
    return {
        "player": {"id": player_id, "name": f"Player {player_id}"},
        "substitute": substitute,
        "captain": captain,
        "shirtNumber": player_id % 99 + 1,
        "position": "M",
    }


def _lineup(player_ids: list[int], captain_id: int):
    return [
        _entry(player_id, substitute=index >= 11, captain=player_id == captain_id)
        for index, player_id in enumerate(player_ids)
    ]


def _mapping(scope: str, provider_id: int, canonical_id: int):
    return {
        "provider": "sofascore",
        "entity_scope": scope,
        "provider_id": provider_id,
        "canonical_id": canonical_id,
        "canonical_namespace": identity_contract.CANONICAL_NAMESPACES[scope],
    }


def _raw_payloads():
    leeds_ids = [
        980643, 827681, 282229, 1118177, 929132, 889861, 847097, 871886, 834308, 372344,
        865523, 886930, 973431, 355528, 803185, 190161, 906075, 866191, 828639, 1146148,
    ]
    brighton_ids = list(range(2000001, 2000021))
    return {
        "event": {
            "id": 16363258,
            "homeTeam": {"id": 30, "name": "Brighton & Hove Albion"},
            "awayTeam": {"id": 34, "name": "Leeds United"},
        },
        "lineups": {
            "confirmed": True,
            "home": {"formation": "4-2-3-1", "players": _lineup(brighton_ids, brighton_ids[0])},
            "away": {"formation": "3-5-2", "players": _lineup(leeds_ids, 847097)},
        },
        "managers": {
            "homeManager": {"id": 788529, "name": "Fabian Hürzeler"},
            "awayManager": {"id": 265307, "name": "Daniel Farke"},
        },
    }


def _mappings():
    leeds_ids = _raw_payloads()["lineups"]["away"]["players"]
    rows = [
        _mapping("match", 16363258, 4857),
        _mapping("opponent_club", 30, 75),
        _mapping("leeds_manager", 265307, 49),
        _mapping("opposition_manager", 788529, 822),
    ]
    for index, entry in enumerate(leeds_ids):
        provider_id = entry["player"]["id"]
        canonical_id = {929132: 877, 871886: 878}.get(provider_id, 10000 + index)
        rows.append(_mapping("leeds_player", provider_id, canonical_id))
    return rows


def test_brighton_source_identity_package_extracts_only_leeds_players():
    result = source_identity.build_source_identity_package(
        raw_payloads=_raw_payloads(),
        leeds_team_provider_id=34,
        mappings=_mappings(),
    )

    assert result["status"] == "PASS"
    assert result["sofascore_event_id"] == 16363258
    assert result["leeds_side"] == "away"
    assert result["source_population"]["leeds_manager_provider_id"] == 265307
    assert result["source_population"]["opposition_manager_provider_id"] == 788529
    assert len(result["source_population"]["leeds_player_provider_ids"]) == 20
    assert result["identity_package"]["opponent_club"]["canonical_id"] == 75
    assert result["identity_package"]["leeds_manager"]["canonical_id"] == 49
    assert result["identity_package"]["opposition_manager"]["canonical_id"] == 822
    assert result["identity_package"]["leeds_players"]["resolved_count"] == 20
    assert result["identity_package"]["opposition_players"]["status"] == "NOT_APPLICABLE"
    assert result["database_writes"] == 0
    assert result["canonical_promotion_performed"] is False


def test_brighton_opposition_captain_is_not_required_in_leeds_player_mapping():
    raw = _raw_payloads()
    opposition_captain_id = raw["lineups"]["home"]["players"][0]["player"]["id"]
    assert all(
        not (
            row["entity_scope"] == "leeds_player"
            and row["provider_id"] == opposition_captain_id
        )
        for row in _mappings()
    )

    result = source_identity.build_source_identity_package(
        raw_payloads=raw,
        leeds_team_provider_id=34,
        mappings=_mappings(),
    )
    assert result["identity_package"]["opposition_players"]["canonical_mapping"] == "NOT_APPLICABLE"


def test_missing_one_leeds_player_mapping_blocks_source_identity_package():
    mappings = _mappings()
    mappings = [
        row for row in mappings
        if not (row["entity_scope"] == "leeds_player" and row["provider_id"] == 929132)
    ]

    with pytest.raises(identity_contract.LufcIdentityContractError, match="unresolved SofaScore leeds_player"):
        source_identity.build_source_identity_package(
            raw_payloads=_raw_payloads(),
            leeds_team_provider_id=34,
            mappings=mappings,
        )


def test_leeds_team_provider_id_is_validated_but_never_mapped_to_clubs():
    result = source_identity.build_source_identity_package(
        raw_payloads=_raw_payloads(),
        leeds_team_provider_id=34,
        mappings=_mappings(),
    )

    assert result["identity_package"]["leeds_team"]["provider_id"] == 34
    assert result["identity_package"]["leeds_team"]["canonical_mapping"] == "NOT_APPLICABLE"
