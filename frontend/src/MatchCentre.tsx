import { ArrowLeft, CalendarDays, MapPin, Users, UserRound, Shield, Clock3 } from 'lucide-react';
import type { MatchCentreSummary, MatchGoal, MatchPlayer, MatchSubstitution } from './services/matches';

type Props={summary:MatchCentreSummary;players:MatchPlayer[];goals:MatchGoal[];substitutions:MatchSubstitution[];onBack:()=>void;onOpponent:(clubId:number)=>void};
const date=(v:string)=>new Date(`${v}T00:00:00`).toLocaleDateString('en-GB',{weekday:'short',day:'numeric',month:'long',year:'numeric'});
export default function MatchCentre({summary:m,players,goals,substitutions,onBack,onOpponent}:Props){
 const starters=players.filter(p=>p.started); const bench=players.filter(p=>!p.started);
 return <main className="main match-centre">
  <button className="back-link" onClick={onBack}><ArrowLeft size={15}/> Back</button>
  <section className="match-hero">
   <div className="match-meta"><span>{m.competition ?? 'Competition'}</span><b>•</b><span>{m.season}</span>{m.round&&<><b>•</b><span>{m.round}</span></>}</div>
   <div className="match-date"><CalendarDays size={14}/>{date(m.match_date)}</div>
   <div className="scoreboard">
    <div className="team leeds"><div className="big-crest leeds-crest">LU</div><strong>Leeds United</strong><small>{m.venue_type==='H'?'Home':m.venue_type==='A'?'Away':'Neutral'}</small></div>
    <div className="score"><span>{m.leeds_score}</span><em>–</em><span>{m.opponent_score}</span><small>{m.result}</small>{m.half_time_leeds_score!=null&&<small>HT {m.half_time_leeds_score}–{m.half_time_opponent_score}</small>}</div>
    <button className="team opponent team-button" onClick={()=>onOpponent(m.opponent_id)}><div className="big-crest">{m.opponent_crest_url?<img src={m.opponent_crest_url} alt=""/>:<Shield/>}</div><strong>{m.opponent}</strong><small>Opponent centre →</small></button>
   </div>
   <div className="match-facts"><span><MapPin size={14}/>{m.stadium ?? '—'}</span><span><Users size={14}/>{m.attendance?.toLocaleString() ?? '—'}</span><span><UserRound size={14}/>{m.referee ?? '—'}</span>{m.kickoff_time&&<span><Clock3 size={14}/>{m.kickoff_time}</span>}</div>
  </section>
  <section className="match-grid">
   <article className="panel match-card"><div className="section-title"><span className="eyebrow">LEEDS UNITED</span><h2>Team</h2></div><div className="lineup-list">{starters.map((p,i)=><div className="player-row" key={p.player_id}><span className="shirt">{i+1}</span><div><strong>{p.player}</strong><small>{p.position_detail||p.position_group||'Player'}{p.captain?' · Captain':''}</small></div>{p.goals>0&&<b className="goal-count">⚽ {p.goals}</b>}</div>)}</div>{bench.length>0&&<><h3 className="subhead">Substitutes</h3><div className="bench-list">{bench.map(p=><span key={p.player_id}>{p.player}</span>)}</div></>}</article>
   <div className="match-side">
    <article className="panel match-card"><div className="section-title"><span className="eyebrow">MATCH EVENTS</span><h2>Goals & substitutions</h2></div>{goals.length===0&&substitutions.length===0?<p className="muted">No recorded Leeds events.</p>:<div className="timeline">{goals.map(g=><div className="event goal-event" key={`g${g.goal_id}`}><b>{g.minute_raw||'—'}</b><span>⚽</span><div><strong>{g.scorer||g.scorer_name_raw||'Leeds goal'}</strong>{(g.assisted_by||g.assisted_by_raw)&&<small>Assist: {g.assisted_by||g.assisted_by_raw}</small>}</div></div>)}{substitutions.map(s=><div className="event" key={`s${s.substitution_id}`}><b>{s.minute_raw||'—'}</b><span>↔</span><div><strong>{s.player_on||'Sub on'}</strong><small>for {s.player_off||'—'}</small></div></div>)}</div>}</article>
    <article className="panel match-card"><div className="section-title"><span className="eyebrow">MATCH CONTEXT</span><h2>People & details</h2></div><dl className="details"><div><dt>Leeds manager</dt><dd>{m.leeds_manager||'—'}</dd></div><div><dt>Captain</dt><dd>{m.captain||'—'}</dd></div><div><dt>Formation</dt><dd>{m.formation||'—'}</dd></div><div><dt>Opposition manager</dt><dd>{m.opposition_manager_name||'—'}</dd></div>{m.man_of_the_match&&<div><dt>Man of the match</dt><dd>{m.man_of_the_match}</dd></div>}</dl></article>
   </div>
  </section>
  {(m.match_info||m.milestones_events)&&<section className="panel match-card notes-card"><span className="eyebrow">ARCHIVE NOTES</span>{m.match_info&&<p>{m.match_info}</p>}{m.milestones_events&&<p>{m.milestones_events}</p>}</section>}
 </main>;
}
