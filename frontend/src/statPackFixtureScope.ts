export type FixtureVenue='H'|'A';

export type FixtureScope={
 opponent:string;
 competition:string;
 venue:FixtureVenue;
};

export type ScopedMatch={
 opponent:string;
 competition:string;
 venue_type:string;
};

/**
 * Canonical exact upcoming-fixture scope.
 *
 * Opponent research must never silently widen from the selected competition or
 * H/A condition. This deliberately does not infer "league" equivalence between
 * competitions: Premier League, Championship, Division One, etc. remain
 * separate historical populations unless a caller explicitly asks for a
 * broader league comparison.
 */
export function matchesExactFixtureScope<T extends ScopedMatch>(
 matches:readonly T[],
 fixture:FixtureScope,
):T[]{
 return matches.filter(match=>isExactFixtureScope(match,fixture));
}

export function isExactFixtureScope(
 match:ScopedMatch,
 fixture:FixtureScope,
):boolean{
 return match.opponent===fixture.opponent&&
  match.competition===fixture.competition&&
  match.venue_type===fixture.venue;
}
