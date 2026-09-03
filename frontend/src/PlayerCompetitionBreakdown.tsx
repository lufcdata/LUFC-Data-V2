import React,{useEffect,useState}from'react';
import{supabase,supabaseConfigError}from'./supabase';
import'./PlayerCompetitionBreakdown.css';

type PlayerMatch={match_id:number};
type MatchRow={match_id:number;competition_id:number|null;result:string};
type CompetitionRow={competition_id:number;canonical_name:string};
type GoalRow={match_id:number};
type CompetitionStat={competitionId:number;competition:string;apps:number;goals:number;won:number;winPct:number};

export default function PlayerCompetitionBreakdown({playerId}:{playerId:number}){
 const[rows,setRows]=useState<CompetitionStat[]>([]),[loading,setLoading]=useState(true),[error,setError]=useState<string|null>(supabaseConfigError);
 useEffect(()=>{let cancelled=false;(async()=>{if(!supabase){setLoading(false);return}setLoading(true);setError(null);
  const{data:pm,error:pmError}=await supabase.from('player_matches').select('match_id').eq('player_id',playerId);if(pmError){if(!cancelled){setError(pmError.message);setLoading(false)}return}
  const matchIds=((pm??[])as PlayerMatch[]).map(r=>r.match_id);if(!matchIds.length){if(!cancelled){setRows([]);setLoading(false)}return}
  const[{data:matches,error:matchError},{data:goals,error:goalError}]=await Promise.all([
   supabase.from('matches').select('match_id,competition_id,result').in('match_id',matchIds),
   supabase.from('goals').select('match_id').eq('leeds_player_id',playerId).eq('is_own_goal',false).in('match_id',matchIds)
  ]);if(matchError||goalError){if(!cancelled){setError((matchError??goalError)?.message??'Unable to load competition breakdown');setLoading(false)}return}
  const matchRows=(matches??[])as MatchRow[],competitionIds=Array.from(new Set(matchRows.map(m=>m.competition_id).filter((v):v is number=>v!=null)));
  const{data:competitionData,error:competitionError}=competitionIds.length?await supabase.from('competitions').select('competition_id,canonical_name').in('competition_id',competitionIds):{data:[],error:null};if(competitionError){if(!cancelled){setError(competitionError.message);setLoading(false)}return}
  const competitionMap=new Map(((competitionData??[])as CompetitionRow[]).map(c=>[c.competition_id,c.canonical_name])),matchMap=new Map(matchRows.map(m=>[m.match_id,m])),agg=new Map<number,{apps:number;goals:number;won:number}>();
  for(const m of matchRows){if(m.competition_id==null)continue;const cur=agg.get(m.competition_id)??{apps:0,goals:0,won:0};cur.apps++;if(m.result==='Won')cur.won++;agg.set(m.competition_id,cur)}
  for(const g of(goals??[])as GoalRow[]){const m=matchMap.get(g.match_id);if(m?.competition_id==null)continue;const cur=agg.get(m.competition_id);if(cur)cur.goals++}
  const next=Array.from(agg.entries()).map(([competitionId,v])=>({competitionId,competition:competitionMap.get(competitionId)??`Competition ${competitionId}`,apps:v.apps,goals:v.goals,won:v.won,winPct:v.apps?v.won/v.apps*100:0})).sort((a,b)=>b.apps-a.apps||a.competition.localeCompare(b.competition));
  if(!cancelled){setRows(next);setLoading(false)}})();return()=>{cancelled=true}},[playerId]);
 return <section className="card player-competition-compact">
  <div className="player-profile-panelhead"><div><span className="section-kicker">Career analysis</span><h2>Competition Breakdown</h2></div><div className="section-kicker">{loading?'…':`${rows.length} ${rows.length===1?'Competition':'Competitions'}`}</div></div>
  {loading?<div className="lb-loading">Loading competition breakdown…</div>:error?<div className="lb-loading">Competition breakdown unavailable</div>:rows.length?<div className="player-competition-compact-list">
   {rows.map(r=><div className="player-competition-compact-row" key={r.competitionId}>
    <div className="player-competition-compact-main"><strong>{r.competition}</strong><span>{r.apps} apps · {r.goals} goals · {r.won} wins</span></div>
    <div className="player-competition-compact-rate"><strong>{r.winPct.toFixed(1)}%</strong><span>Win rate</span></div>
    <div className="player-competition-compact-track"><i style={{width:`${r.winPct}%`}}/></div>
   </div>)}
  </div>:<div className="lb-empty">No competition appearances found for this player.</div>}
 </section>;
}
