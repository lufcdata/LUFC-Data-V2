create or replace view public.own_goal_events as
with for_events as (
  select
    'for-'::text || g.goal_id::text as own_goal_event_id,
    'For'::text as side,
    row_number() over (order by m.match_date, coalesce(g.minute_normalised::integer, 999), g.goal_id)::integer as source_order,
    g.goal_id,
    g.match_id,
    regexp_replace(g.scorer_name_raw, '\s*\((?:[O0]\.G\.|OG)\)\s*$', '', 'i') as scorer_name,
    g.minute_raw,
    g.minute_normalised::integer as minute_normalised,
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
    null::bigint as scorer_player_id,
    null::text as declared_nation
  from public.goals g
  join public.match_centre_summary m on m.match_id = g.match_id
  where g.is_own_goal is true
), against_events as (
  select
    'against-'::text || o.own_goal_against_id::text as own_goal_event_id,
    'Against'::text as side,
    o.source_order,
    null::bigint as goal_id,
    o.match_id,
    coalesce(p.display_name, o.scorer_raw) as scorer_name,
    o.minute_raw,
    case
      when o.minute_raw ~ '^\d+\+\d+$' then split_part(o.minute_raw, '+', 1)::integer + split_part(o.minute_raw, '+', 2)::integer
      when o.minute_raw ~ '^\d+$' then o.minute_raw::integer
      else null::integer
    end as minute_normalised,
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
    o.scorer_player_id,
    p.declared_nation
  from public.leeds_own_goals_against o
  join public.match_centre_summary m on m.match_id = o.match_id
  left join public.players p on p.player_id = o.scorer_player_id
)
select * from for_events
union all
select * from against_events;
