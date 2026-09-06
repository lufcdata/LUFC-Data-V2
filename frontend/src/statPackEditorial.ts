import type{FixtureResearchFinding,FixtureResearchMatch,UpcomingFixtureContext}from'./statPackFixtureResearch';
import{researchCompetitionFirstWin}from'./statPackCompetitionFirstWinResearch';

const words=(n:number)=>['zero','one','two','three','four','five','six','seven','eight','nine','ten'][n]??String(n);
const ordinalWords=(n:number)=>['zeroth','first','second','third','fourth','fifth','sixth','seventh','eighth','ninth','tenth'][n]??`${n}th`;
const monthYear=(d:string)=>new Date(`${d}T00:00:00`).toLocaleDateString('en-GB',{month:'long',year:'numeric'});
const wdl=(xs:readonly FixtureResearchMatch[])=>({w:xs.filter(m=>m.result==='Won').length,d:xs.filter(m=>m.result==='Draw').length,l:xs.filter(m=>m.result==='Lost').length});

export type StatPackEditorialContext={
 matches:readonly FixtureResearchMatch[];
 opponent:string;
 fixture:UpcomingFixtureContext|null;
};

const managerVenueCopy=(finding:FixtureResearchFinding,ctx:StatPackEditorialContext)=>{
 const fixture=ctx.fixture;
 const manager=fixture?.manager;
 if(!fixture||!manager||finding.family!=='manager-venue-run')return finding;
 const chron=[...ctx.matches].sort((a,b)=>a.match_date.localeCompare(b.match_date)||a.match_id-b.match_id);
 const scoped=(m:FixtureResearchMatch)=>m.competition===fixture.competition&&m.venue_type===fixture.venue;
 const own=chron.filter(m=>m.leeds_manager===manager&&scoped(m));
 let currentRun=0;
 for(let i=own.length-1;i>=0&&own[i].result==='Won';i--)currentRun++;
 if(currentRun<1)return finding;
 const target=currentRun+1;
 const previousManagers=Array.from(new Set(chron.map(m=>m.leeds_manager).filter((x):x is string=>Boolean(x)&&x!==manager)));
 let latest:{name:string;date:string}|null=null;
 for(const name of previousManagers){
  let run=0;
  for(const m of chron.filter(x=>x.leeds_manager===name&&scoped(x))){
   if(m.result==='Won'){
    run++;
    if(run>=target&&(!latest||m.match_date>latest.date))latest={name,date:m.match_date};
   }else run=0;
  }
 }
 if(!latest)return finding;
 const where=fixture.venue==='H'?'home':'away';
 const action=target===2?`win back-to-back ${fixture.competition} ${where} matches`:`win ${target} consecutive ${fixture.competition} ${where} matches`;
 return{...finding,text:`${manager} could become the first Leeds manager to ${action} since ${latest.name} in ${monthYear(latest.date)}.`};
};

const careerMilestoneCopy=(finding:FixtureResearchFinding)=>{
 if(finding.family!=='career-milestone')return finding;
 const goal=finding.text.match(/^(.+?) is one goal away from (\d+) Leeds goals\. Reaching it would make him the (\d+(?:st|nd|rd|th)) player in the recorded archive to reach that landmark\.$/);
 if(goal)return{...finding,text:`${goal[1]} is one goal away from becoming the ${goal[3]} different player to score ${goal[2]} goals across all competitions for Leeds United.`};
 const appearance=finding.text.match(/^(.+?) is one appearance away from (\d+) Leeds appearances\. Reaching it would make him the (\d+(?:st|nd|rd|th)) player in the recorded archive to reach that landmark\.$/);
 if(appearance)return{...finding,text:`${appearance[1]} is one appearance away from becoming the ${appearance[3]} different player to make ${appearance[2]} appearances across all competitions for Leeds United.`};
 return finding;
};

const h2hCopy=(finding:FixtureResearchFinding,ctx:StatPackEditorialContext)=>{
 if(finding.family!=='context-h2h')return finding;
 const xs=[...ctx.matches].filter(m=>m.opponent===ctx.opponent).sort((a,b)=>a.match_date.localeCompare(b.match_date)||a.match_id-b.match_id).slice(-6);
 if(!xs.length)return finding;
 const r=wdl(xs),gf=xs.reduce((n,m)=>n+m.leeds_score,0),ga=xs.reduce((n,m)=>n+m.opponent_score,0),total=gf+ga;
 return{...finding,text:`Across their last ${words(xs.length)} meetings with ${ctx.opponent} in all competitions, Leeds United have won ${words(r.w)}, drawn ${words(r.d)} and lost ${words(r.l)} (GF${gf}, GA${ga}), with those matches producing ${total} goals.`};
};

const compactWdl=(finding:FixtureResearchFinding)=>{
 if(finding.family!=='first-goal-recent')return finding;
 return{...finding,text:finding.text.replace(/\((\d+)W (\d+)D (\d+)L\)/,(_m,w,d,l)=>`(W${w} D${d} L${l})`)};
};

const seasonOpeningCopy=(finding:FixtureResearchFinding)=>{
 if(finding.family!=='season-opening-venue')return finding;
 return{...finding,text:finding.text.replace(/opening (\d+) (home|away) matches/g,(_m,n,where)=>`opening ${words(Number(n))} ${where} matches`)};
};

const proseNumbers=(finding:FixtureResearchFinding)=>{
 if(finding.family==='opponent-competition-winless-run'||finding.family==='stadium-away-history'||finding.family.startsWith('current-unbeaten-')){
  return{...finding,text:finding.text.replace(/\blast (\d+)\b/g,(_m,n)=>`last ${words(Number(n))}`)};
 }
 return finding;
};

const cleanSheetCopy=(finding:FixtureResearchFinding)=>{
 if(finding.family!=='opponent-venue-clean-sheet'&&finding.family!=='clean-sheet-opponent-history')return finding;
 let text=finding.text.replace(/\bshutout(s)?\b/gi,(_m,plural)=>plural?'clean sheets':'clean sheet');
 text=text.replace(/\b(\d+)(?:st|nd|rd|th) consecutive\b/g,(_m,n)=>`${ordinalWords(Number(n))} consecutive`);
 return{...finding,text};
};

/**
 * Publication editorial pass plus dedicated late-stage research families that
 * need the fully resolved upcoming fixture context. Every added fact is still
 * derived only from the LUFC database rows supplied by the Stat Pack.
 */
export function editorializeStatPackFindings<T extends FixtureResearchFinding>(findings:readonly T[],ctx:StatPackEditorialContext):T[]{
 const researched:FixtureResearchFinding[]=[...findings,...researchCompetitionFirstWin(ctx.matches,ctx.fixture)];
 return researched.map(original=>{
  let f:FixtureResearchFinding=original;
  f=managerVenueCopy(f,ctx);
  f=careerMilestoneCopy(f);
  f=h2hCopy(f,ctx);
  f=compactWdl(f);
  f=seasonOpeningCopy(f);
  f=proseNumbers(f);
  f=cleanSheetCopy(f);
  return f as T;
 });
}
