-- Complete the shirt-number provenance layer so every raw source row can be
-- resolved to canonical IDs without overwriting the original source payload.

alter table public.shirt_number_source_rows
  add column if not exists source_file_name text,
  add column if not exists source_row_number integer,
  add column if not exists player_id bigint references public.players(player_id) on delete restrict,
  add column if not exists match_id bigint references public.matches(match_id) on delete restrict,
  add column if not exists season_id bigint references public.seasons(season_id) on delete restrict,
  add column if not exists resolution_status text,
  add column if not exists resolution_notes text;

create unique index if not exists shirt_number_source_rows_file_row_uidx
  on public.shirt_number_source_rows(source_file_name, source_row_number)
  where source_file_name is not null and source_row_number is not null;
create index if not exists shirt_number_source_rows_match_idx
  on public.shirt_number_source_rows(match_id);
create index if not exists shirt_number_source_rows_resolution_idx
  on public.shirt_number_source_rows(resolution_status);

comment on column public.shirt_number_source_rows.source_payload is
  'Raw source row preserved as JSON. Canonical resolution fields are stored separately.';
comment on column public.shirt_number_source_rows.resolution_status is
  'Resolution outcome, e.g. resolved_canonical, excluded_noncanonical_player, supplemental_verified.';
