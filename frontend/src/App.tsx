import { useEffect, useMemo, useState } from 'react';
import { Search, Trophy, Users, CalendarDays, Shield, ChevronRight, ArrowLeft } from 'lucide-react';
import {
  getOpponentLeaderboard,
  getOpponentProfile,
  type OpponentLeaderboardRow,
  type OpponentMatchRow,
  type OpponentProfileSummary,
} from './services/opponents';

type SortKey = 'played' | 'won' | 'drawn' | 'lost' | 'goals_for' | 'goals_against' | 'goal_diff' | 'win_pct';
type SortDir = 'asc' | 'desc';

function fmtDate(value: string) {
  return new Date(`${value}T00:00:00`).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' });
}

function initials(name: string) {
  const words = name.split(/\s+/).filter(Boolean);
  return words.length === 1 ? words[0].slice(0, 3).toUpperCase() : words.slice(0, 3).map((word) => word[0]).join('').toUpperCase();
}

function score(match: OpponentMatchRow) {
  return `${match.leeds_score}–${match.opponent_score}`;
}

export default function App() {
  const [rows, setRows] = useState<OpponentLeaderboardRow[]>([]);
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sortKey, setSortKey] = useState<SortKey>('played');
  const [sortDir, setSortDir] = useState<SortDir>('desc');
  const [profile, setProfile] = useState<OpponentProfileSummary | null>(null);
  const [profileMatches, setProfileMatches] = useState<OpponentMatchRow[]>([]);
  const [profileLoading, setProfileLoading] = useState(false);

  useEffect(() => {
    getOpponentLeaderboard().then(setRows).catch((err: Error) => setError(err.message)).finally(() => setLoading(false));
  }, []);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    const values = q ? rows.filter((row) => row.opponent.toLowerCase().includes(q)) : rows;
    return [...values].sort((a, b) => {
      const av = Number(a[sortKey]);
      const bv = Number(b[sortKey]);
      return sortDir === 'desc' ? bv - av : av - bv;
    });
  }, [rows, query, sortKey, sortDir]);

  const summary = useMemo(() => ({
    opponents: rows.length,
    matches: rows.reduce((sum, row) => sum + row.played, 0),
    wins: rows.reduce((sum, row) => sum + row.won, 0),
    goals: rows.reduce((sum, row) => sum + row.goals_for, 0),
  }), [rows]);

  function sort(key: SortKey) {
    if (key === sortKey) setSortDir((dir) => dir === 'desc' ? 'asc' : 'desc');
    else { setSortKey(key); setSortDir('desc'); }
  }

  async function openOpponent(clubId: number) {
    setProfileLoading(true);
    setError(null);
    try {
      const data = await getOpponentProfile(clubId);
      setProfile(data.summary);
      setProfileMatches(data.matches);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not load opponent');
    } finally {
      setProfileLoading(false);
    }
  }

  const head = (label: string, key: SortKey) => <button className="table-sort" onClick={() => sort(key)}>{label}</button>;

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand"><div className="brand-mark">LU</div><div><strong>LUFC DATA</strong><span>Leeds United archive</span></div></div>
        <nav><button><CalendarDays size={17}/> Matches</button><button><Users size={17}/> Players</button><button><Trophy size={17}/> Managers</button><button className="active"><Shield size={17}/> Opponents</button></nav>
        <div className="sidebar-foot">1920 — PRESENT</div>
      </aside>

      <main className="main">
        {profile ? (
          <>
            <button className="back" onClick={() => setProfile(null)}><ArrowLeft size={15}/> All opponents</button>
            <header className="opponent-hero">
              <div className="hero-crest">{profile.crest_url ? <img src={profile.crest_url} alt=""/> : initials(profile.opponent)}</div>
              <div><span className="eyebrow">OPPONENT CENTRE</span><h1>{profile.opponent}</h1><p>Complete competitive head-to-head history against Leeds United.</p></div>
              <div className="live-chip"><span/> LIVE DATABASE</div>
            </header>

            <section className="stats-grid profile-stats">
              <article><span>Meetings</span><strong>{profile.played}</strong><small>{fmtDate(profile.first_meeting)} — {fmtDate(profile.last_meeting)}</small></article>
              <article><span>Leeds record</span><strong>{profile.won}-{profile.drawn}-{profile.lost}</strong><small>Wins · Draws · Losses</small></article>
              <article><span>Goals</span><strong>{profile.goals_for}–{profile.goals_against}</strong><small>For · Against</small></article>
              <article><span>Win rate</span><strong>{Number(profile.win_pct).toFixed(1)}%</strong><small>All competitive meetings</small></article>
            </section>

            <section className="panel">
              <div className="panel-head"><div><span className="eyebrow">MATCH HISTORY</span><h2>Every Leeds v {profile.opponent} fixture</h2><p>{profileMatches.length} matches loaded directly from the canonical match archive.</p></div></div>
              <div className="table-wrap"><table className="matches-table"><thead><tr><th>Date</th><th>Season</th><th>Competition</th><th>Venue</th><th>Score</th><th>Result</th><th>Stadium</th><th/></tr></thead><tbody>
                {profileMatches.map((match) => <tr key={match.match_id}><td>{fmtDate(match.match_date)}</td><td>{match.season ?? '—'}</td><td>{match.competition ?? '—'}</td><td>{match.venue_type}</td><td className="score">{score(match)}</td><td><span className={`result result-${match.result.toLowerCase()}`}>{match.result}</span></td><td>{match.stadium ?? '—'}</td><td><button className="open" title="Match Centre coming next"><ChevronRight size={17}/></button></td></tr>)}
              </tbody></table></div>
            </section>
          </>
        ) : (
          <>
            <header className="topbar"><div><span className="eyebrow">LUFC DATA / OPPONENTS</span><h1>Opponent history</h1><p>Every competitive opponent Leeds United have faced, from one canonical archive.</p></div><div className="live-chip"><span/> LIVE DATABASE</div></header>
            <section className="stats-grid"><article><span>Opponents</span><strong>{loading ? '—' : summary.opponents}</strong><small>Distinct clubs faced</small></article><article><span>Matches</span><strong>{loading ? '—' : summary.matches.toLocaleString()}</strong><small>Competitive fixtures</small></article><article><span>Leeds wins</span><strong>{loading ? '—' : summary.wins.toLocaleString()}</strong><small>Across all opponents</small></article><article><span>Leeds goals</span><strong>{loading ? '—' : summary.goals.toLocaleString()}</strong><small>Against all opponents</small></article></section>
            <section className="panel">
              <div className="panel-head"><div><span className="eyebrow">TEAM COMPARISON</span><h2>All-time opposition leaderboard</h2><p>Sorted from the live Supabase view. No opponent records are hard-coded in React.</p></div><label className="search"><Search size={16}/><input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search opponents"/></label></div>
              {(loading || profileLoading) && <div className="state">Loading opponent history…</div>}{error && <div className="state error">Unable to load opponents: {error}</div>}
              {!loading && !profileLoading && !error && <div className="table-wrap"><table><thead><tr><th>#</th><th>Opponent</th><th>{head('P','played')}</th><th>{head('W','won')}</th><th>{head('D','drawn')}</th><th>{head('L','lost')}</th><th>{head('GF','goals_for')}</th><th>{head('GA','goals_against')}</th><th>{head('GD','goal_diff')}</th><th>{head('WIN %','win_pct')}</th><th>Last 5</th><th/></tr></thead><tbody>
                {filtered.map((row, index) => <tr key={row.club_id} className="clickable-row" onClick={() => void openOpponent(row.club_id)}><td><span className="rank">{index + 1}</span></td><td><div className="club"><span className="crest">{row.crest_url ? <img src={row.crest_url} alt=""/> : initials(row.opponent)}</span><div><strong>{row.opponent}</strong><small>Last met {fmtDate(row.last_meeting)}</small></div></div></td><td className="bold">{row.played}</td><td>{row.won}</td><td>{row.drawn}</td><td>{row.lost}</td><td>{row.goals_for}</td><td>{row.goals_against}</td><td className={row.goal_diff > 0 ? 'positive' : row.goal_diff < 0 ? 'negative' : ''}>{row.goal_diff > 0 ? '+' : ''}{row.goal_diff}</td><td className="bold">{Number(row.win_pct).toFixed(1)}%</td><td><div className="form">{row.last5.split('').map((result, i) => <span key={`${row.club_id}-${i}`} className={`f-${result.toLowerCase()}`}>{result}</span>)}</div></td><td><button className="open" aria-label={`Open ${row.opponent}`}><ChevronRight size={17}/></button></td></tr>)}
              </tbody></table></div>}
            </section>
          </>
        )}
      </main>
    </div>
  );
}
