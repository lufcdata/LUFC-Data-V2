import React,{useEffect,useState}from'react';
import{ArrowLeft,MapPin}from'lucide-react';
import ManagerIcon from'./ManagerIcon';
import NationalityFlag from'./NationalityFlag';
import ManagerInformation from'./ManagerInformation';
import ManagerCareerMetrics from'./ManagerCareerMetrics';
import ManagerCompetitionBreakdown from'./ManagerCompetitionBreakdown';
import ManagerPerformanceRadar from'./ManagerPerformanceRadar';
import ManagerProfileBreakdowns from'./ManagerProfileBreakdowns';
import ManagerDebutantsTable from'./ManagerDebutantsTable';
import{supabase,supabaseConfigError}from'./supabase';
import'./PlayerPage.css';
import'./PlayerPageHero.css';
import'./ManagerPage.css';

type ManagerRow={manager_id:number;canonical_name:string;full_name:string|null;date_of_birth:string|null;place_of_birth:string|null;date_of_death:string|null;declared_nation:string|null;profile_image_url:string|null;did_you_know:string|null;awards:string|null};
type LeaderboardRow={manager_id:number;manager:string;full_name:string|null;declared_nation:string|null;profile_image_url:string|null;spells:number;played:number;won:number;drawn:number;lost:number;goals_for:number;goals_against:number;goal_diff:number;win_pct:number|string;loss_pct:number|string;first_match:string;last_match:string};
type SpellRow={manager_spell_id:number;legacy_manager_order:number|null;role:string|null;date_joined:string|null;date_left:string|null;caretaker:boolean;status:string|null;profile_image_url_override:string|null};
type MetricsRow={manager_id:number;days_in_charge:number;players_used:number;debuts_given:number;clean_sheets:number;opponents_faced:number;opponents_defeated:number;opponents_defeated_pct:number|string;wins_at_elland_road:number;league_points_won:number};
type Summary={manager:ManagerRow;leaderboard:LeaderboardRow;spells:SpellRow[];metrics:MetricsRow};

function careerYears(spells:SpellRow[]){if(!spells.length)return'—';return spells.map(s=>{const a=s.date_joined?.slice(0,4)??'—',b=s.date_left?.slice(0,4)??'present';return a===b?a:`${a}–${b}`}).join(' · ')}
function roleLabel(spells:SpellRow[]){const roles=Array.from(new Set(spells.map(s=>s.role?.trim()).filter((v):v is string=>Boolean(v))));return roles.length?roles.join(' · '):'Manager'}

export default function ManagerPage({managerId,onBack}:{managerId:number;onBack?:()=>void}){
 const[summary,setSummary]=useState<Summary|null>(null),[loading,setLoading]=useState(true),[error,setError]=useState<string|null>(supabaseConfigError);
 useEffect(()=>{let cancelled=false;(async()=>{if(!supabase){setLoading(false);return}setLoading(true);setError(null);const[{data:manager,error:managerError},{data:leaderboard,error:lbError},{data:spells,error:spellsError},{data:metrics,error:metricsError}]=await Promise.all([
  supabase.from('managers').select('manager_id,canonical_name,full_name,date_of_birth,place_of_birth,date_of_death,declared_nation,profile_image_url,did_you_know,awards').eq('manager_id',managerId).maybeSingle(),
  supabase.rpc('filtered_manager_leaderboard',{p_filter:'All',p_venue:'All'}),
  supabase.from('manager_spells').select('manager_spell_id,legacy_manager_order,role,date_joined,date_left,caretaker,status,profile_image_url_override').eq('manager_id',managerId).order('date_joined',{ascending:true}),
  supabase.rpc('get_manager_profile_metrics',{p_manager_id:managerId})
 ]);const firstError=managerError||lbError||spellsError||metricsError;if(firstError){if(!cancelled){setError(firstError.message);setLoading(false)}return}const m=(manager??null)as ManagerRow|null,lb=((leaderboard??[])as LeaderboardRow[]).find(r=>Number(r.manager_id)===managerId),metric=((metrics??[])as MetricsRow[])[0];if(!m||!lb||!metric){if(!cancelled){setError('Manager profile unavailable');setLoading(false)}return}if(!cancelled){setSummary({manager:m,leaderboard:lb,spells:(spells??[])as SpellRow[],metrics:metric});setLoading(false)}})();return()=>{cancelled=true}},[managerId]);
 if(loading)return <div className="player-profile-page"><button className="player-profile-back" onClick={onBack}><ArrowLeft size={13}/> Back to Managers</button><div className="card lb-loading">Loading manager profile…</div></div>;
 if(error||!summary)return <div className="player-profile-page"><button className="player-profile-back" onClick={onBack}><ArrowLeft size={13}/> Back to Managers</button><div className="card lb-loading"><strong>Data connection error:</strong> {error??'Manager profile unavailable'}</div></div>;
 const m=summary.manager,l=summary.leaderboard,status=summary.spells.some(s=>s.status==='Current')?'Current':'Former',roles=roleLabel(summary.spells),years=careerYears(summary.spells),mx=summary.metrics;
 const stats=[['Spells',String(l.spells)],['Matches',String(l.played)],['Wins',String(l.won)],['Draws',String(l.drawn)],['Losses',String(l.lost)],['Win %',`${Number(l.win_pct).toFixed(1)}%`],['GF',String(l.goals_for)],['GA',String(l.goals_against)],['GD',`${l.goal_diff>0?'+':''}${l.goal_diff}`],['Clean Sheets',String(mx.clean_sheets)],['Days In Charge',mx.days_in_charge.toLocaleString('en-GB')],['Players Used',String(mx.players_used)],['Debuts Given',String(mx.debuts_given)],['Opponents Faced',String(mx.opponents_faced)],['Opponents Defeated',String(mx.opponents_defeated)],['Opponents Defeated %',`${Number(mx.opponents_defeated_pct).toFixed(1)}%`],['Wins at Elland Road',String(mx.wins_at_elland_road)],['League Points Won',String(mx.league_points_won)]];
 return <div className="player-profile-page manager-profile-page"><button className="player-profile-back" onClick={onBack}><ArrowLeft size={13}/> Back to Managers</button>
  <section className="card player-profile-hero"><div className="player-profile-hero-main"><div className="player-profile-portrait-wrap"><div className="player-profile-portrait"><ManagerIcon name={m.canonical_name} src={m.profile_image_url}/></div><span className="player-profile-number-badge">#{summary.spells[0]?.legacy_manager_order??m.manager_id}</span></div><div className="player-profile-identity"><span className="section-kicker">Leeds United manager profile</span><h1>{m.canonical_name}</h1><p className="player-profile-fullname">{m.full_name?.trim()||m.canonical_name}</p><div className="player-profile-tags"><span className="player-profile-position">{roles}</span><span className="player-profile-tag-divider"/><span className="player-profile-nation">{m.declared_nation?<><NationalityFlag nation={m.declared_nation}/> {m.declared_nation}</>:<>—</>}</span></div></div></div><div className="player-profile-hero-details"><div className="player-profile-hero-detail"><span className="player-profile-detail-icon"><MapPin size={21}/></span><div><span className="player-profile-detail-label">Place of Birth</span><strong>{m.place_of_birth?.trim()||'—'}</strong></div></div><div className="player-profile-hero-detail"><span className="player-profile-detail-icon player-profile-leeds-icon"><img src="/Leeds.png" alt=""/></span><div><span className="player-profile-detail-label">Leeds United</span><strong>{years}</strong></div></div><div className="player-profile-hero-detail player-profile-status-detail"><div><span className="player-profile-detail-label">Status</span><span className={`manager-status-pill ${status==='Current'?'current':'former'}`}>{status}</span></div></div></div></section>
  <section className="player-profile-statgrid">{stats.map(([label,value])=><div className="card player-profile-stat" key={label}><span>{label}</span><strong>{value}</strong></div>)}</section>
  <ManagerInformation managerId={managerId}/>
  <ManagerPerformanceRadar managerId={managerId}/>
  <div className="player-career-summary-grid"><ManagerCareerMetrics managerId={managerId}/><ManagerCompetitionBreakdown managerId={managerId}/></div>
  <ManagerProfileBreakdowns managerId={managerId}/>
  <ManagerDebutantsTable managerId={managerId}/>
 </div>;
}
