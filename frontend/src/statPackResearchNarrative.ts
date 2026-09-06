import type{FixtureResearchFinding}from'./statPackFixtureResearch';

export type ResearchStory={theme:string;findings:FixtureResearchFinding[];score:number};

const themeOf=(f:FixtureResearchFinding)=>{
 if(f.family.startsWith('geography-')||f.family.startsWith('player-geography-'))return'geography';
 if(f.family.startsWith('league-double'))return'league-double';
 if(f.family.startsWith('opponent-'))return'opponent-history';
 return f.family;
};

/**
 * Groups related Gold findings before publication so several cards describing
 * one underlying story can be ranked together instead of flooding the pack.
 * This does not manufacture new facts: prose composition must only use the
 * already-proven findings/evidence supplied here.
 */
export function clusterResearchStories(findings:FixtureResearchFinding[]):ResearchStory[]{
 const groups=new Map<string,FixtureResearchFinding[]>();
 for(const f of findings){const t=themeOf(f);groups.set(t,[...(groups.get(t)??[]),f])}
 return[...groups].map(([theme,x])=>({theme,findings:[...x].sort((a,b)=>b.priority-a.priority),score:Math.max(...x.map(f=>f.priority))+(x.filter(f=>f.grade==='A').length>1?1:0)})).sort((a,b)=>b.score-a.score);
}

/** Keep the strongest evidence from a clustered story while retaining a second
 * genuinely Gold finding when it adds a different dimension to that story.
 */
export function selectStoryEvidence(story:ResearchStory,max=2):FixtureResearchFinding[]{
 const seen=new Set<string>();const out:FixtureResearchFinding[]=[];
 for(const f of story.findings){if(seen.has(f.family))continue;seen.add(f.family);out.push(f);if(out.length>=max)break}
 return out;
}
