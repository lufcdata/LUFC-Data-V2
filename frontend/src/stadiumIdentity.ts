// Physical-venue identity for Stat Pack research.
// Historical match rows keep their period-correct stadium labels; analytics use
// canonicalStadiumKey so sponsorship/name changes do not split one venue's history.
// Only verified same-site aliases belong here. Replacement grounds must stay separate.

const STADIUM_ALIASES:Record<string,string>={
 'City of Manchester Stadium, Manchester':'Etihad Stadium, Manchester',
 'Britannia Stadium, Stoke':'Bet365 Stadium, Stoke',
 'JJB Stadium, Wigan':'DW Stadium, Wigan',
 'Reebok Stadium, Bolton':'University of Bolton Stadium, Bolton',
 'Macron Stadium, Bolton':'University of Bolton Stadium, Bolton',
 'Ricoh Arena, Coventry':'Coventry Building Society Arena, Coventry',
 'KC Stadium, Hull':'MKM Stadium, Hull',
 'KCOM Stadium, Hull':'MKM Stadium, Hull',
 'Liberty Stadium, Swansea':'Swansea.com Stadium, Swansea',
 'McAlpine Stadium, Huddersfield':"John Smith's Stadium, Huddersfield",
 'Brentford Community Stadium, London':'Gtech Community Stadium, London',
 'Walkers Stadium, Leicester':'King Power Stadium, Leicester',
};

export function canonicalStadiumKey(stadium:string|null|undefined):string|null{
 if(!stadium)return null;
 return STADIUM_ALIASES[stadium]??stadium;
}

export function samePhysicalStadium(a:string|null|undefined,b:string|null|undefined):boolean{
 const ak=canonicalStadiumKey(a),bk=canonicalStadiumKey(b);
 return Boolean(ak&&bk&&ak===bk);
}

export function stadiumAliases():Readonly<Record<string,string>>{
 return STADIUM_ALIASES;
}
