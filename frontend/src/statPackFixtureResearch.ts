export type FixtureResearchMatch={
 match_id:number;
 match_date:string;
 season:string|null;
 opponent:string;
 competition:string;
 venue_type:string;
 leeds_score:number;
 opponent_score:number;
 result:string;
 stadium:string|null;
 leeds_manager:string|null;
 first_goal?:string|null;
};

export type UpcomingFixtureContext={
 opponent:string;
 competition:string;
 venue:'H'|'A';
 stadium?:string|null;
 season:string;
 manager?:string|null;
};

export type FixtureResearchFinding={
 label:string;
 text:string;
 priority:number;
 evidence:string;
 family:string;
 grade:'A'|'B';
};

const won=(m:FixtureResearchMatch)=>m.result==='Won';
const seasonStart=(s:string|null)=>Number((s??'0').slice(0,4))||0;
const wdl=(xs:FixtureResearchMatch[])=>({w:xs.filter(m=>m.result==='Won').length,d:xs.filter(m=>m.result==='Drawn').length,l:xs.filter(m=>m.result==='Lost').length});
const pct=(n:number,d:number)=>d?Math.round(n*100/d):0;

/**
 * Fixture-aware research families. These deliberately require authoritative
 * upcoming venue/competition context so a home-specific story can never be
 * generated merely because an opponent was selected.
 */
export function researchUpcomingFixture(
 matches:FixtureResearchMatch[],
 fixture:UpcomingFixtureContext,
):FixtureResearchFinding[]{
 const chron=[...matches].sort((a,b)=>a.match_date.localeCompare(b.match_date)||a.match_id-b.match_id);
 const out:FixtureResearchFinding[]=[];
 const add=(label:string,text:string,priority:number,evidence:string,family:string,grade:'A'|'B'='A')=>out.push({label,text,priority,evidence,family,grade});
 const scope=(m:FixtureResearchMatch)=>m.competition===fixture.competition;
 const venue=(m:FixtureResearchMatch)=>m.venue_type===fixture.venue;
 const currentSeason=chron.filter(m=>m.season===fixture.season&&scope(m));
 const currentVenue=currentSeason.filter(venue);
 const manager=fixture.manager??[...chron].reverse().find(m=>m.leeds_manager)?.leeds_manager??null;

 // Back-to-back (and longer) home/away wins under the current manager.
 if(manager){
  const managerVenue=chron.filter(m=>m.leeds_manager===manager&&scope(m)&&venue(m));
  let run=0;
  for(let i=managerVenue.length-1;i>=0&&won(managerVenue[i]);i--)run++;
  if(run>=1){
   const target=run+1;
   const priorManagers=Array.from(new Set(chron.map(m=>m.leeds_manager).filter((x):x is string=>Boolean(x)&&x!==manager)));
   let latest:{name:string;date:string}|null=null;
   for(const name of priorManagers){
    let r=0;
    for(const m of chron.filter(x=>x.leeds_manager===name&&scope(x)&&venue(x))){
     if(won(m)){r++;if(r>=target&&(!latest||m.match_date>latest.date))latest={name,date:m.match_date}}else r=0;
    }
   }
   const where=fixture.venue==='H'?'home':'away';
   if(target>=2&&latest)add(`Manager · Consecutive ${fixture.venue==='H'?'Home':'Away'} Wins`,`${manager} can lead Leeds to ${target} consecutive ${fixture.competition} ${where} wins. The last Leeds manager to reach that sequence was ${latest.name} in ${latest.date.slice(0,4)}.`,target>=3?98:94,`${managerVenue.length} ${fixture.competition} ${where} matches under ${manager}; all previous Leeds managers compared`,`manager-venue-run`,target>=3?'A':'B');
  }
 }

 // Opening home/away matches of a league/competition season: exact-stage history.
 const completed=currentVenue.length;
 const allWon=completed>0&&currentVenue.every(won);
 if(allWon&&completed<=5){
  const nextStage=completed+1;
  const priorSeasons=Array.from(new Set(chron.filter(m=>seasonStart(m.season)<seasonStart(fixture.season)).map(m=>m.season).filter((s):s is string=>Boolean(s))));
  const qualifying=priorSeasons.map(s=>({s,x:chron.filter(m=>m.season===s&&scope(m)&&venue(m)).slice(0,nextStage)})).filter(v=>v.x.length===nextStage&&v.x.every(won));
  const latest=qualifying.at(-1);
  const where=fixture.venue==='H'?'home':'away';
  if(latest)add(`Season Start · Opening ${fixture.venue==='H'?'Home':'Away'} Wins`,`Victory over ${fixture.opponent} would mean Leeds have won their opening ${nextStage} ${where} matches of the ${fixture.competition} campaign for the first time since ${latest.s}.`,99,`${priorSeasons.length} previous seasons checked at exactly ${nextStage} ${where} matches`,`season-opening-venue`);
  else if(priorSeasons.length>=10)add(`Season Start · Opening ${fixture.venue==='H'?'Home':'Away'} Record`,`Victory over ${fixture.opponent} would give Leeds wins in their opening ${nextStage} ${where} matches of the ${fixture.competition} campaign, a sequence not found in the recorded archive.`,100,`${priorSeasons.length} previous seasons checked at exactly ${nextStage} ${where} matches`,`season-opening-venue`);
 }

 // Stadium-specific winning sequence. Only legal when the upcoming stadium is known.
 if(fixture.stadium){
  const atGround=chron.filter(m=>m.stadium===fixture.stadium&&scope(m));
  let run=0;
  for(let i=atGround.length-1;i>=0&&won(atGround[i]);i--)run++;
  if(run>=1){
   const target=run+1;
   let historicalMax=0,r=0,lastAtTarget:FixtureResearchMatch|null=null;
   for(const m of atGround.slice(0,-run)){if(won(m)){r++;historicalMax=Math.max(historicalMax,r);if(r>=target)lastAtTarget=m}else r=0}
   if(target>historicalMax)add('Stadium · Winning Sequence',`Victory over ${fixture.opponent} would give Leeds ${target} consecutive ${fixture.competition} wins at ${fixture.stadium}, their longest recorded winning sequence at the ground.`,98,`${atGround.length} previous ${fixture.competition} matches at ${fixture.stadium} checked`,'stadium-run');
   else if(lastAtTarget)add('Stadium · Winning Sequence',`Victory over ${fixture.opponent} would give Leeds ${target} consecutive ${fixture.competition} wins at ${fixture.stadium}, a sequence they last reached there in ${lastAtTarget.match_date.slice(0,4)}.`,95,`${atGround.length} previous ${fixture.competition} matches at ${fixture.stadium} checked`,'stadium-run');
  }
 }

 // First-goal outcome intelligence: recent form plus opponent-specific response.
 // This is descriptive context, so it remains Grade B until a separate historical
 // significance comparator proves a record/first/since angle.
 const scoped=chron.filter(scope);
 for(const state of ['Scored','Conceded'] as const){
  const eligible=scoped.filter(m=>m.first_goal===state);
  const recent=eligible.slice(-20);
  if(recent.length>=10){
   const r=wdl(recent);
   const rate=state==='Scored'?pct(r.w,recent.length):pct(r.d+r.w,recent.length);
   if((state==='Scored'&&rate>=65)||(state==='Conceded'&&rate>=35)){
    const action=state==='Scored'?'when scoring first':'after conceding first';
    add(`First Goal · ${state==='Scored'?'Protection':'Recovery'}`,`Leeds have ${state==='Scored'?'won':'avoided defeat in'} ${state==='Scored'?r.w:r.w+r.d} of their last ${recent.length} ${fixture.competition} matches ${action} (${r.w}W ${r.d}D ${r.l}L).`,84,`${recent.length} most recent ${fixture.competition} matches where Leeds ${state==='Scored'?'scored':'conceded'} first checked`,'first-goal-recent','B');
   }
  }
  const vsOpponent=eligible.filter(m=>m.opponent===fixture.opponent).slice(-12);
  if(vsOpponent.length>=5){
   const r=wdl(vsOpponent);
   const strong=state==='Scored'?r.l<=1:r.w+r.d>=Math.ceil(vsOpponent.length/2);
   if(strong){
    const action=state==='Scored'?'after scoring first':'after conceding first';
    add(`First Goal · ${fixture.opponent}`,`In their last ${vsOpponent.length} ${fixture.competition} meetings with ${fixture.opponent} in which Leeds ${state==='Scored'?'scored':'conceded'} first, Leeds have a record of ${r.w} wins, ${r.d} draws and ${r.l} defeats ${action}.`,86,`${vsOpponent.length} most recent opponent meetings with first-goal state=${state}`,'first-goal-opponent','B');
   }
  }
 }

 return out.sort((a,b)=>b.priority-a.priority);
}
