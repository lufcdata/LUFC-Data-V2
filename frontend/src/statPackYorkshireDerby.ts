export const YORKSHIRE_DERBY_OPPONENTS=new Set([
 'Barnsley',
 'Bradford City',
 'Doncaster Rovers',
 'Huddersfield Town',
 'Hull City',
 'Rotherham United',
 'Rotherham County',
 'Sheffield United',
 'Sheffield Wednesday',
]);

type YorkshireDerbyMatch={
 opponent:string;
};

/**
 * Leeds Yorkshire-derby scope used by Stat Pack.
 *
 * This definition is intentionally explicit rather than geographic/fuzzy. Only
 * the clubs signed off for this metric are included, so future club-name or
 * county assumptions cannot silently change the historical population.
 */
export function isYorkshireDerbyOpponent(opponent:string):boolean{
 return YORKSHIRE_DERBY_OPPONENTS.has(opponent);
}

export function yorkshireDerbyMatches<T extends YorkshireDerbyMatch>(matches:readonly T[]):T[]{
 return matches.filter(match=>isYorkshireDerbyOpponent(match.opponent));
}
