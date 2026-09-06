import type{FixtureResearchFinding,FixtureResearchMatch,UpcomingFixtureContext}from'./statPackFixtureResearch';

const won=(m:FixtureResearchMatch)=>m.result==='Won';
const wdl=(xs:readonly FixtureResearchMatch[])=>({w:xs.filter(m=>m.result==='Won').length,d:xs.filter(m=>m.result==='Draw').length,l:xs.filter(m=>m.result==='Lost').length});
const monthYear=(d:string)=>new Date(`${d}T00:00:00`).toLocaleDateString('en-GB',{month:'long',year:'numeric'});

/**
 * Foundational opponent history across all competitions.
 *
 * This is deliberately separate from exact competition + H/A research. It asks
 * the broader editorial question: how long has it been since Leeds last beat the
 * selected opponent in any competitive fixture? Only a meaningful drought or a
 * genuine first is promoted, preventing an ordinary recent win from becoming
 * filler. Every result, score and date comes from the LUFC database population.
 */
export function researchOpponentAllCompetitionHistory(matches:readonly FixtureResearchMatch[],fixture:UpcomingFixtureContext):FixtureResearchFinding[]{
 const versus=[...matches].filter(m=>m.opponent===fixture.opponent).sort((a,b)=>a.match_date.localeCompare(b.match_date)||a.match_id-b.match_id);
 if(versus.length<5)return[];
 const lastWin=[...versus].reverse().find(won);
 if(!lastWin){
  const r=wdl(versus);
  return[{
   label:'Opponent History · First Win',
   text:`Leeds United are yet to beat ${fixture.opponent} in the recorded competitive history of the fixture, with ${versus.length} meetings returning D${r.d} L${r.l}.`,
   priority:100,
   evidence:`${versus.length} meetings with ${fixture.opponent} checked across all competitions; no Leeds win found; IDs ${versus.map(m=>m.match_id).join(', ')}`,
   family:'opponent-all-comps-last-win',
   grade:'A',
  }];
 }
 const since=versus.filter(m=>m.match_date>lastWin.match_date);
 if(since.length<4||since.some(won))return[];
 const r=wdl(since);
 return[{
  label:'Opponent History · Last Win',
  text:`Leeds United are winless in their last ${since.length} meetings with ${fixture.opponent} across all competitions (D${r.d} L${r.l}), since a ${lastWin.leeds_score}-${lastWin.opponent_score} ${lastWin.competition} victory in ${monthYear(lastWin.match_date)}.`,
  priority:99,
  evidence:`${versus.length} meetings with ${fixture.opponent} checked across all competitions; last win match ${lastWin.match_id}; subsequent IDs ${since.map(m=>m.match_id).join(', ')}`,
  family:'opponent-all-comps-last-win',
  grade:'A',
 }];
}
