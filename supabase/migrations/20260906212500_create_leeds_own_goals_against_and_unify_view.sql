-- Own Goals Against source: data/reference/own_goals_against_source_2026-09-06.csv
-- The 144 source rows were reconciled to canonical match_id + player_id before publication.
create table if not exists public.leeds_own_goals_against (
  own_goal_against_id bigint primary key,
  source_order integer not null unique,
  match_id integer not null references public.matches(match_id),
  scorer_player_id bigint references public.players(player_id),
  source_date date not null,
  source_season text,
  own_goal_number integer,
  scorer_raw text not null,
  opponent_raw text not null,
  minute_raw text,
  score_raw text,
  result_raw text,
  competition_raw text,
  venue_raw text,
  stadium_raw text,
  source_file text not null default 'OWN GOALS AGAINST.csv',
  provenance_note text,
  created_at timestamptz not null default now()
);
alter table public.leeds_own_goals_against enable row level security;
drop policy if exists "Public read leeds own goals against" on public.leeds_own_goals_against;
create policy "Public read leeds own goals against" on public.leeds_own_goals_against for select to anon, authenticated using (true);
grant select on public.leeds_own_goals_against to anon, authenticated;

drop view if exists public.own_goal_events;
create view public.own_goal_events as
with for_events as (
  select
    ('for-' || g.goal_id::text) as own_goal_event_id,
    'For'::text as side,
    row_number() over (order by m.match_date, coalesce(g.minute_normalised,999), g.goal_id)::integer as source_order,
    g.goal_id,
    g.match_id,
    regexp_replace(g.scorer_name_raw, '\s*\((?:[O0]\.G\.|OG)\)\s*$', '', 'i') as scorer_name,
    g.minute_raw,
    g.minute_normalised::integer as minute_normalised,
    m.match_date,
    m.season,
    m.opponent,
    m.opponent_crest_url,
    m.competition,
    m.venue_type,
    m.leeds_score,
    m.opponent_score,
    m.result,
    m.stadium,
    m.leeds_manager
  from public.goals g
  join public.match_centre_summary m on m.match_id=g.match_id
  where g.is_own_goal is true
), against_events as (
  select
    ('against-' || o.own_goal_against_id::text) as own_goal_event_id,
    'Against'::text as side,
    o.source_order,
    null::bigint as goal_id,
    o.match_id,
    coalesce(p.display_name,o.scorer_raw) as scorer_name,
    o.minute_raw,
    case
      when o.minute_raw ~ '^\d+\+\d+$' then split_part(o.minute_raw,'+',1)::integer + split_part(o.minute_raw,'+',2)::integer
      when o.minute_raw ~ '^\d+$' then o.minute_raw::integer
      else null::integer
    end as minute_normalised,
    m.match_date,
    m.season,
    m.opponent,
    m.opponent_crest_url,
    m.competition,
    m.venue_type,
    m.leeds_score,
    m.opponent_score,
    m.result,
    m.stadium,
    m.leeds_manager
  from public.leeds_own_goals_against o
  join public.match_centre_summary m on m.match_id=o.match_id
  left join public.players p on p.player_id=o.scorer_player_id
)
select * from for_events
union all
select * from against_events;
grant select on public.own_goal_events to anon, authenticated;
