from pathlib import Path


ROOT = Path(__file__).parents[1]
STAT_PACK = ROOT / "frontend" / "src" / "StatPack.tsx"
FIXTURE_SCOPE = ROOT / "frontend" / "src" / "statPackFixtureScope.ts"
YORKSHIRE_DERBY = ROOT / "frontend" / "src" / "statPackYorkshireDerby.ts"
STADIUM_IDENTITY = ROOT / "frontend" / "src" / "stadiumIdentity.ts"


def source(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_manager_and_captain_resolve_from_selected_fixture_season():
    stat_pack = source(STAT_PACK)

    assert "find(m=>m.season===fixtureSeason&&m.leeds_manager)" in stat_pack
    assert "find(m=>m.season===fixtureSeason&&m.captain_player_id)" in stat_pack
    assert "find(m=>m.leeds_manager)?.leeds_manager" not in stat_pack
    assert "find(m=>m.captain_player_id)?.captain_player_id" not in stat_pack


def test_date_dependent_scenarios_remain_suppressed_without_fixture_date():
    stat_pack = source(STAT_PACK)

    assert "if(false&&current){const cy=yr(current.match_date)" in stat_pack
    assert "if(false&&current&&fixtureCompetition==='Premier League')" in stat_pack


def test_live_archive_end_scenarios_require_current_fixture_season():
    stat_pack = source(STAT_PACK)

    assert "if(LEAGUE.has(fixtureCompetition)&&fixtureSeason===current?.season)for(const s of seq)" in stat_pack
    assert stat_pack.count("if(manager&&LEAGUE.has(fixtureCompetition)&&fixtureSeason===current?.season)") == 2
    assert stat_pack.count("if(fixtureSeason===current?.season)for(const pid of activeIds)") == 3
    assert "if(fixtureSeason===current?.season&&currentCaptain&&activeIds.includes(currentCaptain))" in stat_pack
    assert "if(fixtureCompetition==='Premier League'&&fixtureSeason===current?.season)for(const p of keepers.filter(p=>p.active))" in stat_pack
    assert "if(fixtureCompetition==='Premier League'&&fixtureSeason===current?.season)for(const pid of activeIds)" in stat_pack
    assert "if(manager&&LEAGUE.has(fixtureCompetition)){" not in stat_pack


def test_exact_fixture_scope_has_one_canonical_predicate():
    fixture_scope = source(FIXTURE_SCOPE)

    assert "return matches.filter(match=>isExactFixtureScope(match,fixture));" in fixture_scope
    assert fixture_scope.count("match.opponent===fixture.opponent") == 1
    assert fixture_scope.count("match.competition===fixture.competition") == 1
    assert fixture_scope.count("match.venue_type===fixture.venue") == 1


def test_locked_context_populations_are_immutable():
    yorkshire_derby = source(YORKSHIRE_DERBY)
    stadium_identity = source(STADIUM_IDENTITY)

    assert "YORKSHIRE_DERBY_OPPONENTS:ReadonlySet<string>" in yorkshire_derby
    assert "STADIUM_ALIASES:Readonly<Record<string,string>>=Object.freeze({" in stadium_identity
