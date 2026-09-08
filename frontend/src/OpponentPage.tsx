import React,{useEffect,useMemo,useState}from'react';
import{ArrowLeft,CalendarDays,MapPin}from'lucide-react';
import{supabase,supabaseConfigError}from'./supabase';
import ClubCrest from'./ClubCrest';
import'./OpponentPage.css';

type Club={club_id:number;display_name:string|null;canonical_name:string;crest_url:string|null;country:string|null;founded_year:number|null;nickname:string|null};
type Summary={club_id:number;opponent:string;crest_url:string|null;played:number;won:number;drawn:number;lost:number;goals_for:number;goals_against:number;goal_diff:number;win_pct:number|string;first_meeting:string|null;last_meeting:string|null};
type MatchRow={match_id:number;match_date:string;season:string|null;competition:string|null;venue_type:string|null;leeds_score:number;opponent_score:number;result:string|null;stadium:string|null;attendance:number|null;round:string|null};

const dateLabel=(value:string|null)=>value?new Date(`${value}T00:00:00`).toLocaleDateString('en-GB',{day:'numeric',month:'short',year:'numeric'}):'—';
const venueLabel=(v:string|null)=>v==='H'?'Home':v==='A'?'Away':v==='N'?'Neutral':v||'—';

export default function OpponentPage({clubId,onBack}:{clubId:number;onBack:()=>void}){
 const[club,setClub]=useState<Club|null>(null),[summary,setSummary]=useState<Summary|null>(null),[matches,setMatches]=useState<MatchRow[]>([]),[loading,setLoading]=useState(true),[error,setError]=useState<string|null>(supabaseConfigError);
 useEffect(()=>{if(!supabase){setLoading(false);return}let cancelled=false;(async()=>{setLoading(true);setError(null);const[{data:c,error:ce},{data:s,error:se},{data:m,error:me}]=await Promise.all([
   supabase!.from('clubs').select('club_id,display_name,canonical_name,crest_url,country,founded_year,nickname').eq('club_id',clubId).single(),
   supabase!.from('opponent_profile_summary').select('*').eq('club_id',clubId).single(),
   supabase!.from('opponent_match_history').select('match_id,match_date,season,competition,venue_type,leeds_score,opponent_score,result,stadium,attendance,round').eq('club_id',clubId).order('match_date',{ascending:false})
 ]);const firstError=ce||se||me;if(firstError){if(!cancelled){setError(firstError.message);setLoading(false)}return}if(!cancelled){setClub(c as Club);setSummary(s as Summary);setMatches((m??[])as MatchRow[]);setLoading(false)}})();return()=>{cancelled=true}},[clubId]);
 const record=useMemo(()=>summary?`${summary.won} - ${summary.drawn} - ${summary.lost}`:'—',[summary]);
 if(loading)return <div className="card opponent-profile-state">Loading opponent profile…</div>;
 if(error||!club||!summary)return <div className="card opponent-profile-state"><strong>Opponent profile could not load.</strong><span>{error||'Opponent not found.'}</span><button onClick={onBack}>Back to Opponents</button></div>;
 const name=club.display_name||club.canonical_name||summary.opponent;
 return <div className="opponent-profile-page">
   <button type="button" className="opponent-back" onClick={onBack}><ArrowLeft size={14}/> Back to Opponents</button>
   <section className="card opponent-hero">
    <div className="opponent-hero-identity"><div className="opponent-hero-crest"><ClubCrest crestUrl={club.crest_url||summary.crest_url} name={name}/></div><div><span className="section-kicker">Opponent Profile</span><h1>{name}</h1><div className="opponent-identity-meta"><span>{club.country||'Country unknown'}</span><span>Founded {club.founded_year??'—'}</span><span>{club.nickname||'Nickname unknown'}</span></div></div></div>
    <div className="opponent-record"><small>LEEDS RECORD</small><strong>{record}</strong><span>W - D - L</span></div>
   </section>
   <section className="opponent-stat-grid">
    <div className="card opponent-stat"><small>Played</small><strong>{summary.played}</strong></div><div className="card opponent-stat"><small>Won</small><strong>{summary.won}</strong></div><div className="card opponent-stat"><small>Drawn</small><strong>{summary.drawn}</strong></div><div className="card opponent-stat"><small>Lost</small><strong>{summary.lost}</strong></div><div className="card opponent-stat"><small>Goals For</small><strong>{summary.goals_for}</strong></div><div className="card opponent-stat"><small>Goals Against</small><strong>{summary.goals_against}</strong></div><div className="card opponent-stat"><small>Goal Diff</small><strong>{summary.goal_diff>0?'+':''}{summary.goal_diff}</strong></div><div className="card opponent-stat"><small>Win %</small><strong>{Number(summary.win_pct).toFixed(1)}%</strong></div>
   </section>
   <section className="card opponent-meetings">
    <div className="opponent-section-head"><div><span className="section-kicker">Head to head</span><h2>Competitive Meetings</h2></div><div className="opponent-meeting-range"><span><CalendarDays size={13}/> First {dateLabel(summary.first_meeting)}</span><span>Last {dateLabel(summary.last_meeting)}</span></div></div>
    <div className="opponent-table-wrap"><table className="opponent-table"><thead><tr><th>Date</th><th>Season</th><th>Competition</th><th>Venue</th><th>Result</th><th>Score</th><th>Round</th><th>Stadium</th><th>Attendance</th></tr></thead><tbody>{matches.map(row=><tr key={row.match_id}><td>{dateLabel(row.match_date)}</td><td>{row.season||'—'}</td><td>{row.competition||'—'}</td><td>{venueLabel(row.venue_type)}</td><td><span className={`opponent-result result-${(row.result||'').toLowerCase()}`}>{row.result||'—'}</span></td><td className="opponent-score">{row.leeds_score}-{row.opponent_score}</td><td>{row.round||'—'}</td><td><span className="opponent-stadium"><MapPin size={12}/>{row.stadium||'—'}</span></td><td>{row.attendance==null?'—':row.attendance.toLocaleString('en-GB')}</td></tr>)}</tbody></table></div>
   </section>
 </div>;
}
