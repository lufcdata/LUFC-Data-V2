from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "sofascore_canonical_diff.py"
SPEC = importlib.util.spec_from_file_location("sofascore_canonical_diff", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
canonical_diff = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = canonical_diff
SPEC.loader.exec_module(canonical_diff)


def _resolution(entity_scope: str, provider_id: int, canonical_id: int) -> dict:
    namespaces = {
        "match": "matches.match_id",
        "opponent_club": "clubs.club_id",
        "leeds_player": "players.player_id",
        "leeds_manager": "managers.manager_id",
        "opposition_manager": "managerial_people.managerial_person_id",
    }
    return {"status":"RESOLVED","provider":"sofascore","entity_scope":entity_scope,"provider_id":provider_id,"canonical_id":canonical_id,"canonical_namespace":namespaces[entity_scope]}


def _identity_package() -> dict:
    ids=[980643,827681,282229,1118177,929132,889861,847097,871886,834308,372344,865523,886930,973431,355528,803185,190161,906075,866191,828639,1146148]
    mapped={929132:877,871886:878}
    return {
        "status":"PASS","match":_resolution("match",16363258,4857),
        "leeds_team":{"status":"VALIDATED_PROVIDER_IDENTITY","provider":"sofascore","provider_id":34,"canonical_mapping":"NOT_APPLICABLE"},
        "opponent_club":_resolution("opponent_club",30,75),
        "leeds_players":{"status":"PASS","resolutions":[_resolution("leeds_player",pid,mapped.get(pid,10000+i)) for i,pid in enumerate(ids)]},
        "leeds_manager":_resolution("leeds_manager",265307,49),
        "opposition_manager":_resolution("opposition_manager",788529,822),
        "opposition_players":{"status":"NOT_APPLICABLE","canonical_mapping":"NOT_APPLICABLE"},
    }


def _fixture() -> dict:
    return {"event_id":16363258,"home_team_provider_id":30,"away_team_provider_id":34,"home_score":1,"away_score":1,"match_date":"2026-09-05","stadium":"American Express Stadium","attendance":31661,"referee":"Stuart Attwell","kickoff_time":"15:00","round":"3","leeds_formation":"3-5-2"}


STARTERS=[980643,827681,282229,1118177,929132,889861,847097,871886,834308,372344,865523]
USED=[886930,973431,355528,803185]
UNUSED=[190161,906075,866191,828639,1146148]


def _appearance_players() -> list[dict]:
    rows=[{"provider_player_id":pid,"started":True,"substitute":False,"source_slot":f"XI{i}"} for i,pid in enumerate(STARTERS,1)]
    rows += [{"provider_player_id":pid,"started":False,"substitute":True,"source_slot":f"SUB{i}"} for i,pid in enumerate(USED,1)]
    return rows


def _full_named_squad() -> list[dict]:
    rows=_appearance_players()
    rows += [{"provider_player_id":pid,"started":False,"substitute":True,"source_slot":f"UNUSED{i}"} for i,pid in enumerate(UNUSED,1)]
    return rows


def _subs() -> list[dict]:
    return [
        {"player_out":929132,"player_in":886930,"minute":"61"},
        {"player_out":865523,"player_in":973431,"minute":"62"},
        {"player_out":871886,"player_in":355528,"minute":"73"},
        {"player_out":372344,"player_in":803185,"minute":"73"},
    ]


def _kwargs() -> dict:
    return {
        "fixture":_fixture(),"identity_package":_identity_package(),"leeds_team_provider_id":34,
        "leeds_manager_provider_id":265307,"leeds_captain_provider_id":847097,
        "leeds_players":_appearance_players(),"leeds_substitutions":_subs(),
        "leeds_goals":[{"provider_event_id":8272133,"provider_player_id":929132,"scorer_name":"Jayden Bogle","minute_raw":"15'","minute_normalised":15,"assist_provider_player_id":871886,"assist_name":"Ao Tanaka","is_own_goal":False,"goal_type":"Corner (3rd Phase)","location":"6 Yard","body_part":"Right Foot","goal_state":"Scored","game_state":"D-W"}],
        "opposition_goals":[{"provider_event_id":8273596,"provider_player_id":1405212,"scorer_name":"Luka Vuskovic","minute_raw":"71'"}],
        "opposition_manager_provider_id":788529,"opposition_captain_provider_id":115365,"attendance_source":"BBC",
    }


def test_brighton_diff_is_read_only_and_blocks_on_explicit_schema_gaps():
    r=canonical_diff.build_proposed_canonical_diff(**_kwargs())
    assert r["status"]=="BLOCKED" and r["database_writes"]==0 and r["promotion_performed"] is False
    assert r["canonical_match_id"]==4857 and r["sofascore_event_id"]==16363258
    assert r["opposition_players_mapped_to_leeds_players"] is False


def test_brighton_regression_is_exactly_11_starters_plus_4_used_subs():
    r=canonical_diff.build_proposed_canonical_diff(**_kwargs())
    rows=[x for x in r["operations"] if x["table"]=="player_matches"]
    assert len(rows)==15
    assert sum(x["values"]["started"] is True for x in rows)==11
    assert sum(x["values"]["substitute"] is True for x in rows)==4
    proposed={x["key"]["player_id"] for x in rows}
    unused_canonical={_resolution("leeds_player",pid,10000+i)["canonical_id"] for i,pid in enumerate(UNUSED)}
    assert proposed.isdisjoint(unused_canonical)


def test_full_20_man_named_squad_is_blocked_as_appearance_population():
    k=_kwargs(); k["leeds_players"]=_full_named_squad()
    with pytest.raises(canonical_diff.CanonicalDiffError,match="exactly match proven substitution player-on population"):
        canonical_diff.build_proposed_canonical_diff(**k)


def test_missing_used_substitute_is_blocked():
    k=_kwargs(); k["leeds_players"]=_appearance_players()[:-1]
    with pytest.raises(canonical_diff.CanonicalDiffError,match="exactly match proven substitution player-on population"):
        canonical_diff.build_proposed_canonical_diff(**k)


def test_duplicate_player_on_is_blocked():
    k=_kwargs(); k["leeds_substitutions"]=_subs()+[_subs()[0]]
    with pytest.raises(canonical_diff.CanonicalDiffError,match="duplicate player-on"):
        canonical_diff.build_proposed_canonical_diff(**k)


def test_bogle_goal_uses_final_verified_taxonomy():
    r=canonical_diff.build_proposed_canonical_diff(**_kwargs())
    goal=next(x for x in r["operations"] if x["table"]=="goals")
    assert goal["values"]["leeds_player_id"]==877
    assert goal["values"]["assist_player_id"]==878
    assert goal["values"]["goal_type"]=="Corner (3rd Phase)"
    assert goal["values"]["location"]=="6 Yard"
    assert goal["values"]["body_part"]=="Right Foot"


def test_substitutions_are_exactly_four_proven_relationships():
    r=canonical_diff.build_proposed_canonical_diff(**_kwargs())
    rows=[x for x in r["operations"] if x["table"]=="match_substitutions"]
    assert len(rows)==4 and r["leeds_substitution_operation_count"]==4
    assert all(x["values"]["relationship_status"]=="proven" for x in rows)
    assert [x["values"]["minute_base"] for x in rows]==[61,62,73,73]


def test_stoppage_time_is_preserved():
    k=_kwargs(); k["leeds_players"]=_appearance_players()[:11]+[_appearance_players()[11]]
    k["leeds_substitutions"]=[{"player_out":929132,"player_in":886930,"minute_base":90,"stoppage_minute":3}]
    r=canonical_diff.build_proposed_canonical_diff(**k)
    row=next(x for x in r["operations"] if x["table"]=="match_substitutions")
    assert row["values"]["minute_raw"]=="90+3'"


def test_opposition_captain_never_requires_leeds_player_mapping():
    r=canonical_diff.build_proposed_canonical_diff(**_kwargs())
    gap=next(x for x in r["schema_gaps"] if x["field"]=="opposition captain")
    assert "must not be inserted into Leeds players" in gap["reason"]


def test_provider_event_id_never_becomes_match_id():
    r=canonical_diff.build_proposed_canonical_diff(**_kwargs())
    assert r["canonical_match_id"] != r["sofascore_event_id"]


def test_unresolved_captain_blocks():
    k=_kwargs(); k["leeds_captain_provider_id"]=999999999
    with pytest.raises(canonical_diff.CanonicalDiffError,match="exactly one Leeds player identity"):
        canonical_diff.build_proposed_canonical_diff(**k)
