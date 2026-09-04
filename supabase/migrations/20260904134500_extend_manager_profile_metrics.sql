drop function if exists public.get_manager_profile_metrics(bigint);

create function public.get_manager_profile_metrics(p_manager_id bigint)
returns table(
  manager_id bigint,
  days_in_charge integer,
  players_used bigint,
  debuts_given bigint,
  clean_sheets bigint,
  opponents_faced bigint,
  opponents_defeated bigint,
  opponents_defeated_pct numeric,
  wins_at_elland_road bigint,
  league_points_won bigint
)
language sql
stable
set search_path to 'public'
as $function$
with selected_spells as (
  select ms.manager_spell_id, ms.manager_id, ms.date_joined, ms.date_left
  from public.manager_spells ms
  where ms.manager_id = p_manager_id
),
manager_matches as (
  select m.match_id, m.match_date, m.opponent_id, m.competition_id, m.result, m.opponent_score, m.stadium
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
match_metrics as (
  select
    count(*) filter (where mm.opponent_score = 0)::bigint as clean_sheets,
    count(distinct mm.opponent_id)::bigint as opponents_faced,
    count(distinct mm.opponent_id) filter (where mm.result = 'Won')::bigint as opponents_defeated,
    round(
      100.0 * count(distinct mm.opponent_id) filter (where mm.result = 'Won')
      / nullif(count(distinct mm.opponent_id),0),
      1
    ) as opponents_defeated_pct,
    count(*) filter (where mm.result = 'Won' and mm.stadium = 'Elland Road, Leeds')::bigint as wins_at_elland_road,
    coalesce(sum(
      case
        when mm.competition_id in (1,3,12,14,15) then
          case
            when mm.result = 'Won' then case when mm.match_date >= date '1981-08-29' then 3 else 2 end
            when mm.result = 'Draw' then 1
            else 0
          end
        else 0
      end
    ),0)::bigint as league_points_won
  from manager_matches mm
),
tenure as (
  select coalesce(sum((coalesce(ss.date_left, current_date) - ss.date_joined) + 1),0)::integer as days_in_charge
  from selected_spells ss
  where ss.date_joined is not null
)
select
  p_manager_id,
  tenure.days_in_charge,
  player_metrics.players_used,
  player_metrics.debuts_given,
  match_metrics.clean_sheets,
  match_metrics.opponents_faced,
  match_metrics.opponents_defeated,
  coalesce(match_metrics.opponents_defeated_pct,0),
  match_metrics.wins_at_elland_road,
  match_metrics.league_points_won
from tenure cross join player_metrics cross join match_metrics;
$function$;

grant execute on function public.get_manager_profile_metrics(bigint) to anon, authenticated;
