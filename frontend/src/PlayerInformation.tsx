import React,{useEffect,useState}from'react';
import{supabase,supabaseConfigError}from'./supabase';
import'./PlayerInformation.css';

type PlayerInfoRow={
 place_of_birth:string|null;
 joined_from:string|null;
 transfer_type:string|null;
 date_joined_or_turned_pro:string|null;
 date_joined_or_turned_pro_raw:string|null;
 date_joined_precision:string|null;
 senior_career_clubs:string|null;
};

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

export default function PlayerInformation({playerId}:{playerId:number}){
 const[data,setData]=useState<PlayerInfoRow|null>(null),[loading,setLoading]=useState(true),[error,setError]=useState<string|null>(supabaseConfigError);
 useEffect(()=>{let cancelled=false;(async()=>{
  if(supabaseConfigError){setLoading(false);return}
  setLoading(true);setError(null);
  const{data:row,error:e}=await supabase.from('players').select('place_of_birth,joined_from,transfer_type,date_joined_or_turned_pro,date_joined_or_turned_pro_raw,date_joined_precision,senior_career_clubs').eq('player_id',playerId).single();
  if(cancelled)return;
  if(e){setError(e.message);setData(null)}else setData(row as PlayerInfoRow);
  setLoading(false);
 })();return()=>{cancelled=true}},[playerId]);
 const value=(v:string|null|undefined)=>v?.trim()||'—';
 return <section className="card player-information-panel">
  <div className="player-information-head"><div><span className="section-kicker">Player information</span><h2>Career Background</h2></div></div>
  {loading?<div className="player-information-state">Loading player information…</div>:error?<div className="player-information-state">Player information unavailable</div>:data?<div className="player-information-grid">
   <div><span>Born</span><strong>{value(data.place_of_birth)}</strong></div>
   <div><span>Joined From</span><strong>{value(data.joined_from)}</strong></div>
   <div><span>Transfer</span><strong>{value(data.transfer_type)}</strong></div>
   <div><span>Date Joined</span><strong>{formatJoined(data)}</strong></div>
   <div className="player-information-career"><span>Senior Career Clubs</span><strong>{value(data.senior_career_clubs)}</strong></div>
  </div>:null}
 </section>;
}
