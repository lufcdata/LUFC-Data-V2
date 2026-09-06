from pathlib import Path


STAT_PACK = Path(__file__).parents[1] / "frontend" / "src" / "StatPack.tsx"


def stat_pack_source() -> str:
    return STAT_PACK.read_text(encoding="utf-8")


def test_manager_and_captain_resolve_from_selected_fixture_season():
    source = stat_pack_source()

    assert "find(m=>m.season===fixtureSeason&&m.leeds_manager)" in source
    assert "find(m=>m.season===fixtureSeason&&m.captain_player_id)" in source
    assert "find(m=>m.leeds_manager)?.leeds_manager" not in source
    assert "find(m=>m.captain_player_id)?.captain_player_id" not in source


def test_date_dependent_scenarios_remain_suppressed_without_fixture_date():
    source = stat_pack_source()

    assert "if(false&&current){const cy=yr(current.match_date)" in source
    assert "if(false&&current&&fixtureCompetition==='Premier League')" in source
