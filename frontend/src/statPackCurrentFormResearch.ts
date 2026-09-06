import type{FixtureResearchFinding,FixtureResearchMatch}from'./statPackFixtureResearch';
import{matchesAtPhysicalStadium}from'./stadiumIdentity';

const FORM_WINDOW=12;
const UNBEATEN_MIN=4;
const SUPPORTED=new Set(['Premier League','Championship','Division One','Division Two','League One']);
const monthYear=(d:string)=>new Date(`${d}T00:00:00`).toLocaleDateString('en-GB',{month:'long',year:'numeric'});
const wdl=(xs:readonly FixtureResearchMatch[])=>({w:xs.filter(m=>m.result==='Won').length,d:xs.filter(m=>m.result==='Draw').length,l:xs.filter(m=>m.result==='Lost').length});
const stadiumName=(s:string)=>s.split(',')[0].trim();

const activeUnbeatenRun=(xs:readonly FixtureResearchMatch[])=>{
 let start=xs.length;
 while(start>0&&xs[start-1].result!=='Lost')start--;
 return xs.slice(start);
};

const previousUnbeatenRunAtLeast=(xs:readonly FixtureResearchMatch[],target:number,currentRun:number)=>{
 let run=0,last:FixtureResearchMatch|null=null;
 const historical=currentRun?xs.slice(0,-currentRun):xs;
 for(const m of historical){
  if(m.result!=='Lost'){run++;if(run>=target)last=m}else run=0;
 }
 return last;
};

type UnbeatenScope={label:string;population:FixtureResearchMatch[];historyLabel:string};

/**
 * Active unbeaten-run research across natural, authoritative populations.
 *
 * Any live unbeaten run of four or more matches deserves consideration. The
 * machine checks all competitions, the selected exact competition, Leeds'
 * current physical home ground, away matches, and competition-specific home/
 * away variants. Identical underlying runs are deduplicated by match IDs so a
 * four-game start to a season cannot be printed several times under different
 * labels merely because the populations happen to coincide.
 */
export function researchActiveUnbeatenRuns(
 matches:readonly FixtureResearchMatch[],
 competition:string,
):FixtureResearchFinding[]{
 const chron=[...matches].sort((a,b)=>a.match_date.localeCompare(b.match_date)||a.match_id-b.match_id);
 if(!chron.length)return[];
 const latestHome=[...chron].reverse().find(m=>m.venue_type==='H'&&Boolean(m.stadium));
 const homeGround=latestHome?.stadium??null;
 const exactCompetition=chron.filter(m=>m.competition===competition);
 const away=chron.filter(m=>m.venue_type==='A');
 const competitionAway=exactCompetition.filter(m=>m.venue_type==='A');
 const atHomeGround=homeGround?matchesAtPhysicalStadium(chron.filter(m=>m.venue_type==='H'),homeGround):[];
 const competitionAtHomeGround=homeGround?matchesAtPhysicalStadium(exactCompetition.filter(m=>m.venue_type==='H'),homeGround):[];
 const homeName=homeGround?stadiumName(homeGround):null;
 const scopes:UnbeatenScope[]=[
  {label:'matches across all competitions',population:chron,historyLabel:'across all competitions'},
  {label:`${competition} matches`,population:exactCompetition,historyLabel:`in the ${competition}`},
  ...(homeGround&&homeName?[{label:`matches at ${homeName}`,population:atHomeGround,historyLabel:`at ${homeName}`}]:[]),
  {label:'away matches across all competitions',population:away,historyLabel:'away from home across all competitions'},
  ...(homeGround&&homeName?[{label:`${competition} matches at ${homeName}`,population:competitionAtHomeGround,historyLabel:`at ${homeName} in the ${competition}`}]:[]),
  {label:`${competition} away matches`,population:competitionAway,historyLabel:`away from home in the ${competition}`},
 ];
 const findings:FixtureResearchFinding[]=[];
 const seenRuns=new Set<string>();
 for(const scope of scopes){
  if(scope.population.length<UNBEATEN_MIN)continue;
  const run=activeUnbeatenRun(scope.population);
  if(run.length<UNBEATEN_MIN)continue;
  const runKey=run.map(m=>m.match_id).join(',');
  if(seenRuns.has(runKey))continue;
  seenRuns.add(runKey);
  const record=wdl(run);
  const previous=previousUnbeatenRunAtLeast(scope.population,run.length,run.length);
  const years=previous?Math.max(0,Number(run.at(-1)!.match_date.slice(0,4))-Number(previous.match_date.slice(0,4))):null;
  const historical=previous
   ?`, their longest unbeaten run ${scope.historyLabel} since ${monthYear(previous.match_date)}`
   :`, their longest recorded unbeaten run ${scope.historyLabel}`;
  findings.push({
   label:`Current Form · ${scope.label}`,
   text:`Leeds United are unbeaten in their last ${run.length} ${scope.label} (W${record.w} D${record.d})${historical}.`,
   priority:years==null?100:years>=25?100:years>=10?99:years>=5?97:94,
   evidence:`Active unbeaten run: ${run.length} ${scope.label}, ${run[0].match_date}–${run.at(-1)!.match_date}, IDs ${runKey}; ${previous?`previous run of at least ${run.length} ended ${previous.match_date} at match ${previous.match_id}`:`no previous run of at least ${run.length} found`} `,
   family:`current-unbeaten-${scope.label.toLowerCase().replace(/[^a-z0-9]+/g,'-')}`,
   grade:'A',
  });
 }
 return findings;
}

/** Return the longest contiguous spell containing a qualifying historical window
 * while preserving its low-defeat ceiling. This turns a 12-game comparator into
 * the larger historical story it belonged to (for example, one defeat in 27).
 */
const expandLowDefeatSpell=(scoped:readonly FixtureResearchMatch[],windowEnd:number,maxLosses:number)=>{
 let start=windowEnd-FORM_WINDOW+1,end=windowEnd,losses=wdl(scoped.slice(start,end+1)).l;
 while(start>0){const extra=scoped[start-1].result==='Lost'?1:0;if(losses+extra>maxLosses)break;start--;losses+=extra}
 while(end<scoped.length-1){const extra=scoped[end+1].result==='Lost'?1:0;if(losses+extra>maxLosses)break;end++;losses+=extra}
 const matches=scoped.slice(start,end+1);
 return{start,end,matches,record:wdl(matches)};
};

/**
 * Opponent-independent current-form research.
 *
 * The population is always one exact competition. Historical context compares
 * like-for-like rolling windows from the same competition only, so Premier
 * League form can never absorb Championship or Division One matches.
 *
 * Consecutive overlapping windows that all meet the current low-defeat standard
 * are treated as one form regime. The historical comparator is the previous
 * qualifying regime, not merely the immediately preceding overlapping window.
 * Once found, that comparator is expanded to the full contiguous low-defeat
 * spell so the machine keeps digging for the stronger historical story.
 */
export function researchCurrentCompetitionForm(
 matches:readonly FixtureResearchMatch[],
 competition:string,
):FixtureResearchFinding[]{
 if(!SUPPORTED.has(competition))return[];
 const scoped=[...matches]
  .filter(m=>m.competition===competition)
  .sort((a,b)=>a.match_date.localeCompare(b.match_date)||a.match_id-b.match_id);
 if(scoped.length<FORM_WINDOW*2)return[];

 const recent=scoped.slice(-FORM_WINDOW);
 const now=wdl(recent);
 if(now.l>1)return[];

 const qualifies=(end:number)=>wdl(scoped.slice(end-FORM_WINDOW+1,end+1)).l<=now.l;
 let regimeStartEnd=scoped.length-1;
 while(regimeStartEnd>FORM_WINDOW-1&&qualifies(regimeStartEnd-1))regimeStartEnd--;

 let previous:{endIndex:number;end:FixtureResearchMatch;record:ReturnType<typeof wdl>}|null=null;
 for(let end=regimeStartEnd-1;end>=FORM_WINDOW-1;end--){
  const window=scoped.slice(end-FORM_WINDOW+1,end+1);
  const record=wdl(window);
  if(record.l<=now.l){previous={endIndex:end,end:scoped[end],record};break;}
 }

 const evidence=`Last ${FORM_WINDOW} ${competition} matches: ${recent.map(m=>m.match_id).join(', ')}; current qualifying rolling-window regime begins with window ending ${scoped[regimeStartEnd].match_date}; earlier rolling ${FORM_WINDOW}-match ${competition} windows checked`;
 if(!previous){
  return[{
   label:'Current Form · Historic Low Defeats',
   text:now.l===0
    ?`Leeds are unbeaten in their last ${FORM_WINDOW} ${competition} games (W${now.w}, D${now.d}), their first such ${FORM_WINDOW}-game run in the recorded history of the competition.`
    :`Leeds have lost just one of their last ${FORM_WINDOW} ${competition} games (W${now.w}, D${now.d}, L${now.l}), with no earlier ${FORM_WINDOW}-game spell in the recorded history of the competition containing so few defeats.`,
   priority:100,
   evidence,
   family:'current-form-low-defeats',
   grade:'A',
  }];
 }

 const currentYear=Number(recent.at(-1)!.match_date.slice(0,4));
 const previousYear=Number(previous.end.match_date.slice(0,4));
 const years=Math.max(0,currentYear-previousYear);
 if(years<5)return[];

 const historicalSpell=expandLowDefeatSpell(scoped,previous.endIndex,now.l);
 const spellRecord=historicalSpell.record;
 const expanded=historicalSpell.matches.length>FORM_WINDOW;
 const historicalContext=expanded
  ?now.l===0
   ?` That previous spell ultimately stretched to ${historicalSpell.matches.length} unbeaten ${competition} games (W${spellRecord.w}, D${spellRecord.d}).`
   :` That previous spell formed part of a ${historicalSpell.matches.length}-game ${competition} run in which Leeds lost just ${spellRecord.l===1?'once':spellRecord.l+' times'} (W${spellRecord.w}, D${spellRecord.d}, L${spellRecord.l}).`
  :'';
 const spellEvidence=expanded
  ?`; expanded historical low-defeat spell ${scoped[historicalSpell.start].match_date}–${scoped[historicalSpell.end].match_date}: ${historicalSpell.matches.length} matches (W${spellRecord.w} D${spellRecord.d} L${spellRecord.l}), IDs ${historicalSpell.matches.map(m=>m.match_id).join(', ')}`
  :'';

 return[{
  label:'Current Form · Low Defeats',
  text:(now.l===0
   ?`Leeds are unbeaten in their last ${FORM_WINDOW} ${competition} games (W${now.w}, D${now.d}), their first ${FORM_WINDOW}-game unbeaten spell in the competition since ${monthYear(previous.end.match_date)}.`
   :`Leeds have lost just one of their last ${FORM_WINDOW} ${competition} games (W${now.w}, D${now.d}, L${now.l}), their fewest defeats across a ${FORM_WINDOW}-game spell in the competition since ${monthYear(previous.end.match_date)}.`)+historicalContext,
  priority:years>=25?100:years>=10?99:97,
  evidence:`${evidence}; previous qualifying regime last contained a window ending ${previous.end.match_date} at match ${previous.end.match_id} (W${previous.record.w} D${previous.record.d} L${previous.record.l})${spellEvidence}`,
  family:'current-form-low-defeats',
  grade:'A',
 }];
}
