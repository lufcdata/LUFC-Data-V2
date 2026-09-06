create or replace view public.own_goal_events as
select
  ('for-' || g.goal_id::text) as own_goal_event_id,
  'For'::text as side,
  g.goal_id as source_order,
  g.goal_id,
  g.match_id,
  regexp_replace(g.scorer_name_raw, '\s*\((?:O\.G\.|OG)\)\s*$', '', 'i') as scorer_name,
  g.minute_raw,
  g.minute_normalised,
  m.match_date,
  m.season,
  m.opponent,
  m.opponent_crest_url,
  m.competition,
  m.venue_type,
  m.leeds_score,
  m.opponent_score,
  m.result,
  m.stadium,
  m.leeds_manager,
  m.referee
from public.goals g
join public.match_centre_summary m on m.match_id = g.match_id
where g.is_own_goal is true;

grant select on public.own_goal_events to anon, authenticated;
