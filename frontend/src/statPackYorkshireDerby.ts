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

type YorkshireDerbyResultMatch=YorkshireDerbyMatch&{
 result:string;
 leeds_score:number;
 opponent_score:number;
};

export type YorkshireDerbyRecord={
 matches:number;
 wins:number;
 draws:number;
 defeats:number;
 goalsFor:number;
 goalsAgainst:number;
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

/**
 * Canonical Yorkshire-derby record calculation.
 *
 * All Stat Pack surfaces should consume this function rather than independently
 * counting W/D/L or goals from the derby population.
 */
export function yorkshireDerbyRecord<T extends YorkshireDerbyResultMatch>(matches:readonly T[]):YorkshireDerbyRecord{
 const derbies=yorkshireDerbyMatches(matches);
 return derbies.reduce<YorkshireDerbyRecord>((record,match)=>{
  record.matches++;
  if(match.result==='Won')record.wins++;
  else if(match.result==='Draw')record.draws++;
  else if(match.result==='Lost')record.defeats++;
  record.goalsFor+=match.leeds_score;
  record.goalsAgainst+=match.opponent_score;
  return record;
 },{matches:0,wins:0,draws:0,defeats:0,goalsFor:0,goalsAgainst:0});
}
