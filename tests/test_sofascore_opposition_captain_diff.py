from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
path = SCRIPTS_DIR / "sofascore_opposition_captain_diff.py"
spec = importlib.util.spec_from_file_location("sofascore_opposition_captain_diff", path)
assert spec is not None and spec.loader is not None
captain_diff = importlib.util.module_from_spec(spec)
sys.modules["sofascore_opposition_captain_diff"] = captain_diff
spec.loader.exec_module(captain_diff)


def _source():
    return {
        "leeds_is_home": False,
        "home_team_provider_id": 30,
        "away_team_provider_id": 34,
        "lineups": {
            "home": {
                "starters": [
                    {"sofascore_player_id": 115365, "name": "Lewis Dunk", "substitute": False},
                    {"sofascore_player_id": 1405212, "name": "Luka Vušković", "substitute": False},
                ],
                "bench": [],
            },
            "away": {"starters": [], "bench": []},
        },
        "database_writes": 0,
        "promotion_performed": False,
    }


def _evidence():
    return {
        "validations": {
            "captains": {
                "status": "PASS",
                "home_captain_provider_id": 115365,
                "away_captain_provider_id": 847097,
            }
        },
        "database_writes": 0,
        "promotion_performed": False,
    }


def test_brighton_captain_is_preserved_without_namespace_contamination():
    result = captain_diff.build_opposition_captain_proposal(
        canonical_match_id=4857,
        source_bundle=_source(),
        evidence_bundle=_evidence(),
    )
    operation = result["operations"][0]

    assert result["status"] == "SCHEMA_GAP"
    assert result["destination_deployed"] is False
    assert result["captain_name_raw"] == "Lewis Dunk"
    assert result["provider_player_id"] == 115365
    assert operation["action"] == "INSERT_AFTER_PARENT_KEY_ALLOCATION_AND_SCHEMA_DEPLOYMENT"
    assert operation["values"] == {
        "match_id": 4857,
        "captain_name_raw": "Lewis Dunk",
        "ingestion_run_id": "<FROM_PARENT_INSERT>",
    }
    assert operation["deferred_parent_key"] == {
        "column": "ingestion_run_id",
        "from_operation": "ingestion.runs",
        "allocation": "FROM_PARENT_INSERT",
    }
    assert operation["provider_evidence"]["provider_player_id"] == 115365
    assert operation["canonical_opposition_player_id"] is None
    assert operation["provider_id_written_to_canonical_id"] is False
    assert result["database_writes"] == 0
    assert result["sql_generated"] is False
    assert result["promotion_performed"] is False


def test_captain_must_reconcile_to_exactly_one_opposition_lineup_row():
    source = _source()
    source["lineups"]["home"]["starters"] = []
    try:
        captain_diff.build_opposition_captain_proposal(
            canonical_match_id=4857,
            source_bundle=source,
            evidence_bundle=_evidence(),
        )
    except captain_diff.OppositionCaptainDiffError as exc:
        assert "matched 0 lineup rows" in str(exc)
    else:
        raise AssertionError("unreconciled opposition captain must fail closed")


def test_provider_id_is_never_treated_as_canonical_player_id():
    result = captain_diff.build_opposition_captain_proposal(
        canonical_match_id=4857,
        source_bundle=_source(),
        evidence_bundle=_evidence(),
    )
    operation = result["operations"][0]
    assert 115365 not in operation["values"].values()
    assert operation["provider_evidence"]["provider_player_id"] == 115365
