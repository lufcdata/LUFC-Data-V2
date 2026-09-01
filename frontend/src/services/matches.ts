import { supabase } from '../supabase';

export type MatchCentreSummary = {
  match_id:number; match_date:string; season:string; opponent_id:number; opponent:string; opponent_crest_url:string|null;
  competition:string|null; round:string|null; venue_type:string; leeds_score:number; opponent_score:number; result:string;
  half_time_leeds_score:number|null; half_time_opponent_score:number|null; stadium:string|null; attendance:number|null; referee:string|null;
  kickoff_time:string|null; formation:string|null; neutral:boolean; match_info:string|null; milestones_events:string|null;
  leeds_penalty_shootout:string|null; opponent_penalty_shootout:string|null; league_position_after_match:number|null; kit_image_url:string|null;
  opponent_scorers_raw:string|null; opposition_manager_name:string|null; opposition_manager_nationality_display:string|null;
  leeds_manager_id:number|null; leeds_manager:string|null; leeds_manager_role:string|null; captain_player_id:number|null; captain:string|null;
  motm_player_id:number|null; man_of_the_match:string|null;
};
export type MatchPlayer = { match_id:number; player_id:number; player:string; position_group:string|null; position_detail:string|null; started:boolean; substitute:boolean; lineup_order:number|null; source_slot:string|null; captain:boolean; man_of_the_match:boolean; goals:number };
export type MatchGoal = { goal_id:number; match_id:number; leeds_player_id:number|null; scorer:string|null; scorer_name_raw:string|null; minute_raw:string|null; minute_normalised:number|null; is_own_goal:boolean; assist_player_id:number|null; assisted_by:string|null; assisted_by_raw:string|null; goal_type:string|null; location:string|null; body_part:string|null; goal_state:string|null; game_state:string|null };
export type MatchSubstitution = { substitution_id:number; match_id:number; player_off_id:number|null; player_off:string|null; player_on_id:number|null; player_on:string|null; minute_raw:string|null; minute_base:number|null; stoppage_minute:number|null; timing_phase:string|null; timing_known:boolean; relationship_status:string|null; note:string|null };

export async function getMatchCentre(matchId:number) {
  const [summaryRes, playersRes, goalsRes, subsRes] = await Promise.all([
    supabase.from('match_centre_summary').select('*').eq('match_id', matchId).single(),
    supabase.from('match_centre_players').select('*').eq('match_id', matchId).order('lineup_order', { ascending:true, nullsFirst:false }),
    supabase.from('match_centre_goals').select('*').eq('match_id', matchId).order('minute_normalised', { ascending:true, nullsFirst:false }),
    supabase.from('match_centre_substitutions').select('*').eq('match_id', matchId).order('minute_base', { ascending:true, nullsFirst:false }),
  ]);
  const error = summaryRes.error || playersRes.error || goalsRes.error || subsRes.error;
  if (error) throw error;
  return { summary: summaryRes.data as MatchCentreSummary, players:(playersRes.data ?? []) as MatchPlayer[], goals:(goalsRes.data ?? []) as MatchGoal[], substitutions:(subsRes.data ?? []) as MatchSubstitution[] };
}
