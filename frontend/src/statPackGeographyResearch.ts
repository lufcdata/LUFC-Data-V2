import type{FixtureResearchFinding,FixtureResearchMatch}from'./statPackFixtureResearch';

export type GeographicMatch=FixtureResearchMatch&{city?:string|null};
export type PlayerGeographicAppearance={match_id:number;player_id:number;player_name:string;started?:boolean};

/**
 * Geography is intentionally data-driven: callers must supply an authoritative
 * LUFC-database city. No stadium-name guessing, fuzzy geography or web geocoding.
 */
export function researchTeamGeography(matches:GeographicMatch[],city:string):FixtureResearchFinding[]{
 const xs=matches.filter(m=>m.city===city).sort((a,b)=>a.match_date.localeCompare(b.match_date)||a.match_id-b.match_id);
 const out:FixtureResearchFinding[]=[];
 const add=(label:string,text:string,priority:number,evidence:string,family:string)=>out.push({label,text,priority,evidence,family,grade:'A'});
 if(xs.length<10)return out;
 const recent=xs.slice(-41);
 const clean=recent.filter(m=>m.opponent_score===0);
 if(recent.length===41&&clean.length<=2)add('Geography · Clean Sheets',`Leeds have kept just ${clean.length===2?'two':clean.length===1?'one':'no'} clean sheets in their last 41 competitive matches in ${city}.`,99,`Last 41 LUFC database matches with authoritative city=${city}; clean sheets ${clean.length}/41`,'geography-clean-sheets');
 const league=xs.filter(m=>/Premier League|Championship|Division One|Division Two|League One|League Two/i.test(m.competition));
 const last19=league.slice(-19);const wins19=last19.filter(m=>m.result==='Won').length;
 if(last19.length===19&&wins19<=1)add('Geography · League Wins',`Leeds have won just ${wins19===1?'one':'none'} of their last 19 league matches in ${city}.`,100,`Last 19 LUFC database league matches with authoritative city=${city}; wins ${wins19}/19`,'geography-league-form');
 const last38=xs.slice(-38);const losses38=last38.filter(m=>m.result==='Lost').length;
 if(last38.length===38&&losses38>=30)add('Geography · Defeats',`Leeds have lost ${losses38} of their last 38 competitive matches in ${city}.`,100,`Last 38 LUFC database matches with authoritative city=${city}; defeats ${losses38}/38`,'geography-defeats');
 return out;
}

export function researchPlayerGeography(matches:GeographicMatch[],appearances:PlayerGeographicAppearance[],city:string):FixtureResearchFinding[]{
 const ids=new Set(matches.filter(m=>m.city===city).map(m=>m.match_id));
 const byPlayer=new Map<number,{name:string,p:number,w:number,d:number,l:number}>();
 const result=new Map(matches.map(m=>[m.match_id,m.result]));
 for(const a of appearances){if(!ids.has(a.match_id))continue;const x=byPlayer.get(a.player_id)??{name:a.player_name,p:0,w:0,d:0,l:0};x.p++;const r=result.get(a.match_id);if(r==='Won')x.w++;else if(r==='Draw')x.d++;else if(r==='Lost')x.l++;byPlayer.set(a.player_id,x)}
 const winless=[...byPlayer.values()].filter(x=>x.w===0&&x.p>=5).sort((a,b)=>b.p-a.p);
 if(!winless.length)return[];
 const leader=winless[0],second=winless[1];
 if(second&&leader.p===second.p)return[];
 return[{label:'Geography · Player Winless Record',text:`${leader.name} has made more Leeds appearances in ${city} without winning than any other player in the club's recorded history (${leader.p} appearances, ${leader.d} draws and ${leader.l} defeats).`,priority:100,evidence:`All supplied LUFC database player appearances in authoritative city=${city} ranked; ${leader.name}: P${leader.p} W0 D${leader.d} L${leader.l}`,family:'player-geography-winless',grade:'A'}];
}
