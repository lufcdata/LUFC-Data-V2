create or replace function public.get_manager_performance_radar(p_manager_id bigint)
returns table(manager_id bigint,attacking_score integer,results_score integer,defensive_score integer,achievements_score integer,discipline_score integer,personnel_score integer,longevity_score integer,goals_per_game numeric,win_rate numeric,goals_against_per_game numeric,clean_sheets_per_game numeric,honours integer,promotions integer,relegations integer,red_cards bigint,players_used bigint,days_in_charge integer)
language sql stable set search_path=public as $function$
with league_tiers as (
 select s.season_id,s.start_year,min(case c.canonical_name when 'Premier League' then 1 when 'Division One' then 1 when 'Championship' then 2 when 'Division Two' then 2 when 'League One' then 3 when 'Division Three' then 3 end) tier
 from seasons s left join matches m on m.season_id=s.season_id left join competitions c on c.competition_id=m.competition_id group by s.season_id,s.start_year
), moves as (select *,lead(tier) over(order by start_year) next_tier from league_tiers), relegation_seasons as (select season_id from moves where tier is not null and next_tier>tier),
final_league_manager as (
 select manager_id,season_id from (
  select ms.manager_id,m.season_id,row_number() over(partition by m.season_id order by m.match_date desc,m.match_id desc) rn
  from matches m join manager_spells ms on ms.manager_spell_id=m.manager_spell_id join competitions c on c.competition_id=m.competition_id
  where m.season_id in(select season_id from relegation_seasons) and c.canonical_name in('Premier League','Division One','Championship','Division Two','League One','Division Three')
 )x where rn=1
), mm as (select ms.manager_id,m.match_id,m.result,m.leeds_score,m.opponent_score from matches m join manager_spells ms on ms.manager_spell_id=m.manager_spell_id),
base as (
 select ma.manager_id,count(mm.match_id)::bigint played,coalesce(sum(mm.leeds_score),0)::numeric gf,coalesce(sum(mm.opponent_score),0)::numeric ga,count(*) filter(where mm.result='Won')::numeric wins,count(*) filter(where mm.opponent_score=0)::numeric clean_sheets,
 coalesce((select count(*) from player_red_cards pr join mm mm2 on mm2.match_id=pr.match_id where mm2.manager_id=ma.manager_id),0)::bigint red_cards,
 coalesce((select count(distinct pm.player_id) from player_matches pm join mm mm3 on mm3.match_id=pm.match_id where mm3.manager_id=ma.manager_id),0)::bigint players_used,
 coalesce((select sum((coalesce(ms.date_left,current_date)-ms.date_joined)+1)::int from manager_spells ms where ms.manager_id=ma.manager_id and ms.date_joined is not null),0)::int days_in_charge,
 coalesce((select sum(coalesce(e.club_honours,0)) from manager_spell_profile_enrichment e join manager_spells ms on ms.manager_spell_id=e.manager_spell_id where ms.manager_id=ma.manager_id),0)::int honours,
 coalesce((select sum(coalesce(e.promotions,0)) from manager_spell_profile_enrichment e join manager_spells ms on ms.manager_spell_id=e.manager_spell_id where ms.manager_id=ma.manager_id),0)::int promotions,
 coalesce((select count(*) from final_league_manager f where f.manager_id=ma.manager_id),0)::int relegations
 from managers ma left join mm on mm.manager_id=ma.manager_id group by ma.manager_id
), club as (select sum(gf)/greatest(sum(played),1) avg_gf,sum(ga)/greatest(sum(played),1) avg_ga,sum(wins)/greatest(sum(played),1) avg_win,sum(clean_sheets)/greatest(sum(played),1) avg_cs,sum(red_cards)::numeric/greatest(sum(played),1) avg_red from base),
adj as (select b.*,(gf+c.avg_gf*10)/(played+10) agf,(ga+c.avg_ga*10)/(played+10) aga,(wins+c.avg_win*10)/(played+10) awin,(clean_sheets+c.avg_cs*10)/(played+10) acs,(red_cards+c.avg_red*20)/(played+20) ared,(honours*5+promotions*3-relegations*10)::numeric achievement_points from base b cross join club c),
ranked as (select a.*,round(100*percent_rank() over(order by agf))::int attacking_score,round(100*percent_rank() over(order by awin))::int results_score,round(50*percent_rank() over(order by aga desc)+50*percent_rank() over(order by acs))::int defensive_score,round(100*percent_rank() over(order by achievement_points))::int achievements_score,round(100*percent_rank() over(order by ared desc))::int discipline_score,round(100*percent_rank() over(order by players_used))::int personnel_score,round(100*percent_rank() over(order by days_in_charge))::int longevity_score from adj a)
select manager_id,attacking_score,results_score,defensive_score,achievements_score,discipline_score,personnel_score,longevity_score,round(gf/nullif(played,0),2),round(100*wins/nullif(played,0),1),round(ga/nullif(played,0),2),round(clean_sheets/nullif(played,0),3),honours,promotions,relegations,red_cards,players_used,days_in_charge from ranked where manager_id=p_manager_id;
$function$;
grant execute on function public.get_manager_performance_radar(bigint) to anon,authenticated;
