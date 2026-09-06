import type{FixtureResearchFinding,FixtureResearchMatch}from'./statPackFixtureResearch';

export type CareerMilestonePlayer={
 player_id:number;
 display_name:string;
 active:boolean|null;
};

export type CareerMilestonePlayerMatch={
 match_id:number;
 player_id:number;
};

const PLAYER_MANAGER_MILESTONES=[50,75,100,150,200,250,300,400,500];

/**
 * Player appearance milestones under one Leeds manager/head coach.
 *
 * Population: competitive Leeds appearances from player_matches joined to
 * match_centre_summary rows where leeds_manager equals the selected current
 * manager. All competitions are intentionally included. The same population is
 * used for every player so the ordinal/first claim is authoritative.
 */
export function researchPlayerManagerAppearanceMilestones(
 matches:readonly FixtureResearchMatch[],
 playerMatches:readonly CareerMilestonePlayerMatch[],
 players:readonly CareerMilestonePlayer[],
 manager:string|null,
):FixtureResearchFinding[]{
 if(!manager)return[];
 const matchById=new Map(matches.map(m=>[m.match_id,m]));
 const counts=new Map<number,number>();
 for(const pm of playerMatches){
  const match=matchById.get(pm.match_id);
  if(!match||match.leeds_manager!==manager)continue;
  counts.set(pm.player_id,(counts.get(pm.player_id)??0)+1);
 }
 const out:FixtureResearchFinding[]=[];
 for(const player of players.filter(p=>p.active)){
  const appearances=counts.get(player.player_id)??0;
  const target=PLAYER_MANAGER_MILESTONES.find(n=>appearances===n-1);
  if(!target)continue;
  const already=players.filter(p=>p.player_id!==player.player_id&&(counts.get(p.player_id)??0)>=target);
  if(already.length===0){
   out.push({
    label:'Player · Manager Appearance Milestone',
    text:`Should ${player.display_name} feature, he will become the first player to reach ${target} appearances for Leeds United across all competitions under ${manager}.`,
    priority:100,
    evidence:`${appearances} completed Leeds appearances under ${manager}; all player_matches joined to match_centre_summary across all competitions; no other player has reached ${target} under ${manager}`,
    family:'player-manager-appearance-milestone',
    grade:'A',
   });
  }else if(target>=100){
   const ordinal=already.length+1;
   const suffix=ordinal%100>=11&&ordinal%100<=13?'th':ordinal%10===1?'st':ordinal%10===2?'nd':ordinal%10===3?'rd':'th';
   out.push({
    label:'Player · Manager Appearance Milestone',
    text:`Should ${player.display_name} feature, he will become the ${ordinal}${suffix} player to reach ${target} appearances for Leeds United across all competitions under ${manager}.`,
    priority:96,
    evidence:`${appearances} completed Leeds appearances under ${manager}; ${already.length} other player${already.length===1?' has':'s have'} already reached ${target} under ${manager}`,
    family:'player-manager-appearance-milestone',
    grade:'A',
   });
  }
 }
 return out;
}
