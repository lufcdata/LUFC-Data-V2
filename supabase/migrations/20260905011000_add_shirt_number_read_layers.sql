create or replace view public.shirt_number_assignments as
select
  'match_worn'::text as fact_type,
  pmn.player_id,
  p.display_name as player_name,
  m.season_id,
  s.display_name as season,
  pmn.match_id,
  m.match_date,
  pmn.shirt_number as shirt_number,
  null::text as assignment_status,
  null::text as notes
from public.player_match_shirt_numbers pmn
join public.players p on p.player_id = pmn.player_id
join public.matches m on m.match_id = pmn.match_id
join public.seasons s on s.season_id = m.season_id
union all
select
  'official_squad'::text as fact_type,
  psn.player_id,
  p.display_name as player_name,
  psn.season_id,
  s.display_name as season,
  null::integer as match_id,
  null::date as match_date,
  psn.squad_number as shirt_number,
  psn.assignment_status,
  psn.notes
from public.player_season_squad_numbers psn
join public.players p on p.player_id = psn.player_id
join public.seasons s on s.season_id = psn.season_id;

comment on view public.shirt_number_assignments is 'Unified read layer for Leeds shirt-number facts. fact_type distinguishes actual match-worn numbers (1991/92-1992/93) from official season squad assignments (1993/94 onward); these semantics must not be conflated.';

create or replace function public.get_player_shirt_number_history(p_player_id bigint)
returns table(
  fact_type text,
  season_id bigint,
  season text,
  match_id integer,
  match_date date,
  shirt_number smallint,
  assignment_status text,
  notes text
)
language sql
stable
security invoker
set search_path = public
as $$
  select
    a.fact_type,
    a.season_id,
    a.season,
    a.match_id,
    a.match_date,
    a.shirt_number,
    a.assignment_status,
    a.notes
  from public.shirt_number_assignments a
  where a.player_id = p_player_id
  order by a.season_id, a.match_date nulls first, a.shirt_number nulls last;
$$;

create or replace function public.get_shirt_number_wearers(p_shirt_number smallint)
returns table(
  fact_type text,
  player_id bigint,
  player_name text,
  season_id bigint,
  season text,
  match_id integer,
  match_date date,
  assignment_status text,
  notes text
)
language sql
stable
security invoker
set search_path = public
as $$
  select
    a.fact_type,
    a.player_id,
    a.player_name,
    a.season_id,
    a.season,
    a.match_id,
    a.match_date,
    a.assignment_status,
    a.notes
  from public.shirt_number_assignments a
  where a.shirt_number = p_shirt_number
  order by a.season_id, a.match_date nulls first, a.player_id;
$$;
