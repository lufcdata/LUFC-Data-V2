create or replace function public.get_manager_profile_metrics(p_manager_id bigint)
returns table (
  manager_id bigint,
  days_in_charge integer,
  players_used bigint,
  debuts_given bigint
)
language sql
stable
security invoker
set search_path = public
as $$
with selected_spells as (
  select ms.manager_spell_id, ms.manager_id, ms.date_joined, ms.date_left
  from public.manager_spells ms
  where ms.manager_id = p_manager_id
),
manager_matches as (
  select m.match_id, m.match_date
  from public.matches m
  join selected_spells ss on ss.manager_spell_id = m.manager_spell_id
),
first_apps as (
  select ranked.player_id, ranked.match_id as first_match_id
  from (
    select pm.player_id, pm.match_id,
           row_number() over (partition by pm.player_id order by m.match_date, pm.match_id) as rn
    from public.player_matches pm
    join public.matches m on m.match_id = pm.match_id
  ) ranked
  where ranked.rn = 1
),
player_metrics as (
  select
    count(distinct pm.player_id)::bigint as players_used,
    count(distinct fa.player_id)::bigint as debuts_given
  from manager_matches mm
  left join public.player_matches pm on pm.match_id = mm.match_id
  left join first_apps fa on fa.first_match_id = mm.match_id
),
tenure as (
  select coalesce(sum((coalesce(ss.date_left, current_date) - ss.date_joined) + 1),0)::integer as days_in_charge
  from selected_spells ss
  where ss.date_joined is not null
)
select p_manager_id, tenure.days_in_charge, player_metrics.players_used, player_metrics.debuts_given
from tenure cross join player_metrics;
$$;

grant execute on function public.get_manager_profile_metrics(bigint) to anon, authenticated;
