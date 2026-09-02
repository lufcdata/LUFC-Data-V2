import React,{useState}from'react';
const flagFiles:Record<string,string>={
  'Spain / Denmark':'Spain & Denmark.png'
};
export default function FlagIcon({nation}:{nation:string|null}){const[failed,setFailed]=useState(false);if(!nation||failed)return <span className="flag-fallback">—</span>;const file=flagFiles[nation]??`${nation}.png`;return <span className="flag-wrap" title={nation}><img className="flag-icon" src={encodeURI(`/flags/${file}`)} alt={nation} onError={()=>setFailed(true)}/></span>;}
