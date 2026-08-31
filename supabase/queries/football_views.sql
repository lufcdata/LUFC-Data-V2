-- LUFC Data V2: football-facing analytical views
-- Derived facts only: atomic matches, appearances and goals remain authoritative.

create or replace view v_player_career_totals as
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
  a.player_id as player_1_id,
  b.player_id as player_2_id,
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
group by a.player_id, b.player_id, p1.display_name, p2.display_name;

-- Match-centre context and milestones.
-- Stable Match ID is the deterministic tie-breaker for same-date historical matches.
create or replace view v_match_player_context as
with goal_counts as (
  select leeds_player_id as player_id, match_id, count(*)::int as goals_in_match
  from goals
  where leeds_player_id is not null
  group by leeds_player_id, match_id
), base as (
  select
    pm.match_id,
    m.match_date,
    pm.player_id,
    p.display_name,
    pm.started,
    pm.substitute,
    pm.lineup_order,
    (m.captain_player_id=pm.player_id) as was_captain,
    coalesce(gc.goals_in_match,0) as goals_in_match,
    case when p.date_of_birth is not null and p.birth_date_precision='exact'
         then extract(year from age(m.match_date,p.date_of_birth))::int end as age_years,
    case when p.date_of_birth is not null and p.birth_date_precision='exact'
         then extract(month from age(m.match_date,p.date_of_birth))::int end as age_months,
    case when p.date_of_birth is not null and p.birth_date_precision='exact'
         then extract(day from age(m.match_date,p.date_of_birth))::int end as age_days
  from player_matches pm
  join matches m on m.match_id=pm.match_id
  join players p on p.player_id=pm.player_id
  left join goal_counts gc on gc.player_id=pm.player_id and gc.match_id=pm.match_id
), numbered as (
  select
    b.*,
    row_number() over (partition by player_id order by match_date,match_id)::bigint as appearance_number,
    row_number() over (partition by player_id order by match_date desc,match_id desc)::bigint as reverse_appearance_number,
    sum(case when started then 1 else 0 end) over (partition by player_id order by match_date,match_id rows unbounded preceding)::bigint as start_number,
    sum(case when substitute then 1 else 0 end) over (partition by player_id order by match_date,match_id rows unbounded preceding)::bigint as substitute_appearance_number,
    sum(case when was_captain then 1 else 0 end) over (partition by player_id order by match_date,match_id rows unbounded preceding)::bigint as captaincy_number,
    sum(goals_in_match) over (partition by player_id order by match_date,match_id rows unbounded preceding)::bigint as career_goals_after_match
  from base b
)
select
  n.*,
  (appearance_number=1) as is_debut,
  (reverse_appearance_number=1) as is_final_appearance,
  (appearance_number in (10,50,100,250,500)) as is_appearance_milestone,
  case when appearance_number in (10,50,100,250,500) then appearance_number end as appearance_milestone,
  (started and start_number in (10,50,100,250,500)) as is_start_milestone,
  case when started and start_number in (10,50,100,250,500) then start_number end as start_milestone,
  (was_captain and captaincy_number in (1,10,50,100,250)) as is_captaincy_milestone,
  case when was_captain and captaincy_number in (1,10,50,100,250) then captaincy_number end as captaincy_milestone,
  (goals_in_match>0 and career_goals_after_match-goals_in_match < 1 and career_goals_after_match >= 1) as is_first_goal,
  case
    when goals_in_match>0 and career_goals_after_match-goals_in_match < 100 and career_goals_after_match >= 100 then 100
    when goals_in_match>0 and career_goals_after_match-goals_in_match < 50 and career_goals_after_match >= 50 then 50
    when goals_in_match>0 and career_goals_after_match-goals_in_match < 25 and career_goals_after_match >= 25 then 25
    when goals_in_match>0 and career_goals_after_match-goals_in_match < 10 and career_goals_after_match >= 10 then 10
  end as goal_milestone
from numbered n;
