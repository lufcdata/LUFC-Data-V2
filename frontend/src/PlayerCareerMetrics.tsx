import React from'react';
import'./PlayerCareerMetrics.css';

type Metric={label:string;value:string;fill:number;rank:string;tone?:'default'|'danger'};

const metrics:Metric[]=[
 {label:'Seasons',value:'18',fill:100,rank:'4th'},
 {label:'Appearances',value:'772',fill:100,rank:'2nd'},
 {label:'Starts',value:'771',fill:99.9,rank:'2nd'},
 {label:'Subbed On',value:'1',fill:1,rank:'407th'},
 {label:'Subbed Off',value:'10',fill:1.3,rank:'160th'},
 {label:'Goals Scored',value:'115',fill:14.9,rank:'5th'},
 {label:'Games Won',value:'406',fill:52.6,rank:'1st'},
 {label:'Win Rate',value:'52.6%',fill:52.6,rank:'117th'},
 {label:'Starts as Captain',value:'489',fill:63.3,rank:'1st'},
 {label:'Goals Per Game',value:'0.15',fill:15,rank:'206th'},
 {label:'Red Cards',value:'3',fill:30,rank:'6th',tone:'danger'},
];

export default function PlayerCareerMetrics(){return <section className="card player-career-metrics"><div className="player-career-metrics-head"><div><span className="section-kicker">Career overview</span><h2>Leeds Career Metrics</h2></div></div><div className="player-career-metrics-list">{metrics.map(metric=><div className="player-career-metrics-row" key={metric.label}><div className="player-career-metrics-copy"><strong>{metric.label}</strong></div><div className="player-career-metrics-line"><span className={`player-career-metrics-track${metric.tone==='danger'?' danger':''}`}><i style={{width:`${metric.fill}%`}}/></span><b>{metric.value}</b><em className="player-career-metrics-rank">{metric.rank}</em></div></div>)}</div></section>}
