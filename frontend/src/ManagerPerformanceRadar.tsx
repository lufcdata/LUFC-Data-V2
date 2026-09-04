import React,{useEffect,useMemo,useState}from'react';
import{supabase,supabaseConfigError}from'./supabase';
import'./ManagerPerformanceRadar.css';

type RadarRow={manager_id:number;attacking_score:number;results_score:number;defensive_score:number;achievements_score:number;discipline_score:number;personnel_score:number;longevity_score:number;goals_per_game:number|string|null;win_rate:number|string|null;goals_against_per_game:number|string|null;clean_sheets_per_game:number|string|null;honours:number;promotions:number;relegations:number;red_cards:number;red_cards_per_game:number|string|null;players_used:number;seasons:number;players_per_season:number|string|null;days_in_charge:number;top_flight_titles:number};
type Axis={label:string;score:number;raw:string};
const cx=205,cy=158,radius=94,labelRadius=132;
function point(index:number,value:number,total:number,r=radius){const a=-Math.PI/2+index*Math.PI*2/total,rr=r*Math.max(0,Math.min(100,value))/100;return{x:cx+Math.cos(a)*rr,y:cy+Math.sin(a)*rr}}
function polygon(values:number[],r=radius){return values.map((v,i)=>{const p=point(i,v,values.length,r);return`${p.x.toFixed(1)},${p.y.toFixed(1)}`}).join(' ')}
function formatDays(n:number){return n.toLocaleString('en-GB')+' days'}

export default function ManagerPerformanceRadar({managerId}:{managerId:number}){
 const[data,setData]=useState<RadarRow|null>(null),[loading,setLoading]=useState(true),[error,setError]=useState<string|null>(supabaseConfigError);
 useEffect(()=>{let cancelled=false;(async()=>{if(!supabase){setLoading(false);return}setLoading(true);setError(null);const{data,error}=await supabase.rpc('get_manager_performance_radar',{p_manager_id:managerId});if(cancelled)return;if(error){setError(error.message);setData(null)}else setData(((data??[])as RadarRow[])[0]??null);setLoading(false)})();return()=>{cancelled=true}},[managerId]);
 const axes=useMemo<Axis[]>(()=>data?[
  {label:'Attacking',score:data.attacking_score,raw:`${Number(data.goals_per_game??0).toFixed(2)} goals/game`},
  {label:'Results',score:data.results_score,raw:`${Number(data.win_rate??0).toFixed(1)}% win rate`},
  {label:'Defensive',score:data.defensive_score,raw:`${Number(data.goals_against_per_game??0).toFixed(2)} GA/game · ${(Number(data.clean_sheets_per_game??0)*100).toFixed(1)}% CS`},
  {label:'Achievements',score:data.achievements_score,raw:`${data.honours} honours · ${data.promotions} promotions · ${data.relegations} relegations`},
  {label:'Discipline',score:data.discipline_score,raw:`${Number(data.red_cards_per_game??0).toFixed(3)} reds/game`},
  {label:'Personnel',score:data.personnel_score,raw:`${Number(data.players_per_season??0).toFixed(1)} players/season`},
  {label:'Longevity',score:data.longevity_score,raw:formatDays(data.days_in_charge)}
 ]:[],[data]);
 if(loading)return <section className="card manager-radar-card"><div className="lb-loading">Loading manager performance profile…</div></section>;
 if(error||!data)return <section className="card manager-radar-card"><div className="lb-loading">Manager performance profile unavailable</div></section>;
 const values=axes.map(a=>a.score),rings=[20,40,60,80,100];
 return <section className="card manager-radar-card"><div className="manager-radar-head"><div><span className="section-kicker">Manager profile</span><h2>Performance Distribution</h2><p>Intentionally harsh Leeds-relative scoring: a larger polygon means a stronger profile.</p></div><span className="manager-radar-scale">0–100</span></div>
  <div className="manager-radar-layout"><svg className="manager-radar-svg" viewBox="0 0 410 330" role="img" aria-label="Manager performance distribution radar chart">
   {rings.map(level=><polygon key={level} className={`manager-radar-ring ${level===100?'outer':''}`} points={polygon(Array(7).fill(100),radius*level/100)}/>)}
   {axes.map((_,i)=>{const p=point(i,100,axes.length);return <line key={i} className="manager-radar-axis" x1={cx} y1={cy} x2={p.x} y2={p.y}/>})}
   <polygon className="manager-radar-shape" points={polygon(values)}/>
   {axes.map((a,i)=>{const p=point(i,100,axes.length,labelRadius),anchor=Math.abs(p.x-cx)<18?'middle':p.x<cx?'end':'start';return <g key={a.label} className="manager-radar-label" transform={`translate(${p.x} ${p.y})`}><text textAnchor={anchor} y="-7" className="manager-radar-score">{a.score}</text><text textAnchor={anchor} y="8" className="manager-radar-name">{a.label}</text><text textAnchor={anchor} y="22" className="manager-radar-raw">{a.raw}</text></g>})}
  </svg><div className="manager-radar-logic"><strong>Scoring logic</strong><p><b>Attacking</b> goals/game · <b>Results</b> win rate · <b>Defensive</b> lower goals conceded/game + clean sheets/game · <b>Achievements</b> honours/promotions with relegations heavily penalised and top-flight-title ceilings · <b>Discipline</b> red cards/game, reversed so fewer is better · <b>Personnel</b> players used ÷ seasons · <b>Longevity</b> days in charge.</p><span>Rate metrics remain stabilised against the Leeds managerial average for very short spells; the overall scale is compressed so elite scores are harder to reach.</span></div></div>
 </section>;
}
