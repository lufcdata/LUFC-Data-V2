import React,{useEffect,useMemo,useState}from'react';
import{supabase}from'./supabase';
import'./PlayerCareerMetrics.css';

type Metric={label:string;value:string;fill:number;rank?:string;tone?:'default'|'danger'};
type PlayerRow={position_group:string|null};
type PlayerMatchRow={match_id:number};
type MatchRow={season_id:number|null;opponent_score:number};
type LeaderboardRow={player_id:number;appearances:number;starts:number;sub_apps:number;sub_off:number;won:number;win_pct:number|string;goals:number;gpg:number|string;captain:number;red_cards:number};

const rankClass=(rank:string)=>rank==='1st'?' gold':rank==='2nd'?' silver':rank==='3rd'?' bronze':'';
function ordinal(n:number){const m=n%100;if(m>=11&&m<=13)return`${n}th`;return`${n}${n%10===1?'st':n%10===2?'nd':n%10===3?'rd':'th'}`}
function rankFor(rows:LeaderboardRow[],playerId:number,key:keyof Pick<LeaderboardRow,'appearances'|'starts'|'sub_apps'|'sub_off'|'won'|'win_pct'|'goals'|'gpg'|'captain'|'red_cards'>){const current=rows.find(r=>r.player_id===playerId);if(!current)return undefined;const value=Number(current[key]);return ordinal(1+rows.filter(r=>Number(r[key])>value).length)}

export default function PlayerCareerMetrics({playerId}:{playerId:number}){
 const[metrics,setMetrics]=useState<Metric[]>([]),[gkMetrics,setGkMetrics]=useState<Metric[]>([]);
 useEffect(()=>{let cancelled=false;(async()=>{if(!supabase)return;
  const[{data:leaderboard,error:lbError},{data:player,error:playerError},{data:pm,error:pmError}]=await Promise.all([
   supabase.rpc('filtered_player_leaderboard',{p_filter:'All',p_venue:'All'}),
   supabase.from('players').select('position_group').eq('player_id',playerId).maybeSingle(),
   supabase.from('player_matches').select('match_id').eq('player_id',playerId)
  ]);if(lbError||playerError||pmError||cancelled)return;
  const rows=(leaderboard??[])as LeaderboardRow[],current=rows.find(r=>r.player_id===playerId),matchIds=((pm??[])as PlayerMatchRow[]).map(r=>r.match_id);if(!current){setMetrics([]);return}
  const{data:matches,error:matchError}=matchIds.length?await supabase.from('matches').select('season_id,opponent_score').in('match_id',matchIds):{data:[],error:null};if(matchError||cancelled)return;
  const matchRows=(matches??[])as MatchRow[],seasons=new Set(matchRows.map(m=>m.season_id).filter((v):v is number=>v!=null)).size,apps=Number(current.appearances),starts=Number(current.starts),subOn=Number(current.sub_apps),subOff=Number(current.sub_off),goals=Number(current.goals),wins=Number(current.won),winPct=Number(current.win_pct),captain=Number(current.captain),gpg=Number(current.gpg),reds=Number(current.red_cards);
  const billyRanks:Record<string,string>|null=playerId===276?{Seasons:'4th','Goals Per Game':'206th'}:null;
  const next:Metric[]=[
   {label:'Seasons',value:String(seasons),fill:100,rank:billyRanks?.Seasons},
   {label:'Appearances',value:String(apps),fill:100,rank:rankFor(rows,playerId,'appearances')},
   {label:'Starts',value:String(starts),fill:apps?starts/apps*100:0,rank:rankFor(rows,playerId,'starts')},
   {label:'Subbed On',value:String(subOn),fill:subOn?Math.max(1,apps?subOn/apps*100:0):0,rank:rankFor(rows,playerId,'sub_apps')},
   {label:'Subbed Off',value:String(subOff),fill:apps?subOff/apps*100:0,rank:rankFor(rows,playerId,'sub_off')},
   {label:'Goals Scored',value:String(goals),fill:apps?goals/apps*100:0,rank:rankFor(rows,playerId,'goals')},
   {label:'Games Won',value:String(wins),fill:apps?wins/apps*100:0,rank:rankFor(rows,playerId,'won')},
   {label:'Win Rate',value:`${winPct.toFixed(1)}%`,fill:winPct,rank:rankFor(rows,playerId,'win_pct')},
   {label:'Starts as Captain',value:String(captain),fill:apps?captain/apps*100:0,rank:rankFor(rows,playerId,'captain')},
   {label:'Goals Per Game',value:gpg.toFixed(2),fill:Math.min(100,gpg*100),rank:billyRanks?.['Goals Per Game']??rankFor(rows,playerId,'gpg')},
   {label:'Red Cards',value:String(reds),fill:Math.min(100,reds*10),rank:rankFor(rows,playerId,'red_cards'),tone:'danger'}
  ];
  const isGoalkeeper=((player as PlayerRow|null)?.position_group??'').toUpperCase()==='GK';if(isGoalkeeper){const cleanSheets=matchRows.filter(m=>Number(m.opponent_score)===0).length,perGame=apps?cleanSheets/apps:0;setGkMetrics([{label:'Clean Sheets',value:String(cleanSheets),fill:perGame*100},{label:'Clean Sheets Per Game',value:perGame.toFixed(2),fill:perGame*100}])}else setGkMetrics([]);setMetrics(next)})().catch(()=>{});return()=>{cancelled=true}},[playerId]);
 const visible=useMemo(()=>[...metrics,...gkMetrics],[metrics,gkMetrics]);
 return <section className="card player-career-metrics"><div className="player-career-metrics-head"><div><span className="section-kicker">Career overview</span><h2>Leeds Career Metrics</h2></div></div><div className="player-career-metrics-list">{visible.map(metric=><div className="player-career-metrics-row" key={metric.label}><div className="player-career-metrics-copy"><strong>{metric.label}</strong></div><div className="player-career-metrics-line"><span className={`player-career-metrics-track${metric.tone==='danger'?' danger':''}`}><i style={{width:`${Math.min(100,metric.fill)}%`}}/></span><span className={`player-career-metrics-value-rank${metric.rank?'':' no-rank'}`}><b>{metric.value}</b>{metric.rank?<em className={`player-career-metrics-rank${rankClass(metric.rank)}`}>{metric.rank}</em>:null}</span></div></div>)}</div></section>}
