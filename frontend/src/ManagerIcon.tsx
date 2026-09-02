import React,{useState}from'react';
const overrides:Record<string,string>={
 'Bill Lambton':'Bill Lambton.png','The Board Committee':'Leeds United Committee.png','Eddie Gray':'Eddie Gray Icon 1982.png','Jesse Marsch':'Jesse Marsh Icon.png','Uwe Rösler':'Uwe Rosler Icon.png'
};
export default function ManagerIcon({name}:{name:string}){const[failed,setFailed]=useState(false);const file=overrides[name]??`${name} Icon.png`;if(failed)return <span className="manager-avatar">{name.split(' ').map(x=>x[0]).slice(0,2).join('')}</span>;return <img className="manager-icon" src={`/managers/${encodeURIComponent(file)}`} alt="" onError={()=>setFailed(true)}/>;}
