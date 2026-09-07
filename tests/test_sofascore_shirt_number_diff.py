from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "sofascore_shirt_number_diff.py"
SPEC = importlib.util.spec_from_file_location("sofascore_shirt_number_diff", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
shirts = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = shirts
SPEC.loader.exec_module(shirts)


def _source_bundle():
    rows = [
        {"sofascore_player_id": 1000 + i, "shirt_number": number}
        for i, number in enumerate([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 14, 15, 17, 18, 20, 21, 22, 23])
    ]
    return {
        "leeds_is_home": False,
        "lineups": {
            "home": {"starters": [], "bench": []},
            "away": {"starters": rows[:11], "bench": rows[11:]},
        },
    }


def _identity_package():
    return {
        "leeds_players": {
            "resolutions": [
                {
                    "entity_scope": "leeds_player",
                    "provider_id": 1000 + i,
                    "canonical_id": 2000 + i,
                }
                for i in range(20)
            ]
        }
    }


def test_builds_exactly_twenty_match_shirt_number_operations_without_allocating_ids():
    result = shirts.build_shirt_number_operations(
        source_bundle=_source_bundle(),
        identity_package=_identity_package(),
        canonical_match_id=4857,
    )

    assert result["status"] == "PASS"
    assert result["operation_count"] == 20
    assert {row["table"] for row in result["operations"]} == {"player_match_shirt_numbers"}
    assert result["operations"][0]["key"] == {"match_id": 4857, "player_id": 2000}
    assert result["operations"][0]["values"] == {"shirt_number": 1, "source_row_id": None}
    assert result["primary_key_allocation_performed"] is False
    assert result["provider_ids_written_to_canonical_ids"] is False
    assert result["database_writes"] == 0
    assert result["promotion_performed"] is False


def test_duplicate_shirt_number_fails_closed():
    source = _source_bundle()
    source["lineups"]["away"]["bench"][0]["shirt_number"] = 1
    with pytest.raises(shirts.ShirtNumberDiffError, match="duplicate Leeds shirt number"):
        shirts.build_shirt_number_operations(
            source_bundle=source,
            identity_package=_identity_package(),
            canonical_match_id=4857,
        )


def test_unresolved_player_fails_closed():
    identities = _identity_package()
    identities["leeds_players"]["resolutions"].pop()
    with pytest.raises(shirts.ShirtNumberDiffError, match="expected exactly one Leeds player identity"):
        shirts.build_shirt_number_operations(
            source_bundle=_source_bundle(),
            identity_package=identities,
            canonical_match_id=4857,
        )


def test_non_positive_shirt_number_fails_closed():
    source = _source_bundle()
    source["lineups"]["away"]["starters"][0]["shirt_number"] = 0
    with pytest.raises(shirts.ShirtNumberDiffError, match="shirt number must be positive"):
        shirts.build_shirt_number_operations(
            source_bundle=source,
            identity_package=_identity_package(),
            canonical_match_id=4857,
        )
