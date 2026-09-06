import type{FixtureResearchFinding,FixtureResearchMatch}from'./statPackFixtureResearch';

const FORM_WINDOW=12;
const SUPPORTED=new Set(['Premier League','Championship','Division One','Division Two','League One']);
const monthYear=(d:string)=>new Date(`${d}T00:00:00`).toLocaleDateString('en-GB',{month:'long',year:'numeric'});
const wdl=(xs:readonly FixtureResearchMatch[])=>({w:xs.filter(m=>m.result==='Won').length,d:xs.filter(m=>m.result==='Draw').length,l:xs.filter(m=>m.result==='Lost').length});

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

 let previous:{end:FixtureResearchMatch;record:ReturnType<typeof wdl>}|null=null;
 for(let end=regimeStartEnd-1;end>=FORM_WINDOW-1;end--){
  const window=scoped.slice(end-FORM_WINDOW+1,end+1);
  const record=wdl(window);
  if(record.l<=now.l){previous={end:scoped[end],record};break;}
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

 return[{
  label:'Current Form · Low Defeats',
  text:now.l===0
   ?`Leeds are unbeaten in their last ${FORM_WINDOW} ${competition} games (W${now.w}, D${now.d}), their first ${FORM_WINDOW}-game unbeaten spell in the competition since ${monthYear(previous.end.match_date)}.`
   :`Leeds have lost just one of their last ${FORM_WINDOW} ${competition} games (W${now.w}, D${now.d}, L${now.l}), their fewest defeats across a ${FORM_WINDOW}-game spell in the competition since ${monthYear(previous.end.match_date)}.`,
  priority:years>=25?100:years>=10?99:97,
  evidence:`${evidence}; previous qualifying regime last contained a window ending ${previous.end.match_date} at match ${previous.end.match_id} (W${previous.record.w} D${previous.record.d} L${previous.record.l})`,
  family:'current-form-low-defeats',
  grade:'A',
 }];
}
