import{matchesAtPhysicalStadium}from'./stadiumIdentity';

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
const wdl=(xs:FixtureResearchMatch[])=>({w:xs.filter(m=>m.result==='Won').length,d:xs.filter(m=>m.result==='Draw').length,l:xs.filter(m=>m.result==='Lost').length});
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

 // Stadium-specific winning sequence. Physical venue identity is canonicalised so
 // sponsorship/name changes do not split one ground's history.
 if(fixture.stadium){
  const atGround=matchesAtPhysicalStadium(chron,fixture.stadium).filter(scope);
  let run=0;
  for(let i=atGround.length-1;i>=0&&won(atGround[i]);i--)run++;
  if(run>=1){
   const target=run+1;
   let historicalMax=0,r=0,lastAtTarget:FixtureResearchMatch|null=null;
   for(const m of atGround.slice(0,-run)){if(won(m)){r++;historicalMax=Math.max(historicalMax,r);if(r>=target)lastAtTarget=m}else r=0}
   if(target>historicalMax)add('Stadium · Winning Sequence',`Victory over ${fixture.opponent} would give Leeds ${target} consecutive ${fixture.competition} wins at ${fixture.stadium}, their longest recorded winning sequence at the ground.`,98,`${atGround.length} previous ${fixture.competition} matches at the same physical stadium checked across verified venue-name aliases`,'stadium-run');
   else if(lastAtTarget)add('Stadium · Winning Sequence',`Victory over ${fixture.opponent} would give Leeds ${target} consecutive ${fixture.competition} wins at ${fixture.stadium}, a sequence they last reached there in ${lastAtTarget.match_date.slice(0,4)}.`,95,`${atGround.length} previous ${fixture.competition} matches at the same physical stadium checked across verified venue-name aliases`,'stadium-run');
  }
 }

 // Opponent + fixture venue sequence. This keeps home/away history separate and
 // only earns Grade A when the current run has a genuine historical comparator.
 const venueH2h=chron.filter(m=>scope(m)&&venue(m)&&m.opponent===fixture.opponent);
 let venueWinRun=0;
 for(let i=venueH2h.length-1;i>=0&&won(venueH2h[i]);i--)venueWinRun++;
 if(venueWinRun>=1){
  const target=venueWinRun+1;
  let historicalMax=0,r=0,lastAtTarget:FixtureResearchMatch|null=null;
  for(const m of venueH2h.slice(0,-venueWinRun)){if(won(m)){r++;historicalMax=Math.max(historicalMax,r);if(r>=target)lastAtTarget=m}else r=0}
  const where=fixture.venue==='H'?'at home':'away';
  if(target>historicalMax)add(`Opponent · ${fixture.venue==='H'?'Home':'Away'} Winning Sequence`,`Victory over ${fixture.opponent} would give Leeds ${target} consecutive ${fixture.competition} wins ${where} against them, their longest recorded winning sequence in this fixture at that venue.`,99,`${venueH2h.length} ${fixture.competition} ${where} meetings with ${fixture.opponent} checked`,'opponent-venue-run');
  else if(lastAtTarget)add(`Opponent · ${fixture.venue==='H'?'Home':'Away'} Winning Sequence`,`Victory over ${fixture.opponent} would give Leeds ${target} consecutive ${fixture.competition} wins ${where} against them, a sequence they last reached in ${lastAtTarget.match_date.slice(0,4)}.`,96,`${venueH2h.length} ${fixture.competition} ${where} meetings with ${fixture.opponent} checked`,'opponent-venue-run');
 }

 // Venue-conditioned unbeaten history against the upcoming opponent. A draw or win
 // in the upcoming fixture extends the run; only record/since comparators earn Grade A.
 let venueUnbeatenRun=0;
 for(let i=venueH2h.length-1;i>=0&&venueH2h[i].result!=='Lost';i--)venueUnbeatenRun++;
 if(venueUnbeatenRun>=2){
  const target=venueUnbeatenRun+1;
  let historicalMax=0,r=0,lastAtTarget:FixtureResearchMatch|null=null;
  for(const m of venueH2h.slice(0,-venueUnbeatenRun)){if(m.result!=='Lost'){r++;historicalMax=Math.max(historicalMax,r);if(r>=target)lastAtTarget=m}else r=0}
  const where=fixture.venue==='H'?'at home':'away';
  if(target>historicalMax)add(`Opponent · ${fixture.venue==='H'?'Home':'Away'} Unbeaten Sequence`,`Avoiding defeat against ${fixture.opponent} would make it ${target} consecutive ${fixture.competition} meetings unbeaten ${where} against them, Leeds' longest recorded unbeaten sequence in this fixture at that venue.`,99,`${venueH2h.length} ${fixture.competition} ${where} meetings with ${fixture.opponent} checked`,'opponent-venue-unbeaten');
  else if(lastAtTarget)add(`Opponent · ${fixture.venue==='H'?'Home':'Away'} Unbeaten Sequence`,`Avoiding defeat against ${fixture.opponent} would make it ${target} consecutive ${fixture.competition} meetings unbeaten ${where} against them, a sequence they last reached in ${lastAtTarget.match_date.slice(0,4)}.`,96,`${venueH2h.length} ${fixture.competition} ${where} meetings with ${fixture.opponent} checked`,'opponent-venue-unbeaten');
 }

 // Venue-conditioned clean-sheet history against the upcoming opponent.
 // This is separate from the all-venue opponent sequence below: the fixture venue
 // is part of the trigger, so home and away shutout histories can never contaminate each other.
 let venueCleanRun=0;
 for(let i=venueH2h.length-1;i>=0&&venueH2h[i].opponent_score===0;i--)venueCleanRun++;
 if(venueCleanRun>=1){
  const target=venueCleanRun+1;
  let historicalMax=0,r=0,lastAtTarget:FixtureResearchMatch|null=null;
  for(const m of venueH2h.slice(0,-venueCleanRun)){if(m.opponent_score===0){r++;historicalMax=Math.max(historicalMax,r);if(r>=target)lastAtTarget=m}else r=0}
  const where=fixture.venue==='H'?'at home':'away';
  if(target>historicalMax)add(`Opponent · ${fixture.venue==='H'?'Home':'Away'} Clean-Sheet Sequence`,`A clean sheet against ${fixture.opponent} would be Leeds' ${target}th consecutive ${fixture.competition} shutout ${where} against them, their longest recorded clean-sheet sequence in this fixture at that venue.`,98,`${venueH2h.length} ${fixture.competition} ${where} meetings with ${fixture.opponent} checked`,'opponent-venue-clean-sheet');
  else if(lastAtTarget)add(`Opponent · ${fixture.venue==='H'?'Home':'Away'} Clean-Sheet Sequence`,`A clean sheet against ${fixture.opponent} would be Leeds' ${target}th consecutive ${fixture.competition} shutout ${where} against them, a sequence they last reached in ${lastAtTarget.match_date.slice(0,4)}.`,95,`${venueH2h.length} ${fixture.competition} ${where} meetings with ${fixture.opponent} checked`,'opponent-venue-clean-sheet');
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

 // Historical significance for first-goal behaviour. Compare the current season
 // at the exact same number of first-goal opportunities with every prior season.
 const priorSeasons=Array.from(new Set(scoped.filter(m=>seasonStart(m.season)<seasonStart(fixture.season)).map(m=>m.season).filter((s):s is string=>Boolean(s))));
 for(const state of ['Scored','Conceded'] as const){
  const now=currentSeason.filter(m=>m.first_goal===state);
  if(now.length>=4){
   const nr=wdl(now),n=now.length;
   const nowSuccess=state==='Scored'?nr.w:nr.w+nr.d;
   const samples=priorSeasons.map(s=>{const x=scoped.filter(m=>m.season===s&&m.first_goal===state).slice(0,n);const r=wdl(x);return{s,x,success:state==='Scored'?r.w:r.w+r.d}}).filter(v=>v.x.length===n);
   if(samples.length>=5){
    const best=Math.max(...samples.map(v=>v.success));
    const latestEqual=[...samples].reverse().find(v=>v.success>=nowSuccess);
    if(nowSuccess>best){
     add(`First Goal · Season ${state==='Scored'?'Conversion':'Recovery'} Record`,state==='Scored'?`Leeds have won ${nowSuccess} of the ${n} ${fixture.competition} matches in which they have scored first this season, their best recorded return through the same number of scoring-first matches.`:`Leeds have avoided defeat in ${nowSuccess} of the ${n} ${fixture.competition} matches in which they have conceded first this season, their best recorded recovery return through the same number of conceding-first matches.`,99,`${samples.length} previous seasons compared after exactly ${n} ${state==='Scored'?'scoring-first':'conceding-first'} matches`,`first-goal-season-history`);
    }else if(latestEqual&&latestEqual.s!==fixture.season&&nowSuccess>=Math.ceil(n*.75)){
     add(`First Goal · Season ${state==='Scored'?'Conversion':'Recovery'} Since`,state==='Scored'?`Leeds have won ${nowSuccess} of the ${n} ${fixture.competition} matches in which they have scored first this season, their best return through the same number of scoring-first matches since ${latestEqual.s}.`:`Leeds have avoided defeat in ${nowSuccess} of the ${n} ${fixture.competition} matches in which they have conceded first this season, their best recovery return through the same number of conceding-first matches since ${latestEqual.s}.`,96,`${samples.length} previous seasons compared after exactly ${n} ${state==='Scored'?'scoring-first':'conceding-first'} matches`,`first-goal-season-history`);
    }
   }
  }

  // Opponent-specific unbeaten/winning sequence conditioned on who scored first.
  const h2h=scoped.filter(m=>m.opponent===fixture.opponent&&m.first_goal===state);
  let run=0;
  const qualifies=(m:FixtureResearchMatch)=>state==='Scored'?m.result==='Won':m.result!=='Lost';
  for(let i=h2h.length-1;i>=0&&qualifies(h2h[i]);i--)run++;
  if(run>=2){
   const target=run+1;
   let historicalMax=0,r=0,lastTarget:FixtureResearchMatch|null=null;
   for(const m of h2h.slice(0,-run)){if(qualifies(m)){r++;historicalMax=Math.max(historicalMax,r);if(r>=target)lastTarget=m}else r=0}
   if(target>historicalMax){
    add(`First Goal · ${fixture.opponent} Sequence`,state==='Scored'?`If Leeds score first against ${fixture.opponent} and win, it would be their ${target}th consecutive ${fixture.competition} victory against them after opening the scoring, the longest such sequence in the recorded archive.`:`If Leeds concede first against ${fixture.opponent} but avoid defeat, it would be the ${target}th consecutive ${fixture.competition} meeting in which they have recovered after falling behind, the longest such sequence in the recorded archive.`,98,`${h2h.length} ${fixture.competition} meetings with ${fixture.opponent} where first-goal state=${state} checked`,`first-goal-opponent-history`);
   }else if(lastTarget){
    add(`First Goal · ${fixture.opponent} Sequence`,state==='Scored'?`If Leeds score first against ${fixture.opponent} and win, it would be their ${target}th consecutive ${fixture.competition} victory against them after opening the scoring, a sequence last reached in ${lastTarget.match_date.slice(0,4)}.`:`If Leeds concede first against ${fixture.opponent} but avoid defeat, it would be the ${target}th consecutive ${fixture.competition} meeting in which they have recovered after falling behind, a sequence last reached in ${lastTarget.match_date.slice(0,4)}.`,95,`${h2h.length} ${fixture.competition} meetings with ${fixture.opponent} where first-goal state=${state} checked`,`first-goal-opponent-history`);
   }
  }
 }

 // Clean-sheet intelligence: exact-stage season comparison plus opponent-specific
 // sequence and win correlation. This uses final scores only, so it is archive-safe.
 if(currentSeason.length>=5){
  const stage=currentSeason.length,clean=currentSeason.filter(m=>m.opponent_score===0).length;
  const samples=priorSeasons.map(s=>{const x=scoped.filter(m=>m.season===s).slice(0,stage);return{s,x,clean:x.filter(m=>m.opponent_score===0).length}}).filter(v=>v.x.length===stage);
  if(samples.length>=5&&clean>=2){
   const best=Math.max(...samples.map(v=>v.clean));
   const latest=[...samples].reverse().find(v=>v.clean>=clean);
   if(clean>best)add('Clean Sheets · Historic Start',`Leeds have kept ${clean} clean sheets through their opening ${stage} ${fixture.competition} matches of ${fixture.season}, their most at this stage of a campaign in the recorded archive.`,98,`${samples.length} previous seasons compared after exactly ${stage} matches`,'clean-sheet-season-history');
   else if(latest&&clean>=Math.ceil(stage*.3))add('Clean Sheets · At This Stage',`Leeds have kept ${clean} clean sheets through their opening ${stage} ${fixture.competition} matches of ${fixture.season}. The last Leeds side with at least as many at this stage was ${latest.s}.`,94,`${samples.length} previous seasons compared after exactly ${stage} matches`,'clean-sheet-season-history');
  }
 }

 const opponentMatches=scoped.filter(m=>m.opponent===fixture.opponent);
 let cleanRun=0;
 for(let i=opponentMatches.length-1;i>=0&&opponentMatches[i].opponent_score===0;i--)cleanRun++;
 if(cleanRun>=1){
  const target=cleanRun+1;
  let max=0,r=0,lastTarget:FixtureResearchMatch|null=null;
  for(const m of opponentMatches.slice(0,-cleanRun)){if(m.opponent_score===0){r++;max=Math.max(max,r);if(r>=target)lastTarget=m}else r=0}
  if(target>max)add('Clean Sheets · Opponent Sequence',`A clean sheet against ${fixture.opponent} would be Leeds' ${target}th consecutive ${fixture.competition} shutout against them, the longest such sequence in the recorded archive.`,97,`${opponentMatches.length} ${fixture.competition} meetings with ${fixture.opponent} checked`,'clean-sheet-opponent-history');
  else if(lastTarget)add('Clean Sheets · Opponent Sequence',`A clean sheet against ${fixture.opponent} would be Leeds' ${target}th consecutive ${fixture.competition} shutout against them, a sequence last reached in ${lastTarget.match_date.slice(0,4)}.`,94,`${opponentMatches.length} ${fixture.competition} meetings with ${fixture.opponent} checked`,'clean-sheet-opponent-history');
 }

 const recentOpponent=opponentMatches.slice(-10),recentWins=recentOpponent.filter(m=>m.result==='Won');
 if(recentOpponent.length>=6&&recentWins.length>=3){
  const cleanWins=recentWins.filter(m=>m.opponent_score===0).length;
  if(cleanWins>=Math.ceil(recentWins.length*.6))add('Clean Sheets · Winning Formula',`Leeds have kept a clean sheet in ${cleanWins} of their ${recentWins.length} wins across the last ${recentOpponent.length} ${fixture.competition} meetings with ${fixture.opponent}.`,86,`${recentOpponent.length} recent opponent meetings checked`,'clean-sheet-win-correlation','B');
 }

 return out.sort((a,b)=>b.priority-a.priority);
}
