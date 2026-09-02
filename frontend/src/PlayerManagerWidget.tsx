import React from'react';
import'./PlayerManagerWidget.css';

type ManagerRow={name:string;src:string;apps:number;won:number;winPct:number};
const managers:ManagerRow[]=[
 {name:'Don Revie',src:'/managers/Don Revie Icon.png',apps:649,won:351,winPct:54.1},
 {name:'Jimmy Armfield',src:'/managers/Jimmy Armfield Icon.png',apps:85,won:42,winPct:49.4},
 {name:'Jack Taylor',src:'/managers/Jack Taylor Icon.png',apps:36,won:13,winPct:36.1},
 {name:'Brian Clough',src:'/managers/Brian Clough Icon.png',apps:2,won:0,winPct:0}
];
const maxApps=Math.max(...managers.map(m=>m.apps));
export default function PlayerManagerWidget(){return <section className="card player-manager-widget"><div className="player-manager-widget-head"><div><span className="section-kicker">Manager comparison</span><h2>Most Appearances Under Leeds Managers</h2></div><span className="section-kicker">Billy Bremner · 4 Managers</span></div><div className="player-manager-list">{managers.map((m,i)=><div className="player-manager-row" key={m.name}><div className="player-manager-rank">#{i+1}</div><div className="player-manager-identity"><img src={m.src} alt="" className="manager-icon"/><div><strong>{m.name}</strong><span>{m.apps} appearances</span></div></div><div className="player-manager-apps"><span className="metric-value">{m.apps}</span><div className="player-manager-track"><i style={{width:`${m.apps/maxApps*100}%`}}/></div></div><div className="player-manager-record"><span>{m.won} wins</span><strong>{m.winPct.toFixed(1)}%</strong></div></div>)}</div></section>}
