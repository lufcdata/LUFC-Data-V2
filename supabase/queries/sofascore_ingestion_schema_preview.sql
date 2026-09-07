-- SofaScore ingestion schema preview — DESIGN ONLY / DO NOT DEPLOY
-- 7 September 2026
--
-- This file intentionally lives under supabase/queries, NOT supabase/migrations.
-- It is a reviewable SQL contract for the private operational ingestion layer.
-- Production DDL is not authorised by this file.
--
-- Deployment prerequisites:
--   1. explicit schema review/approval;
--   2. non-production migration test;
--   3. database/security advisors;
--   4. verified Brighton dry run;
--   5. fresh verified rolling pre-import backup before canonical promotion.

begin;

create schema if not exists ingestion;

-- Keep operational ingestion data outside the public Data API surface.
revoke all on schema ingestion from anon, authenticated;

do $$
begin
  if not exists (select 1 from pg_type t join pg_namespace n on n.oid=t.typnamespace where n.nspname='ingestion' and t.typname='run_status') then
    create type ingestion.run_status as enum ('CAPTURED','VALIDATING','BLOCKED','READY_FOR_PROMOTION','PROMOTED','ROLLED_BACK');
  end if;
end $$;

create table if not exists ingestion.runs (
  ingestion_run_id uuid primary key,
  provider text not null check (provider <> ''),
  provider_event_id text not null check (provider_event_id <> ''),
  status ingestion.run_status not null default 'CAPTURED',
  importer_git_sha text not null check (importer_git_sha <> ''),
  started_at timestamptz not null default now(),
  captured_at timestamptz,
  validated_at timestamptz,
  promoted_at timestamptz,
  canonical_match_id integer references public.matches(match_id) on delete restrict,
  database_writes integer not null default 0 check (database_writes >= 0),
  unique (provider, provider_event_id, importer_git_sha, started_at)
);

-- At most one promoted run may claim a provider event. Historical blocked/retried
-- captures remain immutable and auditable.
create unique index if not exists ingestion_one_promoted_provider_event
  on ingestion.runs (provider, provider_event_id)
  where status = 'PROMOTED';

create table if not exists ingestion.raw_payloads (
  raw_payload_id uuid primary key,
  ingestion_run_id uuid not null references ingestion.runs(ingestion_run_id) on delete restrict,
  provider text not null,
  endpoint_family text not null,
  source_url text,
  captured_at timestamptz not null,
  sha256 text not null check (sha256 ~ '^[0-9a-f]{64}$'),
  payload_json jsonb,
  payload_path text,
  http_status integer,
  capture_status text not null,
  unique (ingestion_run_id, endpoint_family, sha256),
  check (payload_json is not null or payload_path is not null)
);

create table if not exists ingestion.external_identity_mappings (
  external_identity_mapping_id bigint generated always as identity primary key,
  provider text not null,
  entity_scope text not null check (entity_scope in ('match','opponent_club','leeds_player','leeds_manager','opposition_manager')),
  provider_id text not null,
  canonical_namespace text,
  canonical_id bigint,
  mapping_status text not null check (mapping_status in ('CONFIRMED','PROPOSED','REJECTED','NOT_APPLICABLE')),
  evidence_note text,
  confirmed_at timestamptz,
  check (
    (mapping_status = 'CONFIRMED' and canonical_namespace is not null and canonical_id is not null)
    or mapping_status <> 'CONFIRMED'
  )
);

create unique index if not exists ingestion_confirmed_external_identity
  on ingestion.external_identity_mappings(provider, entity_scope, provider_id)
  where mapping_status = 'CONFIRMED';

create table if not exists ingestion.field_provenance (
  field_provenance_id bigint generated always as identity primary key,
  ingestion_run_id uuid not null references ingestion.runs(ingestion_run_id) on delete restrict,
  domain text not null,
  record_key text not null,
  field_name text not null,
  value_json jsonb not null,
  source_provider text not null,
  raw_payload_id uuid references ingestion.raw_payloads(raw_payload_id) on delete restrict,
  source_url text,
  authority text not null check (authority in ('PRIMARY','SECONDARY','DERIVED')),
  validation_status text not null,
  resolution_note text
);

create table if not exists ingestion.validation_results (
  validation_result_id bigint generated always as identity primary key,
  ingestion_run_id uuid not null references ingestion.runs(ingestion_run_id) on delete restrict,
  gate_name text not null,
  status text not null check (status in ('PASS','VALIDATED','RESOLVED','NOT_APPLICABLE','BLOCKED')),
  details_json jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  unique (ingestion_run_id, gate_name)
);

create table if not exists ingestion.staged_events (
  staged_event_id uuid primary key,
  ingestion_run_id uuid not null references ingestion.runs(ingestion_run_id) on delete restrict,
  provider text not null,
  provider_event_id text,
  event_kind text not null check (event_kind in ('goal','shot','substitution','card','penalty','own_goal','period','other')),
  team_side text not null check (team_side in ('LEEDS','OPPONENT')),
  provider_team_id text not null,
  provider_player_id text,
  provider_secondary_player_id text,
  minute_base integer,
  stoppage_minute integer,
  period text,
  sequence_index integer not null check (sequence_index >= 0),
  event_json jsonb not null,
  canonical_destination text,
  promotion_status text not null default 'STAGED' check (promotion_status in ('STAGED','ELIGIBLE','SCHEMA_GAP','PROMOTED')),
  unique (ingestion_run_id, sequence_index),
  check (minute_base is null or minute_base >= 0),
  check (stoppage_minute is null or stoppage_minute >= 0)
);

create table if not exists ingestion.proposed_changes (
  proposed_change_id uuid primary key,
  ingestion_run_id uuid not null references ingestion.runs(ingestion_run_id) on delete restrict,
  sequence_index integer not null check (sequence_index >= 0),
  target_table text not null,
  operation text not null check (operation in ('INSERT','UPDATE')),
  canonical_key_json jsonb not null,
  before_json jsonb,
  after_json jsonb not null,
  status text not null default 'PROPOSED' check (status in ('PROPOSED','BLOCKED','APPROVED','APPLIED','VERIFIED','ROLLED_BACK')),
  blocker_reason text,
  unique (ingestion_run_id, sequence_index)
);

create table if not exists ingestion.backup_manifests (
  backup_manifest_id uuid primary key,
  ingestion_run_id uuid not null unique references ingestion.runs(ingestion_run_id) on delete restrict,
  backup_path text not null,
  sha256 text not null check (sha256 ~ '^[0-9a-f]{64}$'),
  created_at timestamptz not null,
  verified_at timestamptz,
  verification_status text not null,
  rollback_manifest_json jsonb not null,
  retention_class text not null check (retention_class = 'ROLLING_14_DAY'),
  expires_at timestamptz not null,
  check (expires_at > created_at)
);

-- Operational tables are service-side only. Do not grant client roles.
revoke all on all tables in schema ingestion from anon, authenticated;
revoke all on all sequences in schema ingestion from anon, authenticated;

-- DESIGN PREVIEW SAFETY: leave the database exactly as it was if this file is
-- accidentally executed manually. A real approved migration must be generated
-- separately and must not inherit this rollback.
rollback;
