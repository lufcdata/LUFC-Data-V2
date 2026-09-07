from pathlib import Path


SQL_PATH = Path(__file__).resolve().parents[1] / "supabase" / "queries" / "sofascore_ingestion_schema_preview.sql"


def _sql() -> str:
    return SQL_PATH.read_text(encoding="utf-8")


def _sql_without_comments() -> str:
    """Return executable SQL text with line comments removed.

    Privacy assertions must inspect statements, not prose such as
    "do not grant client roles" in a safety comment.
    """
    lines = []
    for line in _sql().splitlines():
        statement = line.split("--", 1)[0]
        if statement.strip():
            lines.append(statement)
    return "\n".join(lines)


def test_preview_is_not_a_migration_and_rolls_back_if_executed():
    sql = _sql().lower()
    assert "design only / do not deploy" in sql
    assert "begin;" in sql
    assert sql.rstrip().endswith("rollback;")
    assert "supabase/migrations" in sql


def test_ingestion_layer_is_private_from_client_roles():
    sql = _sql().lower()
    executable_sql = _sql_without_comments().lower()
    assert "create schema if not exists ingestion" in sql
    assert "revoke all on schema ingestion from anon, authenticated" in sql
    assert "revoke all on all tables in schema ingestion from anon, authenticated" in sql
    assert "revoke all on all sequences in schema ingestion from anon, authenticated" in sql
    assert "grant" not in executable_sql


def test_provider_identity_is_namespaced_and_never_a_canonical_primary_key():
    sql = _sql().lower()
    assert "external_identity_mappings" in sql
    assert "provider_event_id text not null" in sql
    assert "canonical_namespace text" in sql
    assert "canonical_id bigint" in sql
    assert "external_identity_mapping_id bigint generated always as identity primary key" in sql
    assert "provider_event_id integer primary key" not in sql
    assert "provider_id bigint primary key" not in sql


def test_lufc_scoped_identity_contract_is_encoded():
    sql = _sql()
    for scope in ("match", "opponent_club", "leeds_player", "leeds_manager", "opposition_manager"):
        assert f"'{scope}'" in sql
    # Opposition players are deliberately absent: they cannot contaminate Leeds players.
    assert "'opposition_player'" not in sql


def test_brighton_provenance_and_external_event_blockers_have_real_destinations():
    sql = _sql().lower()
    assert "create table if not exists ingestion.field_provenance" in sql
    assert "source_provider text not null" in sql
    assert "authority text not null" in sql
    assert "secondary" in sql
    assert "create table if not exists ingestion.runs" in sql
    assert "provider_event_id text not null" in sql
    assert "ingestion_one_promoted_provider_event" in sql


def test_golden_backup_can_never_enter_routine_ingestion_retention_class():
    sql = _sql()
    assert "retention_class = 'ROLLING_14_DAY'" in sql
    assert "GOLDEN" not in sql.split("create table if not exists ingestion.backup_manifests", 1)[1].split("-- Operational tables", 1)[0]
