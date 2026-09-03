import React,{useEffect,useMemo,useState}from'react';
import{supabase,supabaseConfigError}from'./supabase';
import'./PlayerManagerWidget.css';

type ManagerRow={managerId:number;name:string;src:string|null;apps:number;won:number;winPct:number};
type PlayerMatch={match_id:number};
type MatchRow={match_id:number;manager_spell_id:number|null;result:string};
type SpellRow={manager_spell_id:number;manager_id:number};
type ManagerMeta={manager_id:number;canonical_name:string;profile_image_url:string|null};

export default function PlayerManagerWidget({playerId,playerName}:{playerId:number;playerName:string}){
 const[rows,setRows]=useState<ManagerRow[]>([]),[loading,setLoading]=useState(true),[error,setError]=useState<string|null>(supabaseConfigError);
 useEffect(()=>{let cancelled=false;async function load(){if(!supabase){setLoading(false);return}setLoading(true);setError(null);
  const{data:pm,error:pmError}=await supabase.from('player_matches').select('match_id').eq('player_id',playerId);if(pmError){if(!cancelled){setError(pmError.message);setLoading(false)}return}
  const matchIds=((pm??[])as PlayerMatch[]).map(r=>r.match_id);if(!matchIds.length){if(!cancelled){setRows([]);setLoading(false)}return}
  const{data:matches,error:matchError}=await supabase.from('matches').select('match_id,manager_spell_id,result').in('match_id',matchIds);if(matchError){if(!cancelled){setError(matchError.message);setLoading(false)}return}
  const matchRows=(matches??[])as MatchRow[];const spellIds=Array.from(new Set(matchRows.map(r=>r.manager_spell_id).filter((v):v is number=>v!=null)));
  if(!spellIds.length){if(!cancelled){setRows([]);setLoading(false)}return}
  const{data:spells,error:spellError}=await supabase.from('manager_spells').select('manager_spell_id,manager_id').in('manager_spell_id',spellIds);if(spellError){if(!cancelled){setError(spellError.message);setLoading(false)}return}
  const spellRows=(spells??[])as SpellRow[];const spellToManager=new Map(spellRows.map(s=>[s.manager_spell_id,s.manager_id]));const managerIds=Array.from(new Set(spellRows.map(s=>s.manager_id)));
  const{data:managerData,error:managerError}=await supabase.from('managers').select('manager_id,canonical_name,profile_image_url').in('manager_id',managerIds);if(managerError){if(!cancelled){setError(managerError.message);setLoading(false)}return}
  const meta=new Map(((managerData??[])as ManagerMeta[]).map(m=>[m.manager_id,m]));const agg=new Map<number,{apps:number;won:number}>();for(const match of matchRows){if(match.manager_spell_id==null)continue;const managerId=spellToManager.get(match.manager_spell_id);if(managerId==null)continue;const cur=agg.get(managerId)??{apps:0,won:0};cur.apps++;if(match.result==='Won')cur.won++;agg.set(managerId,cur)}
  const next:Array<ManagerRow>=Array.from(agg.entries()).map(([managerId,v])=>{const m=meta.get(managerId);return{managerId,name:m?.canonical_name??`Manager ${managerId}`,src:m?.profile_image_url??null,apps:v.apps,won:v.won,winPct:v.apps?v.won/v.apps*100:0}}).sort((a,b)=>b.apps-a.apps||a.name.localeCompare(b.name));
  if(!cancelled){setRows(next);setLoading(false)}}load();return()=>{cancelled=true}},[playerId]);
 const maxApps=useMemo(()=>Math.max(1,...rows.map(m=>m.apps)),[rows]);
 return <section className="card player-manager-widget"><div className="player-manager-widget-head"><div><span className="section-kicker">Manager comparison</span><h2>Appearances Under Leeds Managers</h2></div><span className="section-kicker">{playerName} · {loading?'…':`${rows.length} ${rows.length===1?'Manager':'Managers'}`}</span></div>{loading?<div className="lb-loading">Loading manager record…</div>:error?<div className="lb-loading"><strong>Data connection error:</strong> {error}</div>:rows.length?<div className="player-manager-list">{rows.map((m,i)=><div className="player-manager-row" key={m.managerId}><div className="player-manager-rank">#{i+1}</div><div className="player-manager-identity">{m.src?<img src={m.src} alt="" className="manager-icon"/>:<span className="manager-avatar">{m.name.split(' ').map(s=>s[0]).join('').slice(0,2)}</span>}<div><strong>{m.name}</strong><span>{m.apps} appearances</span></div></div><div className="player-manager-apps"><div className="player-manager-track"><i style={{width:`${m.apps/maxApps*100}%`}}/></div></div><div className="player-manager-record"><strong className="player-manager-record-apps">{m.apps} apps</strong><span className="player-manager-record-rate">{m.winPct.toFixed(1)}% win rate</span><span className="player-manager-record-wins">{m.won} {m.won===1?'win':'wins'}</span></div></div>)}</div>:<div className="lb-empty">No Leeds manager appearance record found for this player.</div>}</section>
}
