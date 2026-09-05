import type{FixtureResearchFinding}from'./statPackFixtureResearch';

/**
 * Editorial quality gate for fixture-research findings.
 *
 * The research engine is deliberately generous when discovering historically
 * significant angles. This layer is deliberately strict when deciding which
 * of those angles deserve to survive together in a broadcast-quality pack.
 * It never recalculates football data: it only removes weaker duplicate stories.
 */
export function curateFixtureResearch(findings:readonly FixtureResearchFinding[]):FixtureResearchFinding[]{
 const ordered=[...findings].sort((a,b)=>b.priority-a.priority);
 const families=new Set(ordered.map(f=>f.family));
 return ordered.filter(f=>{
  // A live winning sequence is the stronger version of an identical unbeaten
  // story. The fixture engine already suppresses the exact-run overlap; this
  // protects the final curation layer if another research source adds one later.
  if(f.family==='opponent-venue-unbeaten'&&families.has('opponent-venue-run'))return false;

  // A 3+ victory story is only useful alongside the broader 2+ family when its
  // own historical comparator is genuinely different. The fixture engine owns
  // that comparator test, so no blanket family suppression belongs here.

  return true;
 });
}
