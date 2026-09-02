import React, { useEffect, useMemo, useState } from 'react';
import { ArrowDown, ArrowUp, ChevronsUpDown, Search } from 'lucide-react';
import { supabase, supabaseConfigError } from './supabase';
import ClubCrest from './ClubCrest';

type Opponent = { club_id:number; opponent:string; crest_url:string|null; played:number; won:number; drawn:number; lost:number; goals_for:number; goals_against:number; goal_diff:number; goals_per_game:number|string; clean_sheets:number; win_pct:number|string; loss_pct:number|string; last_meeting:string|null; last_won:string|null; last_lost:string|null; last5:string|null; };
type SortKey='played'|'won'|'drawn'|'lost'|'points'|'goals_for'|'goals_against'|'goal_diff'|'goals_per_game'|'clean_sheets'|'win_pct'|'loss_pct'|'last_meeting'|'last_won'|'last_lost';
type SortDir='asc'|'desc';
type FilterKey='All'|'League'|'Premier League'|'FA Cup'|'League Cup'|'Europe';
type VenueKey='All'|'Home'|'Away'|'Neutral';
const filters:FilterKey[]=['All','League','Premier League','FA Cup','League Cup','Europe'];
const venues:VenueKey[]=['All','Home','Away','Neutral'];
function SortIcon({active,dir}:{active:boolean;dir:SortDir}){if(!active)return <ChevronsUpDown size={12} className="col-sort-idle"/>;return dir==='desc'?<ArrowDown size={12}/>:<ArrowUp size={12}/>;}
function FormBadge({result}:{result:'W'|'D'|'L'}){return <span className={`form-pill form-${result.toLowerCase()}`}>{result}</span>;}
function year(value:string|null){return value?String(new Date(`${value}T00:00:00`).getFullYear()):'-';}
function points(team:Opponent){return Number(team.won)*3+Number(team.drawn);}
function goalDiffFillClass(value:number|string){const gd=Number(value);return gd>0?'win-pct-fill':gd<0?'loss-pct-fill':'soft-fill';}

export default function Leaderboard(){
 const [teams,setTeams]=useState<Opponent[]>([]); const [loading,setLoading]=useState(true); const [error,setError]=useState<string|null>(supabaseConfigError);
 const [sortKey,setSortKey]=useState<SortKey>('played'); const [sortDir,setSortDir]=useState<SortDir>('desc'); const [filter,setFilter]=useState<FilterKey>('All'); const [venue,setVenue]=useState<VenueKey>('All');
 const [fivePlus,setFivePlus]=useState(false); const [search,setSearch]=useState('');
 useEffect(()=>{if(!supabase){setLoading(false);return;} setLoading(true);setError(null); supabase.rpc('filtered_opponent_leaderboard',{p_filter:filter,p_venue:venue}).then(({data,error})=>{if(error)setError(error.message);else setTeams((data??[]) as Opponent[]);setLoading(false);}).catch((err:unknown)=>{setError(err instanceof Error?err.message:String(err));setLoading(false);});},[filter,venue]);
 useEffect(()=>{if(filter!=='Premier League'&&sortKey==='points'){setSortKey('played');setSortDir('desc');}},[filter,sortKey]);
 const visible=useMemo(()=>{const q=search.trim().toLowerCase();return teams.filter(team=>(!fivePlus||Number(team.played)>=5)&&(!q||team.opponent.toLowerCase().includes(q)));},[teams,fivePlus,search]);
 const sorted=useMemo(()=>[...visible].sort((a,b)=>{
   if(sortKey.startsWith('last_')){
     const av=a[sortKey] as string|null; const bv=b[sortKey] as string|null;
     const aMissing=!av || av==='-'; const bMissing=!bv || bv==='-';
     if(aMissing && bMissing) return a.opponent.localeCompare(b.opponent);
     if(aMissing) return sortDir==='asc' ? -1 : 1;
     if(bMissing) return sortDir==='asc' ? 1 : -1;
     const aTime=Date.parse(`${av}T00:00:00`); const bTime=Date.parse(`${bv}T00:00:00`);
     const delta=aTime-bTime;
     if(delta===0) return a.opponent.localeCompare(b.opponent);
     return sortDir==='asc' ? delta : -delta;
   }
   const aValue=sortKey==='points'?points(a):Number(a[sortKey]);
   const bValue=sortKey==='points'?points(b):Number(b[sortKey]);
   const delta=aValue-bValue;
   if(delta===0) return a.opponent.localeCompare(b.opponent);
   return sortDir==='asc'?delta:-delta;
 }),[visible,sortKey,sortDir]);
 const max=useMemo(()=>({gf:Math.max(1,...visible.map(t=>Number(t.goals_for))),ga:Math.max(1,...visible.map(t=>Number(t.goals_against))),gd:Math.max(1,...visible.map(t=>Math.abs(Number(t.goal_diff)))),gpg:Math.max(1,...visible.map(t=>Number(t.goals_per_game))),cs:Math.max(1,...visible.map(t=>Number(t.clean_sheets)))}),[visible]);
 function toggleSort(key:SortKey){if(key===sortKey)setSortDir(d=>d==='asc'?'desc':'asc');else{setSortKey(key);setSortDir('desc');}}
 const sortableHeading=(label:string,key:SortKey)=><button onClick={()=>toggleSort(key)} className={`col-sort ${sortKey===key?'active':''}`}>{label} <SortIcon active={sortKey===key} dir={sortDir}/></button>;
 const isPremierLeague=filter==='Premier League';
 return <>
 <div className="card lb-table-card">
  <div className="lb-table-header"><div className="lb-title-group"><span className="section-kicker">Team comparison</span><h2>Opponents Faced</h2><p>All-time Leeds United record against every competitive opponent</p></div></div>
  <div className="lb-filterbar">
   <div className="lb-filter-section"><span className="lb-filter-label">Competition</span><div className="lb-filter-pills">{filters.map(item=><button key={item} className={`lb-filter-pill ${filter===item?'active':''}`} onClick={()=>setFilter(item)} aria-pressed={filter===item}>{item}</button>)}</div></div>
   <div className="lb-filter-section lb-venue-section"><span className="lb-filter-label">Venue</span><div className="lb-filter-pills">{venues.map(item=><button key={item} className={`lb-filter-pill ${venue===item?'active':''}`} onClick={()=>setVenue(item)} aria-pressed={venue===item}>{item}</button>)}</div></div>
   <button className={`lb-five-toggle ${fivePlus?'active':''}`} onClick={()=>setFivePlus(v=>!v)} aria-pressed={fivePlus}><span className="lb-toggle-track"><span className="lb-toggle-knob"/></span><span>+5 Matches</span></button>
   <label className="lb-search"><Search size={14}/><input value={search} onChange={e=>setSearch(e.target.value)} placeholder="Search opponent" aria-label="Search opponents"/></label>
  </div>
  {loading?<div className="lb-loading">Loading {filter.toLowerCase()} · {venue.toLowerCase()} opponents from the Lufcdatabase…</div>:error?<div className="lb-loading"><strong>Data connection error:</strong> {error}</div>:<div className="lb-table-wrap"><table className="lb-table"><thead><tr><th className="col-rank">#</th><th className="col-team">Opponent</th><th className="col-stat">{sortableHeading('P','played')}</th><th className="col-stat">{sortableHeading('W','won')}</th><th className="col-stat">{sortableHeading('D','drawn')}</th><th className="col-stat">{sortableHeading('L','lost')}</th>{isPremierLeague&&<th className="col-stat col-points">{sortableHeading('Pts','points')}</th>}<th className="col-metric">{sortableHeading('GF','goals_for')}</th><th className="col-metric">{sortableHeading('GA','goals_against')}</th><th className="col-metric">{sortableHeading('GD','goal_diff')}</th><th className="col-metric">{sortableHeading('GPG','goals_per_game')}</th><th className="col-metric">{sortableHeading('CS','clean_sheets')}</th><th className="col-metric">{sortableHeading('Win %','win_pct')}</th><th className="col-metric">{sortableHeading('Loss %','loss_pct')}</th><th className="col-year">{sortableHeading('Last Played','last_meeting')}</th><th className="col-year">{sortableHeading('Last Won','last_won')}</th><th className="col-year">{sortableHeading('Last Lost','last_lost')}</th><th className="col-form">Last 5</th></tr></thead><tbody>
   {sorted.map((team,index)=><tr key={team.club_id} className={index===0&&sortKey==='played'&&sortDir==='desc'?'row-top':''}><td className="col-rank"><span className={`rank-badge ${index===0?'rank-top':index<3?'rank-podium':''}`}>{index+1}</span></td><td className="col-team"><div className="team-cell"><ClubCrest crestUrl={team.crest_url} name={team.opponent}/><span className="team-name">{team.opponent}</span></div></td><td className="col-stat">{team.played}</td><td className="col-stat">{team.won}</td><td className="col-stat">{team.drawn}</td><td className="col-stat">{team.lost}</td>{isPremierLeague&&<td className="col-stat col-points-value">{points(team)}</td>}
   <td className="col-metric"><div className="metric-cell"><span className="metric-value">{team.goals_for}</span><span className="metric-track"><span className="metric-fill orange-fill" style={{width:`${Number(team.goals_for)/max.gf*100}%`}}/></span></div></td>
   <td className="col-metric"><div className="metric-cell"><span className="metric-value">{team.goals_against}</span><span className="metric-track"><span className="metric-fill dark-fill" style={{width:`${Number(team.goals_against)/max.ga*100}%`}}/></span></div></td>
   <td className="col-metric"><div className="metric-cell"><span className="metric-value">{Number(team.goal_diff)>0?'+':''}{team.goal_diff}</span><span className="metric-track"><span className={`metric-fill ${goalDiffFillClass(team.goal_diff)}`} style={{width:`${Math.abs(Number(team.goal_diff))/max.gd*100}%`}}/></span></div></td>
   <td className="col-metric"><div className="metric-cell"><span className="metric-value">{Number(team.goals_per_game).toFixed(2)}</span><span className="metric-track"><span className="metric-fill orange-fill" style={{width:`${Number(team.goals_per_game)/max.gpg*100}%`}}/></span></div></td>
   <td className="col-metric"><div className="metric-cell"><span className="metric-value">{team.clean_sheets}</span><span className="metric-track"><span className="metric-fill soft-fill" style={{width:`${Number(team.clean_sheets)/max.cs*100}%`}}/></span></div></td>
   <td className="col-metric"><div className="metric-cell"><span className="metric-value">{Number(team.win_pct).toFixed(1)}%</span><span className="metric-track"><span className="metric-fill win-pct-fill" style={{width:`${Number(team.win_pct)}%`}}/></span></div></td>
   <td className="col-metric"><div className="metric-cell"><span className="metric-value">{Number(team.loss_pct).toFixed(1)}%</span><span className="metric-track"><span className="metric-fill loss-pct-fill" style={{width:`${Number(team.loss_pct)}%`}}/></span></div></td>
   <td className="col-year metric-value">{year(team.last_meeting)}</td><td className="col-year metric-value">{year(team.last_won)}</td><td className="col-year metric-value">{year(team.last_lost)}</td>
   <td className="col-form"><div className="form-row">{(team.last5??'').split('').filter((r):r is 'W'|'D'|'L'=>r==='W'||r==='D'||r==='L').map((result,resultIndex)=><FormBadge key={resultIndex} result={result}/>)}</div></td></tr>)}
  </tbody></table>{sorted.length===0&&<div className="lb-empty">No opponents match these filters.</div>}</div>}
 </div>
 <div className="card lb-legend" aria-label="Table abbreviations"><div className="lb-legend-items"><span>P Played</span><span>W Won</span><span>D Drawn</span><span>L Lost</span>{isPremierLeague&&<span>Pts Points</span>}<span>GF Goals For</span><span>GA Goals Against</span><span>GD Goal Difference</span><span>GPG Goals Per Game</span><span>CS Clean Sheets</span></div><div className="lb-legend-last5">Last 5 matches played by most recent from right to left</div></div>
 </>;
}
