import React,{useState}from'react';
export default function NationalityFlag({nation}:{nation:string|null}){const[failed,setFailed]=useState(false);if(!nation||failed)return null;const file=nation==='Spain / Denmark'?'Spain & Denmark':nation;return <img className="nationality-flag" src={`/flags/${encodeURIComponent(file)}.png`} alt={nation} title={nation} onError={()=>setFailed(true)}/>;}
