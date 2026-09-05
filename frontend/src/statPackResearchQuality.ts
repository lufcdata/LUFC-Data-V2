import type{FixtureResearchFinding}from'./statPackFixtureResearch';

/**
 * Editorial quality gate for fixture-research findings.
 *
 * The research engine owns football semantics and historical comparator logic.
 * This layer must never infer that one valid family makes another redundant just
 * because both are present. It only performs safe presentation-level curation:
 * exact-text deduplication and one strongest item per family.
 */
export function curateFixtureResearch(findings:readonly FixtureResearchFinding[]):FixtureResearchFinding[]{
 const ordered=[...findings].sort((a,b)=>b.priority-a.priority||a.label.localeCompare(b.label));
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
