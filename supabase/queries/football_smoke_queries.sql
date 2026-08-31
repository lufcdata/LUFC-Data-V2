-- LUFC Data V2: representative football intelligence smoke queries.
-- These queries are intended for manual inspection after Database Load V1.
-- They do not store totals; all answers are derived from atomic rows/views.

-- 1) Most Leeds goals vs Chelsea
select display_name, goals
from v_player_opponent_totals
where opponent = 'Chelsea' and goals > 0
order by goals desc, display_name
limit 20;

-- 2) Most Leeds appearances vs Liverpool
select display_name, appearances, starts
from v_player_opponent_totals
where opponent = 'Liverpool'
order by appearances desc, starts desc, display_name
limit 20;

-- 3) Most-used players under Marcelo Bielsa
select player, appearances, starts, substitute_appearances
from v_manager_player_totals
where manager = 'Marcelo Bielsa'
order by appearances desc, starts desc, player
limit 20;

-- 4) Highest teammate appearance totals
select player_1, player_2, appearances_together, starts_together, wins_together
from v_teammate_partnerships
order by appearances_together desc, starts_together desc, player_1, player_2
limit 25;

-- 5) Gary Kelly Premier League appearance milestones
select match_date, competition_appearance_number, competition_appearance_milestone
from v_match_player_context
where display_name = 'Gary Kelly'
  and competition = 'Premier League'
  and competition_appearance_milestone is not null
order by match_date, match_id;

-- 6) Mark Viduka Premier League goal milestones
select match_date, goals_in_match, competition_goals_after_match, competition_goal_milestone
from v_match_player_context
where display_name = 'Mark Viduka'
  and competition = 'Premier League'
  and competition_goal_milestone is not null
order by match_date, match_id;

-- 7) Marcelo Bielsa manager match/win milestones
select match_date, manager_match_number, manager_match_milestone,
       manager_wins_after_match, manager_win_milestone
from v_match_manager_context
where manager = 'Marcelo Bielsa'
  and (manager_match_milestone is not null or manager_win_milestone is not null)
order by match_date, match_id;

-- 8) Match Centre context for a selected player
select match_date, display_name, age_years, age_months, age_days,
       appearance_number, start_number, substitute_appearance_number,
       captaincy_number, career_goals_after_match,
       appearance_milestone, goal_milestone, captaincy_milestone,
       competition, competition_appearance_number,
       competition_appearance_milestone, competition_goal_milestone
from v_match_player_context
where display_name = 'Billy Bremner'
order by match_date, match_id
limit 50;
