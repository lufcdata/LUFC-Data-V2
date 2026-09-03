import React from'react';
import'./PlayerCareerMetrics.css';

type Metric={label:string;subtitle:string;value:string;fill:number;tone?:'default'|'danger'};

const metrics:Metric[]=[
 {label:'Appearances',subtitle:'All competitions',value:'772',fill:100},
 {label:'Starts',subtitle:'All competitions',value:'771',fill:99.9},
 {label:'Substitute Appearances',subtitle:'All competitions',value:'1',fill:1},
 {label:'Subbed Off',subtitle:'All competitions',value:'10',fill:1.3},
 {label:'Goals Scored',subtitle:'All competitions',value:'115',fill:14.9},
 {label:'Games Won',subtitle:'In appearances',value:'406',fill:52.6},
 {label:'Win Rate',subtitle:'In appearances',value:'52.6%',fill:52.6},
 {label:'Captain',subtitle:'Matches as captain',value:'489',fill:63.3},
 {label:'Goals Per Game',subtitle:'All competitions',value:'0.15',fill:15},
 {label:'Red Cards',subtitle:'All competitions',value:'3',fill:30,tone:'danger'},
];

export default function PlayerCareerMetrics(){return <section className="card player-career-metrics"><div className="player-career-metrics-head"><div><span className="section-kicker">Career overview</span><h2>Leeds Career Metrics</h2></div></div><div className="player-career-metrics-list">{metrics.map(metric=><div className="player-career-metrics-row" key={metric.label}><div className="player-career-metrics-copy"><strong>{metric.label}</strong><span>{metric.subtitle}</span></div><div className="player-career-metrics-line"><span className={`player-career-metrics-track${metric.tone==='danger'?' danger':''}`}><i style={{width:`${metric.fill}%`}}/></span><b>{metric.value}</b></div></div>)}</div></section>}
