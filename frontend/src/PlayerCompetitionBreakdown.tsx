import React from'react';
import'./PlayerCompetitionBreakdown.css';

const comps=[['Division One',453,452,1,58,253,55.8],['Division Two',133,133,0,32,53,39.8],['FA Cup',69,69,0,6,36,52.2],['Inter-City Fairs Cup',51,51,0,10,26,51.0],['League Cup',38,38,0,3,20,52.6],['European Cup',14,14,0,6,10,71.4],["European Cup Winners' Cup",7,7,0,0,4,57.1],['UEFA Cup',5,5,0,0,3,60.0],['FA Charity Shield',2,2,0,0,1,50.0]] as const;

export default function PlayerCompetitionBreakdown(){
 return <section className="card player-competition-compact">
  <div className="player-profile-panelhead"><div><span className="section-kicker">Career analysis</span><h2>Competition Breakdown</h2></div><div className="section-kicker">9 Competitions</div></div>
  <div className="player-competition-compact-list">
   {comps.map(([competition,apps,,,goals,won,winPct])=><div className="player-competition-compact-row" key={competition}>
    <div className="player-competition-compact-main"><strong>{competition}</strong><span>{apps} apps · {goals} goals · {won} wins</span></div>
    <div className="player-competition-compact-rate"><strong>{winPct.toFixed(1)}%</strong><span>Win rate</span></div>
    <div className="player-competition-compact-track"><i style={{width:`${winPct}%`}}/></div>
   </div>)}
  </div>
 </section>;
}
