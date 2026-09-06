import type{FixtureResearchFinding,FixtureResearchMatch,UpcomingFixtureContext}from'./statPackFixtureResearch';
import{researchActiveUnbeatenRuns,researchCurrentCompetitionForm}from'./statPackCurrentFormResearch';
import{researchLondonAwayContext}from'./statPackLondonResearch';
import{matchesAtPhysicalStadium}from'./stadiumIdentity';

const won=(m:FixtureResearchMatch)=>m.result==='Won';
const lost=(m:FixtureResearchMatch)=>m.result==='Lost';
const league=(m:FixtureResearchMatch)=>/Premier League|Championship|Division One|Division Two|League One|League Two/i.test(m.competition);
const margin=(m:FixtureResearchMatch)=>m.leeds_score-m.opponent_score;
const seasonYear=(s:string|null)=>Number((s??'0').slice(0,4))||0;
const monthYear=(d:string)=>new Date(`${d}T00:00:00`).toLocaleDateString('en-GB',{month:'long',year:'numeric'});
const wdl=(xs:readonly FixtureResearchMatch[])=>({w:xs.filter(m=>m.result==='Won').length,d:xs.filter(m=>m.result==='Draw').length,l:xs.filter(m=>m.result==='Lost').length});
const goals=(xs:readonly FixtureResearchMatch[])=>({gf:xs.reduce((n,m)=>n+m.leeds_score,0),ga:xs.reduce((n,m)=>n+m.opponent_score,0)});
const MANAGER_MILESTONES=[50,100,150,200,250,300,400,500];

/** Gold research families that turn a fixture fact into historical context.
 * All inputs are LUFC database rows; this module performs no external lookup.
 */
export function researchHistoricalFixtureContext(matches:FixtureResearchMatch[],fixture:UpcomingFixtureContext):FixtureResearchFinding[]{
 const chron=[...matches].sort((a,b)=>a.match_date.localeCompare(b.match_date)||a.match_id-b.match_id);
 const activeUnbeaten=researchActiveUnbeatenRuns(chron,fixture.competition).filter(f=>fixture.venue==='A'?!f.family.includes('-matches-at-'):!f.family.includes('-away-'));
 const out:FixtureResearchFinding[]=[...activeUnbeaten,...researchCurrentCompetitionForm(chron,fixture.competition),...researchLondonAwayContext(chron,fixture)];
 const add=(label:string,text:string,priority:number,evidence:string,family:string)=>out.push({label,text,priority,evidence,family,grade:'A'});
 const versus=chron.filter(m=>m.opponent===fixture.opponent);
 const competitionVersus=versus.filter(m=>m.competition===fixture.competition);
 const leagueVersus=versus.filter(league);
 const venueLeague=leagueVersus.filter(m=>m.venue_type===fixture.venue);

 // Manager matches-in-charge milestones across all competitions. The selected
 // upcoming fixture supplies the current manager, while the archive determines
 // both the live count and the most recent previous manager/head coach to reach
 // the same landmark. Nothing is hard-coded to a particular manager or era.
 if(fixture.manager){
  const currentManagerMatches=chron.filter(m=>m.leeds_manager===fixture.manager);
  const target=MANAGER_MILESTONES.find(n=>currentManagerMatches.length===n-1);
  if(target){
   const managers=Array.from(new Set(chron.map(m=>m.leeds_manager).filter((n):n is string=>Boolean(n)&&n!==fixture.manager)));
   const previous=managers.map(name=>{
    const xs=chron.filter(m=>m.leeds_manager===name);
    return xs.length>=target?{name,match:xs[target-1]}:null;
   }).filter((x):x is {name:string;match:FixtureResearchMatch}=>Boolean(x)).sort((a,b)=>a.match.match_date.localeCompare(b.match.match_date)||a.match.match_id-b.match.match_id).at(-1);
   if(previous){
    add('Manager · Matches in Charge',`${fixture.manager} is set to become the first manager or head coach to reach ${target} matches in charge of Leeds United across all competitions since ${previous.name} in ${monthYear(previous.match.match_date)}.`,100,`${currentManagerMatches.length} completed matches under ${fixture.manager}; previous managers/head coaches compared across all competitions; ${previous.name}'s ${target}th match was ${previous.match.match_id} on ${previous.match.match_date}`,'manager-matches-milestone');
   }else{
    add('Manager · Matches in Charge',`${fixture.manager} is set to reach ${target} matches in charge of Leeds United across all competitions, with no earlier manager or head coach found at that landmark in the recorded archive.`,100,`${currentManagerMatches.length} completed matches under ${fixture.manager}; all previous managers/head coaches compared across all competitions`,'manager-matches-milestone');
   }
  }
 }

 // Foundational away-ground research. This deliberately uses physical-stadium
 // identity across all competitions, so verified venue renames cannot split the
 // history. The wording adapts: long droughts lead with the last win, while a
 // genuinely positive recent record leads with the successful run.
 if(fixture.venue==='A'&&fixture.stadium){
  const visits=matchesAtPhysicalStadium(chron.filter(m=>m.venue_type==='A'),fixture.stadium);
  if(visits.length>=4){
   const recent=visits.slice(-4),recentRecord=wdl(recent),recentGoals=goals(recent);
   const lastWin=[...visits].reverse().find(won);
   if(recentRecord.w>=2){
    add('Stadium History · Recent Visits',`Leeds United have won ${recentRecord.w} of their last four visits to ${fixture.stadium} across all competitions (W${recentRecord.w} D${recentRecord.d} L${recentRecord.l}), scoring ${recentGoals.gf} goals and conceding ${recentGoals.ga}.`,98,`${visits.length} away matches at the same physical stadium checked across verified venue-name aliases; recent IDs ${recent.map(m=>m.match_id).join(', ')}`,'stadium-away-history');
   }else if(lastWin){
    const since=visits.filter(m=>m.match_date>lastWin.match_date);
    if(since.length>=4&&since.every(m=>!won(m))){
     const r=wdl(since);
     add('Stadium History · Last Win',`Leeds United are winless on their last ${since.length} visits to ${fixture.stadium} across all competitions (D${r.d} L${r.l}), since a ${lastWin.leeds_score}-${lastWin.opponent_score} ${lastWin.competition} victory in ${monthYear(lastWin.match_date)}.`,100,`${visits.length} away matches at the same physical stadium checked across verified venue-name aliases; last win match ${lastWin.match_id}; subsequent visit IDs ${since.map(m=>m.match_id).join(', ')}`,'stadium-away-history');
    }
   }else if(visits.length>=5){
    const r=wdl(visits);
    add('Stadium History · First Win',`Leeds United are yet to win at ${fixture.stadium} across all competitions, with their ${visits.length} recorded visits returning D${r.d} L${r.l}.`,100,`${visits.length} away matches at the same physical stadium checked across verified venue-name aliases; no Leeds win found`,'stadium-away-history');
   }
  }
 }

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
   if(years>=5)add(`Opponent History · Consecutive ${fixture.venue==='H'?'Home':'Away'} League Wins`,`Leeds are looking to record ${target===2?'back-to-back':`${target} consecutive`} ${fixture.venue==='H'?'home':'away'} league wins against ${fixture.opponent} for the first time since ${monthYear(previousCompletion.match_date)}.`,years>=25?100:years>=10?99:97,`${venueLeague.length} ${fixture.venue==='H'?'home':'away'} league meetings checked; previous ${target}-win sequence completed in match ${previousCompletion.match_id}`,'opponent-league-win-run');
  }
 }

 // All-venue winless sequence in the selected competition. This deliberately
 // keeps competition exact while allowing home and away meetings to form one
 // opponent narrative, matching publication language such as "last six meetings".
 let winlessRun=0;
 for(let i=competitionVersus.length-1;i>=0&&!won(competitionVersus[i]);i--)winlessRun++;
 if(winlessRun>=3){
  let run=0,historicalMax=0,lastAtLeast:FixtureResearchMatch|null=null;
  for(const m of competitionVersus.slice(0,-winlessRun)){
   if(!won(m)){run++;historicalMax=Math.max(historicalMax,run);if(run>=winlessRun)lastAtLeast=m}else run=0;
  }
  const current=competitionVersus.slice(-winlessRun),r=wdl(current);
  if(winlessRun>historicalMax){
   add('Opponent History · Winless Run',`Leeds United are winless in their last ${winlessRun} ${fixture.competition} meetings with ${fixture.opponent} (D${r.d} L${r.l}), their longest run without a win against ${fixture.opponent} in the competition's history.`,100,`${competitionVersus.length} ${fixture.competition} meetings checked; current winless run=${winlessRun}; previous maximum=${historicalMax}; current IDs ${current.map(m=>m.match_id).join(', ')}`,'opponent-competition-winless-run');
  }else if(lastAtLeast){
   const years=Math.max(0,seasonYear(fixture.season)-Number(lastAtLeast.match_date.slice(0,4)));
   if(years>=5)add('Opponent History · Winless Run',`Leeds United are winless in their last ${winlessRun} ${fixture.competition} meetings with ${fixture.opponent} (D${r.d} L${r.l}), their longest run without a win against them since ${monthYear(lastAtLeast.match_date)}.`,years>=25?100:years>=10?99:97,`${competitionVersus.length} ${fixture.competition} meetings checked; previous run of at least ${winlessRun} ended in match ${lastAtLeast.match_id}; current IDs ${current.map(m=>m.match_id).join(', ')}`,'opponent-competition-winless-run');
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
