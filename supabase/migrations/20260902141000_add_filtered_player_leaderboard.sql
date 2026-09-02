create or replace function public.filtered_player_leaderboard(p_filter text default 'All', p_venue text default 'All')
returns table(player_id bigint, legacy_player_id integer, player text, status text, player_position text, declared_nation text, profile_image_url text, appearances bigint, starts bigint, sub_apps bigint, goals bigint, first_match date, last_match date)
language sql
stable
as $function$
with selected_matches as (
  select mt.match_id, mt.match_date
  from public.matches mt
  left join public.competition_names cn on cn.competition_name_id = mt.competition_name_id
  where
    (p_venue = 'All' or (p_venue = 'Home' and mt.venue_type='H') or (p_venue='Away' and mt.venue_type='A') or (p_venue='Neutral' and mt.venue_type='N'))
    and (
      p_filter='All'
      or (p_filter='League' and coalesce(cn.display_name,mt.source_comp) in ('Division One','Division Two','Division Three','Championship','League One','Premier League'))
      or (p_filter='Premier League' and coalesce(cn.display_name,mt.source_comp)='Premier League')
      or (p_filter='FA Cup' and coalesce(cn.display_name,mt.source_comp)='FA Cup')
      or (p_filter='League Cup' and coalesce(cn.display_name,mt.source_comp) in ('League Cup','EFL Cup'))
      or (p_filter='Europe' and coalesce(cn.display_name,mt.source_comp) in ('European Cup','European Cup Winners Cup','European Cup Winners'' Cup','Inter-Cities Fairs Cup','UEFA Cup','UEFA Champions League','UEFA Europa League'))
    )
), apps as (
  select pm.player_id,count(*)::bigint as appearances,count(*) filter(where pm.started)::bigint as starts,count(*) filter(where pm.substitute)::bigint as sub_apps,min(sm.match_date) as first_match,max(sm.match_date) as last_match
  from public.player_matches pm join selected_matches sm on sm.match_id=pm.match_id group by pm.player_id
), scorer_goals as (
  select g.leeds_player_id as player_id,count(*)::bigint as goals from public.goals g join selected_matches sm on sm.match_id=g.match_id where g.leeds_player_id is not null and coalesce(g.is_own_goal,false)=false group by g.leeds_player_id
)
select p.player_id,p.legacy_player_id,p.display_name,p.status,p.position_group,p.declared_nation,p.profile_image_url,
       coalesce(a.appearances,0)::bigint,coalesce(a.starts,0)::bigint,coalesce(a.sub_apps,0)::bigint,coalesce(sg.goals,0)::bigint,a.first_match,a.last_match
from public.players p left join apps a on a.player_id=p.player_id left join scorer_goals sg on sg.player_id=p.player_id
where (p_filter='All' and p_venue='All') or a.appearances is not null
order by coalesce(a.appearances,0) desc,p.display_name;
$function$;
