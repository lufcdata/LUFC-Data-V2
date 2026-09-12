import React, { useEffect, useMemo, useState } from 'react';
import { supabase, supabaseConfigError } from './supabase';

type SeasonRef = {
  season_id: number;
  display_name: string;
  start_year: number;
  end_year: number;
};

type SeasonMatch = {
  match_id: number;
  match_date: string;
  season: string | null;
  competition: string;
  round: string | null;
  leeds_score: number;
  opponent_score: number;
  result: string;
  leeds_manager: string | null;
  league_tier: number | null;
  league_position_after_match: number | null;
  league_points_after_match: number | null;
};

type SeasonSummary = {
  season: SeasonRef;
  tier: number | null;
  finalTier: number | null;
  finalPosition: number | null;
  matchesPlayed: number;
  won: number;
  drawn: number;
  lost: number;
  goalsFor: number;
  goalsAgainst: number;
  goalDifference: number;
  cleanSheets: number;
  points: number | null;
  managers: string[];
  statuses: string[];
  faCup: string;
  leagueCup: string;
  europe: string;
};

const PAGE_SIZE = 1000;
const LEAGUE_MATCH_MAX = 46;
const EUROPEAN_COMPETITIONS = new Set([
  'Inter-City Fairs Cup',
  'European Cup',
  'UEFA Cup',
  "European Cup Winners' Cup",
  'Champions League',
]);

const ordinal = (value: number | null) => {
  if (value == null) return '—';
  const mod100 = value % 100;
  const mod10 = value % 10;
  const suffix = mod100 >= 11 && mod100 <= 13 ? 'th' : mod10 === 1 ? 'st' : mod10 === 2 ? 'nd' : mod10 === 3 ? 'rd' : 'th';
  return `${value}${suffix}`;
};

const normaliseRound = (round: string | null) => {
  if (!round) return '—';
  const clean = round.replace(/ \(R\)$/i, '').trim();
  if (clean === 'Stage 1') return 'GS1';
  if (clean === 'Stage 2') return 'GS2';
  return clean;
};

const roundRank = (round: string | null) => {
  const clean = normaliseRound(round);
  const ranks: Record<string, number> = {
    '—': 0,
    PR: 1,
    Q: 2,
    PO: 3,
    'R1 PO': 4,
    R1: 10,
    R2: 20,
    R3: 30,
    R4: 40,
    R5: 50,
    GS1: 55,
    GS2: 60,
    QF: 70,
    SF: 80,
    F: 90,
  };
  return ranks[clean] ?? 5;
};

const furthestRound = (matches: SeasonMatch[]) => {
  if (!matches.length) return '—';
  return normaliseRound(matches.reduce((best, match) => roundRank(match.round) > roundRank(best.round) ? match : best).round);
};

const europeanLabel = (competition: string) => {
  if (competition === 'Inter-City Fairs Cup') return 'Fairs';
  if (competition === 'European Cup') return 'EC';
  if (competition === 'UEFA Cup') return 'UEFA';
  if (competition === "European Cup Winners' Cup") return 'CWC';
  if (competition === 'Champions League') return 'UCL';
  return competition;
};

const statusClass = (status: string) => {
  if (status === 'Champions') return 'season-status-champions';
  if (status === 'Promoted') return 'season-status-promoted';
  if (status === 'Relegated') return 'season-status-relegated';
  return 'season-status-current';
};

const seasonStyles = `
.seasons-toolbar{display:flex;align-items:flex-end;gap:18px;flex-wrap:wrap;padding:0 0 16px;border-bottom:1px solid #eceeee}
.season-slider-block{display:flex;flex-direction:column;gap:6px;min-width:330px;flex:1;max-width:520px}
.season-slider-row{display:flex;align-items:center;gap:10px}
.season-slider{width:100%;accent-color:#2F91ED;cursor:pointer}
.season-slider-value{min-width:34px;text-align:center;font-family:'DM Mono',monospace;font-size:11px;font-weight:700;color:#2F91ED}
.seasons-table{min-width:1540px;table-layout:auto}
.seasons-table thead th{text-align:center}
.seasons-table thead th:first-child{text-align:left}
.seasons-table tbody td{text-align:center;white-space:nowrap}
.seasons-table .season-name-col,.seasons-table .season-name-cell{position:sticky;left:0;z-index:4;background:#fff;text-align:left;min-width:98px}
.seasons-table thead .season-name-col{z-index:6}
.seasons-table tbody tr:hover .season-name-cell{background:#fafbfb}
.season-name-cell{font-family:'Urbanist',sans-serif;font-size:12.5px;font-weight:700;color:#23292b}
.season-tier{font-family:'DM Mono',monospace;font-weight:700}
.season-manager-cell{min-width:220px;max-width:280px;text-align:left!important;white-space:normal!important;line-height:1.45}
.season-status-cell{min-width:170px;white-space:normal!important}
.season-statuses{display:flex;justify-content:center;gap:5px;flex-wrap:wrap}
.season-status-pill{display:inline-flex;align-items:center;height:21px;padding:0 7px;border-radius:999px;font-size:8px;font-weight:800;letter-spacing:.04em;text-transform:uppercase}
.season-status-champions{background:#F2E01F;color:#161a1d}
.season-status-promoted{background:#89F0DD;color:#264f49}
.season-status-relegated{background:#E6739B;color:#fff}
.season-status-current{background:#2F91ED;color:#fff}
.season-positive{color:#50E5E0!important;font-weight:700}
.season-negative{color:#F73475!important;font-weight:700}
.season-cup-cell{font-family:'DM Mono',monospace;font-size:10px;font-weight:600}
.theme-dark .seasons-toolbar{border-bottom-color:#2c3752}
.theme-dark .seasons-table .season-name-col,.theme-dark .seasons-table .season-name-cell{background:#192031}
.theme-dark .seasons-table tbody tr:hover .season-name-cell{background:#222b42}
.theme-dark .season-name-cell{color:#F5F5F5}
@media(max-width:700px){.season-slider-block{min-width:100%;max-width:none}.seasons-toolbar>.lb-filter-section{width:auto}}
`;

async function loadAllSeasonMatches() {
  if (!supabase) return [] as SeasonMatch[];
  const all: SeasonMatch[] = [];
  for (let start = 0; ; start += PAGE_SIZE) {
    const { data, error } = await supabase
      .from('match_centre_summary')
      .select('match_id,match_date,season,competition,round,leeds_score,opponent_score,result,leeds_manager,league_tier,league_position_after_match,league_points_after_match')
      .order('match_date', { ascending: true })
      .order('match_id', { ascending: true })
      .range(start, start + PAGE_SIZE - 1);
    if (error) throw error;
    const batch = (data ?? []) as SeasonMatch[];
    all.push(...batch);
    if (batch.length < PAGE_SIZE) break;
  }
  return all;
}

export default function Seasons() {
  const [seasons, setSeasons] = useState<SeasonRef[]>([]);
  const [matches, setMatches] = useState<SeasonMatch[]>([]);
  const [tierFilter, setTierFilter] = useState('All Tiers');
  const [matchLimit, setMatchLimit] = useState(46);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(supabaseConfigError);

  useEffect(() => {
    if (!supabase) {
      setLoading(false);
      return;
    }
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const [{ data: seasonData, error: seasonError }, allMatches] = await Promise.all([
          supabase!
            .from('seasons')
            .select('season_id,display_name,start_year,end_year')
            .order('start_year', { ascending: false }),
          loadAllSeasonMatches(),
        ]);
        if (seasonError) throw seasonError;
        if (!cancelled) {
          setSeasons((seasonData ?? []) as SeasonRef[]);
          setMatches(allMatches);
        }
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : String(e));
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => { cancelled = true; };
  }, []);

  const matchesBySeason = useMemo(() => {
    const map = new Map<string, SeasonMatch[]>();
    for (const match of matches) {
      if (!match.season) continue;
      const list = map.get(match.season) ?? [];
      list.push(match);
      map.set(match.season, list);
    }
    for (const list of map.values()) {
      list.sort((a, b) => a.match_date.localeCompare(b.match_date) || a.match_id - b.match_id);
    }
    return map;
  }, [matches]);

  const fullSeasonState = useMemo(() => {
    return seasons.map((season) => {
      const seasonMatches = matchesBySeason.get(season.display_name) ?? [];
      const leagueMatches = seasonMatches.filter((m) => m.league_tier != null);
      const final = leagueMatches.at(-1) ?? null;
      return {
        season,
        tier: leagueMatches[0]?.league_tier ?? null,
        finalPosition: final?.league_position_after_match ?? null,
      };
    });
  }, [seasons, matchesBySeason]);

  const summaries = useMemo<SeasonSummary[]>(() => {
    const stateBySeasonId = new Map(fullSeasonState.map((x) => [x.season.season_id, x]));
    const orderedAscending = [...seasons].sort((a, b) => a.start_year - b.start_year);

    const nextLeagueTier = (season: SeasonRef) => {
      const index = orderedAscending.findIndex((s) => s.season_id === season.season_id);
      for (let i = index + 1; i < orderedAscending.length; i += 1) {
        const state = stateBySeasonId.get(orderedAscending[i].season_id);
        if (state?.tier != null) return state.tier;
      }
      return null;
    };

    const newestSeasonId = Math.max(...seasons.map((s) => s.season_id), 0);

    return seasons.map((season) => {
      const seasonMatches = matchesBySeason.get(season.display_name) ?? [];
      const leagueMatches = seasonMatches.filter((m) => m.league_tier != null);
      const sampleCount = Math.min(matchLimit, leagueMatches.length);
      const sampled = leagueMatches.slice(0, sampleCount);
      const sampledLast = sampled.at(-1) ?? null;
      const final = leagueMatches.at(-1) ?? null;
      const won = sampled.filter((m) => m.result === 'Won').length;
      const drawn = sampled.filter((m) => m.result === 'Draw').length;
      const lost = sampled.filter((m) => m.result === 'Lost').length;
      const goalsFor = sampled.reduce((sum, m) => sum + Number(m.leeds_score || 0), 0);
      const goalsAgainst = sampled.reduce((sum, m) => sum + Number(m.opponent_score || 0), 0);
      const cleanSheets = sampled.filter((m) => Number(m.opponent_score) === 0).length;
      const managers = Array.from(new Set(seasonMatches.map((m) => m.leeds_manager).filter((m): m is string => Boolean(m))));
      const tier = leagueMatches[0]?.league_tier ?? null;
      const finalTier = tier;
      const finalPosition = final?.league_position_after_match ?? null;
      const nextTier = nextLeagueTier(season);
      const statuses: string[] = [];
      if (finalPosition === 1) statuses.push('Champions');
      if (finalTier != null && nextTier != null && nextTier < finalTier) statuses.push('Promoted');
      if (finalTier != null && nextTier != null && nextTier > finalTier) statuses.push('Relegated');
      if (season.season_id === newestSeasonId) statuses.push('Current');

      const faCup = furthestRound(seasonMatches.filter((m) => m.competition === 'FA Cup'));
      const leagueCup = furthestRound(seasonMatches.filter((m) => m.competition === 'League Cup'));
      const europeanGroups = new Map<string, SeasonMatch[]>();
      for (const match of seasonMatches.filter((m) => EUROPEAN_COMPETITIONS.has(m.competition))) {
        const list = europeanGroups.get(match.competition) ?? [];
        list.push(match);
        europeanGroups.set(match.competition, list);
      }
      const europe = europeanGroups.size
        ? Array.from(europeanGroups.entries()).map(([competition, compMatches]) => `${europeanLabel(competition)} ${furthestRound(compMatches)}`).join(' · ')
        : '—';

      return {
        season,
        tier,
        finalTier,
        finalPosition: sampledLast?.league_position_after_match ?? null,
        matchesPlayed: sampleCount,
        won,
        drawn,
        lost,
        goalsFor,
        goalsAgainst,
        goalDifference: goalsFor - goalsAgainst,
        cleanSheets,
        points: sampledLast?.league_points_after_match ?? null,
        managers,
        statuses,
        faCup,
        leagueCup,
        europe,
      };
    });
  }, [seasons, matchesBySeason, fullSeasonState, matchLimit]);

  const tiers = useMemo(() => Array.from(new Set(summaries.map((s) => s.tier).filter((n): n is number => n != null))).sort((a, b) => a - b), [summaries]);
  const visible = useMemo(() => summaries.filter((s) => tierFilter === 'All Tiers' || s.tier === Number(tierFilter)), [summaries, tierFilter]);

  return (
    <>
      <style>{seasonStyles}</style>
      <div className="card lb-table-card">
        <div className="lb-table-header">
          <div className="lb-title-group">
            <span className="section-kicker">Leeds United history</span>
            <h2>Seasons</h2>
            <p>League record, managers and cup progression across every Leeds United season</p>
          </div>
          <div className="section-kicker lb-match-count">{loading ? '…' : `${visible.length} Seasons Shown`}</div>
        </div>

        <div className="seasons-toolbar">
          <div className="lb-filter-section">
            <span className="lb-filter-label">League Tier</span>
            <select className="lb-filter-select" value={tierFilter} onChange={(e) => setTierFilter(e.target.value)} aria-label="League tier">
              <option value="All Tiers">All Tiers</option>
              {tiers.map((tier) => <option key={tier} value={tier}>Tier {tier}</option>)}
            </select>
          </div>
          <div className="season-slider-block">
            <span className="lb-filter-label">League record after match</span>
            <div className="season-slider-row">
              <input
                className="season-slider"
                type="range"
                min={1}
                max={LEAGUE_MATCH_MAX}
                step={1}
                value={matchLimit}
                onChange={(e) => setMatchLimit(Number(e.target.value))}
                aria-label="League matches elapsed"
              />
              <span className="season-slider-value">{matchLimit}</span>
            </div>
          </div>
        </div>

        {loading ? (
          <div className="lb-loading">Building Leeds United season records…</div>
        ) : error ? (
          <div className="lb-loading"><strong>Data connection error:</strong> {error}</div>
        ) : (
          <div className="lb-table-wrap">
            <table className="lb-table seasons-table">
              <thead>
                <tr>
                  <th className="season-name-col">Season</th>
                  <th>Tier</th>
                  <th>Pos</th>
                  <th>Matches</th>
                  <th>Won</th>
                  <th>Draw</th>
                  <th>Lost</th>
                  <th>For</th>
                  <th>Against</th>
                  <th>GD</th>
                  <th>CS</th>
                  <th>PTS</th>
                  <th>Leeds Managers</th>
                  <th>Champions / Promotion / Relegation</th>
                  <th>FA Cup</th>
                  <th>League Cup</th>
                  <th>Europe</th>
                </tr>
              </thead>
              <tbody>
                {visible.map((row) => (
                  <tr key={row.season.season_id}>
                    <td className="season-name-cell">{row.season.display_name.replace('/', '/')}</td>
                    <td className="metric-value season-tier">{row.tier == null ? '—' : `T${row.tier}`}</td>
                    <td className="metric-value" style={{ fontWeight: 700 }}>{ordinal(row.finalPosition)}</td>
                    <td className="metric-value">{row.matchesPlayed || '—'}</td>
                    <td className="metric-value">{row.matchesPlayed ? row.won : '—'}</td>
                    <td className="metric-value">{row.matchesPlayed ? row.drawn : '—'}</td>
                    <td className="metric-value">{row.matchesPlayed ? row.lost : '—'}</td>
                    <td className="metric-value">{row.matchesPlayed ? row.goalsFor : '—'}</td>
                    <td className="metric-value">{row.matchesPlayed ? row.goalsAgainst : '—'}</td>
                    <td className={`metric-value ${row.goalDifference > 0 ? 'season-positive' : row.goalDifference < 0 ? 'season-negative' : ''}`}>{row.matchesPlayed ? (row.goalDifference > 0 ? `+${row.goalDifference}` : row.goalDifference) : '—'}</td>
                    <td className="metric-value">{row.matchesPlayed ? row.cleanSheets : '—'}</td>
                    <td className="metric-value" style={{ fontWeight: 700 }}>{row.points ?? '—'}</td>
                    <td className="season-manager-cell">{row.managers.length ? row.managers.join(' / ') : '—'}</td>
                    <td className="season-status-cell">
                      {row.statuses.length ? <div className="season-statuses">{row.statuses.map((status) => <span key={status} className={`season-status-pill ${statusClass(status)}`}>{status}</span>)}</div> : '—'}
                    </td>
                    <td className="season-cup-cell">{row.faCup}</td>
                    <td className="season-cup-cell">{row.leagueCup}</td>
                    <td className="season-cup-cell">{row.europe}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {!visible.length && <div className="lb-empty">No seasons match this tier.</div>}
          </div>
        )}
      </div>

      <div className="card lb-legend">
        <div className="lb-legend-items">
          <span>The slider recalculates Pos, Matches, W/D/L, For/Against, GD, CS and PTS after the selected number of league matches.</span>
          <span>When a season contained fewer league matches than the selected number, its final available league record is shown.</span>
          <span>Champions / Promoted / Relegated are season-end outcomes and do not change with the slider.</span>
          <span>Cup columns show the furthest round reached: R1–R5, QF, SF, F; European group stages use GS1 / GS2.</span>
          <span>Europe includes the Fairs Cup, European Cup, UEFA Cup, Cup Winners' Cup and Champions League.</span>
        </div>
      </div>
    </>
  );
}
