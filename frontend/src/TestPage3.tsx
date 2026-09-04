import React,{useMemo,useState}from'react';
import{ChevronDown}from'lucide-react';
import'./TestPage3.css';

type Row={rank:number;player:string;position:string;apps:number;goals:number;assists:number;passes:number;winPct:number};
type SortKey='rank'|'player'|'apps'|'goals'|'assists'|'passes'|'winPct';

const DATA:Row[]=[
 {rank:1,player:'Billy Bremner',position:'Midfielder',apps:587,goals:90,assists:46,passes:18421,winPct:52.6},
 {rank:2,player:'Jack Charlton',position:'Defender',apps:773,goals:96,assists:18,passes:16280,winPct:51.8},
 {rank:3,player:'Norman Hunter',position:'Defender',apps:726,goals:21,assists:24,passes:17564,winPct:52.2},
 {rank:4,player:'Peter Lorimer',position:'Midfielder',apps:705,goals:238,assists:71,passes:15392,winPct:50.9},
 {rank:5,player:'Paul Reaney',position:'Defender',apps:748,goals:7,assists:14,passes:16631,winPct:52.0},
 {rank:6,player:'Johnny Giles',position:'Midfielder',apps:527,goals:115,assists:83,passes:14918,winPct:55.2},
 {rank:7,player:'Paul Madeley',position:'Defender',apps:724,goals:34,assists:31,passes:16902,winPct:51.7},
 {rank:8,player:'Allan Clarke',position:'Forward',apps:366,goals:151,assists:37,passes:8210,winPct:57.1},
];

export default function TestPage3(){
 const[sortKey,setSortKey]=useState<SortKey>('rank'),[desc,setDesc]=useState(false);
 const sorted=useMemo(()=>[...DATA].sort((a,b)=>{const av=a[sortKey],bv=b[sortKey];const d=typeof av==='string'?av.localeCompare(String(bv)):Number(av)-Number(bv);return desc?-d:d}),[sortKey,desc]);
 const changeSort=(key:SortKey)=>{if(key===sortKey)setDesc(v=>!v);else{setSortKey(key);setDesc(false)}};
 return <section className="test3-page" aria-label="Test 3 isolated stats table experiment">
  <div className="test3-shell">
   <div className="test3-eyebrow">UI EXPERIMENT · DUMMY DATA</div>
   <div className="test3-panel">
    <div className="test3-panel-head">
     <div><span className="test3-kicker">Leeds United</span><h1>Player Stats</h1></div>
     <button className="test3-sort" type="button" onClick={()=>changeSort(sortKey)}>Sort by <ChevronDown size={14}/></button>
    </div>
    <div className="test3-table-wrap">
     <table className="test3-table">
      <thead><tr>
       <th><button onClick={()=>changeSort('rank')}>ID</button></th>
       <th><button onClick={()=>changeSort('player')}>PLAYER</button></th>
       <th>TYPE</th>
       <th><button onClick={()=>changeSort('apps')}>APPS</button></th>
       <th><button onClick={()=>changeSort('goals')}>GOALS</button></th>
       <th><button onClick={()=>changeSort('assists')}>ASSISTS</button></th>
       <th><button onClick={()=>changeSort('passes')}>PASSES</button></th>
       <th><button onClick={()=>changeSort('winPct')}>WIN %</button></th>
      </tr></thead>
      <tbody>{sorted.map((r,i)=><tr key={r.rank} className={i===1?'is-highlighted':''}>
       <td>{r.rank}</td><td className="test3-player">{r.player}</td><td>{r.position}</td><td>{r.apps}</td><td>{r.goals}</td><td>{r.assists}</td><td>{r.passes.toLocaleString('en-GB')}</td><td>{r.winPct.toFixed(1)}%</td>
      </tr>)}</tbody>
     </table>
    </div>
   </div>
  </div>
 </section>;
}
