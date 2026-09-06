import type{FixtureResearchFinding}from'./statPackFixtureResearch';

type HistoricalFinding=FixtureResearchFinding&{
 historicalDepthYears?:number;
 historicalSignificance?:'record'|'first'|'rank'|'since'|'context';
};

const historicalBoost=(finding:HistoricalFinding)=>{
 if(finding.grade!=='A')return 0;
 const depth=finding.historicalDepthYears;
 switch(finding.historicalSignificance){
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
 * Historical depth is also a first-class editorial ranking signal when the
 * research engine supplies it. Records, firsts and all-time ranks stay strongest;
 * long-distance "since" comparisons rise above recent ones, while a comparator
 * less than a year old is heavily demoted rather than being treated as Grade A
 * simply because it technically qualifies as a historical first/since story.
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
