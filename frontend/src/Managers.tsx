import React,{useEffect,useMemo,useState}from'react';
import{ArrowDown,ArrowUp,ChevronsUpDown,Search}from'lucide-react';
import{supabase,supabaseConfigError}from'./supabase';
import ManagerIcon from'./ManagerIcon';
import NationalityFlag from'./NationalityFlag';

type ManagerSpell={
  manager_spell_id:number;
  manager_id:number;
  sequence_order:number;
  manager_order:number|null;
  caretaker_label:string|null;
  manager:string;
  status:string;
  declared_nation:string|null;
  profile_image_url:string|null;
  played:number;
  won:number;
  drawn:number;
  lost:number;
  goals_for:number;
  goals_against:number;
  goal_diff:number;
  win_pct:number|string;
  loss_pct:number|string;
  first_match:string;
  last_match:string;
};
type SortKey='sequence_order'|'played'|'won'|'drawn'|'lost'|'goals_for'|'goals_against'|'goal_diff'|'win_pct'|'loss_pct'|'first_match'|'last_match';
type SortDir='asc'|'desc';
type FilterKey='All'|'League'|'Premier League'|'FA Cup'|'League Cup'|'Europe';
type VenueKey='All'|'Home'|'Away'|'Neutral';
const filters:FilterKey[]=['All','League','Premier League','FA Cup','League Cup','Europe'];
const venues:VenueKey[]=['All','Home','Away','Neutral'];

function SortIcon({active,dir}:{active:boolean;dir:SortDir}){
  return!active?<ChevronsUpDown size={12} className="col-sort-idle"/>:dir==='desc'?<ArrowDown size={12}/>:<ArrowUp size={12}/>;
}
function year(v:string|null){return v?String(new Date(`${v}T00:00:00`).getFullYear()):'-'}
function gdFill(v:number){return v>0?'win-pct-fill':v<0?'loss-pct-fill':'soft-fill'}

export default function Managers(){
  const[rows,setRows]=useState<ManagerSpell[]>([]);
  const[loading,setLoading]=useState(true);
  const[error,setError]=useState<string|null>(supabaseConfigError);
  const[search,setSearch]=useState('');
  const[sortKey,setSortKey]=useState<SortKey>('sequence_order');
  const[sortDir,setSortDir]=useState<SortDir>('desc');
  const[filter,setFilter]=useState<FilterKey>('All');
  const[venue,setVenue]=useState<VenueKey>('All');
  const[fivePlus,setFivePlus]=useState(false);

  useEffect(()=>{
    if(!supabase){setLoading(false);return}
    setLoading(true);
    setError(null);
    supabase.rpc('filtered_manager_spell_leaderboard',{p_filter:filter,p_venue:venue}).then(({data,error})=>{
      if(error)setError(error.message);else setRows((data??[])as ManagerSpell[]);
      setLoading(false);
    });
  },[filter,venue]);

  const visible=useMemo(()=>{
    const q=search.trim().toLowerCase();
    return rows.filter(r=>(!fivePlus||+r.played>=5)&&(!q||r.manager.toLowerCase().includes(q)||(r.declared_nation??'').toLowerCase().includes(q)));
  },[rows,search,fivePlus]);
  const selected=useMemo(()=>visible.reduce((n,r)=>n+Number(r.played),0),[visible]);
  const managersSelected=useMemo(()=>new Set(visible.map(r=>r.manager_id)).size,[visible]);
  const sorted=useMemo(()=>[...visible].sort((a,b)=>{
    if(sortKey==='first_match'||sortKey==='last_match'){
      const d=Date.parse(a[sortKey])-Date.parse(b[sortKey]);
      return sortDir==='asc'?d:-d;
    }
    const d=Number(a[sortKey])-Number(b[sortKey]);
    return d===0?a.sequence_order-b.sequence_order:(sortDir==='asc'?d:-d);
  }),[visible,sortKey,sortDir]);
  const max=useMemo(()=>({
    gf:Math.max(1,...visible.map(r=>+r.goals_for)),
    ga:Math.max(1,...visible.map(r=>+r.goals_against)),
    gd:Math.max(1,...visible.map(r=>Math.abs(+r.goal_diff)))
  }),[visible]);

  function toggleSort(k:SortKey){
    if(k===sortKey)setSortDir(d=>d==='asc'?'desc':'asc');
    else{setSortKey(k);setSortDir('desc')}
  }
  const heading=(l:string,k:SortKey)=><button className={`col-sort ${sortKey===k?'active':''}`} onClick={()=>toggleSort(k)}>{l}<SortIcon active={sortKey===k} dir={sortDir}/></button>;

  return <>
    <div className="card lb-table-card">
      <div className="lb-table-header">
        <div className="lb-title-group"><span className="section-kicker">Leeds United history</span><h2>Managers</h2><p>All-time Leeds United managerial record</p></div>
        <div className="section-kicker lb-match-count"><div>{loading?'…':selected.toLocaleString('en-GB')} Matches Selected</div><div>{loading?'…':managersSelected.toLocaleString('en-GB')} Managers Selected</div></div>
      </div>
      <div className="lb-filterbar">
        <div className="lb-filter-section"><span className="lb-filter-label">Competition</span><div className="lb-filter-pills">{filters.map(x=><button key={x} className={`lb-filter-pill ${filter===x?'active':''}`} onClick={()=>setFilter(x)}>{x}</button>)}</div></div>
        <div className="lb-filter-section lb-venue-section"><span className="lb-filter-label">Venue</span><div className="lb-filter-pills">{venues.map(x=><button key={x} className={`lb-filter-pill ${venue===x?'active':''}`} onClick={()=>setVenue(x)}>{x}</button>)}</div></div>
        <button className={`lb-five-toggle ${fivePlus?'active':''}`} onClick={()=>setFivePlus(v=>!v)}><span className="lb-toggle-track"><span className="lb-toggle-knob"/></span><span>+5 Matches</span></button>
        <label className="lb-search"><Search size={14}/><input value={search} onChange={e=>setSearch(e.target.value)} placeholder="Search manager"/></label>
      </div>
      {loading?<div className="lb-loading">Loading {filter.toLowerCase()} · {venue.toLowerCase()} managers from the Lufcdatabase…</div>:error?<div className="lb-loading"><strong>Data connection error:</strong> {error}</div>:<div className="lb-table-wrap">
        <table className="lb-table managers-table">
          <thead><tr>
            <th className="manager-order-col">{heading('#','sequence_order')}</th>
            <th className="manager-icon-col" aria-label="Manager icon"></th>
            <th className="manager-name-col">Manager / Coach</th>
            <th className="manager-status-col">Status</th>
            <th className="manager-nat-col">Nat</th>
            <th className="manager-nation-col">Declared Nation</th>
            <th className="col-stat">{heading('P','played')}</th>
            <th className="col-stat">{heading('W','won')}</th>
            <th className="col-stat">{heading('D','drawn')}</th>
            <th className="col-stat">{heading('L','lost')}</th>
            <th className="col-metric">{heading('GF','goals_for')}</th>
            <th className="col-metric">{heading('GA','goals_against')}</th>
            <th className="col-metric">{heading('GD','goal_diff')}</th>
            <th className="col-metric">{heading('Win %','win_pct')}</th>
            <th className="col-metric">{heading('Loss %','loss_pct')}</th>
            <th className="col-year">{heading('First Match','first_match')}</th>
            <th className="col-year">{heading('Last Match','last_match')}</th>
          </tr></thead>
          <tbody>{sorted.map(r=><tr key={r.manager_spell_id}>
            <td className="manager-order-cell"><span>{r.caretaker_label??r.manager_order}</span></td>
            <td className="manager-icon-cell"><ManagerIcon name={r.manager} src={r.profile_image_url}/></td>
            <td className="manager-name-cell"><span className="team-name">{r.manager}</span></td>
            <td className="manager-status-cell"><span className={`manager-status-pill ${r.status==='Current'?'current':'former'}`}>{r.status}</span></td>
            <td className="manager-nat-cell"><NationalityFlag nation={r.declared_nation}/></td>
            <td className="manager-nation-cell">{r.declared_nation??'—'}</td>
            <td className="col-stat">{r.played}</td>
            <td className="col-stat">{r.won}</td>
            <td className="col-stat">{r.drawn}</td>
            <td className="col-stat">{r.lost}</td>
            <td className="col-metric"><div className="metric-cell"><span className="metric-value">{r.goals_for}</span><span className="metric-track"><span className="metric-fill orange-fill" style={{width:`${+r.goals_for/max.gf*100}%`}}/></span></div></td>
            <td className="col-metric"><div className="metric-cell"><span className="metric-value">{r.goals_against}</span><span className="metric-track"><span className="metric-fill dark-fill" style={{width:`${+r.goals_against/max.ga*100}%`}}/></span></div></td>
            <td className="col-metric"><div className="metric-cell"><span className="metric-value">{r.goal_diff>0?'+':''}{r.goal_diff}</span><span className="metric-track"><span className={`metric-fill ${gdFill(+r.goal_diff)}`} style={{width:`${Math.abs(+r.goal_diff)/max.gd*100}%`}}/></span></div></td>
            <td className="col-metric"><div className="metric-cell"><span className="metric-value">{Number(r.win_pct).toFixed(1)}%</span><span className="metric-track"><span className="metric-fill win-pct-fill" style={{width:`${+r.win_pct}%`}}/></span></div></td>
            <td className="col-metric"><div className="metric-cell"><span className="metric-value">{Number(r.loss_pct).toFixed(1)}%</span><span className="metric-track"><span className="metric-fill loss-pct-fill" style={{width:`${+r.loss_pct}%`}}/></span></div></td>
            <td className="col-year metric-value">{year(r.first_match)}</td>
            <td className="col-year metric-value">{year(r.last_match)}</td>
          </tr>)}</tbody>
        </table>
        {!sorted.length&&<div className="lb-empty">No managers match these filters.</div>}
      </div>}
    </div>
    <div className="card lb-legend"><div className="lb-legend-items"><span>(C) Caretaker</span><span>P Played</span><span>W Won</span><span>D Drawn</span><span>L Lost</span><span>GF Goals For</span><span>GA Goals Against</span><span>GD Goal Difference</span></div></div>
  </>;
}
