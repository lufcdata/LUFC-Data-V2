from pathlib import Path
import re


SQL_PATH = Path(__file__).resolve().parents[1] / "supabase" / "queries" / "sofascore_opposition_match_facts_schema_preview.sql"
MIGRATIONS_PATH = Path(__file__).resolve().parents[1] / "supabase" / "migrations"


def _sql() -> str:
    return SQL_PATH.read_text(encoding="utf-8")


def _without_line_comments(sql: str) -> str:
    return "\n".join(line.split("--", 1)[0] for line in sql.splitlines())


def test_preview_is_non_deployable_and_rollback_protected():
    sql = _sql()
    executable = _without_line_comments(sql).strip().lower()
    assert "design only / do not deploy" in sql.lower()
    assert executable.startswith("begin;")
    assert executable.endswith("rollback;")
    assert SQL_PATH.parent.name == "queries"
    assert not (MIGRATIONS_PATH / SQL_PATH.name).exists()


def test_preview_creates_only_purpose_built_opposition_populations():
    sql = _without_line_comments(_sql()).lower()
    assert "create table if not exists public.opposition_goals" in sql
    assert "create table if not exists public.opposition_captains" in sql
    assert "create table if not exists public.players" not in sql
    assert "alter table public.players" not in sql


def test_opposition_goals_preserve_match_sequence_and_uniqueness():
    sql = _without_line_comments(_sql()).lower()
    assert "sequence_in_match integer not null" in sql
    assert "opposition_goal_number_in_match integer not null" in sql
    assert "unique (match_id, sequence_in_match)" in sql
    assert "unique (match_id, opposition_goal_number_in_match)" in sql
    assert "scorer_name_raw text not null" in sql
    assert "score_leeds_after integer not null" in sql
    assert "score_opponent_after integer not null" in sql
    assert "game_state_before text not null" in sql


def test_opposition_captain_is_exactly_one_fixture_fact_per_match():
    sql = _without_line_comments(_sql()).lower()
    captain_block = sql.split("create table if not exists public.opposition_captains", 1)[1].split(");", 1)[0]
    assert "captain_name_raw text not null" in captain_block
    assert "unique (match_id)" in captain_block
    assert "player_id" not in captain_block


def test_canonical_primary_keys_are_generated_and_never_provider_ids():
    sql = _without_line_comments(_sql()).lower()
    assert "opposition_goal_id bigint generated always as identity primary key" in sql
    assert "opposition_captain_id bigint generated always as identity primary key" in sql
    assert "sofascore" not in sql
    assert "provider_player_id" not in sql
    assert "provider_event_id" not in sql


def test_both_populations_require_private_ingestion_run_provenance():
    sql = _without_line_comments(_sql()).lower()
    assert sql.count("ingestion_run_id uuid not null") == 2
    assert "foreign key (ingestion_run_id)\n  references ingestion.runs(ingestion_run_id)" in sql
    assert sql.count("references ingestion.runs(ingestion_run_id)") == 2


def test_no_opposition_player_foreign_key_can_target_leeds_players():
    sql = _without_line_comments(_sql()).lower()
    assert "references public.players" not in sql
    assert "references players" not in sql
    assert not re.search(r"\b(leeds_)?player_id\b", sql)
