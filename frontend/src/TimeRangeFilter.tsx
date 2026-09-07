import React from'react';
import'./TimeRangeFilter.css';

export const FIRST_HALF_ADDED_VALUE=45.25;
export const HT_VALUE=45.5;
export const SECOND_HALF_ADDED_VALUE=90.25;
export const REGULATION_END_VALUE=90.5;
export const ET_FIRST_HALF_ADDED_VALUE=105.25;
export const ET_HT_VALUE=105.5;
export const ET_SECOND_HALF_ADDED_VALUE=120.25;
export const FT_VALUE=121;
export const AFT_VALUE=122;

function addedTimePhase(base:number){
 if(base<=45)return FIRST_HALF_ADDED_VALUE;
 if(base<=90)return SECOND_HALF_ADDED_VALUE;
 if(base<=105)return ET_FIRST_HALF_ADDED_VALUE;
 return ET_SECOND_HALF_ADDED_VALUE;
}

export function eventMinuteValue(raw:string|null|undefined,normalised?:number|null){
 const value=(raw??'').trim().toUpperCase();
 if(value==='AFT')return AFT_VALUE;
 if(value==='FT')return FT_VALUE;
 if(value==='HT')return HT_VALUE;
 const m=value.match(/^(\d+)(?:\+(\d+))?\s*'?$/);
 if(m){
  const base=Number(m[1]),added=Number(m[2]??0);
  return added>0?addedTimePhase(base):base;
 }
 if(normalised!=null&&Number.isFinite(Number(normalised)))return Number(normalised);
 return null;
}

const label=(v:number)=>v===AFT_VALUE?'AFT':v===FT_VALUE?'FT':v===ET_SECOND_HALF_ADDED_VALUE?'120+':v===ET_HT_VALUE?'ET HT':v===ET_FIRST_HALF_ADDED_VALUE?'105+':v===REGULATION_END_VALUE?'FT / ET':v===SECOND_HALF_ADDED_VALUE?'90+':v===HT_VALUE?'HT':v===FIRST_HALF_ADDED_VALUE?'45+':String(v);

const ALL_POINTS=[
 ...Array.from({length:121},(_,i)=>i),
 FIRST_HALF_ADDED_VALUE,HT_VALUE,SECOND_HALF_ADDED_VALUE,REGULATION_END_VALUE,
 ET_FIRST_HALF_ADDED_VALUE,ET_HT_VALUE,ET_SECOND_HALF_ADDED_VALUE,FT_VALUE,AFT_VALUE,
].sort((a,b)=>a-b);

function snap(value:number,max:number){
 let best=ALL_POINTS[0],distance=Infinity;
 for(const point of ALL_POINTS){
  if(point>max)continue;
  const next=Math.abs(point-value);
  if(next<distance){best=point;distance=next}
 }
 return best;
}

export default function TimeRangeFilter({start,end,onChange,includeAfterFullTime=false}:{start:number;end:number;onChange:(start:number,end:number)=>void;includeAfterFullTime?:boolean}){
 const max=includeAfterFullTime?AFT_VALUE:FT_VALUE;
 const ticks=includeAfterFullTime?[0,45,FIRST_HALF_ADDED_VALUE,HT_VALUE,90,SECOND_HALF_ADDED_VALUE,REGULATION_END_VALUE,105,ET_HT_VALUE,120,ET_SECOND_HALF_ADDED_VALUE,FT_VALUE,AFT_VALUE]:[0,45,FIRST_HALF_ADDED_VALUE,HT_VALUE,90,SECOND_HALF_ADDED_VALUE,REGULATION_END_VALUE,105,ET_HT_VALUE,120,ET_SECOND_HALF_ADDED_VALUE,FT_VALUE];
 const left=start/max*100,right=end/max*100;
 const setStart=(n:number)=>{const next=snap(n,max);onChange(Math.min(next,end),end)};
 const setEnd=(n:number)=>{const next=snap(n,max);onChange(start,Math.max(next,start))};
 return <div className="time-range-filter"><div className="time-range-head"><span>Time Range</span><strong>{label(start)} - {label(end)}</strong></div><div className="time-range-control"><div className="time-range-track" style={{'--range-left':`${left}%`,'--range-right':`${right}%`} as React.CSSProperties}/><input className="time-range-input time-range-start" type="range" min="0" max={max} step="0.25" value={start} onChange={e=>setStart(Number(e.target.value))} aria-label="Time range start"/><input className="time-range-input time-range-end" type="range" min="0" max={max} step="0.25" value={end} onChange={e=>setEnd(Number(e.target.value))} aria-label="Time range end"/></div><div className="time-range-ticks">{ticks.map(v=><span key={v} className={v%1?'time-range-phase-tick':''} style={{left:`${v/max*100}%`}}>{label(v)}</span>)}</div><div className="time-range-key">45+ = 1H added · 90+ = 2H added · 91–120 = extra time</div></div>;
}
