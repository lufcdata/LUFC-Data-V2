drop function if exists public.get_manager_performance_radar(bigint);

create function public.get_manager_performance_radar(p_manager_id bigint)
returns table(
  manager_id bigint,
  attacking_score integer,
  results_score integer,
  defensive_score integer,
  achievements_score integer,
  discipline_score integer,
  personnel_score integer,
  longevity_score integer,
  avg_attacking_score integer,
  avg_results_score integer,
  avg_defensive_score integer,
  avg_achievements_score integer,
  avg_discipline_score integer,
  avg_personnel_score integer,
  avg_longevity_score integer,
  goals_per_game numeric,
  win_rate numeric,
  goals_against_per_game numeric,
  clean_sheets_per_game numeric,
  honours integer,
  promotions integer,
  relegations integer,
  red_cards bigint,
  red_cards_per_game numeric,
  players_used bigint,
  seasons integer,
  players_per_season numeric,
  days_in_charge integer,
  top_flight_titles integer
)
language sql
stable
set search_path to 'public'
as $function$
with league_tiers as (
  select s.season_id,s.start_year,
    min(case c.canonical_name
      when 'Premier League' then 1
      when 'Division One' then 1
      when 'Championship' then 2
      when 'Division Two' then 2
      when 'League One' then 3
      when 'Division Three' then 3
    end) tier
  from seasons s
  left join matches m on m.season_id=s.season_id
  left join competitions c on c.competition_id=m.competition_id
  group by s.season_id,s.start_year
), moves as (
  select *,lead(tier) over(order by start_year) next_tier from league_tiers
), relegation_seasons as (
  select season_id from moves where tier is not null and next_tier>tier
), final_league_manager as (
  select manager_id,season_id from (
    select ms.manager_id,m.season_id,
      row_number() over(partition by m.season_id order by m.match_date desc,m.match_id desc) rn
    from matches m
    join manager_spells ms on ms.manager_spell_id=m.manager_spell_id
    join competitions c on c.competition_id=m.competition_id
    where m.season_id in(select season_id from relegation_seasons)
      and c.canonical_name in('Premier League','Division One','Championship','Division Two','League One','Division Three')
  ) x where rn=1
), mm as (
  select ms.manager_id,m.match_id,m.season_id,m.result,m.leeds_score,m.opponent_score
  from matches m
  join manager_spells ms on ms.manager_spell_id=m.manager_spell_id
), base as (
  select ma.manager_id,
    count(mm.match_id)::bigint played,
    count(distinct mm.season_id)::int seasons,
    coalesce(sum(mm.leeds_score),0)::numeric gf,
    coalesce(sum(mm.opponent_score),0)::numeric ga,
    count(*) filter(where mm.result='Won')::numeric wins,
    count(*) filter(where mm.opponent_score=0)::numeric clean_sheets,
    coalesce((select count(*) from player_red_cards pr join mm mm2 on mm2.match_id=pr.match_id where mm2.manager_id=ma.manager_id),0)::bigint red_cards,
    coalesce((select count(distinct pm.player_id) from player_matches pm join mm mm3 on mm3.match_id=pm.match_id where mm3.manager_id=ma.manager_id),0)::bigint players_used,
    coalesce((select sum((coalesce(ms.date_left,current_date)-ms.date_joined)+1)::int from manager_spells ms where ms.manager_id=ma.manager_id and ms.date_joined is not null),0)::int days_in_charge,
    coalesce((select sum(coalesce(e.club_honours,0)) from manager_spell_profile_enrichment e join manager_spells ms on ms.manager_spell_id=e.manager_spell_id where ms.manager_id=ma.manager_id),0)::int honours,
    coalesce((select sum(coalesce(e.promotions,0)) from manager_spell_profile_enrichment e join manager_spells ms on ms.manager_spell_id=e.manager_spell_id where ms.manager_id=ma.manager_id),0)::int promotions,
    coalesce((select count(*) from final_league_manager f where f.manager_id=ma.manager_id),0)::int relegations,
    coalesce((select sum(
      ((length(lower(coalesce(e.achievements,'')))-length(replace(lower(coalesce(e.achievements,'')),'division one winners','')))/length('division one winners'))
      +((length(lower(coalesce(e.achievements,'')))-length(replace(lower(coalesce(e.achievements,'')),'premier league winners','')))/length('premier league winners'))
    ) from manager_spell_profile_enrichment e join manager_spells ms on ms.manager_spell_id=e.manager_spell_id where ms.manager_id=ma.manager_id),0)::int top_flight_titles
  from managers ma
  left join mm on mm.manager_id=ma.manager_id
  group by ma.manager_id
), club as (
  select sum(gf)/greatest(sum(played),1) avg_gf,
    sum(ga)/greatest(sum(played),1) avg_ga,
    sum(wins)/greatest(sum(played),1) avg_win,
    sum(clean_sheets)/greatest(sum(played),1) avg_cs,
    sum(red_cards)::numeric/greatest(sum(played),1) avg_red
  from base
), adj as (
  select b.*,
    (gf+c.avg_gf*10)/(played+10) agf,
    (ga+c.avg_ga*10)/(played+10) aga,
    (wins+c.avg_win*10)/(played+10) awin,
    (clean_sheets+c.avg_cs*10)/(played+10) acs,
    (red_cards+c.avg_red*20)/(played+20) ared_rate,
    players_used::numeric/nullif(seasons,0) players_per_season,
    ((honours*5+promotions*3-relegations*12)::numeric/nullif(sqrt(greatest(seasons,1)::numeric),0)) achievement_efficiency
  from base b cross join club c
), ranked as (
  select a.*,
    round(94*percent_rank() over(order by agf))::int attacking_score,
    round(94*percent_rank() over(order by awin))::int results_score,
    round(94*(0.5*percent_rank() over(order by aga desc)+0.5*percent_rank() over(order by acs)))::int defensive_score,
    least(
      case when top_flight_titles>=2 then 92 when top_flight_titles=1 then 82 when honours>0 or promotions>0 then 72 else 55 end,
      round(94*percent_rank() over(order by achievement_efficiency))::int
    )::int achievements_score,
    round(94*percent_rank() over(order by ared_rate desc))::int discipline_score,
    round(94*percent_rank() over(order by players_per_season desc))::int personnel_score,
    round(94*percent_rank() over(order by days_in_charge))::int longevity_score
  from adj a
), averages as (
  select round(avg(attacking_score))::int avg_attacking_score,
    round(avg(results_score))::int avg_results_score,
    round(avg(defensive_score))::int avg_defensive_score,
    round(avg(achievements_score))::int avg_achievements_score,
    round(avg(discipline_score))::int avg_discipline_score,
    round(avg(personnel_score))::int avg_personnel_score,
    round(avg(longevity_score))::int avg_longevity_score
  from ranked
)
select r.manager_id,r.attacking_score,r.results_score,r.defensive_score,r.achievements_score,r.discipline_score,r.personnel_score,r.longevity_score,
  a.avg_attacking_score,a.avg_results_score,a.avg_defensive_score,a.avg_achievements_score,a.avg_discipline_score,a.avg_personnel_score,a.avg_longevity_score,
  round(r.gf/nullif(r.played,0),2),round(100*r.wins/nullif(r.played,0),1),round(r.ga/nullif(r.played,0),2),round(r.clean_sheets/nullif(r.played,0),3),
  r.honours,r.promotions,r.relegations,r.red_cards,round(r.red_cards::numeric/nullif(r.played,0),4),r.players_used,r.seasons,round(r.players_per_season,2),r.days_in_charge,r.top_flight_titles
from ranked r
cross join averages a
where r.manager_id=p_manager_id;
$function$;

grant execute on function public.get_manager_performance_radar(bigint) to anon, authenticated;
