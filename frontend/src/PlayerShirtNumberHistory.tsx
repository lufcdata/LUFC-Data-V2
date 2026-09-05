import React,{useEffect,useMemo,useState}from'react';
import{supabase,supabaseConfigError}from'./supabase';
import'./PlayerShirtNumberHistory.css';

type ShirtHistoryRow={fact_type:'match_worn'|'official_squad';season_id:number;season:string;match_id:number|null;match_date:string|null;shirt_number:number|null;assignment_status:string|null;notes:string|null};
type PlayerMatchRow={match_id:number};
type MatchRow={match_id:number;season_id:number|null};
type NumberTotal={shirtNumber:number|null;appearances:number};

export default function PlayerShirtNumberHistory({playerId}:{playerId:number}){
 const[rows,setRows]=useState<ShirtHistoryRow[]>([]),[playerMatchIds,setPlayerMatchIds]=useState<Set<number>>(new Set()),[seasonAppearanceCounts,setSeasonAppearanceCounts]=useState<Map<number,number>>(new Map()),[loading,setLoading]=useState(true),[error,setError]=useState<string|null>(supabaseConfigError);
 useEffect(()=>{let cancelled=false;(async()=>{if(!supabase){setLoading(false);return}setLoading(true);setError(null);
  const[{data:history,error:historyError},{data:pm,error:pmError}]=await Promise.all([
   supabase.rpc('get_player_shirt_number_history',{p_player_id:playerId}),
   supabase.from('player_matches').select('match_id').eq('player_id',playerId)
  ]);if(cancelled)return;const firstError=historyError??pmError;if(firstError){setError(firstError.message);setLoading(false);return}
  const matchIds=((pm??[])as PlayerMatchRow[]).map(r=>r.match_id),matchIdSet=new Set(matchIds);let matches:MatchRow[]=[];
  if(matchIds.length){const{data:matchData,error:matchError}=await supabase.from('matches').select('match_id,season_id').in('match_id',matchIds);if(cancelled)return;if(matchError){setError(matchError.message);setLoading(false);return}matches=(matchData??[])as MatchRow[]}
  const counts=new Map<number,number>();for(const match of matches){if(match.season_id==null)continue;counts.set(match.season_id,(counts.get(match.season_id)??0)+1)}
  setRows((history??[])as ShirtHistoryRow[]);setPlayerMatchIds(matchIdSet);setSeasonAppearanceCounts(counts);setLoading(false)})();return()=>{cancelled=true}},[playerId]);
 const numberTotals=useMemo(()=>{const totals=new Map<string,NumberTotal>();
  for(const row of rows){const key=row.shirt_number==null?'tbc':String(row.shirt_number),current=totals.get(key)??{shirtNumber:row.shirt_number,appearances:0};
   if(row.fact_type==='match_worn'){if(row.match_id!=null&&playerMatchIds.has(row.match_id))current.appearances+=1}
   else{current.appearances+=seasonAppearanceCounts.get(row.season_id)??0}
   totals.set(key,current)
  }
  return Array.from(totals.values()).sort((a,b)=>a.shirtNumber==null?1:b.shirtNumber==null?-1:a.shirtNumber-b.shirtNumber)
 },[rows,playerMatchIds,seasonAppearanceCounts]);
 if(loading)return <section className="card player-profile-panel player-shirt-history"><div className="player-profile-panelhead"><div><span className="section-kicker">Leeds United Shirt Numbers</span><h2>Shirt Numbers</h2></div></div><div className="lb-loading">Loading shirt numbers…</div></section>;
 if(error)return <section className="card player-profile-panel player-shirt-history"><div className="player-profile-panelhead"><div><span className="section-kicker">Leeds United Shirt Numbers</span><h2>Shirt Numbers</h2></div></div><div className="lb-loading"><strong>Data connection error:</strong> {error}</div></section>;
 if(!numberTotals.length)return null;
 return <section className="card player-profile-panel player-shirt-history"><div className="player-profile-panelhead"><div><span className="section-kicker">Leeds United Shirt Numbers</span><h2>Shirt Numbers</h2><p className="player-shirt-history-note">Total Leeds appearances made with each recorded shirt number.</p></div></div><div className="lb-table-wrap"><table className="lb-table player-shirt-history-table"><thead><tr><th>Shirt Number</th><th className="col-stat">Appearances</th></tr></thead><tbody>{numberTotals.map(row=><tr key={row.shirtNumber??'tbc'}><td><div className="player-shirt-number-list">{row.shirtNumber!=null?<span className="player-shirt-number">#{row.shirtNumber}</span>:<span className="player-shirt-number unknown">TBC</span>}</div></td><td className="col-stat player-stat-value">{row.appearances}</td></tr>)}</tbody></table></div></section>
}
