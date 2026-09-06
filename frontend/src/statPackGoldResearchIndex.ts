// Isolated Gold research surface. This deliberately does not alter the signed-off
// production Stat Pack pipeline until each family is verified against LUFC Data.
export{researchHistoricalFixtureContext}from'./statPackHistoricalResearch';
export{researchTeamGeography,researchPlayerGeography}from'./statPackGeographyResearch';
export{clusterResearchStories,selectStoryEvidence}from'./statPackResearchNarrative';
export{significanceScore,rankSignificantFindings,premiumWorthy}from'./statPackResearchSignificance';
export type{GeographicMatch,PlayerGeographicAppearance}from'./statPackGeographyResearch';
export type{ResearchStory}from'./statPackResearchNarrative';
export type{ResearchSignificance,SignificantFinding}from'./statPackResearchSignificance';
