import type{FixtureResearchFinding}from'./statPackFixtureResearch';

type HistoricalFinding=FixtureResearchFinding&{
 historicalDepthYears?:number;
 historicalSignificance?:'record'|'first'|'rank'|'since'|'context';
};

const inferredDepth=(finding:HistoricalFinding)=>{
 if(finding.historicalDepthYears!=null)return finding.historicalDepthYears;
 if(!/\b(since|last reached|last achieved|last managed|last did)\b/i.test(finding.text))return undefined;
 const years=Array.from(finding.text.matchAll(/\b(?:19|20)\d{2}\b/g),m=>Number(m[0]));
 if(!years.length)return undefined;
 const currentYear=new Date().getFullYear();
 const comparatorYear=Math.max(...years.filter(y=>y<=currentYear));
 return Number.isFinite(comparatorYear)?Math.max(0,currentYear-comparatorYear):undefined;
};

const inferredSignificance=(finding:HistoricalFinding)=>{
 if(finding.historicalSignificance)return finding.historicalSignificance;
 if(/\bsince\b/i.test(finding.text))return'since' as const;
 if(/\b(first (?:recorded|ever)|first time|no previous|not found in the recorded archive)\b/i.test(finding.text))return'first' as const;
 if(/\b(longest|record|joint-most|joint-highest|highest|lowest|most|fewest)\b/i.test(finding.text))return'record' as const;
 return undefined;
};

const historicalBoost=(finding:HistoricalFinding)=>{
 if(finding.grade!=='A')return 0;
 const significance=inferredSignificance(finding),depth=inferredDepth(finding);
 switch(significance){
  case'record':return 8;
  case'first':return 7;
  case'rank':return 6;
 }
 if(depth==null)return 0;
 if(depth>=50)return 7;
 if(depth>=25)return 6;
 if(depth>=10)return 5;
 if(depth>=5)return 3;
 if(depth>=2)return 1;
 if(depth<1)return-8;
 return 0;
};

/**
 * Editorial quality gate for fixture-research findings.
 *
 * The research engine owns football semantics and historical comparator logic.
 * This layer must never infer that one valid family makes another redundant just
 * because both are present. It only performs safe presentation-level curation:
 * exact-text deduplication and one strongest item per family.
 *
 * Historical depth is also a first-class editorial ranking signal. Explicit
 * research metadata wins when supplied; otherwise the gate safely infers depth
 * from database-derived comparator years already present in the finding text.
 * Records, firsts and all-time ranks stay strongest; long-distance "since"
 * comparisons rise above recent ones, while a comparator less than a year old is
 * heavily demoted rather than being treated as Grade A merely because it is a
 * technically valid first/since story.
 */
export function curateFixtureResearch(findings:readonly FixtureResearchFinding[]):FixtureResearchFinding[]{
 const weighted=(findings as readonly HistoricalFinding[]).map(f=>({...f,priority:f.priority+historicalBoost(f)}));
 const ordered=weighted.sort((a,b)=>b.priority-a.priority||a.label.localeCompare(b.label));
 const exact=new Set<string>();
 const families=new Set<string>();
 const curated:FixtureResearchFinding[]=[];

 for(const f of ordered){
  const textKey=f.text.toLowerCase().replace(/\s+/g,' ').trim();
  if(exact.has(textKey))continue;
  exact.add(textKey);

  // Grade A research is capped at one strongest item per authoritative family.
  // Grade B context can coexist because it is descriptive rather than claiming
  // a record/first/since achievement.
  if(f.grade==='A'){
   if(families.has(f.family))continue;
   families.add(f.family);
  }

  curated.push(f);
 }

 return curated;
}
