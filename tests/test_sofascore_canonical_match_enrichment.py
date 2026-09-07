from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "sofascore_canonical_match_enrichment.py"
SPEC = importlib.util.spec_from_file_location("sofascore_canonical_match_enrichment", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
module = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = module
SPEC.loader.exec_module(module)


def _source_bundle():
    return {
        "status": "PASS",
        "sofascore_event_id": 16363258,
        "leeds_is_home": False,
        "reconciliation": {
            "goals": {
                "status": "PASS",
                "half_time_score": {"home": 0, "away": 1},
                "final_score": {"home": 1, "away": 1},
                "chronology": [
                    {"time": 15, "added_time": 0, "is_home": False, "sofascore_player_id": 929132, "home_score": 0, "away_score": 1},
                    {"time": 71, "added_time": 0, "is_home": True, "sofascore_player_id": 1405212, "home_score": 1, "away_score": 1},
                ],
            }
        },
        "database_writes": 0,
        "promotion_performed": False,
    }


def _evidence_bundle():
    return {
        "status": "PASS",
        "validations": {
            "attendance": {
                "status": "SECONDARY_SOURCE_FACT",
                "attendance": 31661,
                "source": "BBC Sport",
            },
            "formations": {
                "status": "VALIDATED",
                "home": {"status": "VALIDATED", "formation": "4-2-3-1", "source": "sofascore"},
                "away": {"status": "VALIDATED", "formation": "3-5-2", "source": "sofascore"},
            },
            "league_position": {
                "status": "PASS",
                "provider": "sofascore",
                "position": 9,
                "round": 3,
                "played": 3,
                "points": 5,
            },
        },
        "database_writes": 0,
        "promotion_performed": False,
    }


def _context():
    return {
        "season_id": 101,
        "competition_id": 12,
        "competition_name_id": 12,
        "manager_spell_id": 57,
    }


def test_brighton_match_enrichment_routes_verified_values_to_existing_columns():
    result = module.build_canonical_match_enrichment(
        source_bundle=_source_bundle(),
        evidence_bundle=_evidence_bundle(),
        canonical_context=_context(),
    )

    assert result["status"] == "PASS"
    assert result["reconciled_final_score"] == {"leeds": 1, "opponent": 1}
    assert result["values"] == {
        "season_id": 101,
        "competition_id": 12,
        "competition_name_id": 12,
        "manager_spell_id": 57,
        "half_time_leeds_score": 1,
        "half_time_opponent_score": 0,
        "first_goal": "Scored",
        "league_position_after_match": 9,
        "attendance": 31661,
        "formation": "3-5-2",
    }
    assert result["field_sources"]["attendance"] == "BBC Sport"
    assert result["database_writes"] == 0
    assert result["canonical_promotion_performed"] is False


def test_first_goal_is_relative_to_leeds_not_home_team():
    source = _source_bundle()
    source["reconciliation"]["goals"]["chronology"][0]["is_home"] = True

    result = module.build_canonical_match_enrichment(
        source_bundle=source,
        evidence_bundle=_evidence_bundle(),
        canonical_context=_context(),
    )

    assert result["values"]["first_goal"] == "Conceded"


def test_non_league_fixture_does_not_invent_a_league_position():
    evidence = _evidence_bundle()
    evidence["validations"]["league_position"] = {
        "status": "NOT_APPLICABLE",
        "reason": "non-league fixture: FA Cup",
    }

    result = module.build_canonical_match_enrichment(
        source_bundle=_source_bundle(),
        evidence_bundle=evidence,
        canonical_context=_context(),
    )

    assert result["values"]["league_position_after_match"] is None


def test_missing_canonical_manager_spell_blocks_enrichment():
    context = _context()
    context.pop("manager_spell_id")

    with pytest.raises(module.CanonicalMatchEnrichmentError, match="manager_spell_id"):
        module.build_canonical_match_enrichment(
            source_bundle=_source_bundle(),
            evidence_bundle=_evidence_bundle(),
            canonical_context=context,
        )


def test_non_pass_source_bundle_blocks_enrichment():
    source = _source_bundle()
    source["status"] = "BLOCKED"

    with pytest.raises(module.CanonicalMatchEnrichmentError, match="source bundle is not PASS"):
        module.build_canonical_match_enrichment(
            source_bundle=source,
            evidence_bundle=_evidence_bundle(),
            canonical_context=_context(),
        )
