create or replace function public.get_manager_profile_breakdowns(p_manager_id bigint)
returns table(category text, entity_type text, entity_id bigint, label text, value bigint, secondary text, rank_order integer)
language sql
stable
set search_path to 'public'
as $function$
with manager_matches as (
  select m.match_id,m.match_date,m.opponent_id,m.result,m.leeds_score,m.opponent_score
  from public.matches m
  join public.manager_spells ms on ms.manager_spell_id=m.manager_spell_id
  where ms.manager_id=p_manager_id
), opponent_stats as (
  select mm.opponent_id,c.display_name,
         count(*)::bigint matches,
         count(*) filter(where mm.result='Won')::bigint wins,
         count(*) filter(where mm.result='Lost')::bigint defeats,
         coalesce(sum(mm.leeds_score),0)::bigint goals_for,
         coalesce(sum(mm.opponent_score),0)::bigint goals_against
  from manager_matches mm
  join public.clubs c on c.club_id=mm.opponent_id
  group by mm.opponent_id,c.display_name
), player_apps as (
  select pm.player_id,p.display_name,count(*)::bigint apps
  from public.player_matches pm
  join manager_matches mm on mm.match_id=pm.match_id
  join public.players p on p.player_id=pm.player_id
  group by pm.player_id,p.display_name
), player_goals as (
  select g.leeds_player_id player_id,p.display_name,count(*)::bigint goals
  from public.goals g
  join manager_matches mm on mm.match_id=g.match_id
  join public.players p on p.player_id=g.leeds_player_id
  where g.leeds_player_id is not null and coalesce(g.is_own_goal,false)=false
  group by g.leeds_player_id,p.display_name
), player_assists as (
  select g.assist_player_id player_id,p.display_name,count(*)::bigint assists
  from public.goals g
  join manager_matches mm on mm.match_id=g.match_id
  join public.players p on p.player_id=g.assist_player_id
  where g.assist_player_id is not null and coalesce(g.is_own_goal,false)=false
  group by g.assist_player_id,p.display_name
), first_apps as (
  select player_id,match_id,match_date from (
    select pm.player_id,pm.match_id,m.match_date,
           row_number() over(partition by pm.player_id order by m.match_date,m.match_id) rn
    from public.player_matches pm
    join public.matches m on m.match_id=pm.match_id
  ) x where rn=1
), debutants as (
  select fa.player_id,p.display_name,fa.match_date,coalesce(pa.apps,0)::bigint manager_apps
  from first_apps fa
  join manager_matches mm on mm.match_id=fa.match_id
  join public.players p on p.player_id=fa.player_id
  left join player_apps pa on pa.player_id=fa.player_id
), rows as (
  select 'Opponents Faced'::text category,'club'::text entity_type,opponent_id::bigint entity_id,display_name label,matches value,
         (wins||' wins · '||defeats||' defeats')::text secondary,
         row_number() over(order by matches desc,display_name)::int rank_order from opponent_stats
  union all
  select 'Most Wins','club',opponent_id,display_name,wins,(matches||' matches')::text,row_number() over(order by wins desc,matches desc,display_name)::int from opponent_stats where wins>0
  union all
  select 'Most Defeats','club',opponent_id,display_name,defeats,(matches||' matches')::text,row_number() over(order by defeats desc,matches desc,display_name)::int from opponent_stats where defeats>0
  union all
  select 'Most Goals Against','club',opponent_id,display_name,goals_for,(matches||' matches')::text,row_number() over(order by goals_for desc,matches desc,display_name)::int from opponent_stats where goals_for>0
  union all
  select 'Most Conceded Against','club',opponent_id,display_name,goals_against,(matches||' matches')::text,row_number() over(order by goals_against desc,matches desc,display_name)::int from opponent_stats where goals_against>0
  union all
  select 'Top Appearances','player',player_id,display_name,apps,'appearances under manager',row_number() over(order by apps desc,display_name)::int from player_apps
  union all
  select 'Top Goalscorers','player',player_id,display_name,goals,'goals under manager',row_number() over(order by goals desc,display_name)::int from player_goals
  union all
  select 'Top Assists','player',player_id,display_name,assists,'recorded assists under manager',row_number() over(order by assists desc,display_name)::int from player_assists
  union all
  select 'Debutants','player',player_id,display_name,manager_apps,('Leeds debut '||to_char(match_date,'DD Mon YYYY'))::text,row_number() over(order by manager_apps desc,match_date,display_name)::int from debutants
)
select category,entity_type,entity_id,label,value,secondary,rank_order
from rows
order by case category
  when 'Opponents Faced' then 1 when 'Most Wins' then 2 when 'Most Defeats' then 3 when 'Most Goals Against' then 4 when 'Most Conceded Against' then 5 when 'Top Appearances' then 6 when 'Top Goalscorers' then 7 when 'Top Assists' then 8 when 'Debutants' then 9 else 99 end,rank_order;
$function$;

grant execute on function public.get_manager_profile_breakdowns(bigint) to anon, authenticated;
