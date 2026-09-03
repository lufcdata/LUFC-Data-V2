import React,{useEffect,useMemo,useState}from'react';
import{supabase}from'./supabase';
import'./PlayerCareerMetrics.css';

type Metric={label:string;value:string;fill:number;rank?:string;tone?:'default'|'danger'};
type PlayerRow={position_group:string|null};
type PlayerMatchRow={match_id:number};
type MatchRow={opponent_score:number};

const baseMetrics:Metric[]=[
 {label:'Seasons',value:'18',fill:100,rank:'4th'},
 {label:'Appearances',value:'772',fill:100,rank:'2nd'},
 {label:'Starts',value:'771',fill:99.9,rank:'2nd'},
 {label:'Subbed On',value:'1',fill:1,rank:'407th'},
 {label:'Subbed Off',value:'10',fill:1.3,rank:'160th'},
 {label:'Goals Scored',value:'115',fill:14.9,rank:'5th'},
 {label:'Games Won',value:'406',fill:52.6,rank:'1st'},
 {label:'Win Rate',value:'52.6%',fill:52.6,rank:'117th'},
 {label:'Starts as Captain',value:'489',fill:63.3,rank:'1st'},
 {label:'Goals Per Game',value:'0.15',fill:15,rank:'206th'},
 {label:'Red Cards',value:'3',fill:30,rank:'6th',tone:'danger'},
];

const rankClass=(rank:string)=>rank==='1st'?' gold':rank==='2nd'?' silver':rank==='3rd'?' bronze':'';

export default function PlayerCareerMetrics({playerId=276}:{playerId?:number}){
 const[gkMetrics,setGkMetrics]=useState<Metric[]>([]);
 useEffect(()=>{let cancelled=false;async function load(){if(!supabase)return;const{data:player,error:playerError}=await supabase.from('players').select('position_group').eq('player_id',playerId).maybeSingle();if(playerError||cancelled)return;const isGoalkeeper=((player as PlayerRow|null)?.position_group??'').toUpperCase()==='GK';if(!isGoalkeeper){setGkMetrics([]);return}const{data:pm,error:pmError}=await supabase.from('player_matches').select('match_id').eq('player_id',playerId);if(pmError||cancelled)return;const matchIds=((pm??[])as PlayerMatchRow[]).map(r=>r.match_id);if(!matchIds.length){setGkMetrics([{label:'Clean Sheets',value:'0',fill:0},{label:'Clean Sheets Per Game',value:'0.00',fill:0}]);return}const{data:matches,error:matchError}=await supabase.from('matches').select('opponent_score').in('match_id',matchIds);if(matchError||cancelled)return;const rows=(matches??[])as MatchRow[];const apps=rows.length;const cleanSheets=rows.filter(m=>Number(m.opponent_score)===0).length;const perGame=apps?cleanSheets/apps:0;setGkMetrics([{label:'Clean Sheets',value:String(cleanSheets),fill:Math.min(100,perGame*100)},{label:'Clean Sheets Per Game',value:perGame.toFixed(2),fill:Math.min(100,perGame*100)}])}load();return()=>{cancelled=true}},[playerId]);
 const metrics=useMemo(()=>[...baseMetrics,...gkMetrics],[gkMetrics]);
 return <section className="card player-career-metrics"><div className="player-career-metrics-head"><div><span className="section-kicker">Career overview</span><h2>Leeds Career Metrics</h2></div></div><div className="player-career-metrics-list">{metrics.map(metric=><div className="player-career-metrics-row" key={metric.label}><div className="player-career-metrics-copy"><strong>{metric.label}</strong></div><div className="player-career-metrics-line"><span className={`player-career-metrics-track${metric.tone==='danger'?' danger':''}`}><i style={{width:`${metric.fill}%`}}/></span><span className={`player-career-metrics-value-rank${metric.rank?'':' no-rank'}`}><b>{metric.value}</b>{metric.rank?<em className={`player-career-metrics-rank${rankClass(metric.rank)}`}>{metric.rank}</em>:null}</span></div></div>)}</div></section>}
