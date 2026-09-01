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

export async function getOpponentLeaderboard() {
  const { data, error } = await supabase
    .from('opponent_leaderboard')
    .select('club_id,opponent,crest_url,played,won,drawn,lost,goals_for,goals_against,goal_diff,win_pct,last_meeting,last5')
    .order('played', { ascending: false })
    .order('opponent', { ascending: true });

  if (error) throw error;
  return (data ?? []) as OpponentLeaderboardRow[];
}
