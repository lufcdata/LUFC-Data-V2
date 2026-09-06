export const GOLD_HISTORY={
 suppressOrdinarySinceUnderYears:1,
 contextualSinceYears:2,
 strongSinceYears:5,
 veryStrongSinceYears:10,
 exceptionalSinceYears:25,
 extraordinarySinceYears:50,
}as const;

export function historicalDepthBand(years:number){
 if(years>=GOLD_HISTORY.extraordinarySinceYears)return'extraordinary';
 if(years>=GOLD_HISTORY.exceptionalSinceYears)return'exceptional';
 if(years>=GOLD_HISTORY.veryStrongSinceYears)return'very-strong';
 if(years>=GOLD_HISTORY.strongSinceYears)return'strong';
 if(years>=GOLD_HISTORY.contextualSinceYears)return'useful';
 if(years>=GOLD_HISTORY.suppressOrdinarySinceUnderYears)return'contextual';
 return'suppress';
}
