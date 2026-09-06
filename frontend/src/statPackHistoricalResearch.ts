import type{FixtureResearchFinding,FixtureResearchMatch,UpcomingFixtureContext}from'./statPackFixtureResearch';

const won=(m:FixtureResearchMatch)=>m.result==='Won';
const lost=(m:FixtureResearchMatch)=>m.result==='Lost';
const league=(m:FixtureResearchMatch)=>/Premier League|Championship|Division One|Division Two|League One|League Two/i.test(m.competition);
const margin=(m:FixtureResearchMatch)=>m.leeds_score-m.opponent_score;
const seasonYear=(s:string|null)=>Number((s??'0').slice(0,4))||0;
const monthYear=(d:string)=>new Date(`${d}T00:00:00`).toLocaleDateString('en-GB',{month:'long',year:'numeric'});

/** Gold research families that turn a fixture fact into historical context.
 * All inputs are LUFC database rows; this module performs no external lookup.
 */
export function researchHistoricalFixtureContext(matches:FixtureResearchMatch[],fixture:UpcomingFixtureContext):FixtureResearchFinding[]{
 const chron=[...matches].sort((a,b)=>a.match_date.localeCompare(b.match_date)||a.match_id-b.match_id);
 const out:FixtureResearchFinding[]=[];
 const add=(label:string,text:string,priority:number,evidence:string,family:string)=>out.push({label,text,priority,evidence,family,grade:'A'});
 const versus=chron.filter(m=>m.opponent===fixture.opponent);
 const leagueVersus=versus.filter(league);
 const venueLeague=leagueVersus.filter(m=>m.venue_type===fixture.venue);

 // Opponent result magnitude: contextualise the most recent meeting against the
 // entire earlier opponent history instead of merely repeating its scoreline.
 const last=versus.at(-1);
 if(last&&won(last)){
  const previous=versus.slice(0,-1).filter(won);
  const lastMargin=margin(last);
  const priorAtLeast=[...previous].reverse().find(m=>margin(m)>=lastMargin);
  if(lastMargin>=2&&priorAtLeast){
   const years=Math.max(0,Number(last.match_date.slice(0,4))-Number(priorAtLeast.match_date.slice(0,4)));
   if(years>=5)add('Opponent History · Winning Margin',`Leeds' last meeting with ${fixture.opponent} was their biggest win against them since a ${priorAtLeast.leeds_score}-${priorAtLeast.opponent_score} victory in ${monthYear(priorAtLeast.match_date)}.`,98,`${versus.length} competitive meetings checked; previous equal-or-greater Leeds winning margin was match ${priorAtLeast.match_id}`,'opponent-winning-margin');
  }else if(lastMargin>=3&&previous.every(m=>margin(m)<lastMargin))add('Opponent History · Record Winning Margin',`Leeds' last meeting with ${fixture.opponent} was their biggest recorded win against them.`,100,`${versus.length} competitive meetings checked`,'opponent-winning-margin');
 }

 // Consecutive home/away league wins against this opponent. A one-win current
 // run becomes interesting only when the next win would revive a historic pair.
 let currentRun=0;
 for(let i=venueLeague.length-1;i>=0&&won(venueLeague[i]);i--)currentRun++;
 if(currentRun>=1){
  const target=currentRun+1;
  let run=0,previousCompletion:FixtureResearchMatch|null=null;
  for(const m of venueLeague.slice(0,-currentRun)){
   if(won(m)){run++;if(run>=target)previousCompletion=m}else run=0;
  }
  if(previousCompletion){
   const years=Math.max(0,seasonYear(fixture.season)-Number(previousCompletion.match_date.slice(0,4)));
   if(years>=5)add(`Opponent History · Consecutive ${fixture.venue==='H'?'Home':'Away'} League Wins`,`Leeds are looking to record ${target===2?'consecutive':`${target} consecutive`} ${fixture.venue==='H'?'home':'away'} league wins against ${fixture.opponent} for the first time since ${previousCompletion.match_date.slice(0,4)}.`,years>=25?100:years>=10?99:97,`${venueLeague.length} ${fixture.venue==='H'?'home':'away'} league meetings checked; previous ${target}-win sequence completed in match ${previousCompletion.match_id}`,'opponent-league-win-run');
  }
 }

 // League doubles: same opponent, same season, one home and one away league win.
 // This covers both Leeds pursuing a double and trying to avoid suffering one.
 const seasonLeague=leagueVersus.filter(m=>m.season===fixture.season);
 const reverseVenue=fixture.venue==='H'?'A':'H';
 const reverse=seasonLeague.find(m=>m.venue_type===reverseVenue);
 if(reverse){
  const priorSeasons=Array.from(new Set(leagueVersus.filter(m=>seasonYear(m.season)<seasonYear(fixture.season)).map(m=>m.season).filter((s):s is string=>Boolean(s))));
  const completed=(s:string,forLeeds:boolean)=>{
   const xs=leagueVersus.filter(m=>m.season===s);
   return ['H','A'].every(v=>xs.some(m=>m.venue_type===v&&(forLeeds?won(m):lost(m))));
  };
  if(won(reverse)){
   const previous=[...priorSeasons].reverse().find(s=>completed(s,true));
   if(previous){const years=seasonYear(fixture.season)-seasonYear(previous);if(years>=5)add('League Double · Leeds',`Leeds could complete a league double over ${fixture.opponent} for the first time since the ${previous} season.`,years>=25?100:years>=10?99:97,`${priorSeasons.length} previous league seasons against ${fixture.opponent} checked; previous Leeds double: ${previous}`,'league-double');}
   else if(priorSeasons.length>=5)add('League Double · Leeds',`Leeds could complete a league double over ${fixture.opponent} for the first time in their recorded league history.`,100,`${priorSeasons.length} previous league seasons against ${fixture.opponent} checked; no Leeds home-and-away league double found`,'league-double');
  }else if(lost(reverse)){
   const previous=[...priorSeasons].reverse().find(s=>completed(s,false));
   if(previous){const years=seasonYear(fixture.season)-seasonYear(previous);if(years>=5)add('League Double · Against Leeds',`${fixture.opponent} could complete a league double over Leeds for the first time since the ${previous} season.`,years>=25?100:years>=10?99:97,`${priorSeasons.length} previous league seasons against ${fixture.opponent} checked; previous double against Leeds: ${previous}`,'league-double-against');}
   else if(priorSeasons.length>=5)add('League Double · Against Leeds',`${fixture.opponent} could complete a league double over Leeds for the first time in the recorded league history of the fixture.`,100,`${priorSeasons.length} previous league seasons against ${fixture.opponent} checked; no opponent home-and-away league double found`,'league-double-against');
  }
 }
 return out;
}
