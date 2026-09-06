import React from'react';
import'./TimeRangeFilter.css';

export const FT_VALUE=121;
export const AFT_VALUE=122;
export function eventMinuteValue(raw:string|null|undefined,normalised?:number|null){const value=(raw??'').trim().toUpperCase();if(value==='AFT')return AFT_VALUE;if(value==='FT')return FT_VALUE;if(value==='HT')return 45;if(normalised!=null&&Number.isFinite(Number(normalised)))return Number(normalised);const m=value.match(/(\d+)(?:\+(\d+))?/);return m?Number(m[1])+Number(m[2]??0):null}
const label=(v:number)=>v===AFT_VALUE?'AFT':v===FT_VALUE?'FT':String(v);
export default function TimeRangeFilter({start,end,onChange,includeAfterFullTime=false}:{start:number;end:number;onChange:(start:number,end:number)=>void;includeAfterFullTime?:boolean}){
 const max=includeAfterFullTime?AFT_VALUE:FT_VALUE,ticks=includeAfterFullTime?[0,15,30,45,60,75,90,105,120,FT_VALUE,AFT_VALUE]:[0,15,30,45,60,75,90,105,120,FT_VALUE];
 const left=start/max*100,right=end/max*100;
 const setStart=(n:number)=>onChange(Math.min(n,end),end),setEnd=(n:number)=>onChange(start,Math.max(n,start));
 return <div className="time-range-filter"><div className="time-range-head"><span>Time Range</span><strong>{label(start)} - {label(end)}</strong></div><div className="time-range-control"><div className="time-range-track" style={{'--range-left':`${left}%`,'--range-right':`${right}%`} as React.CSSProperties}/><input className="time-range-input time-range-start" type="range" min="0" max={max} step="1" value={start} onChange={e=>setStart(Number(e.target.value))} aria-label="Time range start"/><input className="time-range-input time-range-end" type="range" min="0" max={max} step="1" value={end} onChange={e=>setEnd(Number(e.target.value))} aria-label="Time range end"/></div><div className="time-range-ticks">{ticks.map(v=><span key={v} style={{left:`${v/max*100}%`}}>{label(v)}</span>)}</div></div>;
}
