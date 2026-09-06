import type{FixtureResearchFinding,FixtureResearchMatch,UpcomingFixtureContext}from'./statPackFixtureResearch';

export const LONDON_OPPONENTS:ReadonlySet<string>=new Set([
 'Arsenal',
 'Barnet',
 'Brentford',
 'Charlton Athletic',
 'Chelsea',
 'Crystal Palace',
 'Fulham',
 'Leyton Orient',
 'Millwall',
 'Queens Park Rangers',
 'Sutton United',
 'Tottenham Hotspur',
 'West Ham United',
 'Wimbledon',
]);

export function isLondonOpponent(opponent:string):boolean{
 return LONDON_OPPONENTS.has(opponent);
}

const won=(m:FixtureResearchMatch)=>m.result==='Won';
const wdl=(xs:readonly FixtureResearchMatch[])=>({w:xs.filter(m=>m.result==='Won').length,d:xs.filter(m=>m.result==='Draw').length,l:xs.filter(m=>m.result==='Lost').length});
const goals=(xs:readonly FixtureResearchMatch[])=>({gf:xs.reduce((n,m)=>n+m.leeds_score,0),ga:xs.reduce((n,m)=>n+m.opponent_score,0)});
const monthYear=(d:string)=>new Date(`${d}T00:00:00`).toLocaleDateString('en-GB',{month:'long',year:'numeric'});

/**
 * Canonical Stat Pack geography family for away matches against London clubs.
 *
 * The opponent taxonomy is explicit rather than inferred from stadium text, so
 * historical venue-name inconsistencies cannot silently change the population.
 * Match results, dates and scores always come from the LUFC database rows passed
 * into this helper. The family only runs for an upcoming away fixture against a
 * London opponent.
 */
export function researchLondonAwayContext(matches:readonly FixtureResearchMatch[],fixture:UpcomingFixtureContext):FixtureResearchFinding[]{
 if(fixture.venue!=='A'||!isLondonOpponent(fixture.opponent))return[];
 const chron=[...matches].sort((a,b)=>a.match_date.localeCompare(b.match_date)||a.match_id-b.match_id);
 const londonAway=chron.filter(m=>m.venue_type==='A'&&isLondonOpponent(m.opponent));
 if(londonAway.length<4)return[];
 const out:FixtureResearchFinding[]=[];
 const add=(label:string,text:string,priority:number,evidence:string,family:string,grade:'A'|'B'='A')=>out.push({label,text,priority,evidence,family,grade});

 // Active London-away winless run. Four matches is the minimum threshold; the
 // archive is then searched for the previous run of at least the same length so
 // the current sequence is published with real historical context.
 let currentWinless=0;
 for(let i=londonAway.length-1;i>=0&&!won(londonAway[i]);i--)currentWinless++;
 if(currentWinless>=4){
  const current=londonAway.slice(-currentWinless),r=wdl(current);
  let run=0,historicalMax=0,lastAtLeast:FixtureResearchMatch|null=null,lastAtLeastLength=0;
  for(const m of londonAway.slice(0,-currentWinless)){
   if(!won(m)){
    run++;
    historicalMax=Math.max(historicalMax,run);
    if(run>=currentWinless){lastAtLeast=m;lastAtLeastLength=run;}
   }else run=0;
  }
  if(currentWinless>historicalMax){
   add('London Away · Winless Run',`Leeds United are winless in their last ${currentWinless} away matches against London clubs across all competitions (D${r.d} L${r.l}), their longest such run in club history.`,100,`${londonAway.length} London away matches checked across all competitions; current IDs ${current.map(m=>m.match_id).join(', ')}; previous maximum=${historicalMax}`,'london-away-winless');
  }else if(lastAtLeast){
   add('London Away · Winless Run',`Leeds United are winless in their last ${currentWinless} away matches against London clubs across all competitions (D${r.d} L${r.l}), their longest such run since ${monthYear(lastAtLeast.match_date)}, when they completed a ${lastAtLeastLength}-match sequence without a win.`,99,`${londonAway.length} London away matches checked across all competitions; current IDs ${current.map(m=>m.match_id).join(', ')}; previous qualifying run completed in match ${lastAtLeast.match_id}`,'london-away-winless');
  }
 }

 // Broader recent London-away context. This is deliberately Grade B unless the
 // active run above earns a historical claim. A 20-match window provides a
 // stable, publication-friendly snapshot without pretending to be a record.
 if(londonAway.length>=20){
  const recent=londonAway.slice(-20),r=wdl(recent),g=goals(recent);
  if(r.w<=4)add('London Away · Recent Record',`Leeds United have won just ${r.w} of their last 20 away matches against London clubs across all competitions (W${r.w} D${r.d} L${r.l}), scoring ${g.gf} goals and conceding ${g.ga}.`,82,`Last 20 London away matches; IDs ${recent.map(m=>m.match_id).join(', ')}`,'london-away-recent','B');
 }

 return out;
}
