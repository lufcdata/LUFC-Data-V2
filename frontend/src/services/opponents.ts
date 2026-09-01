import { supabase } from '../supabase';

export type OpponentLeaderboardRow = {
  club_id: number;
  opponent: string;
  crest_url: string | null;
  played: number;
  won: number;
  drawn: number;
  lost: number;
  goals_for: number;
  goals_against: number;
  goal_diff: number;
  win_pct: number | string;
  last_meeting: string;
  last5: string;
};

export type OpponentProfileSummary = {
  club_id: number;
  opponent: string;
  crest_url: string | null;
  played: number;
  won: number;
  drawn: number;
  lost: number;
  goals_for: number;
  goals_against: number;
  goal_diff: number;
  win_pct: number | string;
  first_meeting: string;
  last_meeting: string;
};

export type OpponentMatchRow = {
  match_id: number;
  club_id: number;
  opponent: string;
  match_date: string;
  season_id: number;
  season: string | null;
  competition_id: number;
  competition: string | null;
  venue_type: string;
  leeds_score: number;
  opponent_score: number;
  result: 'Won' | 'Draw' | 'Lost';
  stadium: string | null;
  attendance: number | null;
  round: string | null;
};

export async function getOpponentLeaderboard() {
  const { data, error } = await supabase
    .from('opponent_leaderboard')
    .select('club_id,opponent,crest_url,played,won,drawn,lost,goals_for,goals_against,goal_diff,win_pct,last_meeting,last5')
    .order('played', { ascending: false })
    .order('opponent', { ascending: true });

  if (error) throw error;
  return (data ?? []) as OpponentLeaderboardRow[];
}

export async function getOpponentProfile(clubId: number) {
  const [{ data: summary, error: summaryError }, { data: matches, error: matchesError }] = await Promise.all([
    supabase
      .from('opponent_profile_summary')
      .select('*')
      .eq('club_id', clubId)
      .single(),
    supabase
      .from('opponent_match_history')
      .select('*')
      .eq('club_id', clubId)
      .order('match_date', { ascending: false }),
  ]);

  if (summaryError) throw summaryError;
  if (matchesError) throw matchesError;

  return {
    summary: summary as OpponentProfileSummary,
    matches: (matches ?? []) as OpponentMatchRow[],
  };
}
