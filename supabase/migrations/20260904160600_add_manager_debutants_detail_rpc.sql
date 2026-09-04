create or replace function public.get_manager_debutants_detail(p_manager_id bigint)
returns table(
  debut_number integer,
  match_id integer,
  match_date date,
  player_id bigint,
  player_name text,
  player_profile_image_url text,
  opponent_id bigint,
  opponent_name text,
  opponent_crest_url text,
  leeds_score smallint,
  opponent_score smallint,
  result text,
  venue_type text,
  competition text,
  started boolean,
  substitute boolean,
  age_years integer,
  age_days integer,
  declared_nation text,
  scored boolean,
  sent_off boolean
)
language sql
stable
set search_path to public
as $function$
with first_apps as (
  select pm.player_id,pm.match_id,pm.started,pm.substitute,pm.lineup_order,m.match_date,
         row_number() over(partition by pm.player_id order by m.match_date,m.match_id) as player_app_rank
  from public.player_matches pm
  join public.matches m on m.match_id=pm.match_id
), manager_debuts as (
  select fa.*,m.opponent_id,m.leeds_score,m.opponent_score,m.result,m.venue_type,m.competition_id,m.competition_name_id,
         row_number() over(order by fa.match_date,fa.match_id,coalesce(fa.lineup_order,99),fa.player_id)::int as debut_number
  from first_apps fa
  join public.matches m on m.match_id=fa.match_id
  join public.manager_spells ms on ms.manager_spell_id=m.manager_spell_id
  where fa.player_app_rank=1 and ms.manager_id=p_manager_id
), goal_flags as (
  select g.match_id,g.leeds_player_id player_id,true as scored
  from public.goals g
  where g.leeds_player_id is not null and coalesce(g.is_own_goal,false)=false
  group by g.match_id,g.leeds_player_id
), red_flags as (
  select prc.match_id,prc.player_id,true as sent_off
  from public.player_red_cards prc
  where prc.player_id is not null
  group by prc.match_id,prc.player_id
)
select md.debut_number,md.match_id,md.match_date,p.player_id,p.display_name,p.profile_image_url,
       c.club_id,coalesce(c.display_name,c.canonical_name),c.crest_url,
       md.leeds_score,md.opponent_score,md.result,md.venue_type,
       coalesce(cn.display_name,comp.canonical_name,md.competition_id::text),
       md.started,md.substitute,
       case when p.date_of_birth is not null and p.birth_date_precision='exact' then extract(year from age(md.match_date,p.date_of_birth))::int end as age_years,
       case when p.date_of_birth is not null and p.birth_date_precision='exact' then (md.match_date - (p.date_of_birth + make_interval(years=>extract(year from age(md.match_date,p.date_of_birth))::int))::date)::int end as age_days,
       p.declared_nation,
       coalesce(gf.scored,false),coalesce(rf.sent_off,false)
from manager_debuts md
join public.players p on p.player_id=md.player_id
join public.clubs c on c.club_id=md.opponent_id
left join public.competition_names cn on cn.competition_name_id=md.competition_name_id
left join public.competitions comp on comp.competition_id=md.competition_id
left join goal_flags gf on gf.match_id=md.match_id and gf.player_id=md.player_id
left join red_flags rf on rf.match_id=md.match_id and rf.player_id=md.player_id
order by md.debut_number;
$function$;
grant execute on function public.get_manager_debutants_detail(bigint) to anon,authenticated;
