import React,{useState}from'react';
export default function ManagerIcon({name,src}:{name:string;src:string|null}){const[failed,setFailed]=useState(false);if(failed||!src)return <span className="manager-avatar">{name.split(' ').map(x=>x[0]).slice(0,2).join('')}</span>;return <img className="manager-icon" src={encodeURI(src)} alt="" onError={()=>setFailed(true)}/>;}
