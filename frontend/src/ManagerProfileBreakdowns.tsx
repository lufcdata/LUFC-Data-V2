import React,{useEffect,useMemo,useState}from'react';
import{supabase,supabaseConfigError}from'./supabase';
import'./PlayerCompetitionBreakdown.css';
import'./ManagerProfileBreakdowns.css';

type BreakdownRow={category:string;entity_type:'club'|'player';entity_id:number;label:string;value:number;secondary:string;rank_order:number};
const categories=['Opponents Faced','Most Wins','Most Defeats','Most Goals Against','Most Conceded Against','Top Appearances','Top Goalscorers','Top Assists','Debutants'] as const;
const valueLabels:Record<string,string>={
 'Opponents Faced':'matches','Most Wins':'wins','Most Defeats':'defeats','Most Goals Against':'goals','Most Conceded Against':'goals conceded','Top Appearances':'apps','Top Goalscorers':'goals','Top Assists':'assists','Debutants':'apps'
};
function emptyCopy(category:string){return category==='Top Assists'?'No recorded assist data is available for this manager.':`No ${category.toLowerCase()} data found.`}

export default function ManagerProfileBreakdowns({managerId}:{managerId:number}){
 const[rows,setRows]=useState<BreakdownRow[]>([]),[loading,setLoading]=useState(true),[error,setError]=useState<string|null>(supabaseConfigError);
 useEffect(()=>{let cancelled=false;(async()=>{if(!supabase){setLoading(false);return}setLoading(true);setError(null);const{data,error}=await supabase.rpc('get_manager_profile_breakdowns',{p_manager_id:managerId});if(cancelled)return;if(error){setError(error.message);setRows([])}else setRows((data??[])as BreakdownRow[]);setLoading(false)})();return()=>{cancelled=true}},[managerId]);
 const grouped=useMemo(()=>new Map(categories.map(category=>[category,rows.filter(r=>r.category===category).sort((a,b)=>a.rank_order-b.rank_order)])),[rows]);
 return <section className="manager-breakdown-grid" aria-label="Manager career breakdowns">
  {categories.map(category=>{const items=grouped.get(category)??[],max=Math.max(1,...items.map(r=>Number(r.value)));return <section className="card player-competition-compact manager-breakdown-card" key={category}>
   <div className="player-profile-panelhead"><div><span className="section-kicker">Manager analysis</span><h2>{category}</h2></div><div className="section-kicker">{loading?'…':items.length?`Top ${items.length}`:'—'}</div></div>
   {loading?<div className="lb-loading">Loading breakdown…</div>:error?<div className="lb-loading">Breakdown unavailable</div>:items.length?<div className="player-competition-compact-list">
    {items.map(r=><div className="player-competition-compact-row" key={`${category}-${r.entity_type}-${r.entity_id}`}>
     <div className="player-competition-compact-main"><strong>{r.label}</strong><span>{r.secondary}</span></div>
     <div className="player-competition-compact-rate"><strong>{Number(r.value).toLocaleString('en-GB')}</strong><span>{valueLabels[category]}</span></div>
     <div className="player-competition-compact-track"><i style={{width:`${Math.max(4,Number(r.value)/max*100)}%`}}/></div>
    </div>)}
   </div>:<div className="lb-empty manager-breakdown-empty">{emptyCopy(category)}</div>}
  </section>})}
 </section>;
}
