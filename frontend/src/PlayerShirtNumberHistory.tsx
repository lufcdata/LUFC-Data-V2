import React,{useEffect,useMemo,useState}from'react';
import{supabase,supabaseConfigError}from'./supabase';
import'./PlayerShirtNumberHistory.css';

type ShirtHistoryRow={fact_type:'match_worn'|'official_squad';season_id:number;season:string;match_id:number|null;match_date:string|null;shirt_number:number|null;assignment_status:string|null;notes:string|null};
type PlayerMatchRow={match_id:number};
type MatchRow={match_id:number;season_id:number|null};
type SeasonHistory={seasonId:number;season:string;factType:'match_worn'|'official_squad';numbers:number[];records:number;appearances:number;notes:string[]};

export default function PlayerShirtNumberHistory({playerId}:{playerId:number}){
 const[rows,setRows]=useState<ShirtHistoryRow[]>([]),[appearanceCounts,setAppearanceCounts]=useState<Map<number,number>>(new Map()),[loading,setLoading]=useState(true),[error,setError]=useState<string|null>(supabaseConfigError);
 useEffect(()=>{let cancelled=false;(async()=>{if(!supabase){setLoading(false);return}setLoading(true);setError(null);
  const[{data:history,error:historyError},{data:pm,error:pmError}]=await Promise.all([
   supabase.rpc('get_player_shirt_number_history',{p_player_id:playerId}),
   supabase.from('player_matches').select('match_id').eq('player_id',playerId)
  ]);if(cancelled)return;const firstError=historyError??pmError;if(firstError){setError(firstError.message);setLoading(false);return}
  const matchIds=((pm??[])as PlayerMatchRow[]).map(r=>r.match_id);let matches:MatchRow[]=[];
  if(matchIds.length){const{data:matchData,error:matchError}=await supabase.from('matches').select('match_id,season_id').in('match_id',matchIds);if(cancelled)return;if(matchError){setError(matchError.message);setLoading(false);return}matches=(matchData??[])as MatchRow[]}
  const counts=new Map<number,number>();for(const match of matches){if(match.season_id==null)continue;counts.set(match.season_id,(counts.get(match.season_id)??0)+1)}
  setRows((history??[])as ShirtHistoryRow[]);setAppearanceCounts(counts);setLoading(false)})();return()=>{cancelled=true}},[playerId]);
 const seasons=useMemo(()=>{const grouped=new Map<string,SeasonHistory>();for(const row of rows){const key=`${row.season_id}:${row.fact_type}`,current=grouped.get(key)??{seasonId:row.season_id,season:row.season,factType:row.fact_type,numbers:[],records:0,appearances:appearanceCounts.get(row.season_id)??0,notes:[]};current.records+=1;if(row.shirt_number!=null&&!current.numbers.includes(row.shirt_number))current.numbers.push(row.shirt_number);if(row.notes&&!current.notes.includes(row.notes))current.notes.push(row.notes);grouped.set(key,current)}return Array.from(grouped.values()).map(r=>({...r,numbers:r.numbers.sort((a,b)=>a-b)})).sort((a,b)=>b.seasonId-a.seasonId)},[rows,appearanceCounts]);
 if(loading)return <section className="card player-profile-panel player-shirt-history"><div className="player-profile-panelhead"><div><span className="section-kicker">Leeds United Shirt Numbers</span><h2>Shirt Number History</h2></div></div><div className="lb-loading">Loading shirt numbers…</div></section>;
 if(error)return <section className="card player-profile-panel player-shirt-history"><div className="player-profile-panelhead"><div><span className="section-kicker">Leeds United Shirt Numbers</span><h2>Shirt Number History</h2></div></div><div className="lb-loading"><strong>Data connection error:</strong> {error}</div></section>;
 if(!seasons.length)return null;
 return <section className="card player-profile-panel player-shirt-history"><div className="player-profile-panelhead"><div><span className="section-kicker">Leeds United Shirt Numbers</span><h2>Shirt Number History</h2><p className="player-shirt-history-note">1991/92–1992/93 shows match-by-match numbers and match-sheet selections. From 1993/94, numbers are official seasonal squad assignments and Selections mirrors the player's appearances that season.</p></div></div><div className="lb-table-wrap"><table className="lb-table player-shirt-history-table"><thead><tr><th>Season</th><th>Number</th><th>Type</th><th className="col-stat">Selections</th></tr></thead><tbody>{seasons.map(row=><tr key={`${row.seasonId}:${row.factType}`}><td><span className="team-name">{row.season}</span></td><td><div className="player-shirt-number-list">{row.numbers.length?row.numbers.map(n=><span className="player-shirt-number" key={n}>#{n}</span>):<span className="player-shirt-number unknown">TBC</span>}</div></td><td><span className={`player-shirt-type ${row.factType==='official_squad'?'official':'match'}`}>{row.factType==='official_squad'?'Official Squad':'Match-by-Match'}</span></td><td className="col-stat player-stat-value">{row.factType==='match_worn'?row.records:row.appearances}</td></tr>)}</tbody></table></div></section>
}
