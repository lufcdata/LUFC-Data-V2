create or replace view public.match_centre_summary as
select m.match_id,
    m.match_date,
    s.display_name as season,
    c.club_id as opponent_id,
    coalesce(c.display_name, c.canonical_name) as opponent,
    c.crest_url as opponent_crest_url,
    cn.display_name as competition,
    m.round,
    m.venue_type,
    m.leeds_score,
    m.opponent_score,
    m.result,
    m.half_time_leeds_score,
    m.half_time_opponent_score,
    m.stadium,
    m.attendance,
    m.referee,
    m.kickoff_time,
    m.formation,
    m.neutral,
    m.match_info,
    m.milestones_events,
    m.final_match_name,
    m.leeds_penalty_shootout,
    m.opponent_penalty_shootout,
    m.league_position_after_match,
    m.kit_image_url,
    m.opponent_scorers_raw,
    m.opposition_manager_name,
    m.opposition_manager_nationality_display,
    m.opposition_manager_authority_type,
    mgr.manager_id as leeds_manager_id,
    mgr.canonical_name as leeds_manager,
    ms.role as leeds_manager_role,
    cap.player_id as captain_player_id,
    cap.display_name as captain,
    motm.player_id as motm_player_id,
    motm.display_name as man_of_the_match,
    m.first_goal
from public.matches m
join public.clubs c on c.club_id = m.opponent_id
left join public.seasons s on s.season_id = m.season_id
left join public.competition_names cn on cn.competition_name_id = m.competition_name_id
left join public.manager_spells ms on ms.manager_spell_id = m.manager_spell_id
left join public.managers mgr on mgr.manager_id = ms.manager_id
left join public.players cap on cap.player_id = m.captain_player_id
left join public.players motm on motm.player_id = m.motm_player_id;
