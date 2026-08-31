-- LUFC Data V2: football-facing analytical views
-- Derived facts only: atomic matches, appearances and goals remain authoritative.

create or replace view v_player_career_totals as
select
  p.player_id,
  p.legacy_player_id,
  p.display_name,
  count(pm.player_match_id)::bigint as appearances,
  count(*) filter (where pm.started)::bigint as starts,
  count(*) filter (where pm.substitute)::bigint as substitute_appearances,
  count(g.goal_id) filter (where g.leeds_player_id = p.player_id)::bigint as goals
from players p
left join player_matches pm on pm.player_id = p.player_id
left join goals g on g.match_id = pm.match_id and g.leeds_player_id = p.player_id
-- A player can score multiple goals in one appearance, so aggregate appearances separately below.
group by p.player_id, p.legacy_player_id, p.display_name;

-- Correct career aggregation without goal fan-out.
create or replace view v_player_career_summary as
with apps as (
  select player_id,
         count(*)::bigint as appearances,
         count(*) filter (where started)::bigint as starts,
         count(*) filter (where substitute)::bigint as substitute_appearances
  from player_matches
  group by player_id
), goal_totals as (
  select leeds_player_id as player_id, count(*)::bigint as goals
  from goals
  where leeds_player_id is not null
  group by leeds_player_id
)
select p.player_id, p.legacy_player_id, p.display_name,
       coalesce(a.appearances,0) as appearances,
       coalesce(a.starts,0) as starts,
       coalesce(a.substitute_appearances,0) as substitute_appearances,
       coalesce(g.goals,0) as goals
from players p
left join apps a using (player_id)
left join goal_totals g using (player_id);

drop view if exists v_player_career_totals;
alter view v_player_career_summary rename to v_player_career_totals;

create or replace view v_player_opponent_totals as
with apps as (
  select pm.player_id, m.opponent_id,
         count(*)::bigint as appearances,
         count(*) filter (where pm.started)::bigint as starts
  from player_matches pm
  join matches m on m.match_id = pm.match_id
  group by pm.player_id, m.opponent_id
), goal_totals as (
  select g.leeds_player_id as player_id, m.opponent_id, count(*)::bigint as goals
  from goals g
  join matches m on m.match_id = g.match_id
  where g.leeds_player_id is not null
  group by g.leeds_player_id, m.opponent_id
)
select p.player_id, p.display_name, c.club_id, c.display_name as opponent,
       coalesce(a.appearances,0) as appearances,
       coalesce(a.starts,0) as starts,
       coalesce(g.goals,0) as goals
from players p
cross join clubs c
left join apps a on a.player_id=p.player_id and a.opponent_id=c.club_id
left join goal_totals g on g.player_id=p.player_id and g.opponent_id=c.club_id
where a.player_id is not null or g.player_id is not null;

create or replace view v_manager_player_totals as
select
  mgr.manager_id,
  mgr.canonical_name as manager,
  p.player_id,
  p.display_name as player,
  count(*)::bigint as appearances,
  count(*) filter (where pm.started)::bigint as starts,
  count(*) filter (where pm.substitute)::bigint as substitute_appearances,
  count(distinct m.manager_spell_id)::bigint as manager_spells
from player_matches pm
join matches m on m.match_id=pm.match_id
join manager_spells ms on ms.manager_spell_id=m.manager_spell_id
join managers mgr on mgr.manager_id=ms.manager_id
join players p on p.player_id=pm.player_id
group by mgr.manager_id, mgr.canonical_name, p.player_id, p.display_name;

create or replace view v_teammate_partnerships as
select
  least(a.player_id,b.player_id) as player_1_id,
  greatest(a.player_id,b.player_id) as player_2_id,
  p1.display_name as player_1,
  p2.display_name as player_2,
  count(*)::bigint as appearances_together,
  count(*) filter (where a.started and b.started)::bigint as starts_together,
  count(*) filter (where m.result='Won')::bigint as wins_together
from player_matches a
join player_matches b on b.match_id=a.match_id and b.player_id>a.player_id
join matches m on m.match_id=a.match_id
join players p1 on p1.player_id=a.player_id
join players p2 on p2.player_id=b.player_id
group by least(a.player_id,b.player_id), greatest(a.player_id,b.player_id), p1.display_name, p2.display_name;

-- Match-centre context: age and chronological Leeds appearance number on the day.
create or replace view v_match_player_context as
select
  pm.match_id,
  m.match_date,
  pm.player_id,
  p.display_name,
  pm.started,
  pm.substitute,
  pm.lineup_order,
  case when p.date_of_birth is not null and p.birth_date_precision='exact'
       then extract(year from age(m.match_date,p.date_of_birth))::int end as age_years,
  case when p.date_of_birth is not null and p.birth_date_precision='exact'
       then extract(month from age(m.match_date,p.date_of_birth))::int end as age_months,
  case when p.date_of_birth is not null and p.birth_date_precision='exact'
       then extract(day from age(m.match_date,p.date_of_birth))::int end as age_days,
  row_number() over (partition by pm.player_id order by m.match_date,m.match_id)::bigint as appearance_number,
  row_number() over (partition by pm.player_id, pm.started order by m.match_date,m.match_id)::bigint as status_appearance_number
from player_matches pm
join matches m on m.match_id=pm.match_id
join players p on p.player_id=pm.player_id;
