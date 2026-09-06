import type{FixtureResearchFinding,FixtureResearchMatch,UpcomingFixtureContext}from'./statPackFixtureResearch';

const words=(n:number)=>['zero','one','two','three','four','five','six','seven','eight','nine','ten'][n]??String(n);

export function researchCompetitionFirstWin(
 matches:readonly FixtureResearchMatch[],
 fixture:UpcomingFixtureContext|null,
):FixtureResearchFinding[]{
 if(!fixture)return[];
 const scoped=[...matches]
  .filter(m=>m.opponent===fixture.opponent&&m.competition===fixture.competition)
  .sort((a,b)=>a.match_date.localeCompare(b.match_date)||a.match_id-b.match_id);
 if(scoped.length<2||scoped.some(m=>m.result==='Won'))return[];
 const d=scoped.filter(m=>m.result==='Draw').length;
 const l=scoped.filter(m=>m.result==='Lost').length;
 return[{
  label:'Opponent History · First Competition Win',
  text:`Leeds are seeking their first win over ${fixture.opponent} in the ${fixture.competition}, having failed to win any of their previous ${words(scoped.length)} attempts in the competition (W0, D${d}, L${l}).`,
  priority:100,
  evidence:`${scoped.length} ${fixture.competition} meetings with ${fixture.opponent} checked across all venues; no Leeds win found; IDs ${scoped.map(m=>m.match_id).join(', ')}`,
  family:'opponent-competition-first-win',
  grade:'A',
 }];
}
