import React,{useEffect,useMemo,useState}from'react';
import ClubCrest from'./ClubCrest';
import PlayerIcon from'./PlayerIcon';
import{supabase,supabaseConfigError}from'./supabase';
import'./PlayerOpponentWidgets.css';

type PlayerMatch={match_id:number};
type MatchRow={match_id:number;opponent_id:number;result:string};
type ClubRow={club_id:number;canonical_name:string;crest_url:string|null};
type GoalRow={match_id:number};
type OpponentRow={clubId:number;club:string;crest:string|null;apps:number;wins:number;winPct:number;goals:number;gpg:number};
type TeammateAppearance={match_id:number;player_id:number};
type TeammateMeta={player_id:number;display_name:string;profile_image_url:string|null;position_group:string|null};
type TeammateRow={playerId:number;name:string;src:string|null;position:string|null;apps:number};

function ScopeToggle({all,onChange}:{all:boolean;onChange:(value:boolean)=>void}){return <div className="player-opponent-scope" role="group" aria-label="Rows shown"><button type="button" className={!all?'active':''} onClick={()=>onChange(false)}>Top 5</button><button type="button" className={all?'active':''} onClick={()=>onChange(true)}>All</button></div>}

export default function PlayerOpponentWidgets({playerId}:{playerId:number}){
 const[rows,setRows]=useState<OpponentRow[]>([]),[teammates,setTeammates]=useState<TeammateRow[]>([]),[loading,setLoading]=useState(true),[error,setError]=useState<string|null>(supabaseConfigError);
 const[allApps,setAllApps]=useState(false),[allGoals,setAllGoals]=useState(false),[allTeammates,setAllTeammates]=useState(false);
 useEffect(()=>{let cancelled=false;(async()=>{if(!supabase){setLoading(false);return}setLoading(true);setError(null);
  const{data:pm,error:pmError}=await supabase.from('player_matches').select('match_id').eq('player_id',playerId);if(pmError){if(!cancelled){setError(pmError.message);setLoading(false)}return}
  const matchIds=((pm??[])as PlayerMatch[]).map(r=>r.match_id);if(!matchIds.length){if(!cancelled){setRows([]);setTeammates([]);setLoading(false)}return}
  const[{data:matchData,error:matchError},{data:teammateData,error:teammateError}]=await Promise.all([
   supabase.from('matches').select('match_id,opponent_id,result').in('match_id',matchIds),
   supabase.from('player_matches').select('match_id,player_id').in('match_id',matchIds).neq('player_id',playerId)
  ]);
  if(matchError||teammateError){if(!cancelled){setError((matchError??teammateError)?.message??'Unable to load player comparison');setLoading(false)}return}
  const matches=(matchData??[])as MatchRow[];const opponentIds=Array.from(new Set(matches.map(m=>m.opponent_id)));
  const teammateAppearances=(teammateData??[])as TeammateAppearance[];const teammateIds=Array.from(new Set(teammateAppearances.map(r=>r.player_id)));
  const[{data:clubData,error:clubError},{data:goalData,error:goalError},{data:teammateMetaData,error:teammateMetaError}]=await Promise.all([
   supabase.from('clubs').select('club_id,canonical_name,crest_url').in('club_id',opponentIds),
   supabase.from('goals').select('match_id').eq('leeds_player_id',playerId).eq('is_own_goal',false).in('match_id',matchIds),
   teammateIds.length?supabase.from('players').select('player_id,display_name,profile_image_url,position_group').in('player_id',teammateIds):Promise.resolve({data:[],error:null})
  ]);
  if(clubError||goalError||teammateMetaError){if(!cancelled){setError((clubError??goalError??teammateMetaError)?.message??'Unable to load player comparison');setLoading(false)}return}
  const clubs=new Map(((clubData??[])as ClubRow[]).map(c=>[c.club_id,c]));const matchById=new Map(matches.map(m=>[m.match_id,m]));const agg=new Map<number,{apps:number;wins:number;goals:number}>();
  for(const m of matches){const cur=agg.get(m.opponent_id)??{apps:0,wins:0,goals:0};cur.apps++;if(m.result==='Won')cur.wins++;agg.set(m.opponent_id,cur)}
  for(const g of(goalData??[])as GoalRow[]){const m=matchById.get(g.match_id);if(!m)continue;const cur=agg.get(m.opponent_id);if(cur)cur.goals++}
  const next=Array.from(agg.entries()).map(([clubId,v])=>{const c=clubs.get(clubId);return{clubId,club:c?.canonical_name??`Club ${clubId}`,crest:c?.crest_url??null,apps:v.apps,wins:v.wins,winPct:v.apps?v.wins/v.apps*100:0,goals:v.goals,gpg:v.apps?v.goals/v.apps:0}});
  const teammateCounts=new Map<number,Set<number>>();for(const row of teammateAppearances){const matchesForPlayer=teammateCounts.get(row.player_id)??new Set<number>();matchesForPlayer.add(row.match_id);teammateCounts.set(row.player_id,matchesForPlayer)}
  const teammateMeta=new Map(((teammateMetaData??[])as TeammateMeta[]).map(p=>[p.player_id,p]));
  const teammateRows=Array.from(teammateCounts.entries()).map(([id,sharedMatches])=>{const p=teammateMeta.get(id);return{playerId:id,name:p?.display_name??`Player ${id}`,src:p?.profile_image_url??null,position:p?.position_group??null,apps:sharedMatches.size}}).sort((a,b)=>b.apps-a.apps||a.name.localeCompare(b.name));
  if(!cancelled){setRows(next);setTeammates(teammateRows);setLoading(false)}})();return()=>{cancelled=true}},[playerId]);
 const byApps=useMemo(()=>[...rows].sort((a,b)=>b.apps-a.apps||a.club.localeCompare(b.club)),[rows]);
 const byGoals=useMemo(()=>rows.filter(r=>r.goals>0).sort((a,b)=>b.goals-a.goals||b.apps-a.apps||a.club.localeCompare(b.club)),[rows]);
 const maxGoals=Math.max(1,...byGoals.map(r=>r.goals));
 const maxTeammateApps=Math.max(1,...teammates.map(r=>r.apps));
 const state=loading?<div className="lb-loading">Loading opposition record…</div>:error?<div className="lb-loading">Opposition record unavailable</div>:null;
 const teammateState=loading?<div className="lb-loading">Loading teammate record…</div>:error?<div className="lb-loading">Teammate record unavailable</div>:null;
 return <>
  <section className={`card player-opponent-widget${!allApps?' top-five':''}`}><div className="player-opponent-widget-head"><div><span className="section-kicker">Opposition analysis</span><h2>Most Appearances vs Clubs</h2></div><ScopeToggle all={allApps} onChange={setAllApps}/></div>{state??<div className="player-opponent-widget-list">{(allApps?byApps:byApps.slice(0,5)).map(r=><div className="player-opponent-widget-row" key={r.clubId}><div className="player-opponent-widget-club"><ClubCrest crestUrl={r.crest} name={r.club}/><div><strong>{r.club}</strong><span><b>{r.wins}</b> wins / {r.apps} appearances</span></div></div><div className="player-opponent-widget-value"><strong>{r.winPct.toFixed(1)}%</strong><span>Win rate</span></div><div className="player-opponent-widget-track"><i style={{width:`${r.winPct}%`}}/></div></div>)}</div>}</section>
  <section className={`card player-opponent-widget${!allGoals?' top-five':''}`}><div className="player-opponent-widget-head"><div><span className="section-kicker">Opposition analysis</span><h2>Most Goals vs Clubs</h2></div><ScopeToggle all={allGoals} onChange={setAllGoals}/></div>{state??<div className="player-opponent-widget-list">{(allGoals?byGoals:byGoals.slice(0,5)).map(r=><div className="player-opponent-widget-row" key={r.clubId}><div className="player-opponent-widget-club"><ClubCrest crestUrl={r.crest} name={r.club}/><div><strong>{r.club}</strong><span><b>{r.goals}</b> goals / {r.apps} appearances</span></div></div><div className="player-opponent-widget-value"><strong>{r.gpg.toFixed(2)}</strong><span>Goals / app</span></div><div className="player-opponent-widget-track"><i style={{width:`${r.goals/maxGoals*100}%`}}/></div></div>)}</div>}</section>
  <section className={`card player-opponent-widget player-played-alongside-widget${!allTeammates?' top-five':''}`}><div className="player-opponent-widget-head"><div><span className="section-kicker">Teammate history</span><h2>Played Alongside</h2></div><ScopeToggle all={allTeammates} onChange={setAllTeammates}/></div>{teammateState??<div className="player-opponent-widget-list">{(allTeammates?teammates:teammates.slice(0,5)).map(r=><div className="player-opponent-widget-row" key={r.playerId}><div className="player-opponent-widget-club player-played-alongside-player"><PlayerIcon name={r.name} src={r.src}/><div><strong>{r.name}</strong><span>{r.position??'Player'} · <b>{r.apps}</b> shared appearances</span></div></div><div className="player-opponent-widget-value"><strong>{r.apps}</strong><span>Matches together</span></div><div className="player-opponent-widget-track"><i style={{width:`${r.apps/maxTeammateApps*100}%`}}/></div></div>)}</div>}</section>
 </>
}
