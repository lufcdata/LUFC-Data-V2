import type{FixtureResearchFinding}from'./statPackFixtureResearch';

export type ResearchSignificance='record'|'first'|'historical-rank'|'rare'|'long-since'|'since'|'trend';
export type SignificantFinding=FixtureResearchFinding&{significance:ResearchSignificance;historicalYears?:number};

const base:Record<ResearchSignificance,number>={record:50,first:48,'historical-rank':46,rare:44,'long-since':40,since:30,trend:20};

/** Explicit editorial scoring for new structured research families. Historical
 * age is supplied by database-derived comparison dates/seasons, never scraped
 * from prose. Existing legacy findings can continue through the old curator.
 */
export function significanceScore(f:SignificantFinding){
 const y=f.historicalYears??0;
 const depth=y>=50?12:y>=25?10:y>=10?7:y>=5?4:y>=2?1:y<1&&f.significance==='since'?-8:0;
 return base[f.significance]+depth+f.priority/100;
}

export function rankSignificantFindings(xs:SignificantFinding[]){return[...xs].sort((a,b)=>significanceScore(b)-significanceScore(a)||b.priority-a.priority)}

export function premiumWorthy(f:SignificantFinding){
 if(['record','first','historical-rank','rare'].includes(f.significance))return true;
 if(f.significance==='long-since')return(f.historicalYears??0)>=5;
 if(f.significance==='since')return(f.historicalYears??0)>=2;
 return false;
}
