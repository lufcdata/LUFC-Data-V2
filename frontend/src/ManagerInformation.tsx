import React,{useEffect,useMemo,useState}from'react';
import NationalityFlag from'./NationalityFlag';
import{supabase,supabaseConfigError}from'./supabase';
import'./PlayerInformation.css';

type ManagerRow={full_name:string|null;declared_nation:string|null;date_of_birth:string|null;place_of_birth:string|null;date_of_death:string|null};
type SpellRow={manager_spell_id:number;role:string|null;date_joined:string|null;date_left:string|null;status:string|null};
type EnrichmentRow={manager_spell_id:number;coaching_staff:string|null;club_honours:number|null;promotions:number|null};
type MatchRow={season:string|null};

const formatDate=(value:string|null)=>{if(!value)return'—';const d=new Date(`${value}T12:00:00Z`);return Number.isNaN(d.getTime())?'—':new Intl.DateTimeFormat('en-GB',{day:'numeric',month:'short',year:'numeric'}).format(d)};
const value=(v:string|null|undefined)=>v?.trim()||'—';

export default function ManagerInformation({managerId}:{managerId:number}){
 const[data,setData]=useState<ManagerRow|null>(null),[spells,setSpells]=useState<SpellRow[]>([]),[enrichment,setEnrichment]=useState<EnrichmentRow[]>([]),[matches,setMatches]=useState<MatchRow[]>([]),[loading,setLoading]=useState(true),[error,setError]=useState<string|null>(supabaseConfigError);
 useEffect(()=>{let cancelled=false;(async()=>{if(!supabase){setLoading(false);return}setLoading(true);setError(null);const[{data:m,error:me},{data:s,error:se},{data:mm,error:mme}]=await Promise.all([
  supabase.from('managers').select('full_name,declared_nation,date_of_birth,place_of_birth,date_of_death').eq('manager_id',managerId).maybeSingle(),
  supabase.from('manager_spells').select('manager_spell_id,role,date_joined,date_left,status').eq('manager_id',managerId).order('date_joined',{ascending:true}),
  supabase.from('match_centre_summary').select('season').eq('leeds_manager_id',managerId)
 ]);if(me||se||mme){if(!cancelled){setError((me??se??mme)?.message??'Manager information unavailable');setLoading(false)}return}const spellRows=(s??[])as SpellRow[],ids=spellRows.map(x=>x.manager_spell_id);let extra:EnrichmentRow[]=[];if(ids.length){const{data:e,error:ee}=await supabase.from('manager_spell_profile_enrichment').select('manager_spell_id,coaching_staff,club_honours,promotions').in('manager_spell_id',ids);if(ee){if(!cancelled){setError(ee.message);setLoading(false)}return}extra=(e??[])as EnrichmentRow[]}if(!cancelled){setData((m??null)as ManagerRow|null);setSpells(spellRows);setEnrichment(extra);setMatches((mm??[])as MatchRow[]);setLoading(false)}})();return()=>{cancelled=true}},[managerId]);
 const meta=useMemo(()=>{const roles=Array.from(new Set(spells.map(s=>s.role?.trim()).filter((v):v is string=>Boolean(v))));const joins=spells.map(s=>formatDate(s.date_joined)).filter(v=>v!=='—'),leaves=spells.map(s=>s.date_left?formatDate(s.date_left):'present');const seasons=new Set(matches.map(m=>m.season).filter((v):v is string=>Boolean(v))).size;const coaching=Array.from(new Set(enrichment.flatMap(e=>(e.coaching_staff??'').split(',').map(v=>v.trim()).filter(Boolean)))).join(', ');const honours=enrichment.reduce((n,e)=>n+Number(e.club_honours??0),0),promotions=enrichment.reduce((n,e)=>n+Number(e.promotions??0),0),status=spells.some(s=>s.status==='Current')?'Current':'Former';return{role:roles.join(' · ')||'Manager',joined:joins.join(' · ')||'—',left:leaves.join(' · ')||'—',seasons,coaching,honours,promotions,status}},[spells,enrichment,matches]);
 return <section className="card player-information-panel"><div className="player-information-head"><div><span className="section-kicker">Manager information</span><h2>Career Background</h2></div></div>{loading?<div className="player-information-state">Loading manager information…</div>:error?<div className="player-information-state">Manager information unavailable</div>:data?<div className="player-information-grid">
  <div><span>Full Name</span><strong>{value(data.full_name)}</strong></div>
  <div><span>Role</span><strong>{meta.role}</strong></div>
  <div><span>Place of Birth</span><strong>{value(data.place_of_birth)}</strong></div>
  <div><span>Declared Nation</span><strong className="player-information-nation">{data.declared_nation?<><NationalityFlag nation={data.declared_nation}/>{data.declared_nation}</>:<>—</>}</strong></div>
  <div><span>Date of Birth</span><strong>{formatDate(data.date_of_birth)}</strong></div>
  <div><span>Date Joined</span><strong>{meta.joined}</strong></div>
  <div><span>Date Left</span><strong>{meta.left}</strong></div>
  <div><span>Date of Death</span><strong>{formatDate(data.date_of_death)}</strong></div>
  <div><span>Seasons at Leeds</span><strong>{meta.seasons||'—'}</strong></div>
  <div><span>Status</span><strong>{meta.status}</strong></div>
  <div><span>Club Honours</span><strong>{meta.honours}</strong></div>
  <div><span>Promotions</span><strong>{meta.promotions}</strong></div>
  <div className="player-information-career"><span>Coaching Staff</span><strong>{meta.coaching||'—'}</strong></div>
 </div>:null}</section>;
}
