import React,{useEffect,useState}from'react';
export default function PlayerIcon({name,src}:{name:string;src:string|null}){const[failed,setFailed]=useState(false);useEffect(()=>setFailed(false),[src]);if(!src||failed)return null;return <img className="player-icon" src={src} alt={name} title={name} onError={()=>setFailed(true)}/>}
