import React,{useEffect,useMemo,useState}from'react';
import{supabase}from'./supabase';
import'./PlayerCareerMetrics.css';

type Metric={label:string;value:string;fill:number;tone?:'default'|'danger'};
type LeaderboardRow={manager_id:number;spells:number;played:number;won:number;drawn:number;lost:number;goals_for:number;goals_against:number;goal_diff:number;win_pct:number|string};
type MetricsRow={manager_id:number;days_in_charge:number;players_used:number;debuts_given:number;clean_sheets:number;opponents_faced:number;opponents_defeated:number;opponents_defeated_pct:number|string;wins_at_elland_road:number;league_points_won:number};
type MatchRow={season:string|null};

export default function ManagerCareerMetrics({managerId}:{managerId:number}){
 const[metrics,setMetrics]=useState<Metric[]>([]);
 useEffect(()=>{let cancelled=false;(async()=>{if(!supabase)return;const[{data:leaderboard,error:lbError},{data:extra,error:extraError},{data:matches,error:matchError}]=await Promise.all([
  supabase.rpc('filtered_manager_leaderboard',{p_filter:'All',p_venue:'All'}),
  supabase.rpc('get_manager_profile_metrics',{p_manager_id:managerId}),
  supabase.from('match_centre_summary').select('season').eq('leeds_manager_id',managerId)
 ]);if(lbError||extraError||matchError||cancelled)return;const current=((leaderboard??[])as LeaderboardRow[]).find(r=>Number(r.manager_id)===managerId),x=((extra??[])as MetricsRow[])[0];if(!current||!x){setMetrics([]);return}const seasons=new Set(((matches??[])as MatchRow[]).map(m=>m.season).filter((v):v is string=>Boolean(v))).size,p=Number(current.played),won=Number(current.won),drawn=Number(current.drawn),lost=Number(current.lost),gf=Number(current.goals_for),ga=Number(current.goals_against),gd=Number(current.goal_diff),winPct=Number(current.win_pct),oppPct=Number(x.opponents_defeated_pct);const next:Metric[]=[
  {label:'Seasons',value:String(seasons),fill:100},
  {label:'Matches',value:String(p),fill:100},
  {label:'Wins',value:String(won),fill:p?won/p*100:0},
  {label:'Draws',value:String(drawn),fill:p?drawn/p*100:0},
  {label:'Losses',value:String(lost),fill:p?lost/p*100:0,tone:'danger'},
  {label:'Win Rate',value:`${winPct.toFixed(1)}%`,fill:winPct},
  {label:'Goals For',value:String(gf),fill:p?Math.min(100,gf/p/2*100):0},
  {label:'Goals Against',value:String(ga),fill:p?Math.min(100,ga/p/2*100):0},
  {label:'Goal Difference',value:`${gd>0?'+':''}${gd}`,fill:p?Math.min(100,Math.abs(gd)/p*100):0},
  {label:'Clean Sheets',value:String(x.clean_sheets),fill:p?Number(x.clean_sheets)/p*100:0},
  {label:'Days In Charge',value:Number(x.days_in_charge).toLocaleString('en-GB'),fill:100},
  {label:'Players Used',value:String(x.players_used),fill:Math.min(100,Number(x.players_used))},
  {label:'Debuts Given',value:String(x.debuts_given),fill:Number(x.players_used)?Number(x.debuts_given)/Number(x.players_used)*100:0},
  {label:'Opponents Faced',value:String(x.opponents_faced),fill:100},
  {label:'Opponents Defeated',value:String(x.opponents_defeated),fill:Number(x.opponents_faced)?Number(x.opponents_defeated)/Number(x.opponents_faced)*100:0},
  {label:'Opponents Defeated %',value:`${oppPct.toFixed(1)}%`,fill:oppPct},
  {label:'Wins at Elland Road',value:String(x.wins_at_elland_road),fill:won?Number(x.wins_at_elland_road)/won*100:0},
  {label:'League Points Won',value:Number(x.league_points_won).toLocaleString('en-GB'),fill:p?Math.min(100,Number(x.league_points_won)/(p*3)*100):0}
 ];if(!cancelled)setMetrics(next)})().catch(()=>{});return()=>{cancelled=true}},[managerId]);
 const visible=useMemo(()=>metrics,[metrics]);
 return <section className="card player-career-metrics"><div className="player-career-metrics-head"><div><span className="section-kicker">Career overview</span><h2>Leeds Career Metrics</h2></div></div><div className="player-career-metrics-list">{visible.map(metric=><div className="player-career-metrics-row" key={metric.label}><div className="player-career-metrics-copy"><strong>{metric.label}</strong></div><div className="player-career-metrics-line"><span className={`player-career-metrics-track${metric.tone==='danger'?' danger':''}`}><i style={{width:`${Math.min(100,Math.max(0,metric.fill))}%`}}/></span><span className="player-career-metrics-value-rank no-rank"><b>{metric.value}</b></span></div></div>)}</div></section>;
}
