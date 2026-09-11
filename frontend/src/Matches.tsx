import React, { useEffect, useMemo, useState } from 'react';
import { Search } from 'lucide-react';
import { supabase, supabaseConfigError } from './supabase';
import ClubCrest from './ClubCrest';

type MatchRow = {
  match_id: number;
  match_date: string;
  season: string | null;
  opponent: string;
  opponent_crest_url: string | null;
  competition: string;
  round: string | null;
  venue_type: string;
  leeds_score: number;
  opponent_score: number;
  result: string;
  half_time_leeds_score: number | null;
  half_time_opponent_score: number | null;
  stadium: string | null;
  attendance: number | null;
  leeds_manager: string | null;
  opposition_manager_name: string | null;
  first_goal: string | null;
};

type RedCardRef = { match_id: number; side: 'Leeds' | 'Opponent' };
type VenueFilter = 'All' | 'Home' | 'Away' | 'Neutral';
type GoalRange = [number, number];
type HTStateFilter = 'All HT States' | 'Leading' | 'Level' | 'Trailing';

const PAGE_SIZE = 1000;
const venueLabel = (v: string) => (v === 'H' ? 'Home' : v === 'A' ? 'Away' : 'Neutral');
const resultCode = (r: string) => (r === 'Won' ? 'W' : r === 'Draw' ? 'D' : 'L');
const day = (d: string) => new Date(`${d}T00:00:00`).toLocaleDateString('en-GB', { weekday: 'short' });
const halfTimeState = (r: MatchRow): 'Leading' | 'Level' | 'Trailing' | null => {
  if (r.half_time_leeds_score == null || r.half_time_opponent_score == null) return null;
  if (r.half_time_leeds_score > r.half_time_opponent_score) return 'Leading';
  if (r.half_time_leeds_score < r.half_time_opponent_score) return 'Trailing';
  return 'Level';
};
const halfTimeColour = (state: ReturnType<typeof halfTimeState>) =>
  state === 'Leading' ? '#89f1de' : state === 'Level' ? '#f0cb7d' : state === 'Trailing' ? '#e6739b' : undefined;
const venues: VenueFilter[] = ['Home', 'Away', 'Neutral'];
const competitions = [
  'Associate Members Cup',
  'Champions League',
  'Championship',
  'Division One',
  'Division Two',
  'European Cup',
  "European Cup Winners' Cup",
  'FA Charity Shield',
  'FA Cup',
  'Full Members Cup',
  'Inter-City Fairs Cup',
  'League Cup',
  'League One',
  'Play-Off',
  'Premier League',
  'UEFA Cup',
];
const competitionDataValue = (v: string) =>
  v === 'Associate Members Cup' ? 'Football League Trophy' : v === 'Play-Off' ? 'Play-Offs' : v;
const redCardIcon = '/appicons/Red%20Card%20Icon2.png';
const goalRangeSliderCss = `
.match-goal-range{position:relative;width:118px;height:18px}
.match-goal-range-track{position:absolute;left:5px;right:5px;top:7px;height:4px;border-radius:999px;background:#303a52;pointer-events:none}
.match-goal-range-fill{position:absolute;top:0;height:4px;border-radius:999px;background:#50E5E0}
.match-goal-range input[type="range"]{position:absolute;left:0;top:0;width:118px;height:18px;margin:0;padding:0;appearance:none;-webkit-appearance:none;background:transparent;pointer-events:none;outline:none}
.match-goal-range input[type="range"]::-webkit-slider-runnable-track{height:4px;background:transparent;border:0}
.match-goal-range input[type="range"]::-webkit-slider-thumb{appearance:none;-webkit-appearance:none;width:12px;height:12px;margin-top:-4px;border-radius:50%;border:2px solid #10182b;background:#50E5E0;pointer-events:auto;cursor:pointer}
.match-goal-range input[type="range"]::-moz-range-track{height:4px;background:transparent;border:0}
.match-goal-range input[type="range"]::-moz-range-thumb{width:10px;height:10px;border-radius:50%;border:2px solid #10182b;background:#50E5E0;pointer-events:auto;cursor:pointer}
`;

function FormBadge({ result }: { result: 'W' | 'D' | 'L' }) {
  return <span className={`form-pill form-${result.toLowerCase()}`}>{result}</span>;
}

function GoalMargin({ forGoals, againstGoals }: { forGoals: number; againstGoals: number }) {
  const margin = forGoals - againstGoals;
  const max = 10;
  const width = (Math.min(Math.abs(margin), max) / max) * 50;
  const positive = margin > 0;
  const negative = margin < 0;
  return (
    <div style={{ width: 76, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 3 }}>
      <span className="metric-value" style={{ color: positive ? '#50E5E0' : negative ? '#F73475' : undefined, fontWeight: 700, fontSize: 9 }}>
        {positive ? `+${margin}` : margin}
      </span>
      <span style={{ position: 'relative', display: 'block', width: 62, height: 4, borderRadius: 999, background: '#303a52', overflow: 'hidden' }}>
        <span style={{ position: 'absolute', left: '50%', top: 0, bottom: 0, width: 1, background: '#667089', transform: 'translateX(-.5px)', zIndex: 2 }} />
        {margin !== 0 && (
          <span
            style={{
              position: 'absolute',
              top: 0,
              bottom: 0,
              borderRadius: 999,
              background: positive ? '#50E5E0' : '#F73475',
              ...(positive ? { left: '50%', width: `${width}%` } : { right: '50%', width: `${width}%` }),
            }}
          />
        )}
      </span>
    </div>
  );
}

function RedCardMark({ count }: { count: number }) {
  return count > 0 ? (
    <span style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: 4, minWidth: 28 }} title={`${count} red card${count === 1 ? '' : 's'}`}>
      <img src={redCardIcon} alt="Red card" style={{ width: 16, height: 16, objectFit: 'contain' }} />
      {count > 1 ? <span className="metric-value">×{count}</span> : null}
    </span>
  ) : (
    <span>—</span>
  );
}

function RedCardFilter({ label, checked, onChange }: { label: string; checked: boolean; onChange: (checked: boolean) => void }) {
  return (
    <label style={{ height: 30, display: 'inline-flex', alignItems: 'center', gap: 6, padding: '0 9px', border: '1px solid #33405e', borderRadius: 8, cursor: 'pointer', whiteSpace: 'nowrap', fontSize: 10, fontWeight: 600 }}>
      <input type="checkbox" checked={checked} onChange={(e) => onChange(e.target.checked)} style={{ margin: 0 }} />
      <span>{label}</span>
      <img src={redCardIcon} alt="" aria-hidden="true" style={{ width: 13, height: 13, objectFit: 'contain' }} />
    </label>
  );
}

function GoalRangeSlider({
  label,
  value,
  max,
  onChange,
}: {
  label: string;
  value: GoalRange | null;
  max: number;
  onChange: (value: GoalRange | null) => void;
}) {
  const upper = Math.max(0, max);
  const minValue = value?.[0] ?? 0;
  const maxValue = value?.[1] ?? upper;
  const denominator = Math.max(1, upper);
  const left = (minValue / denominator) * 100;
  const right = 100 - (maxValue / denominator) * 100;
  const labelValue = value == null ? 'All' : minValue === maxValue ? String(minValue) : `${minValue}–${maxValue}`;
  const normalise = (nextMin: number, nextMax: number): GoalRange | null =>
    nextMin === 0 && nextMax === upper ? null : [nextMin, nextMax];

  return (
    <div className="lb-filter-section" style={{ minWidth: 126 }}>
      <span className="lb-filter-label">
        {label} <span className="metric-value">{labelValue}</span>
      </span>
      <div className="match-goal-range">
        <div className="match-goal-range-track">
          <span className="match-goal-range-fill" style={{ left: `${left}%`, right: `${right}%` }} />
        </div>
        <input
          type="range"
          min={0}
          max={upper}
          step={1}
          value={minValue}
          onChange={(e) => {
            const next = Math.min(Number(e.target.value), maxValue);
            onChange(normalise(next, maxValue));
          }}
          aria-label={`${label} goals minimum`}
          aria-valuetext={`Minimum ${minValue}`}
          style={{ zIndex: minValue >= maxValue - 1 ? 4 : 3 }}
        />
        <input
          type="range"
          min={0}
          max={upper}
          step={1}
          value={maxValue}
          onChange={(e) => {
            const next = Math.max(Number(e.target.value), minValue);
            onChange(normalise(minValue, next));
          }}
          aria-label={`${label} goals maximum`}
          aria-valuetext={`Maximum ${maxValue}`}
          style={{ zIndex: 3 }}
        />
      </div>
    </div>
  );
}

async function loadRedCards() {
  if (!supabase) return [] as RedCardRef[];
  const out: RedCardRef[] = [];
  for (let start = 0; ; start += PAGE_SIZE) {
    const { data, error } = await supabase.from('red_card_events').select('match_id,side').order('match_id').range(start, start + PAGE_SIZE - 1);
    if (error) throw error;
    const batch = (data ?? []) as RedCardRef[];
    out.push(...batch);
    if (batch.length < PAGE_SIZE) break;
  }
  return out;
}

export default function Matches({ onSelectMatch }: { onSelectMatch?: (matchId: number) => void }) {
  const [rows, setRows] = useState<MatchRow[]>([]);
  const [redCards, setRedCards] = useState<RedCardRef[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(supabaseConfigError);
  const [search, setSearch] = useState('');
  const [competition, setCompetition] = useState('All Comps');
  const [venue, setVenue] = useState<VenueFilter>('All');
  const [opponent, setOpponent] = useState('All Opponents');
  const [result, setResult] = useState('All Results');
  const [firstGoal, setFirstGoal] = useState('All First Goals');
  const [leedsRedOnly, setLeedsRedOnly] = useState(false);
  const [oppRedOnly, setOppRedOnly] = useState(false);
  const [forGoals, setForGoals] = useState<GoalRange | null>(null);
  const [againstGoals, setAgainstGoals] = useState<GoalRange | null>(null);
  const [htScore, setHtScore] = useState('All HT Scores');
  const [htState, setHtState] = useState<HTStateFilter>('All HT States');
  const [goalMargin, setGoalMargin] = useState('All');
  const [leedsManager, setLeedsManager] = useState('All Leeds Managers');
  const [page, setPage] = useState(1);

  useEffect(() => {
    if (!supabase) {
      setLoading(false);
      return;
    }
    let cancelled = false;
    async function loadAllMatches() {
      setLoading(true);
      setError(null);
      try {
        const all: MatchRow[] = [];
        for (let start = 0; ; start += PAGE_SIZE) {
          const { data, error } = await supabase!
            .from('match_centre_summary')
            .select('match_id,match_date,season,opponent,opponent_crest_url,competition,round,venue_type,leeds_score,opponent_score,result,half_time_leeds_score,half_time_opponent_score,stadium,attendance,leeds_manager,opposition_manager_name,first_goal')
            .order('match_date', { ascending: false })
            .order('match_id', { ascending: false })
            .range(start, start + PAGE_SIZE - 1);
          if (error) throw error;
          const batch = (data ?? []) as MatchRow[];
          all.push(...batch);
          if (batch.length < PAGE_SIZE) break;
        }
        const reds = await loadRedCards();
        if (!cancelled) {
          setRows(all);
          setRedCards(reds);
        }
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : String(e));
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    loadAllMatches();
    return () => {
      cancelled = true;
    };
  }, []);

  const redCounts = useMemo(() => {
    const map = new Map<string, number>();
    for (const r of redCards) {
      const key = `${r.match_id}:${r.side}`;
      map.set(key, (map.get(key) ?? 0) + 1);
    }
    return map;
  }, [redCards]);

  const opponents = useMemo(() => Array.from(new Set(rows.map((r) => r.opponent).filter(Boolean))).sort((a, b) => a.localeCompare(b)), [rows]);
  const managers = useMemo(() => Array.from(new Set(rows.map((r) => r.leeds_manager).filter((m): m is string => Boolean(m)))).sort((a, b) => a.localeCompare(b)), [rows]);
  const firstGoalOptions = useMemo(() => {
    const order = ['Scored', 'Conceded', 'None', 'TBC'];
    const values = Array.from(new Set(rows.map((r) => r.first_goal).filter((v): v is string => Boolean(v))));
    return values.sort((a, b) => {
      const ai = order.indexOf(a);
      const bi = order.indexOf(b);
      return (ai < 0 ? 99 : ai) - (bi < 0 ? 99 : bi) || a.localeCompare(b);
    });
  }, [rows]);
  const maxForGoals = useMemo(() => rows.reduce((max, r) => Math.max(max, Number(r.leeds_score) || 0), 0), [rows]);
  const maxAgainstGoals = useMemo(() => rows.reduce((max, r) => Math.max(max, Number(r.opponent_score) || 0), 0), [rows]);
  const htScoreOptions = useMemo(() => {
    const scores = new Set<string>();
    for (const r of rows) {
      if (r.half_time_leeds_score == null || r.half_time_opponent_score == null) continue;
      scores.add(`${r.half_time_leeds_score}–${r.half_time_opponent_score}`);
    }
    return Array.from(scores).sort((a, b) => {
      const [af, aa] = a.split('–').map(Number);
      const [bf, ba] = b.split('–').map(Number);
      return af - bf || aa - ba;
    });
  }, [rows]);
  const marginOptions = useMemo(() => Array.from(new Set(rows.map((r) => Number(r.leeds_score) - Number(r.opponent_score)))).sort((a, b) => b - a), [rows]);

  const visible = useMemo(() => {
    const q = search.trim().toLowerCase();
    return rows.filter((r) => {
      const leedsReds = redCounts.get(`${r.match_id}:Leeds`) ?? 0;
      const oppReds = redCounts.get(`${r.match_id}:Opponent`) ?? 0;
      const rowHtScore = r.half_time_leeds_score == null || r.half_time_opponent_score == null ? null : `${r.half_time_leeds_score}–${r.half_time_opponent_score}`;
      const rowHtState = halfTimeState(r);
      return (
        (competition === 'All Comps' || r.competition === competitionDataValue(competition)) &&
        (venue === 'All' || venueLabel(r.venue_type) === venue) &&
        (opponent === 'All Opponents' || r.opponent === opponent) &&
        (result === 'All Results' || r.result === result) &&
        (firstGoal === 'All First Goals' || r.first_goal === firstGoal) &&
        (!leedsRedOnly || leedsReds > 0) &&
        (!oppRedOnly || oppReds > 0) &&
        (forGoals == null || (r.leeds_score >= forGoals[0] && r.leeds_score <= forGoals[1])) &&
        (againstGoals == null || (r.opponent_score >= againstGoals[0] && r.opponent_score <= againstGoals[1])) &&
        (htScore === 'All HT Scores' || rowHtScore === htScore) &&
        (htState === 'All HT States' || rowHtState === htState) &&
        (goalMargin === 'All' || r.leeds_score - r.opponent_score === Number(goalMargin)) &&
        (leedsManager === 'All Leeds Managers' || r.leeds_manager === leedsManager) &&
        (!q ||
          r.opponent.toLowerCase().includes(q) ||
          r.competition.toLowerCase().includes(q) ||
          (r.leeds_manager ?? '').toLowerCase().includes(q) ||
          (r.opposition_manager_name ?? '').toLowerCase().includes(q) ||
          (r.stadium ?? '').toLowerCase().includes(q) ||
          (r.season ?? '').toLowerCase().includes(q) ||
          (r.round ?? '').toLowerCase().includes(q) ||
          (r.first_goal ?? '').toLowerCase().includes(q))
      );
    });
  }, [rows, redCounts, search, competition, venue, opponent, result, firstGoal, leedsRedOnly, oppRedOnly, forGoals, againstGoals, htScore, htState, goalMargin, leedsManager]);

  useEffect(() => setPage(1), [search, competition, venue, opponent, result, firstGoal, leedsRedOnly, oppRedOnly, forGoals, againstGoals, htScore, htState, goalMargin, leedsManager]);

  const pageCount = Math.max(1, Math.ceil(visible.length / PAGE_SIZE));
  const safePage = Math.min(page, pageCount);
  const pageRows = useMemo(() => visible.slice((safePage - 1) * PAGE_SIZE, safePage * PAGE_SIZE), [visible, safePage]);
  const pageStart = visible.length ? (safePage - 1) * PAGE_SIZE + 1 : 0;
  const pageEnd = Math.min(safePage * PAGE_SIZE, visible.length);

  return (
    <>
      <style>{goalRangeSliderCss}</style>
      <div className="card lb-table-card">
        <div className="lb-table-header">
          <div className="lb-title-group">
            <span className="section-kicker">Leeds United history</span>
            <h2>Matches</h2>
            <p>Leeds United match archive</p>
          </div>
          <div className="section-kicker lb-match-count">{loading ? '…' : visible.length.toLocaleString('en-GB')} Matches Shown</div>
        </div>
        <div className="lb-filterbar">
          <div className="lb-filter-section">
            <span className="lb-filter-label">Competition</span>
            <select className="lb-filter-select" value={competition} onChange={(e) => setCompetition(e.target.value)} aria-label="Competition">
              <option value="All Comps">All Comps</option>
              {competitions.map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
          <div className="lb-filter-section lb-venue-section">
            <span className="lb-filter-label">Venue</span>
            <div className="lb-filter-pills">
              <button className={`lb-filter-pill ${venue === 'All' ? 'active' : ''}`} onClick={() => setVenue('All')}>All</button>
              {venues.map((v) => <button key={v} className={`lb-filter-pill ${venue === v ? 'active' : ''}`} onClick={() => setVenue(v)}>{v}</button>)}
            </div>
          </div>
          <div className="lb-filter-section">
            <span className="lb-filter-label">Opponent</span>
            <select className="lb-filter-select" value={opponent} onChange={(e) => setOpponent(e.target.value)} aria-label="Opponent">
              <option value="All Opponents">All Opponents</option>
              {opponents.map((o) => <option key={o} value={o}>{o}</option>)}
            </select>
          </div>
          <div className="lb-filter-section">
            <span className="lb-filter-label">Result</span>
            <select className="lb-filter-select" value={result} onChange={(e) => setResult(e.target.value)} aria-label="Result">
              <option value="All Results">All Results</option>
              <option value="Won">Won</option>
              <option value="Draw">Drawn</option>
              <option value="Lost">Lost</option>
            </select>
          </div>
          <div className="lb-filter-section">
            <span className="lb-filter-label">First Goal</span>
            <select className="lb-filter-select" value={firstGoal} onChange={(e) => setFirstGoal(e.target.value)} aria-label="First goal">
              <option value="All First Goals">All First Goals</option>
              {firstGoalOptions.map((v) => <option key={v} value={v}>{v}</option>)}
            </select>
          </div>
          <div className="lb-filter-section">
            <span className="lb-filter-label">Red Cards</span>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <RedCardFilter label="Leeds" checked={leedsRedOnly} onChange={setLeedsRedOnly} />
              <RedCardFilter label="Opp" checked={oppRedOnly} onChange={setOppRedOnly} />
            </div>
          </div>
          <GoalRangeSlider label="For" value={forGoals} max={maxForGoals} onChange={setForGoals} />
          <GoalRangeSlider label="Against" value={againstGoals} max={maxAgainstGoals} onChange={setAgainstGoals} />
          <div className="lb-filter-section">
            <span className="lb-filter-label">HT Score</span>
            <select className="lb-filter-select" style={{ minWidth: 104, width: 104 }} value={htScore} onChange={(e) => setHtScore(e.target.value)} aria-label="Half-time score">
              <option value="All HT Scores">All HT</option>
              {htScoreOptions.map((score) => <option key={score} value={score}>{score}</option>)}
            </select>
          </div>
          <div className="lb-filter-section">
            <span className="lb-filter-label">HT State</span>
            <select className="lb-filter-select" style={{ minWidth: 104, width: 104 }} value={htState} onChange={(e) => setHtState(e.target.value as HTStateFilter)} aria-label="Half-time state">
              <option value="All HT States">All States</option>
              <option value="Leading">Leading</option>
              <option value="Level">Level</option>
              <option value="Trailing">Trailing</option>
            </select>
          </div>
          <div className="lb-filter-section">
            <span className="lb-filter-label">Goal Margin</span>
            <select className="lb-filter-select" style={{ minWidth: 94, width: 94 }} value={goalMargin} onChange={(e) => setGoalMargin(e.target.value)} aria-label="Goal margin">
              <option value="All">Margin</option>
              {marginOptions.map((n) => <option key={n} value={n}>{n > 0 ? `+${n}` : n}</option>)}
            </select>
          </div>
          <div className="lb-filter-section">
            <span className="lb-filter-label">Leeds Manager</span>
            <select className="lb-filter-select" value={leedsManager} onChange={(e) => setLeedsManager(e.target.value)} aria-label="Leeds manager">
              <option value="All Leeds Managers">Leeds Managers</option>
              {managers.map((m) => <option key={m} value={m}>{m}</option>)}
            </select>
          </div>
          <label className="lb-search matches-search" style={{ height: 30, minWidth: 180, width: 180, maxWidth: 180, marginLeft: 'auto' }}>
            <Search size={13} />
            <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search" />
          </label>
        </div>

        {loading ? (
          <div className="lb-loading">Loading the full Leeds United match history…</div>
        ) : error ? (
          <div className="lb-loading"><strong>Data connection error:</strong> {error}</div>
        ) : (
          <>
            <div className="lb-table-wrap">
              <table className="lb-table matches-table">
                <thead>
                  <tr>
                    <th>Match</th><th>Season</th><th>Day</th><th>Date</th><th style={{ minWidth: 190 }}>Opponent</th><th>Venue</th><th>Competition</th><th>R</th><th>Form</th><th>Score</th><th>Goal Margin</th>
                    <th style={{ textAlign: 'center' }}><span style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: 5 }}>Leeds <img src={redCardIcon} alt="Red card" style={{ width: 13, height: 13, objectFit: 'contain' }} /></span></th>
                    <th style={{ textAlign: 'center' }}><span style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: 5 }}>Opp <img src={redCardIcon} alt="Red card" style={{ width: 13, height: 13, objectFit: 'contain' }} /></span></th>
                    <th>Stadium</th><th>First Goal</th><th>HT Score</th><th>Attendance</th><th>Leeds Manager</th><th>Opposition Manager</th>
                  </tr>
                </thead>
                <tbody>
                  {pageRows.map((r) => {
                    const form = resultCode(r.result) as 'W' | 'D' | 'L';
                    const open = () => onSelectMatch?.(r.match_id);
                    const leedsReds = redCounts.get(`${r.match_id}:Leeds`) ?? 0;
                    const oppReds = redCounts.get(`${r.match_id}:Opponent`) ?? 0;
                    const rowHtState = halfTimeState(r);
                    return (
                      <tr
                        key={r.match_id}
                        style={{ height: 44, cursor: onSelectMatch ? 'pointer' : undefined }}
                        onClick={open}
                        onKeyDown={(e) => {
                          if (onSelectMatch && (e.key === 'Enter' || e.key === ' ')) {
                            e.preventDefault();
                            open();
                          }
                        }}
                        role={onSelectMatch ? 'button' : undefined}
                        tabIndex={onSelectMatch ? 0 : undefined}
                        aria-label={onSelectMatch ? `Open match #${r.match_id}, ${r.opponent}` : undefined}
                      >
                        <td className="metric-value match-number">#{r.match_id}</td>
                        <td>{r.season ?? '—'}</td>
                        <td>{day(r.match_date)}</td>
                        <td className="metric-value">{new Date(`${r.match_date}T00:00:00`).toLocaleDateString('en-GB')}</td>
                        <td style={{ minWidth: 190 }}><div className="team-cell" style={{ whiteSpace: 'nowrap' }}><ClubCrest crestUrl={r.opponent_crest_url} name={r.opponent} /><span className="team-name" style={{ whiteSpace: 'nowrap' }}>{r.opponent}</span></div></td>
                        <td>{venueLabel(r.venue_type)}</td>
                        <td>{r.competition}</td>
                        <td className="metric-value">{r.round ?? '—'}</td>
                        <td><FormBadge result={form} /></td>
                        <td className="metric-value">{r.leeds_score}–{r.opponent_score}</td>
                        <td><GoalMargin forGoals={r.leeds_score} againstGoals={r.opponent_score} /></td>
                        <td style={{ textAlign: 'center' }}><RedCardMark count={leedsReds} /></td>
                        <td style={{ textAlign: 'center' }}><RedCardMark count={oppReds} /></td>
                        <td>{r.stadium ?? '—'}</td>
                        <td>{r.first_goal ?? '—'}</td>
                        <td className="metric-value" style={{ color: halfTimeColour(rowHtState) }}>{r.half_time_leeds_score == null || r.half_time_opponent_score == null ? '—' : `${r.half_time_leeds_score}–${r.half_time_opponent_score}`}</td>
                        <td className="metric-value">{r.attendance == null ? '—' : r.attendance.toLocaleString('en-GB')}</td>
                        <td>{r.leeds_manager ?? '—'}</td>
                        <td>{r.opposition_manager_name ?? '—'}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
              {!visible.length && <div className="lb-empty">No matches match these filters.</div>}
            </div>
            {visible.length > 0 && (
              <div className="lb-legend">
                <div className="lb-legend-items"><span>Showing {pageStart.toLocaleString('en-GB')}–{pageEnd.toLocaleString('en-GB')} of {visible.length.toLocaleString('en-GB')} matches</span></div>
                <div className="lb-filter-pills">{Array.from({ length: pageCount }, (_, i) => i + 1).map((n) => <button key={n} className={`lb-filter-pill ${safePage === n ? 'active' : ''}`} onClick={() => setPage(n)}>{n}</button>)}</div>
              </div>
            )}
          </>
        )}
      </div>
      <div className="card lb-legend">
        <div className="lb-legend-items">
          <span>Full Leeds United competitive match archive, paged in blocks of 1,000.</span>
          <span>Red-card columns and filters are populated from the canonical red-card event source.</span>
          <span>For / Against dual sliders select an inclusive minimum-to-maximum goal range; the full range is All.</span>
          <span>Goal Margin: green = positive, red = negative</span>
          <span>R Cup round</span>
          <span>First Goal Scored / Conceded / None</span>
          <span>HT Score Leeds score – opponent score at half-time</span>
          <span>HT State: Leading / Level / Trailing from the Leeds perspective</span>
          <span>W Win</span><span>D Draw</span><span>L Loss</span>
        </div>
      </div>
    </>
  );
}
