-- Opposition match facts schema preview — DESIGN ONLY / DO NOT DEPLOY
-- 7 September 2026
--
-- This file intentionally lives under supabase/queries, NOT supabase/migrations.
-- It translates the reviewed opposition-goal and opposition-captain contracts into
-- reviewable SQL without authorising production DDL.
--
-- Deployment prerequisites:
--   1. explicit schema review/approval;
--   2. private ingestion provenance schema deployed and verified first;
--   3. non-production migration/restore test;
--   4. database/security advisors;
--   5. Brighton dry run proving exact reconciliation;
--   6. fresh verified rolling pre-import backup before canonical promotion.

begin;

create table if not exists public.opposition_goals (
  opposition_goal_id bigint generated always as identity primary key,
  match_id integer not null references public.matches(match_id) on delete restrict,
  sequence_in_match integer not null check (sequence_in_match > 0),
  opposition_goal_number_in_match integer not null check (opposition_goal_number_in_match > 0),
  scorer_name_raw text not null check (btrim(scorer_name_raw) <> ''),
  assist_name_raw text,
  scorer_external_identity_key text,
  assist_external_identity_key text,
  minute_raw text not null check (btrim(minute_raw) <> ''),
  minute_normalised integer not null check (minute_normalised >= 0),
  stoppage_minute integer check (stoppage_minute is null or stoppage_minute >= 0),
  period text,
  is_own_goal boolean not null default false,
  score_leeds_after integer not null check (score_leeds_after >= 0),
  score_opponent_after integer not null check (score_opponent_after >= 0),
  game_state_before text not null check (btrim(game_state_before) <> ''),
  goal_type text,
  location text,
  body_part text,
  ingestion_run_id uuid not null,
  created_at timestamptz not null default now(),
  unique (match_id, sequence_in_match),
  unique (match_id, opposition_goal_number_in_match)
);

create table if not exists public.opposition_captains (
  opposition_captain_id bigint generated always as identity primary key,
  match_id integer not null references public.matches(match_id) on delete restrict,
  captain_name_raw text not null check (btrim(captain_name_raw) <> ''),
  captain_external_identity_key text,
  ingestion_run_id uuid not null,
  created_at timestamptz not null default now(),
  unique (match_id)
);

-- The ingestion schema is deliberately referenced only after its separately reviewed
-- deployment. This preview must not be promoted before ingestion.runs exists.
alter table public.opposition_goals
  add constraint opposition_goals_ingestion_run_fk
  foreign key (ingestion_run_id)
  references ingestion.runs(ingestion_run_id)
  on delete restrict;

alter table public.opposition_captains
  add constraint opposition_captains_ingestion_run_fk
  foreign key (ingestion_run_id)
  references ingestion.runs(ingestion_run_id)
  on delete restrict;

-- Provider player/event IDs are intentionally absent from canonical ID columns.
-- They belong in the private provider-namespaced ingestion/provenance layer.
-- No opposition-player foreign key to public.players is permitted.

-- DESIGN PREVIEW SAFETY: leave the database exactly as it was if this file is
-- accidentally executed manually. A real approved migration must be generated
-- separately and must not inherit this rollback.
rollback;
