import React,{useEffect,useState}from'react';
import PlayerIcon from'./PlayerIcon';
import{supabase,supabaseConfigError}from'./supabase';
import'./PlayerOpponentWidgets.css';

type PlayerMatch={match_id:number};
type TeammateAppearance={match_id:number;player_id:number};
type TeammateMeta={player_id:number;display_name:string;profile_image_url:string|null;position_group:string|null};
type TeammateRow={playerId:number;name:string;src:string|null;position:string|null;apps:number};

function ScopeToggle({all,onChange}:{all:boolean;onChange:(value:boolean)=>void}){return <div className="player-opponent-scope" role="group" aria-label="Rows shown"><button type="button" className={!all?'active':''} onClick={()=>onChange(false)}>Top 5</button><button type="button" className={all?'active':''} onClick={()=>onChange(true)}>All</button></div>}

async function loadTeammateAppearances(matchIds:number[],playerId:number){
 const pageSize=1000,rows:TeammateAppearance[]=[];
 for(let from=0;;from+=pageSize){
  const{data,error}=await supabase.from('player_matches').select('match_id,player_id').in('match_id',matchIds).neq('player_id',playerId).order('match_id',{ascending:true}).order('player_id',{ascending:true}).range(from,from+pageSize-1);
  if(error)return{data:null,error};
  const page=(data??[])as TeammateAppearance[];rows.push(...page);
  if(page.length<pageSize)return{data:rows,error:null};
 }
}

export default function PlayerPlayedAlongsideWidget({playerId}:{playerId:number}){
 const[rows,setRows]=useState<TeammateRow[]>([]),[loading,setLoading]=useState(true),[error,setError]=useState<string|null>(supabaseConfigError),[all,setAll]=useState(false);
 useEffect(()=>{let cancelled=false;(async()=>{if(!supabase){setLoading(false);return}setLoading(true);setError(null);
  const{data:pm,error:pmError}=await supabase.from('player_matches').select('match_id').eq('player_id',playerId);if(pmError){if(!cancelled){setError(pmError.message);setLoading(false)}return}
  const matchIds=((pm??[])as PlayerMatch[]).map(r=>r.match_id);if(!matchIds.length){if(!cancelled){setRows([]);setLoading(false)}return}
  const{data:teammateData,error:teammateError}=await loadTeammateAppearances(matchIds,playerId);if(teammateError){if(!cancelled){setError(teammateError.message);setLoading(false)}return}
  const appearances=(teammateData??[])as TeammateAppearance[],ids=Array.from(new Set(appearances.map(r=>r.player_id)));
  const{data:metaData,error:metaError}=ids.length?await supabase.from('players').select('player_id,display_name,profile_image_url,position_group').in('player_id',ids):{data:[],error:null};if(metaError){if(!cancelled){setError(metaError.message);setLoading(false)}return}
  const counts=new Map<number,Set<number>>();for(const row of appearances){const set=counts.get(row.player_id)??new Set<number>();set.add(row.match_id);counts.set(row.player_id,set)}
  const meta=new Map(((metaData??[])as TeammateMeta[]).map(p=>[p.player_id,p]));const next=Array.from(counts.entries()).map(([id,shared])=>{const p=meta.get(id);return{playerId:id,name:p?.display_name??`Player ${id}`,src:p?.profile_image_url??null,position:p?.position_group??null,apps:shared.size}}).sort((a,b)=>b.apps-a.apps||a.name.localeCompare(b.name));
  if(!cancelled){setRows(next);setLoading(false)}})();return()=>{cancelled=true}},[playerId]);
 const maxApps=Math.max(1,...rows.map(r=>r.apps)),visible=all?rows:rows.slice(0,5);
 return <section className={`card player-opponent-widget player-played-alongside-widget${!all?' top-five':''}`}><div className="player-opponent-widget-head"><div><span className="section-kicker">Teammate history</span><h2>Played Alongside</h2></div><ScopeToggle all={all} onChange={setAll}/></div>{loading?<div className="lb-loading">Loading teammate record…</div>:error?<div className="lb-loading">Teammate record unavailable</div>:<div className="player-opponent-widget-list">{visible.map(r=><div className="player-opponent-widget-row" key={r.playerId}><div className="player-opponent-widget-club player-played-alongside-player"><PlayerIcon name={r.name} src={r.src}/><div><strong>{r.name}</strong><span>{r.position??'Player'} · <b>{r.apps}</b> shared appearances</span></div></div><div className="player-opponent-widget-value"><strong>{r.apps}</strong><span>Matches together</span></div><div className="player-opponent-widget-track"><i style={{width:`${r.apps/maxApps*100}%`}}/></div></div>)}</div>}</section>
}
