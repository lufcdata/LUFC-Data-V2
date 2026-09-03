import React,{useEffect,useState}from'react';
import NationalityFlag from'./NationalityFlag';
import{supabase,supabaseConfigError}from'./supabase';
import'./PlayerInformation.css';

type PlayerInfoRow={
 full_name:string|null;
 position_group:string|null;
 position_detail:string|null;
 declared_nation:string|null;
 date_of_birth:string|null;
 birth_date_precision:string|null;
 place_of_birth:string|null;
 joined_from:string|null;
 transfer_type:string|null;
 date_joined_or_turned_pro:string|null;
 date_joined_or_turned_pro_raw:string|null;
 date_joined_precision:string|null;
 senior_career_clubs:string|null;
 status:string|null;
};
type PlayerMatchRow={match_id:number};
type MatchRow={match_id:number;match_date:string;season_id:number|null};
type CareerMeta={seasons:number;firstApp:string;lastApp:string};

function formatJoined(row:PlayerInfoRow){
 const raw=row.date_joined_or_turned_pro_raw?.trim();
 if(raw){
  const monthMatch=raw.match(/^(\d{4})\s+([A-Za-z]+)$/);
  if(monthMatch)return`${monthMatch[2]} ${monthMatch[1]}`;
  const isoMatch=raw.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if(isoMatch)return new Intl.DateTimeFormat('en-GB',{day:'numeric',month:'short',year:'numeric'}).format(new Date(`${raw}T12:00:00Z`));
  return raw;
 }
 if(row.date_joined_or_turned_pro)return new Intl.DateTimeFormat('en-GB',{day:'numeric',month:'short',year:'numeric'}).format(new Date(`${row.date_joined_or_turned_pro}T12:00:00Z`));
 return'—';
}
function formatDob(value:string|null,precision:string|null){if(!value)return'—';if(precision!=='exact')return value;return new Intl.DateTimeFormat('en-GB',{day:'numeric',month:'short',year:'numeric'}).format(new Date(`${value}T12:00:00Z`))}
function positionLabel(row:PlayerInfoRow){return row.position_detail?.trim()||row.position_group?.trim()||'—'}

export default function PlayerInformation({playerId}:{playerId:number}){
 const[data,setData]=useState<PlayerInfoRow|null>(null),[career,setCareer]=useState<CareerMeta>({seasons:0,firstApp:'—',lastApp:'—'}),[loading,setLoading]=useState(true),[error,setError]=useState<string|null>(supabaseConfigError);
 useEffect(()=>{let cancelled=false;(async()=>{
  if(supabaseConfigError){setLoading(false);return}
  setLoading(true);setError(null);
  const[{data:row,error:e},{data:pm,error:pmError}]=await Promise.all([
   supabase.from('players').select('full_name,position_group,position_detail,declared_nation,date_of_birth,birth_date_precision,place_of_birth,joined_from,transfer_type,date_joined_or_turned_pro,date_joined_or_turned_pro_raw,date_joined_precision,senior_career_clubs,status').eq('player_id',playerId).single(),
   supabase.from('player_matches').select('match_id').eq('player_id',playerId)
  ]);
  if(cancelled)return;
  if(e||pmError){setError((e||pmError)?.message||'Player information unavailable');setData(null);setLoading(false);return}
  setData(row as PlayerInfoRow);
  const ids=((pm??[])as PlayerMatchRow[]).map(r=>r.match_id);
  if(ids.length){const{data:matches,error:matchError}=await supabase.from('matches').select('match_id,match_date,season_id').in('match_id',ids);if(cancelled)return;if(matchError){setError(matchError.message);setLoading(false);return}const ms=((matches??[])as MatchRow[]).filter(m=>m.match_date).sort((a,b)=>a.match_date.localeCompare(b.match_date));const seasons=new Set(ms.map(m=>m.season_id).filter((v):v is number=>v!=null)).size;setCareer({seasons,firstApp:ms[0]?.match_date?.slice(0,4)||'—',lastApp:ms.at(-1)?.match_date?.slice(0,4)||'—'})}
  setLoading(false);
 })();return()=>{cancelled=true}},[playerId]);
 const value=(v:string|null|undefined)=>v?.trim()||'—';
 return <section className="card player-information-panel">
  <div className="player-information-head"><div><span className="section-kicker">Player information</span><h2>Career Background</h2></div></div>
  {loading?<div className="player-information-state">Loading player information…</div>:error?<div className="player-information-state">Player information unavailable</div>:data?<div className="player-information-grid">
   <div><span>Full Name</span><strong>{value(data.full_name)}</strong></div>
   <div><span>Primary Position</span><strong>{positionLabel(data)}</strong></div>
   <div><span>Born</span><strong>{value(data.place_of_birth)}</strong></div>
   <div><span>Declared Nation</span><strong className="player-information-nation">{data.declared_nation?<><NationalityFlag nation={data.declared_nation}/>{data.declared_nation}</>:<>—</>}</strong></div>
   <div><span>Date of Birth</span><strong>{formatDob(data.date_of_birth,data.birth_date_precision)}</strong></div>
   <div><span>Joined / Turned Pro</span><strong>{formatJoined(data)}</strong></div>
   <div><span>Joined From</span><strong>{value(data.joined_from)}</strong></div>
   <div><span>Transfer Type</span><strong>{value(data.transfer_type)}</strong></div>
   <div><span>Seasons at Leeds</span><strong>{career.seasons||'—'}</strong></div>
   <div><span>Status</span><strong>{value(data.status)}</strong></div>
   <div><span>First App</span><strong>{career.firstApp}</strong></div>
   <div><span>Last App</span><strong>{career.lastApp}</strong></div>
   <div className="player-information-career"><span>Senior Career Clubs</span><strong>{value(data.senior_career_clubs)}</strong></div>
  </div>:null}
 </section>;
}
