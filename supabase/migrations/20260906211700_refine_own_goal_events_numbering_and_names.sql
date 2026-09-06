create or replace view public.own_goal_events as
with own_goals as (
  select
    g.*,
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
    m.referee,
    row_number() over (
      order by m.match_date asc, coalesce(g.minute_normalised, 999) asc, g.goal_id asc
    )::bigint as own_goal_number
  from public.goals g
  join public.match_centre_summary m on m.match_id = g.match_id
  where g.is_own_goal is true
)
select
  ('for-' || goal_id::text) as own_goal_event_id,
  'For'::text as side,
  own_goal_number as source_order,
  goal_id,
  match_id,
  regexp_replace(scorer_name_raw, '\s*\((?:O\.G\.|0\.G\.|OG)\)\s*$', '', 'i') as scorer_name,
  minute_raw,
  minute_normalised,
  match_date,
  season,
  opponent,
  opponent_crest_url,
  competition,
  venue_type,
  leeds_score,
  opponent_score,
  result,
  stadium,
  leeds_manager,
  referee
from own_goals;

grant select on public.own_goal_events to anon, authenticated;
