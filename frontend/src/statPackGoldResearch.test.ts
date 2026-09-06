// GOLD STAT PACK RESEARCH CONTRACT
//
// These invariants document the editorial/data contract for the research layer.
// They deliberately contain no fixture-specific corrections or target numbers.
//
// 1. LUFC database rows are the only source of published Stat Pack facts.
// 2. Geography requires an authoritative database city; never infer it from a
//    stadium string, opponent name, web lookup or fuzzy alias.
// 3. League doubles require the same opponent and season, league fixtures, and
//    wins at both H and A. The inverse definition applies to doubles suffered.
// 4. Winning-margin context compares numeric goal margin, not scoreline text.
// 5. Home/away opponent sequences remain separate populations.
// 6. Historical context is preferred to an isolated current count; shallow
//    ordinary 'since' stories should not displace records or long-history facts.
// 7. Positive and negative research families must remain symmetric.
// 8. A research seed is not automatically publication-worthy: curation decides
//    whether the historical implication is significant enough to surface.
// 9. Generated copy is third-person Leeds language: Leeds/their, never we/our.
// 10. No arbitrary filter stacking is permitted to manufacture uniqueness.
export{};
