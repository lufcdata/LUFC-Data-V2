from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_football_views_use_fanout_safe_career_aggregation():
    sql = (ROOT / "supabase" / "queries" / "football_views.sql").read_text(encoding="utf-8")
    assert "with apps as" in sql
    assert "goal_totals as" in sql
    assert "drop view if exists v_player_career_totals" not in sql
    assert "left join goals g on g.match_id = pm.match_id" not in sql


def test_match_context_includes_age_appearance_and_milestones():
    sql = (ROOT / "supabase" / "queries" / "football_views.sql").read_text(encoding="utf-8")
    for token in (
        "age_years",
        "appearance_number",
        "is_debut",
        "is_final_appearance",
        "appearance_milestone",
        "goal_milestone",
        "captaincy_milestone",
        "competition_appearance_number",
        "competition_appearance_milestone",
        "competition_goals_after_match",
        "competition_goal_milestone",
    ):
        assert token in sql


def test_manager_context_includes_match_and_win_milestones():
    sql = (ROOT / "supabase" / "queries" / "football_views.sql").read_text(encoding="utf-8")
    for token in (
        "v_match_manager_context",
        "manager_match_number",
        "spell_match_number",
        "manager_wins_after_match",
        "manager_match_milestone",
        "manager_win_milestone",
    ):
        assert token in sql


def test_loader_is_non_destructive_by_default_and_resets_sequences():
    source = (ROOT / "scripts" / "load_postgres.py").read_text(encoding="utf-8")
    assert 'action="store_true"' in source
    assert "if args.replace:" in source
    assert "reset_identity_sequences" in source
    assert "pg_get_serial_sequence" in source
    assert "conn.rollback()" in source


def test_executable_database_validator_protects_historical_regressions():
    source = (ROOT / "scripts" / "validate_postgres.py").read_text(encoding="utf-8")
    for token in (
        "4856",
        "58527",
        "53416",
        "5111",
        "6046",
        "3868",
        "legacy_player_id in (518,705)",
        "DATABASE LOAD V1 VALIDATION PASSED",
    ):
        assert token in source


def test_independent_intelligence_validator_protects_unique_features():
    source = (ROOT / "scripts" / "validate_historical_intelligence.py").read_text(encoding="utf-8")
    for token in (
        "Paul Reaney",
        "Norman Hunter",
        "637",
        "Gary Kelly",
        "1995-03-22",
        "2001-12-22",
        "Mark Viduka",
        "2003-08-30",
        "Marcelo Bielsa",
        "2020-07-22",
        "HISTORICAL INTELLIGENCE VALIDATION PASSED",
    ):
        assert token in source
