import React, { useEffect, useMemo, useState } from 'react';
import { ArrowDown, ArrowUp, ChevronsUpDown } from 'lucide-react';
import { supabase, supabaseConfigError } from './supabase';
import ClubCrest from './ClubCrest';

type Opponent = { club_id:number; opponent:string; crest_url:string|null; played:number; won:number; drawn:number; lost:number; goals_for:number; goals_against:number; goal_diff:number; win_pct:number|string; last5:string|null; last_meeting:string|null; };
type SortKey='played'|'won'|'drawn'|'lost'|'goals_for'|'goals_against'|'goal_diff'|'win_pct';
type SortDir='asc'|'desc';
type FilterKey='All'|'League'|'FA Cup'|'League Cup'|'Europe'|'Home'|'Away';
const filters:FilterKey[]=['All','League','FA Cup','League Cup','Europe','Home','Away'];
function SortIcon({active,dir}:{active:boolean;dir:SortDir}){if(!active)return <ChevronsUpDown size={12} className="col-sort-idle"/>;return dir==='desc'?<ArrowDown size={12}/>:<ArrowUp size={12}/>;}
function FormBadge({result}:{result:'W'|'D'|'L'}){return <span className={`form-pill form-${result.toLowerCase()}`}>{result}</span>;}

export default function Leaderboard(){
 const [teams,setTeams]=useState<Opponent[]>([]); const [loading,setLoading]=useState(true); const [error,setError]=useState<string|null>(supabaseConfigError);
 const [sortKey,setSortKey]=useState<SortKey>('played'); const [sortDir,setSortDir]=useState<SortDir>('desc'); const [filter,setFilter]=useState<FilterKey>('All');
 useEffect(()=>{
   if(!supabase){setLoading(false);return;}
   setLoading(true); setError(null);
   supabase.rpc('filtered_opponent_leaderboard',{p_filter:filter}).then(({data,error})=>{
     if(error)setError(error.message); else setTeams((data??[]) as Opponent[]); setLoading(false);
   }).catch((err:unknown)=>{setError(err instanceof Error?err.message:String(err));setLoading(false);});
 },[filter]);
 const sorted=useMemo(()=>[...teams].sort((a,b)=>{const delta=Number(a[sortKey])-Number(b[sortKey]);return sortDir==='asc'?delta:-delta;}),[teams,sortKey,sortDir]);
 const max=useMemo(()=>({gf:Math.max(1,...teams.map(t=>Number(t.goals_for))),ga:Math.max(1,...teams.map(t=>Number(t.goals_against))),gd:Math.max(1,...teams.map(t=>Math.abs(Number(t.goal_diff))))}),[teams]);
 function toggleSort(key:SortKey){if(key===sortKey)setSortDir(d=>d==='asc'?'desc':'asc');else{setSortKey(key);setSortDir('desc');}}
 const sortableHeading=(label:string,key:SortKey)=><button onClick={()=>toggleSort(key)} className={`col-sort ${sortKey===key?'active':''}`}>{label} <SortIcon active={sortKey===key} dir={sortDir}/></button>;
 return <div className="card lb-table-card">
  <div className="lb-table-header"><div className="lb-title-group"><span className="section-kicker">Team comparison</span><h2>League leaderboard</h2><p>All-time Leeds United record against every competitive opponent</p></div><div className="lb-table-meta"><span><i className="legend-dot orange-dot"/> Most played</span><span><i className="legend-dot dark-dot"/> Historical opponent</span></div></div>
  <div className="lb-filterbar"><span className="lb-filter-label">Competition</span><div className="lb-filter-pills">{filters.map(item=><button key={item} className={`lb-filter-pill ${filter===item?'active':''}`} onClick={()=>setFilter(item)} aria-pressed={filter===item}>{item}</button>)}</div></div>
  {loading?<div className="lb-loading">Loading {filter.toLowerCase()} opponents from Supabase…</div>:error?<div className="lb-loading"><strong>Data connection error:</strong> {error}</div>:<div className="lb-table-wrap"><table className="lb-table"><thead><tr><th className="col-rank">#</th><th className="col-team">Opponent</th><th className="col-stat">{sortableHeading('P','played')}</th><th className="col-stat">{sortableHeading('W','won')}</th><th className="col-stat">{sortableHeading('D','drawn')}</th><th className="col-stat">{sortableHeading('L','lost')}</th><th className="col-metric">{sortableHeading('GF','goals_for')}</th><th className="col-metric">{sortableHeading('GA','goals_against')}</th><th className="col-metric">{sortableHeading('GD','goal_diff')}</th><th className="col-metric">{sortableHeading('Win %','win_pct')}</th><th className="col-form">Last 5</th></tr></thead><tbody>
   {sorted.map((team,index)=><tr key={team.club_id} className={index===0&&sortKey==='played'&&sortDir==='desc'?'row-top':''}><td className="col-rank"><span className={`rank-badge ${index===0?'rank-top':index<3?'rank-podium':''}`}>{index+1}</span></td><td className="col-team"><div className="team-cell"><ClubCrest crestUrl={team.crest_url} name={team.opponent}/><span className="team-name">{team.opponent}</span></div></td><td className="col-stat">{team.played}</td><td className="col-stat">{team.won}</td><td className="col-stat">{team.drawn}</td><td className="col-stat">{team.lost}</td>
   <td className="col-metric"><div className="metric-cell"><span className="metric-value">{team.goals_for}</span><span className="metric-track"><span className="metric-fill orange-fill" style={{width:`${Number(team.goals_for)/max.gf*100}%`}}/></span></div></td>
   <td className="col-metric"><div className="metric-cell"><span className="metric-value">{team.goals_against}</span><span className="metric-track"><span className="metric-fill dark-fill" style={{width:`${Number(team.goals_against)/max.ga*100}%`}}/></span></div></td>
   <td className="col-metric"><div className="metric-cell"><span className="metric-value">{Number(team.goal_diff)>0?'+':''}{team.goal_diff}</span><span className="metric-track"><span className="metric-fill soft-fill" style={{width:`${Math.abs(Number(team.goal_diff))/max.gd*100}%`}}/></span></div></td>
   <td className="col-metric"><div className="metric-cell"><span className="metric-value">{Number(team.win_pct).toFixed(1)}%</span><span className="metric-track"><span className="metric-fill win-pct-fill" style={{width:`${Number(team.win_pct)}%`}}/></span></div></td>
   <td className="col-form"><div className="form-row">{(team.last5??'').split('').filter((r):r is 'W'|'D'|'L'=>r==='W'||r==='D'||r==='L').map((result,resultIndex)=><FormBadge key={resultIndex} result={result}/>)}</div></td></tr>)}
  </tbody></table></div>}
 </div>;
}
