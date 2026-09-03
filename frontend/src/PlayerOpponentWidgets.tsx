import React,{useEffect,useMemo,useState}from'react';
import ClubCrest from'./ClubCrest';
import{supabase,supabaseConfigError}from'./supabase';
import'./PlayerOpponentWidgets.css';

type PlayerMatch={match_id:number};
type MatchRow={match_id:number;opponent_id:number;result:string};
type ClubRow={club_id:number;canonical_name:string;crest_url:string|null};
type GoalRow={match_id:number};
type OpponentRow={clubId:number;club:string;crest:string|null;apps:number;wins:number;winPct:number;goals:number;gpg:number};

function ScopeToggle({all,onChange}:{all:boolean;onChange:(value:boolean)=>void}){return <div className="player-opponent-scope" role="group" aria-label="Rows shown"><button type="button" className={!all?'active':''} onClick={()=>onChange(false)}>Top 5</button><button type="button" className={all?'active':''} onClick={()=>onChange(true)}>All</button></div>}

export default function PlayerOpponentWidgets({playerId}:{playerId:number}){
 const[rows,setRows]=useState<OpponentRow[]>([]),[loading,setLoading]=useState(true),[error,setError]=useState<string|null>(supabaseConfigError);
 const[allApps,setAllApps]=useState(false),[allGoals,setAllGoals]=useState(false);
 useEffect(()=>{let cancelled=false;(async()=>{if(!supabase){setLoading(false);return}setLoading(true);setError(null);
  const{data:pm,error:pmError}=await supabase.from('player_matches').select('match_id').eq('player_id',playerId);if(pmError){if(!cancelled){setError(pmError.message);setLoading(false)}return}
  const matchIds=((pm??[])as PlayerMatch[]).map(r=>r.match_id);if(!matchIds.length){if(!cancelled){setRows([]);setLoading(false)}return}
  const{data:matchData,error:matchError}=await supabase.from('matches').select('match_id,opponent_id,result').in('match_id',matchIds);if(matchError){if(!cancelled){setError(matchError.message);setLoading(false)}return}
  const matches=(matchData??[])as MatchRow[];const opponentIds=Array.from(new Set(matches.map(m=>m.opponent_id)));
  const{data:clubData,error:clubError}=await supabase.from('clubs').select('club_id,canonical_name,crest_url').in('club_id',opponentIds);if(clubError){if(!cancelled){setError(clubError.message);setLoading(false)}return}
  const{data:goalData,error:goalError}=await supabase.from('goals').select('match_id').eq('leeds_player_id',playerId).eq('is_own_goal',false).in('match_id',matchIds);if(goalError){if(!cancelled){setError(goalError.message);setLoading(false)}return}
  const clubs=new Map(((clubData??[])as ClubRow[]).map(c=>[c.club_id,c]));const matchById=new Map(matches.map(m=>[m.match_id,m]));const agg=new Map<number,{apps:number;wins:number;goals:number}>();
  for(const m of matches){const cur=agg.get(m.opponent_id)??{apps:0,wins:0,goals:0};cur.apps++;if(m.result==='Won')cur.wins++;agg.set(m.opponent_id,cur)}
  for(const g of(goalData??[])as GoalRow[]){const m=matchById.get(g.match_id);if(!m)continue;const cur=agg.get(m.opponent_id);if(cur)cur.goals++}
  const next=Array.from(agg.entries()).map(([clubId,v])=>{const c=clubs.get(clubId);return{clubId,club:c?.canonical_name??`Club ${clubId}`,crest:c?.crest_url??null,apps:v.apps,wins:v.wins,winPct:v.apps?v.wins/v.apps*100:0,goals:v.goals,gpg:v.apps?v.goals/v.apps:0}});
  if(!cancelled){setRows(next);setLoading(false)}})();return()=>{cancelled=true}},[playerId]);
 const byApps=useMemo(()=>[...rows].sort((a,b)=>b.apps-a.apps||a.club.localeCompare(b.club)),[rows]);
 const byGoals=useMemo(()=>rows.filter(r=>r.goals>0).sort((a,b)=>b.goals-a.goals||b.apps-a.apps||a.club.localeCompare(b.club)),[rows]);
 const maxGoals=Math.max(1,...byGoals.map(r=>r.goals));
 const state=loading?<div className="lb-loading">Loading opposition record…</div>:error?<div className="lb-loading">Opposition record unavailable</div>:null;
 return <>
  <section className={`card player-opponent-widget${!allApps?' top-five':''}`}><div className="player-opponent-widget-head"><div><span className="section-kicker">Opposition analysis</span><h2>Most Appearances vs Clubs</h2></div><ScopeToggle all={allApps} onChange={setAllApps}/></div>{state??<div className="player-opponent-widget-list">{(allApps?byApps:byApps.slice(0,5)).map(r=><div className="player-opponent-widget-row" key={r.clubId}><div className="player-opponent-widget-club"><ClubCrest crestUrl={r.crest} name={r.club}/><div><strong>{r.club}</strong><span><b>{r.wins}</b> wins / {r.apps} appearances</span></div></div><div className="player-opponent-widget-value"><strong>{r.winPct.toFixed(1)}%</strong><span>Win rate</span></div><div className="player-opponent-widget-track"><i style={{width:`${r.winPct}%`}}/></div></div>)}</div>}</section>
  <section className={`card player-opponent-widget${!allGoals?' top-five':''}`}><div className="player-opponent-widget-head"><div><span className="section-kicker">Opposition analysis</span><h2>Most Goals vs Clubs</h2></div><ScopeToggle all={allGoals} onChange={setAllGoals}/></div>{state??<div className="player-opponent-widget-list">{(allGoals?byGoals:byGoals.slice(0,5)).map(r=><div className="player-opponent-widget-row" key={r.clubId}><div className="player-opponent-widget-club"><ClubCrest crestUrl={r.crest} name={r.club}/><div><strong>{r.club}</strong><span><b>{r.goals}</b> goals / {r.apps} appearances</span></div></div><div className="player-opponent-widget-value"><strong>{r.gpg.toFixed(2)}</strong><span>Goals / app</span></div><div className="player-opponent-widget-track"><i style={{width:`${r.goals/maxGoals*100}%`}}/></div></div>)}</div>}</section>
 </>
}
