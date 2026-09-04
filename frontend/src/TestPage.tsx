import React from 'react';
import './TestPage.css';

type SeasonRow={season:string;games:number;goals:number;penalties:number};
const rows:SeasonRow[]=[
 {season:'2026/27',games:34,goals:18,penalties:3},
 {season:'2025/26',games:38,goals:15,penalties:2},
 {season:'2024/25',games:36,goals:12,penalties:1},
 {season:'2023/24',games:31,goals:10,penalties:2},
 {season:'2022/23',games:33,goals:9,penalties:1},
 {season:'2021/22',games:29,goals:7,penalties:0},
 {season:'2020/21',games:35,goals:13,penalties:2},
 {season:'2019/20',games:28,goals:8,penalties:1},
];
const goalRows=[
 ['2026/27','18','3'],['2025/26','15','2'],['2024/25','12','1'],['2023/24','10','2'],['2022/23','9','1'],['2021/22','7','0'],['2020/21','13','2'],['2019/20','8','1'],
];

export default function TestPage(){
 const maxGames=Math.max(...rows.map(r=>r.games));
 return <div className="test-performance-page">
  <div className="test-performance-shell">
   <div className="test-player-chip" aria-label="Dummy player"><div className="test-player-avatar">DP</div><div><strong>Dummy Player</strong><span>Forward · #9</span></div></div>
   <h1>Performance</h1>
   <div className="test-performance-grid">
    <section className="test-games-panel">
     <h2>Games played/Goals</h2>
     <div className="test-season-bars">{rows.map((r,i)=>{const totalPct=r.games/maxGames*100;const goalPct=r.goals/r.games*100;const penPct=r.penalties/r.games*100;return <div className="test-season-row" key={r.season}>
      <span className={`test-season-label ${i===0?'active':''}`}>{i===0?<i/>:null}{r.season}</span>
      <div className="test-bar-wrap" title={`${r.games} games · ${r.goals} goals · ${r.penalties} penalties`}>
       <div className="test-bar-total" style={{width:`${totalPct}%`}}><span className="test-bar-pen" style={{width:`${penPct}%`}}/><span className="test-bar-goals" style={{width:`${goalPct}%`}}/><b>{r.goals}</b><em>{r.games}</em></div>
      </div>
     </div>})}</div>
     <button className="test-show-all">Show all</button>
     <div className="test-legend"><span><i className="games"/>Games played</span><span><i className="goals"/>Goals</span><span><i className="pens"/>Penalty</span></div>
    </section>
    <section className="test-goals-panel">
     <h2>Goals</h2>
     <div className="test-goals-head"><span>YEAR</span><span>TOTAL GOALS</span><span>PENALTIES</span><span/></div>
     <div className="test-goals-list">{goalRows.map(r=><div className="test-goals-row" key={r[0]}><span>{r[0]}</span><strong>{r[1]}</strong><strong>{r[2]}</strong><button>details</button></div>)}</div>
     <button className="test-show-all test-show-all-right">Show all</button>
    </section>
   </div>
   <div className="test-performance-lower">
    <button className="test-season-select">THIS SEASON <span>▼</span></button>
    <section className="test-fouls-card"><h2>Fouls/Cards</h2><div><span>Fouls</span><strong>42</strong></div><div><span>Yellow cards</span><strong>6</strong></div><div><span>Red cards</span><strong>1</strong></div></section>
   </div>
  </div>
 </div>
}
