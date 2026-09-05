-- Restore the canonical Inter-City Fairs Cup to the Player Stats Europe grouping.
-- The 22 Sep 1971 Barcelona match is the one-off Fairs Cup Trophy Play-Off
-- (round = 'PO'), not a competitive Fairs Cup tie, so it remains outside
-- competitive European player totals.

create or replace function public.filtered_player_leaderboard(p_filter text default 'All'::text, p_venue text default 'All'::text)
returns table(player_id bigint, legacy_player_id integer, player text, status text, player_position text, declared_nation text, profile_image_url text, appearances bigint, starts bigint, sub_apps bigint, sub_off bigint, won bigint, win_pct numeric, start_pct numeric, goals bigint, gpg numeric, captain bigint, red_cards bigint, first_match date, last_match date)
language sql
stable
as $function$
with selected_matches as (
  select mt.match_id,mt.match_date,mt.result,mt.captain_player_id
  from public.matches mt
  left join public.competition_names cn on cn.competition_name_id=mt.competition_name_id
  where (p_venue='All' or (p_venue='Home' and mt.venue_type='H') or (p_venue='Away' and mt.venue_type='A') or (p_venue='Neutral' and mt.venue_type='N'))
    and (p_filter='All'
      or (p_filter='League' and coalesce(cn.display_name,mt.source_comp) in ('Division One','Division Two','Division Three','Championship','League One','Premier League'))
      or (p_filter='Premier League' and coalesce(cn.display_name,mt.source_comp)='Premier League')
      or (p_filter='FA Cup' and coalesce(cn.display_name,mt.source_comp)='FA Cup')
      or (p_filter='League Cup' and coalesce(cn.display_name,mt.source_comp) in ('League Cup','EFL Cup'))
      or (p_filter='Europe' and (
        coalesce(cn.display_name,mt.source_comp) in ('European Cup','European Cup Winners Cup','European Cup Winners'' Cup','UEFA Cup','UEFA Champions League','UEFA Europa League','Champions League')
        or (coalesce(cn.display_name,mt.source_comp)='Inter-City Fairs Cup' and coalesce(mt.round,'')<>'PO')
      )))
), apps as (
 select pm.player_id,count(*)::bigint appearances,count(*) filter(where pm.started)::bigint starts,count(*) filter(where pm.substitute)::bigint sub_apps,count(*) filter(where sm.result='Won')::bigint won,min(sm.match_date) first_match,max(sm.match_date) last_match
 from public.player_matches pm join selected_matches sm on sm.match_id=pm.match_id group by pm.player_id
), sub_offs as (
 select ms.player_off_id player_id,count(*)::bigint sub_off from public.match_substitutions ms join selected_matches sm on sm.match_id=ms.match_id where ms.player_off_id is not null group by ms.player_off_id
), scorer_goals as (
 select g.leeds_player_id player_id,count(*)::bigint goals from public.goals g join selected_matches sm on sm.match_id=g.match_id where g.leeds_player_id is not null and coalesce(g.is_own_goal,false)=false group by g.leeds_player_id
), captains as (
 select sm.captain_player_id player_id,count(*)::bigint captain from selected_matches sm where sm.captain_player_id is not null group by sm.captain_player_id
), reds as (
 select prc.player_id,count(*)::bigint red_cards from public.player_red_cards prc join selected_matches sm on sm.match_id=prc.match_id group by prc.player_id
)
select p.player_id,p.legacy_player_id,p.display_name,p.status,p.position_detail,p.declared_nation,p.profile_image_url,
 coalesce(a.appearances,0)::bigint,coalesce(a.starts,0)::bigint,coalesce(a.sub_apps,0)::bigint,coalesce(so.sub_off,0)::bigint,coalesce(a.won,0)::bigint,
 case when coalesce(a.appearances,0)>0 then round(a.won::numeric*100/a.appearances,1) else 0 end,
 case when coalesce(a.appearances,0)>0 then round(a.starts::numeric*100/a.appearances,1) else 0 end,
 coalesce(sg.goals,0)::bigint,case when coalesce(a.appearances,0)>0 then round(coalesce(sg.goals,0)::numeric/a.appearances,3) else 0 end,
 coalesce(c.captain,0)::bigint,coalesce(r.red_cards,0)::bigint,a.first_match,a.last_match
from public.players p
left join apps a on a.player_id=p.player_id
left join sub_offs so on so.player_id=p.player_id
left join scorer_goals sg on sg.player_id=p.player_id
left join captains c on c.player_id=p.player_id
left join reds r on r.player_id=p.player_id
where (p_filter='All' and p_venue='All') or a.appearances is not null
order by coalesce(a.appearances,0) desc,p.display_name;
$function$;
