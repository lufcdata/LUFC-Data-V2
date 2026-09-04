import React,{useEffect,useMemo,useState}from'react';
import ClubCrest from'./ClubCrest';
import PlayerIcon from'./PlayerIcon';
import{supabase,supabaseConfigError}from'./supabase';
import'./PlayerCompetitionBreakdown.css';
import'./PlayerOpponentWidgets.css';
import'./ManagerProfileBreakdowns.css';

type BreakdownRow={category:string;entity_type:'club'|'player';entity_id:number;label:string;value:number;secondary:string;rank_order:number};
type ClubMeta={club_id:number;canonical_name:string;crest_url:string|null};
type PlayerMeta={player_id:number;display_name:string;profile_image_url:string|null};
const categories=['Opponents Faced','Most Wins','Most Defeats','Most Goals Against','Most Conceded Against','Top Appearances','Top Goalscorers','Top Assists'] as const;
type Category=typeof categories[number];
const valueLabels:Record<string,string>={
 'Opponents Faced':'matches','Most Wins':'wins','Most Defeats':'defeats','Most Goals Against':'goals','Most Conceded Against':'goals conceded','Top Appearances':'apps','Top Goalscorers':'goals','Top Assists':'assists'
};
function emptyCopy(category:string){return category==='Top Assists'?'No recorded assist data is available for this manager.':`No ${category.toLowerCase()} data found.`}
function ScopeToggle({all,onChange,label}:{all:boolean;onChange:(value:boolean)=>void;label:string}){return <div className="player-opponent-scope" role="group" aria-label={`${label} rows shown`}><button type="button" className={!all?'active':''} onClick={()=>onChange(false)}>Top 5</button><button type="button" className={all?'active':''} onClick={()=>onChange(true)}>All</button></div>}

export default function ManagerProfileBreakdowns({managerId}:{managerId:number}){
 const[rows,setRows]=useState<BreakdownRow[]>([]),[clubMeta,setClubMeta]=useState<Map<number,ClubMeta>>(new Map()),[playerMeta,setPlayerMeta]=useState<Map<number,PlayerMeta>>(new Map()),[loading,setLoading]=useState(true),[error,setError]=useState<string|null>(supabaseConfigError);
 const[showAll,setShowAll]=useState<Record<string,boolean>>({});
 useEffect(()=>{setShowAll({})},[managerId]);
 useEffect(()=>{let cancelled=false;(async()=>{if(!supabase){setLoading(false);return}setLoading(true);setError(null);const{data,error}=await supabase.rpc('get_manager_profile_breakdowns',{p_manager_id:managerId});if(cancelled)return;if(error){setError(error.message);setRows([]);setClubMeta(new Map());setPlayerMeta(new Map());setLoading(false);return}const breakdown=(data??[])as BreakdownRow[],clubIds=Array.from(new Set(breakdown.filter(r=>r.entity_type==='club').map(r=>r.entity_id))),playerIds=Array.from(new Set(breakdown.filter(r=>r.entity_type==='player').map(r=>r.entity_id)));
  const[{data:clubs,error:clubError},{data:players,error:playerError}]=await Promise.all([
   clubIds.length?supabase.from('clubs').select('club_id,canonical_name,crest_url').in('club_id',clubIds):Promise.resolve({data:[],error:null}),
   playerIds.length?supabase.from('players').select('player_id,display_name,profile_image_url').in('player_id',playerIds):Promise.resolve({data:[],error:null})
  ]);if(cancelled)return;if(clubError||playerError){setError((clubError??playerError)?.message??'Unable to load breakdown identities');setRows([]);setLoading(false);return}setRows(breakdown);setClubMeta(new Map(((clubs??[])as ClubMeta[]).map(c=>[c.club_id,c])));setPlayerMeta(new Map(((players??[])as PlayerMeta[]).map(p=>[p.player_id,p])));setLoading(false)})();return()=>{cancelled=true}},[managerId]);
 const grouped=useMemo(()=>new Map(categories.map(category=>[category,rows.filter(r=>r.category===category).sort((a,b)=>a.rank_order-b.rank_order)])),[rows]);
 return <section className="manager-breakdown-grid" aria-label="Manager career breakdowns">
  {categories.map(category=>{const items=grouped.get(category)??[],all=Boolean(showAll[category]),visible=all?items:items.slice(0,5),max=Math.max(1,...items.map(r=>Number(r.value)));return <section className={`card player-competition-compact manager-breakdown-card${!all?' top-five':''}`} key={category}>
   <div className="player-profile-panelhead"><div><span className="section-kicker">Manager analysis</span><h2>{category}</h2></div><ScopeToggle all={all} onChange={value=>setShowAll(current=>({...current,[category]:value}))} label={category}/></div>
   {loading?<div className="lb-loading">Loading breakdown…</div>:error?<div className="lb-loading">Breakdown unavailable</div>:visible.length?<div className="player-competition-compact-list">
    {visible.map(r=>{const club=r.entity_type==='club'?clubMeta.get(r.entity_id):null,player=r.entity_type==='player'?playerMeta.get(r.entity_id):null;return <div className="player-competition-compact-row" key={`${category}-${r.entity_type}-${r.entity_id}`}>
     <div className={`player-competition-compact-main manager-breakdown-identity ${r.entity_type==='player'?'manager-breakdown-player':'manager-breakdown-club'}`}>{r.entity_type==='club'?<ClubCrest crestUrl={club?.crest_url??null} name={club?.canonical_name??r.label}/>:<PlayerIcon name={player?.display_name??r.label} src={player?.profile_image_url??null}/>}<div><strong>{r.label}</strong><span>{r.secondary}</span></div></div>
     <div className="player-competition-compact-rate"><strong>{Number(r.value).toLocaleString('en-GB')}</strong><span>{valueLabels[category]}</span></div>
     <div className="player-competition-compact-track"><i style={{width:`${Math.max(4,Number(r.value)/max*100)}%`}}/></div>
    </div>})}
   </div>:<div className="lb-empty manager-breakdown-empty">{emptyCopy(category)}</div>}
  </section>})}
 </section>;
}
